"""Playlist manager for the music bot."""

import logging
from collections.abc import Callable

from discord import Color, Embed
from discord.ext.commands import Context

from ...utils.constants import MAX_PLAYLIST_DISPLAY

logger = logging.getLogger(__name__)


class PlaylistManager:
    """Manages the music playlist and queue."""

    def __init__(self) -> None:
        """Initialize the playlist manager."""
        self.playlist: list[dict] = []
        self.backup: list[dict] = []
        self.current_song: dict | None = None
        self.loop_queue = False
        self.loop_song = False
        self._song_ended_callbacks: list[Callable] = []

    def add_to_queue(self, song_info: dict) -> None:
        """Add a song to the playlist."""
        self.playlist.append(song_info)
        # Log addition to verify queue state
        logger.debug(
            f"Added song to queue: {song_info.get('title')}. Queue size: {len(self.playlist)}"
        )

    def clear_queue(self) -> None:
        """Clear the playlist."""
        self.playlist.clear()
        self.backup.clear()
        self.current_song = None
        logger.debug("Queue cleared")

    def register_song_ended_callback(self, callback: Callable) -> None:
        """Register a callback for when a song ends to trigger next song."""
        self._song_ended_callbacks.append(callback)

    def song_finished(self) -> dict | None:
        """Called when a song has finished playing naturally."""
        # If we're looping the current song, just return it again
        if self.loop_song and self.current_song:
            logger.debug("Song loop enabled, replaying current song")
            return self.current_song

        # Otherwise get the next song from the queue
        next_song = self.get_next_song()
        if next_song:
            logger.debug(f"Song finished, next song: {next_song.get('title')}")
        else:
            logger.debug("Song finished, no next song in queue")

        return next_song

    def get_next_song(self) -> dict | None:
        """Get the next song from the playlist."""
        # Handle empty playlist
        if not self.playlist:
            if self.loop_queue and self.backup:
                logger.debug("Queue empty but loop enabled, restoring from backup")
                self.playlist = self.backup.copy()
            elif self.loop_queue and self.current_song:
                # If queue is empty but loop is enabled and we have a current song
                logger.debug("Queue empty with loop enabled, adding current song back")
                self.playlist = [self.current_song]
            else:
                logger.debug("Queue empty, no song to play")
                self.current_song = None
                return None

        # Get next song
        next_song = self.playlist.pop(0)
        logger.debug(
            f"Getting next song: {next_song.get('title')}. Remaining queue: {len(self.playlist)}"
        )

        # Add song to backup if queue loop is enabled
        if self.loop_queue and next_song not in self.backup:
            self.backup.append(next_song)
            logger.debug(f"Added to backup queue: {next_song.get('title')}")

        # Update current song reference
        self.current_song = next_song
        return next_song

    def skip_current(self) -> dict | None:
        """Skip the current song and return next song."""
        logger.debug("Skip requested")
        # If loop song is enabled, disable it and continue with next song
        if self.loop_song:
            self.loop_song = False
            logger.debug("Song loop disabled on skip")

        # If there are songs in queue, prioritize them over loop
        if self.playlist:
            return self.get_next_song()

        # If queue is empty but loop is enabled
        if self.loop_queue:
            self.playlist = self.backup.copy()
            if self.current_song in self.playlist:
                self.playlist.remove(self.current_song)
            return self.get_next_song()

        # Clear current song reference if we're not getting a new song
        self.current_song = None
        return None

    def toggle_loop_queue(self) -> bool:
        """Toggle queue loop and update backup."""
        self.loop_queue = not self.loop_queue
        self.loop_song = False
        logger.debug(f"Queue loop {'enabled' if self.loop_queue else 'disabled'}")

        if self.loop_queue:
            # Create backup including current song
            self.backup = self.playlist.copy()
            if self.current_song and self.current_song not in self.backup:
                self.backup.append(self.current_song)
                logger.debug(f"Created backup queue with {len(self.backup)} songs")
        else:
            self.backup.clear()
            logger.debug("Cleared backup queue")

        return self.loop_queue

    def toggle_loop_song(self) -> bool:
        """Toggle song loop."""
        self.loop_song = not self.loop_song
        self.loop_queue = False
        logger.debug(f"Song loop {'enabled' if self.loop_song else 'disabled'}")
        return self.loop_song

    def get_queue_songs(self) -> list[dict]:
        """Get all songs in queue (without modifying the queue)."""
        return self.playlist.copy()

    async def show_queue(self, context: Context) -> None:
        """Display the current playlist."""
        if not self.playlist:
            await context.send("📝 The queue is empty!")
            return

        embed = Embed(title="📝 Current Queue", color=Color.blue())
        for i, song in enumerate(self.playlist[:MAX_PLAYLIST_DISPLAY], 1):
            embed.add_field(
                name=f"{i}. {song['title']}",
                value=f"Duration: {song.get('duration', '??:??')}",
                inline=False,
            )

        if len(self.playlist) > MAX_PLAYLIST_DISPLAY:
            embed.set_footer(
                text=f"And {len(self.playlist) - MAX_PLAYLIST_DISPLAY} more songs..."
            )

        await context.send(embed=embed)

    def generate_search_query(self, track_info: dict) -> str:
        """Generate a search query from track information."""
        search_query = (
            f"{track_info['name']} "
            f"{' '.join(artist['name'] for artist in track_info['artists'])}"
        )
        return search_query
