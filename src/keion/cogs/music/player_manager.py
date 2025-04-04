"""Music player manager for the music bot."""

import logging
import asyncio
import re
from typing import Optional
import yt_dlp
from urllib.parse import urlparse
from discord import FFmpegOpusAudio, VoiceState, Member
from discord.ext.commands import Context, Bot

from ...utils.cache import SongCache
from ...utils.embed import EmbedBuilder
from ...utils.audio import youtube_dl_options, ffmpeg_opts
from ...utils.spotify_client import SpotifyClient
from .playlist_manager import PlaylistManager
from .voice_manager import VoiceManager

logger = logging.getLogger(__name__)

class PlayerManager:
    """Manages music playback functionality."""

    def __init__(self, bot: Bot, playlist_manager: PlaylistManager, voice_manager: VoiceManager) -> None:
        """Initialize the player manager."""
        self.bot = bot
        self.playlist_manager = playlist_manager
        self.voice_manager = voice_manager
        self.downloader = yt_dlp.YoutubeDL(youtube_dl_options)
        self.cache = SongCache()
        self.embed_builder = EmbedBuilder()
        self.spotify_client = SpotifyClient()

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

        spotify_track_pattern = (
            r"(?:spotify:track:|https://open\.spotify\.com/(?:intl-[a-z]{2}/)?track/)([a-zA-Z0-9]+)"
        )
        if match := re.search(spotify_track_pattern, query):
            track_id = match.group(1)
            track_info = self.spotify_client.get_track_info(track_id)
            search_query = f"{track_info['name']} {' '.join(artist['name'] for artist in track_info['artists'])}"
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

    async def play_song(self, context: Context, song_info: dict) -> None:
        """Play a song in the voice channel."""
        logger.info("Playing song: %s in guild: %s", 
                   song_info.get('title', 'Unknown'), 
                   context.guild.name if context.guild else 'Unknown')
        url = song_info["url"]
        self.playlist_manager.current_song = song_info

        audio_stream = FFmpegOpusAudio(url, **ffmpeg_opts)
        self.voice_manager.voice_clients[context.guild.id].play(
            audio_stream, after=lambda error: self.play_next(context, error)
        )

        embed = self.embed_builder.now_playing(song_info)
        await context.send(embed=embed)

    async def play_next(self, context: Context, error: Optional[Exception] = None) -> None:
        """Handle playing the next song in queue."""
        if error:
            logger.error("Error during playback: %s", str(error), exc_info=error)

        if next_song := self.playlist_manager.get_next_song():
            await self.play_song(context, next_song)
        else:
            # Start the inactivity timer instead of disconnecting immediately
            await self.voice_manager.start_inactivity_timer(context.guild.id)