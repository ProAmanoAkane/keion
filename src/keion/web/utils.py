"""Utility functions for web interface."""

import collections
from datetime import UTC, datetime  # Added timezone
from typing import Any

from fastapi import Request, WebSocket

# Adjust import path based on your project structure
from ..cogs.music import MusicCog


def format_uptime(start_time: datetime) -> str:
    """Format uptime from bot start_time to human readable string."""
    if not start_time:
        return "N/A"

    # Ensure start_time is timezone-aware (assume UTC if not)
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=UTC)

    now = datetime.now(UTC)
    uptime_seconds = (now - start_time).total_seconds()

    days = int(uptime_seconds // (3600 * 24))
    hours = int((uptime_seconds % (3600 * 24)) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes >= 0:  # Always show minutes unless uptime is 0
        # Show seconds if uptime is less than a minute
        if days == 0 and hours == 0 and minutes == 0:
            seconds = int(uptime_seconds % 60)
            return f"{seconds}s"
        parts.append(f"{minutes}m")

    return " ".join(parts) if parts else "0m"


async def get_stats(req_or_ws: Request | WebSocket) -> dict[str, Any]:
    """Get bot statistics.

    Args:
        req_or_ws: FastAPI Request or WebSocket object

    Returns:
        Dictionary containing bot statistics
    """
    # Get bot instance from app state
    bot = req_or_ws.app.state.bot
    music_cog: MusicCog = bot.get_cog("MusicCog")

    if not music_cog:
        # Handle case where cog might not be loaded
        return {
            "servers": len(bot.guilds),
            "active_voice": 0,
            "total_songs": 0,  # Or indicate cog unavailable
            "uptime": format_uptime(getattr(bot, "start_time", None)),
            "error": "Music Cog not loaded",
        }

    # Calculate uptime using start_time attribute
    start_time = getattr(bot, "start_time", None)  # Use None if not set
    uptime_str = format_uptime(start_time)

    # Assuming a global playlist for total_songs. Adapt if per-guild.
    total_songs_in_queues = 0
    if hasattr(music_cog.playlist_manager, "get_total_queued_count"):
        total_songs_in_queues = music_cog.playlist_manager.get_total_queued_count()
    elif hasattr(music_cog.playlist_manager, "playlist"):
        # Fallback: Check if it's a single global queue (like deque)
        if isinstance(
            music_cog.playlist_manager.playlist, (list | type(collections.deque()))
        ):
            total_songs_in_queues = len(music_cog.playlist_manager.playlist)

    return {
        "servers": len(bot.guilds),
        "active_voice": len(music_cog.voice_manager.voice_clients),
        "total_songs": total_songs_in_queues,  # Sum of songs across all queues
        "uptime": uptime_str,
    }


async def get_players(req_or_ws: Request | WebSocket) -> list[dict[str, Any]]:
    """Get all active music players, including their full playlists."""
    bot = req_or_ws.app.state.bot
    music_cog: MusicCog = bot.get_cog("MusicCog")

    if not music_cog:
        return []  # Return empty list if cog is not available

    players = []
    for guild_id, voice_client in music_cog.voice_manager.voice_clients.items():
        guild = bot.get_guild(guild_id)
        if guild and voice_client.is_connected():
            # Get current song
            current_song = music_cog.playlist_manager.current_song

            # Get playlist - ensure it returns a serializable format
            playlist = []
            for (
                song
            ) in music_cog.playlist_manager.get_queue_songs():  # Use the new method
                if isinstance(song, dict):
                    playlist.append(
                        {
                            "title": song.get("title", "Unknown"),
                            "duration": song.get("duration", 0),
                            "requester": song.get("requester", "Unknown"),
                        }
                    )

            players.append(
                {
                    "guild_name": guild.name,
                    "guild_id": guild_id,
                    "current_song_title": (
                        current_song.get("title", "Unknown") if current_song else None
                    ),
                    "playlist": playlist,
                    "queue_length": len(playlist),
                    "is_playing": voice_client.is_playing(),
                    "is_paused": voice_client.is_paused(),
                }
            )

    return players
