"""Voice connection manager for the music bot."""

import logging
from typing import Dict
from discord import VoiceClient
from discord.ext.commands import Context, CommandError

logger = logging.getLogger(__name__)

class VoiceManager:
    """Manages voice connections for the music bot."""
    
    def __init__(self) -> None:
        """Initialize the voice manager."""
        self.voice_clients: Dict[int, VoiceClient] = {}

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
            raise CommandError(
                "You must be in the same voice channel as the bot!"
            )

    async def disconnect(self, guild_id: int) -> None:
        """Disconnect from a voice channel."""
        if guild_id in self.voice_clients:
            await self.voice_clients[guild_id].disconnect()
            del self.voice_clients[guild_id]

    async def cleanup(self) -> None:
        """Disconnect from all voice channels."""
        for guild_id in list(self.voice_clients.keys()):
            if self.voice_clients[guild_id].is_connected():
                await self.voice_clients[guild_id].disconnect()
            del self.voice_clients[guild_id]