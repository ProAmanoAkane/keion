"""Music playback cog implementation."""

import logging

from discord import Color, Embed, Member, VoiceState
from discord.ext import commands
from discord.ext.commands import Context

from keion.utils.constants import MAX_PLAYLIST_DISPLAY
from keion.utils.musicbrainz_client import MusicBrainzClient  # Import the client

from .player_manager import PlayerManager
from .playlist_manager import PlaylistManager
from .voice_manager import VoiceManager

logger = logging.getLogger(__name__)


class MusicCog(commands.Cog):
    """A Discord cog that provides music playback functionality."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the music cog."""
        self.bot = bot
        self.playlist_manager = PlaylistManager()
        self.voice_manager = VoiceManager()
        self.player_manager = PlayerManager(
            bot, self.playlist_manager, self.voice_manager
        )
        self.musicbrainz_client = MusicBrainzClient()  # Initialize the client
        logger.info("Music cog initialized")

    async def cog_unload(self) -> None:
        """Clean up resources when the cog is unloaded."""
        # Close the MusicBrainz client's session if it exists
        await self.musicbrainz_client.close_session()
        logger.info("MusicBrainz client session closed.")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Event handler for when the bot is ready."""
        logger.info("Music module ready for bot: %s", self.bot.user)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: Member, before: VoiceState, after: VoiceState
    ) -> None:
        """Handle voice state updates."""
        await self.voice_manager.handle_voice_state_update(member, before, after)

    @commands.command()
    async def play(self, context: Context, *, query: str) -> None:
        """Play a song from URL or search query."""
        info = await self.player_manager.get_music_info(query)
        self.playlist_manager.add_to_queue(info)

        # Get the voice client using guild ID
        voice_client = self.voice_manager.voice_clients.get(context.guild.id)

        if voice_client and not voice_client.is_playing():
            next_song = self.playlist_manager.get_next_song()
            await self.player_manager.play_song(context, next_song)
        else:
            embed = Embed(title="🎵 Added to Queue", color=Color.green())
            embed.add_field(
                name=info["title"],
                value=f"Position: #{len(self.playlist_manager.playlist)}",
                inline=False,
            )
            await context.send(embed=embed)

    @commands.command()
    async def skip(self, context: Context) -> None:
        """Skip the currently playing song."""
        if (
            context.guild.id in self.voice_manager.voice_clients
            and self.voice_manager.voice_clients[context.guild.id].is_playing()
        ):
            self.voice_manager.voice_clients[context.guild.id].stop()
            # Force next song to be from queue if available
            next_song = self.playlist_manager.skip_current()
            if next_song:
                await self.player_manager.play_song(context, next_song)
            await context.send("⏭️ Skipped the current song!")
        else:
            await context.send("❌ No song is currently playing!")

    @commands.command()
    async def pause(self, context: Context) -> None:
        """Pause the current playback."""
        if (
            context.guild.id in self.voice_manager.voice_clients
            and self.voice_manager.voice_clients[context.guild.id].is_playing()
        ):
            self.voice_manager.voice_clients[context.guild.id].pause()
        else:
            await context.send("❌ Nothing to pause!")

    @commands.command()
    async def resume(self, context: Context) -> None:
        """Resume paused playback."""
        if (
            context.guild.id in self.voice_manager.voice_clients
            and self.voice_manager.voice_clients[context.guild.id].is_paused()
        ):
            self.voice_manager.voice_clients[context.guild.id].resume()
        else:
            await context.send("❌ Nothing to resume!")

    @commands.command()
    async def stop(self, context: Context) -> None:
        """Stop playback and clear the queue."""
        if context.guild.id in self.voice_manager.voice_clients:
            self.playlist_manager.clear_queue()
            await self.voice_manager.disconnect(context.guild.id)

    @commands.command()
    async def queue(self, context: Context) -> None:
        """Display the current queue and loop status."""
        if (
            not self.playlist_manager.playlist
            and not self.playlist_manager.current_song
        ):
            await context.send("📝 The queue is empty!")
            return

        embed = Embed(title="📝 Current Queue", color=Color.blue())

        # Show current song
        if self.playlist_manager.current_song:
            embed.add_field(
                name="🎵 Now Playing",
                value=f"{self.playlist_manager.current_song['title']}",
                inline=False,
            )

        # Show queue
        for i, song in enumerate(self.playlist_manager.playlist[:10], 1):
            embed.add_field(
                name=f"{i}. {song['title']}",
                value=f"Duration: {song.get('duration', '??:??')}",
                inline=False,
            )

        # Show remaining count
        if len(self.playlist_manager.playlist) > MAX_PLAYLIST_DISPLAY:
            embed.set_footer(
                text=f"And {len(self.playlist_manager.playlist) - 10} more songs..."
            )

        # Show loop status
        loop_status = (
            "🔁 Queue"
            if self.playlist_manager.loop_queue
            else "🔂 Song" if self.playlist_manager.loop_song else "❌ Off"
        )
        embed.add_field(name="Loop Status", value=loop_status, inline=False)

        await context.send(embed=embed)

    @commands.command()
    async def loop(self, context: Context, mode: str = "queue") -> None:
        """Toggle loop mode for queue or current song."""
        if mode == "queue":
            is_enabled = self.playlist_manager.toggle_loop_queue()
            await context.send(
                f"🔁 Queue loop {'enabled' if is_enabled else 'disabled'}!"
            )
        elif mode == "song":
            is_enabled = self.playlist_manager.toggle_loop_song()
            await context.send(
                f"🔂 Song loop {'enabled' if is_enabled else 'disabled'}!"
            )
        else:
            await context.send("❌ Invalid loop mode. Use 'queue' or 'song'!")

    @commands.command(aliases=["new"])
    async def newreleases(self, context: Context, days: int = 1) -> None:
        """Show new music releases from the last few days (default: 1)."""
        if days < 1 or days > 7:  # Limit range for performance/API usage
            await context.send("Please specify a number of days between 1 and 7.")
            return

        await context.typing()  # Indicate bot is working

        try:
            # Fetch releases using the client
            releases = await self.musicbrainz_client.get_daily_releases(days_ago=days)

            if not releases:
                await context.send(
                    f"Couldn't find any new releases from the last {days} day(s)."
                )
                return

            embed = Embed(
                title=f"🎸 New Releases ({days} Day{'s' if days > 1 else ''} Ago)",
                color=Color.random(),  # Use a random color
            )

            output = []
            for release in releases[:10]:  # Limit to 10 results for embed readability
                title = release.get("title", "Unknown Title")
                artist_credit = release.get("artist-credit-phrase", "Unknown Artist")
                date = release.get("date", "Unknown Date")
                output.append(f"**{title}** by {artist_credit} ({date})")

            embed.description = "\n".join(output)
            if len(releases) > 10:
                embed.set_footer(text=f"Showing 10 of {len(releases)} results.")

            await context.send(embed=embed)

        except Exception as e:
            logger.error(f"Error fetching new releases: {e}", exc_info=True)
            await context.send("An error occurred while fetching new releases.")

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
        await self.voice_manager.ensure_voice(context)
