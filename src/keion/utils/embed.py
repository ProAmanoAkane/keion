"""Discord embed builders for the music bot."""

import json
import logging
import random
from pathlib import Path

from discord import Color, Embed

logger = logging.getLogger(__name__)


class EmbedBuilder:
    """Builder class for Discord embeds with consistent styling."""

    def __init__(self):
        """Load message templates from resources."""
        messages_path = Path(__file__).parent.parent / "resources" / "messages.json"
        try:
            with open(messages_path) as f:
                self.messages = json.load(f)
            logger.info("Loaded message templates from %s", messages_path)
        except Exception as e:
            logger.error("Failed to load message templates: %s", str(e))
            raise

    def now_playing(self, song_info: dict) -> Embed:
        """Create a Now Playing embed."""
        title = song_info["title"]
        url = song_info.get("webpage_url", song_info.get("url", ""))

        embed = Embed(
            title=title,  # Plain title
            description=f"[View on YouTube]({url})",  # Link in description
            color=Color.purple(),
        )

        # Use Spotify metadata if available
        if spotify_meta := song_info.get("spotify_metadata"):
            artist = ", ".join(artist["name"] for artist in spotify_meta["artists"])
            thumbnail_url = (
                spotify_meta["album"]["images"][0]["url"]
                if spotify_meta["album"]["images"]
                else None
            )
        else:
            artist = song_info.get("artist") or song_info.get(
                "uploader", "Unknown Artist"
            )
            thumbnail_url = song_info.get("thumbnail")

        duration = song_info.get("duration")
        duration_str = self._format_duration(duration)

        # Add a field with artist and duration
        embed.add_field(
            name="Artist:",
            value=f"🎤 {artist}\n⏱️ Duration: {duration_str}",
            inline=False,
        )

        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)

        # Add a random footer
        embed.set_footer(text=random.choice(self.messages["footers"]))
        return embed

    @staticmethod
    def _format_duration(duration: int) -> str:
        """Format duration in seconds to MM:SS string."""
        if not duration:
            return "??:??"
        minutes, seconds = divmod(duration, 60)
        return f"{minutes:02d}:{seconds:02d}"
