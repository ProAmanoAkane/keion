"""Main entry point for the Keion Discord bot."""

import asyncio
import logging
import os

import discord

from keion import setup_bot
from keion.utils.logging import setup_logging

# Initialize logger
logger = logging.getLogger(__name__)

# Add performance intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

# Setup logging
setup_logging()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if DISCORD_TOKEN is None:
    logger.critical("DISCORD_TOKEN environment variable is not set")
    raise ValueError("DISCORD_TOKEN environment variable is not set")


async def main() -> None:
    """Main entry point for the bot."""
    try:
        bot = await setup_bot()

        async with bot:
            logger.info("Starting bot with Discord.py version %s", discord.__version__)
            await bot.start(DISCORD_TOKEN)
    except Exception as e:
        logger.exception("Fatal error starting bot: %s", str(e))
        raise


if __name__ == "__main__":
    # Use uvloop if available for better async performance
    try:
        import uvloop

        uvloop.install()
        logger.info("Using uvloop for improved async performance")
    except ImportError:
        logger.info("uvloop not available, using default event loop")

    asyncio.run(main())
