"""Keion Discord music bot package."""

import discord
from discord.ext import commands
from .cogs.music import MusicCog

__version__ = "0.1.0"


async def setup_bot() -> commands.Bot:
    """Initialize and configure the Discord bot."""
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True

    bot = commands.Bot(
        command_prefix=commands.when_mentioned_or("/", "!"),
        description="Keion music bot",
        intents=intents,
    )
    await bot.add_cog(MusicCog(bot))

    return bot
