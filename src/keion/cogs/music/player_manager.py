"""Music player manager for the music bot."""

import asyncio
import logging
import re
from urllib.parse import urlparse

import yt_dlp
from discord import FFmpegOpusAudio
from discord.ext.commands import Bot, Context

from ...utils.audio import ffmpeg_opts, youtube_dl_options
from ...utils.cache import SongCache
from ...utils.embed import EmbedBuilder
from ...utils.spotify_client import SpotifyClient
from .playlist_manager import PlaylistManager
from .voice_manager import VoiceManager

logger = logging.getLogger(__name__)


class PlayerManager:
    """Manages music playback functionality."""

    def __init__(
        self, bot: Bot, playlist_manager: PlaylistManager, voice_manager: VoiceManager
    ) -> None:
        """Initialize the player manager."""
        self.bot = bot
        self.playlist_manager = playlist_manager
        self.voice_manager = voice_manager
        self.downloader = yt_dlp.YoutubeDL(youtube_dl_options)
        self.cache = SongCache()
        self.embed_builder = EmbedBuilder()
        self.spotify_client = SpotifyClient()
        # Track text channel IDs for responding
        self.text_channels = {}

    async def get_music_info(self, query: str) -> dict:
        """Fetch music information from URL or search query."""
        logger.debug("Fetching music info for query: %s", query)
        loop = asyncio.get_event_loop()

        def is_valid_url(url: str) -> bool:
            try:
                result = urlparse(url)
                return all([result.scheme, result.netloc])
            except ValueError:
                return False

        spotify_track_pattern = r"(?:spotify:track:|https://open\.spotify\.com/(?:intl-[a-z]{2}/)?track/)([a-zA-Z0-9]+)"
        if match := re.search(spotify_track_pattern, query):
            track_id = match.group(1)
            track_info = self.spotify_client.get_track_info(track_id)
            search_query = (
                f"{track_info['name']} "
                f"{' '.join(artist['name'] for artist in track_info['artists'])}"
            )
            search = await loop.run_in_executor(
                None, self.downloader.extract_info, f"ytsearch1:{search_query}", False
            )
            info = search["entries"][0]
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

    async def play_song(self, guild_id_or_ctx: int | Context, song_info: dict) -> bool:
        """Play a song in the voice channel.

        Args:
            guild_id_or_ctx: Either guild ID or command Context
            song_info: Song information dictionary

        Returns:
            True if playback started
        """
        # Extract guild ID and save text channel for responses
        if isinstance(guild_id_or_ctx, Context):
            guild_id = guild_id_or_ctx.guild.id
            # Store the text channel for future use
            self.voice_manager.text_channels[guild_id] = guild_id_or_ctx.channel.id
            text_channel = guild_id_or_ctx.channel
        else:
            guild_id = guild_id_or_ctx
            text_channel_id = self.voice_manager.text_channels.get(guild_id)
            text_channel = (
                self.bot.get_channel(text_channel_id) if text_channel_id else None
            )

        logger.info(
            "Playing song: %s in guild: %s",
            song_info.get("title", "Unknown"),
            (
                self.bot.get_guild(guild_id).name
                if self.bot.get_guild(guild_id)
                else "Unknown"
            ),
        )
        url = song_info["url"]
        self.playlist_manager.current_song = song_info

        audio_source = FFmpegOpusAudio(url, **ffmpeg_opts)
        voice_client = self.voice_manager.voice_clients[guild_id]

        # Set up the after function to handle when a song finishes
        def after_playing(error):
            if error:
                logger.error(f"Error playing song: {error}")
                return

            # Get the next song and play it
            asyncio.run_coroutine_threadsafe(
                self._handle_song_finished(guild_id), self.bot.loop
            )

        # Start playing with the callback
        voice_client.play(audio_source, after=after_playing)

        embed = self.embed_builder.now_playing(song_info)

        # Send to appropriate text channel if available
        if text_channel:
            await text_channel.send(embed=embed)

        return True

    async def _handle_song_finished(self, guild_id: int) -> None:
        """Handle song completion and start the next song if available."""
        # Get next song from playlist manager
        next_song = self.playlist_manager.song_finished()

        if next_song:
            logger.info(f"Song finished, playing next: {next_song.get('title')}")
            await self.play_song(guild_id, next_song)
        else:
            logger.info("No more songs in queue")
            # Optionally disconnect after some idle time
            await self.voice_manager.start_inactivity_timer(guild_id)

    async def play_next(self, context: Context, error: Exception | None = None) -> None:
        """Handle playing the next song in queue."""
        if error:
            logger.error("Error during playback: %s", str(error), exc_info=error)

        if next_song := self.playlist_manager.get_next_song():
            await self.play_song(context.guild.id, next_song)
        else:
            # Start the inactivity timer instead of disconnecting immediately
            await self.voice_manager.start_inactivity_timer(context.guild.id)
