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
        self.playlist_backup: List[Dict] = []
        self.current_song: Optional[Dict] = None
        self.loop_queue = False
        self.loop_song = False

    def add_to_queue(self, song_info: Dict) -> None:
        """Add a song to the playlist."""
        self.playlist.append(song_info)

    def clear_queue(self) -> None:
        """Clear the playlist."""
        self.playlist.clear()
        self.current_song = None

    def get_next_song(self) -> Optional[Dict]:
        """Get the next song from the playlist."""
        if self.loop_song and self.current_song:
            return self.current_song

        if self.playlist:
            return self.playlist.pop(0)
        elif self.loop_queue:
            self.playlist = self.playlist_backup.copy()
            return self.get_next_song() if self.playlist else None
        return None

    def backup_playlist(self) -> None:
        """Create a backup of the current playlist."""
        self.playlist_backup = self.playlist.copy()

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