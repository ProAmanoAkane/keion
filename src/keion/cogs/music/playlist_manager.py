"""Playlist manager for the music bot."""

import logging
from typing import List, Dict, Optional
from discord.ext.commands import Context
from discord import Embed, Color

logger = logging.getLogger(__name__)


class PlaylistManager:
    """Manages the music playlist and queue."""

    def __init__(self) -> None:
        """Initialize the playlist manager."""
        self.playlist: List[Dict] = []
        self.backup: List[Dict] = []
        self.current_song: Optional[Dict] = None
        self.loop_queue = False
        self.loop_song = False

    def add_to_queue(self, song_info: Dict) -> None:
        """Add a song to the playlist."""
        self.playlist.append(song_info)

    def clear_queue(self) -> None:
        """Clear the playlist."""
        self.playlist.clear()
        self.backup.clear()
        self.current_song = None

    def get_next_song(self) -> Optional[Dict]:
        """Get the next song from the playlist."""
        # Handle empty playlist
        if not self.playlist:
            if self.loop_queue and self.backup:
                self.playlist = self.backup.copy()
            elif self.loop_queue and self.current_song:
                # If queue is empty but loop is enabled and we have a current song
                self.playlist = [self.current_song]
            else:
                self.current_song = None
                return None

        # Get next song
        next_song = self.playlist.pop(0)

        # Add song to backup if queue loop is enabled
        if self.loop_queue and next_song not in self.backup:
            self.backup.append(next_song)

        self.current_song = next_song
        return next_song

    def skip_current(self) -> Optional[Dict]:
        """Skip the current song and return next song."""
        # If there are songs in queue, prioritize them over loop
        if self.playlist:
            return self.get_next_song()

        # If queue is empty but loop is enabled
        if self.loop_queue:
            self.playlist = self.backup.copy()
            if self.current_song in self.playlist:
                self.playlist.remove(self.current_song)
            return self.get_next_song()

        return None

    def toggle_loop_queue(self) -> bool:
        """Toggle queue loop and update backup."""
        self.loop_queue = not self.loop_queue
        self.loop_song = False

        if self.loop_queue:
            # Create backup including current song
            self.backup = self.playlist.copy()
            if self.current_song and self.current_song not in self.backup:
                self.backup.append(self.current_song)
        else:
            self.backup.clear()

        return self.loop_queue

    def toggle_loop_song(self) -> bool:
        """Toggle song loop."""
        self.loop_song = not self.loop_song
        self.loop_queue = False
        return self.loop_song

    async def show_queue(self, context: Context) -> None:
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
