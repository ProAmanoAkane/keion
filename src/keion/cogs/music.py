"""Music player cog for the Discord bot."""

import asyncio
from typing import Optional
import yt_dlp
from urllib.parse import urlparse
from discord.ext import commands
from discord.ext.commands import Context
from discord import FFmpegOpusAudio, VoiceClient, Embed, Color
import re

from ..utils.cache import SongCache
from ..utils.embed import EmbedBuilder
from ..utils.audio import youtube_dl_options, ffmpeg_opts
from ..utils.spotify_client import SpotifyClient


class MusicCog(commands.Cog):
    """A Discord cog that provides music playback functionality."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the music cog."""
        self.bot = bot
        self.downloader = yt_dlp.YoutubeDL(youtube_dl_options)
        self.voice_clients: dict[int, VoiceClient] = {}
        self.playlist: list[dict] = []
        self.loop_queue = False
        self.loop_song = False
        self.current_song: Optional[dict] = None
        self.playlist_backup: list[dict] = []

        # Initialize utilities
        self.cache = SongCache()
        self.embed_builder = EmbedBuilder()
        self.spotify_client = SpotifyClient()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Event handler for when the bot is ready."""
        print(f"Music module initialized for {self.bot.user}!")

    # Core functionality methods
    async def get_music_info(self, query: str) -> dict:
        """Fetch music information from URL or search query."""
        loop = asyncio.get_event_loop()

        def is_valid_url(url: str) -> bool:
            try:
                result = urlparse(url)
                return all([result.scheme, result.netloc])
            except ValueError:
                return False

        # Add Spotify track URL handling
        spotify_track_pattern = (
            r"(?:spotify:track:|https://open\.spotify\.com/(?:intl-[a-z]{2}/)?track/)([a-zA-Z0-9]+)"
        )
        if match := re.search(spotify_track_pattern, query):
            track_id = match.group(1)
            track_info = self.spotify_client.get_track_info(track_id)

            print(f"Spotify track info: {track_info}")

            # Format search query for YouTube
            search_query = f"{track_info['name']} {' '.join(artist['name'] for artist in track_info['artists'])}"

            # Use the existing YouTube search functionality 
            search = await loop.run_in_executor(
                None, self.downloader.extract_info, f"ytsearch1:{search_query}", False
            )

            info = search["entries"][0]
            # Add Spotify metadata
            info["spotify_metadata"] = track_info
            return info
        
        if is_valid_url(query) and (cached_info := self.cache.get(query)):
            return cached_info

        if is_valid_url(query):
            info = await loop.run_in_executor(
                None, self.downloader.extract_info, query, False
            )
        else:
            search = await loop.run_in_executor(
                None, self.downloader.extract_info, f"ytsearch1:{query}", False
            )
            info = search["entries"][0]

        self.cache.add(info["webpage_url"], info)
        return info

    async def play_song(self, context: Context, song_info: dict) -> None:
        """Play a song in the voice channel."""
        url = song_info["url"]
        self.current_song = song_info

        audio_stream = FFmpegOpusAudio(url, **ffmpeg_opts)
        self.voice_clients[context.guild.id].play(
            audio_stream, after=lambda error: self.play_next(context, error)
        )

        embed = self.embed_builder.now_playing(song_info)
        await context.send(embed=embed)

    def play_next(self, context: Context, error: Exception = None) -> None:
        """Handle playing the next song in queue."""
        if error:
            print(f"Playback error: {error}")

        if self.loop_song and self.current_song:
            asyncio.run_coroutine_threadsafe(
                self.play_song(context, self.current_song), self.bot.loop
            )
            return

        if self.playlist:
            next_song = self.playlist.pop(0)
            asyncio.run_coroutine_threadsafe(
                self.play_song(context, next_song), self.bot.loop
            )
        elif self.loop_queue:
            self.playlist = self.playlist_backup.copy()
            self.play_next(context)
        else:
            asyncio.run_coroutine_threadsafe(
                self.voice_clients[context.guild.id].disconnect(), self.bot.loop
            )

    # Command implementations
    @commands.command()
    async def play(self, context: Context, *, query: str) -> None:
        """Play a song from URL or search query."""
        info = await self.get_music_info(query)
        self.playlist.append(info)

        if not self.voice_clients[context.guild.id].is_playing():
            await self.play_song(context, self.playlist.pop(0))
        else:
            embed = Embed(title="🎵 Added to Queue", color=Color.green())
            embed.add_field(
                name=info["title"],
                value=f"Position: #{len(self.playlist)}",
                inline=False,
            )
            await context.send(embed=embed)

    @commands.command()
    async def skip(self, context: Context) -> None:
        """Skip the currently playing song."""
        if (
            context.guild.id in self.voice_clients
            and self.voice_clients[context.guild.id].is_playing()
        ):
            self.voice_clients[context.guild.id].stop()
            await context.send("⏭️ Skipped the current song!")
        else:
            await context.send("❌ No song is currently playing!")

    @commands.command()
    async def pause(self, context: Context) -> None:
        """Pause the current playback."""
        if (
            context.guild.id in self.voice_clients
            and self.voice_clients[context.guild.id].is_playing()
        ):
            self.voice_clients[context.guild.id].pause()
        else:
            await context.send("❌ Nothing to pause!")

    @commands.command()
    async def resume(self, context: Context) -> None:
        """Resume paused playback."""
        if (
            context.guild.id in self.voice_clients
            and self.voice_clients[context.guild.id].is_paused()
        ):
            self.voice_clients[context.guild.id].resume()
        else:
            await context.send("❌ Nothing to resume!")

    @commands.command()
    async def stop(self, context: Context) -> None:
        """Stop playback and clear the queue."""
        if context.guild.id in self.voice_clients:
            self.playlist.clear()
            self.current_song = None
            await self.voice_clients[context.guild.id].disconnect()
            del self.voice_clients[context.guild.id]

    @commands.command()
    async def queue(self, context: Context) -> None:
        """Display the current playlist."""
        if not self.playlist:
            await context.send("📝 The queue is empty!")
            return

        embed = Embed(title="📝 Current Queue", color=Color.blue())
        for i, song in enumerate(self.playlist[:10], 1):
            embed.add_field(
                name=f"{i}. {song['title']}",
                value=f"Duration: {song.get('duration', '??:??')}",
                inline=False,
            )

        if len(self.playlist) > 10:
            embed.set_footer(text=f"And {len(self.playlist) - 10} more songs...")

        await context.send(embed=embed)

    @commands.command()
    async def loop(self, context: Context, mode: str = "queue") -> None:
        """Toggle loop mode for queue or current song."""
        if mode == "queue":
            self.loop_queue = not self.loop_queue
            self.loop_song = False
            await context.send(
                f"🔁 Queue loop {'enabled' if self.loop_queue else 'disabled'}!"
            )
            self.playlist_backup = self.playlist.copy()
        elif mode == "song":
            self.loop_song = not self.loop_song
            self.loop_queue = False
            await context.send(
                f"🔂 Song loop {'enabled' if self.loop_song else 'disabled'}!"
            )
        else:
            await context.send("❌ Invalid loop mode. Use 'queue' or 'song'!")

    # Voice state management
    @play.before_invoke
    @skip.before_invoke
    @pause.before_invoke
    @resume.before_invoke
    @stop.before_invoke
    @queue.before_invoke
    @loop.before_invoke
    async def ensure_voice(self, context: Context) -> None:
        """Ensure proper voice channel connection."""
        if context.voice_client is None:
            if context.author.voice:
                self.voice_clients[context.guild.id] = (
                    await context.author.voice.channel.connect()
                )
            else:
                raise commands.CommandError("You must be in a voice channel!")
        elif context.voice_client.channel != context.author.voice.channel:
            raise commands.CommandError(
                "You must be in the same voice channel as the bot!"
            )
