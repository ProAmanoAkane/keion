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
    """Get all active music players, including their full playlists.

    Args:
        req_or_ws: FastAPI Request or WebSocket object

    Returns:
        List of dictionaries containing player information and playlists
    """
    bot = req_or_ws.app.state.bot
    music_cog: MusicCog = bot.get_cog("MusicCog")

    if not music_cog:
        return []  # Return empty list if cog is not available

    players = []
    for guild_id, voice_client in music_cog.voice_manager.voice_clients.items():
        guild = bot.get_guild(guild_id)
        if guild and voice_client.is_connected():
            # --- Adapt how you get current_song and playlist based on your Manager ---
            # Example: If PlaylistManager handles multiple guilds via methods
            current_song = None
            playlist = []
            if hasattr(music_cog.playlist_manager, "get_current_song"):
                current_song = music_cog.playlist_manager.get_current_song(guild_id)
            if hasattr(music_cog.playlist_manager, "get_queue"):
                playlist = list(
                    music_cog.playlist_manager.get_queue(guild_id)
                )  # Get a copy

            serializable_playlist = []
            for song in playlist:
                if isinstance(song, dict):
                    serializable_playlist.append(
                        {
                            "title": song.get("title", "Unknown Title"),
                            "requester": song.get("requester", "Unknown"),
                            "duration": song.get("duration", 0),  # Example field
                            # Add other relevant fields: url, thumbnail etc.
                        }
                    )
                # Add elif for specific object types if needed

            players.append(
                {
                    "guild_name": guild.name,
                    "guild_id": guild_id,
                    # Ensure current_song is also serializable or just get title
                    "current_song_title": (
                        current_song.get("title")
                        if current_song and isinstance(current_song, dict)
                        else None
                    ),
                    "playlist": serializable_playlist,  # Use the processed list
                    "queue_length": len(serializable_playlist),
                    "is_playing": voice_client.is_playing(),
                    "is_paused": voice_client.is_paused(),
                }
            )

    return players
