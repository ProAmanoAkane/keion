"""Music playback cog implementation."""

import logging
from discord.ext import commands
from discord.ext.commands import Context
from discord import Embed, Color

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
        self.player_manager = PlayerManager(bot, self.playlist_manager, self.voice_manager)
        logger.info("Music cog initialized")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Event handler for when the bot is ready."""
        logger.info("Music module ready for bot: %s", self.bot.user)

    @commands.command()
    async def play(self, context: Context, *, query: str) -> None:
        """Play a song from URL or search query."""
        info = await self.player_manager.get_music_info(query)
        self.playlist_manager.add_to_queue(info)

        if not self.voice_manager.voice_clients[context.guild.id].is_playing():
            await self.player_manager.play_song(context, self.playlist_manager.get_next_song())
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
        """Display the current playlist."""
        await self.playlist_manager.show_queue(context)

    @commands.command()
    async def loop(self, context: Context, mode: str = "queue") -> None:
        """Toggle loop mode for queue or current song."""
        if mode == "queue":
            self.playlist_manager.loop_queue = not self.playlist_manager.loop_queue
            self.playlist_manager.loop_song = False
            await context.send(
                f"🔁 Queue loop {'enabled' if self.playlist_manager.loop_queue else 'disabled'}!"
            )
            self.playlist_manager.backup_playlist()
        elif mode == "song":
            self.playlist_manager.loop_song = not self.playlist_manager.loop_song
            self.playlist_manager.loop_queue = False
            await context.send(
                f"🔂 Song loop {'enabled' if self.playlist_manager.loop_song else 'disabled'}!"
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
        await self.voice_manager.ensure_voice(context)