"""Voice connection manager for the music bot."""

import asyncio
import logging

from discord import Member, VoiceClient, VoiceState
from discord.ext.commands import CommandError, Context

logger = logging.getLogger(__name__)


class VoiceManager:
    """Manages voice connections for the music bot."""

    def __init__(self) -> None:
        """Initialize the voice manager."""
        self.voice_clients: dict[int, VoiceClient] = {}
        self.inactivity_timers: dict[int, asyncio.Task] = {}
        self.INACTIVITY_TIMEOUT = 120  # 2 minutes

    async def ensure_voice(self, context: Context) -> None:
        """Ensure proper voice channel connection."""
        if context.voice_client is None:
            if context.author.voice:
                self.voice_clients[context.guild.id] = (
                    await context.author.voice.channel.connect()
                )
            else:
                raise CommandError("You must be in a voice channel!")
        elif context.voice_client.channel != context.author.voice.channel:
            raise CommandError("You must be in the same voice channel as the bot!")

    async def start_inactivity_timer(self, guild_id: int) -> None:
        """Start the inactivity timer for a guild."""
        # Cancel any existing timer
        if guild_id in self.inactivity_timers:
            self.inactivity_timers[guild_id].cancel()

        # Start new timer
        self.inactivity_timers[guild_id] = asyncio.create_task(
            self._disconnect_after_timeout(guild_id)
        )

    async def _disconnect_after_timeout(self, guild_id: int) -> None:
        """Disconnect after timeout if no activity."""
        try:
            await asyncio.sleep(self.INACTIVITY_TIMEOUT)
            # Only disconnect if we're not playing anything
            if (
                voice_client := self.voice_clients.get(guild_id)
            ) and not voice_client.is_playing():
                await self.disconnect(guild_id)
        except asyncio.CancelledError:
            pass  # Timer was cancelled, do nothing
        finally:
            # Clean up timer
            self.inactivity_timers.pop(guild_id, None)

    async def handle_voice_state_update(
        self, member: Member, before: VoiceState, after: VoiceState
    ) -> None:
        """Handle voice state updates to detect when to disconnect."""
        if member.bot:
            return  # Ignore bot voice updates

        guild_id = member.guild.id
        if guild_id not in self.voice_clients:
            return

        voice_client = self.voice_clients[guild_id]

        # Check if the bot is alone in the channel
        if voice_client.channel and len(voice_client.channel.members) == 1:
            # Only the bot is left
            await self.disconnect(guild_id)

    async def disconnect(self, guild_id: int) -> None:
        """Disconnect from a voice channel."""
        # Cancel any running timer
        if guild_id in self.inactivity_timers:
            self.inactivity_timers[guild_id].cancel()
            self.inactivity_timers.pop(guild_id)

        if guild_id in self.voice_clients:
            await self.voice_clients[guild_id].disconnect()
            del self.voice_clients[guild_id]

    async def cleanup(self) -> None:
        """Disconnect from all voice channels and clean up timers."""
        # Cancel all timers
        for timer in self.inactivity_timers.values():
            timer.cancel()
        self.inactivity_timers.clear()

        # Disconnect from all voice channels
        for guild_id in list(self.voice_clients.keys()):
            if self.voice_clients[guild_id].is_connected():
                await self.voice_clients[guild_id].disconnect()
            del self.voice_clients[guild_id]
