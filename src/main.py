"""Main entry point for the Keion Discord bot."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import discord
import uvicorn
from discord.ext import commands

from keion.cogs.music import MusicCog
from keion.utils.logging import setup_logging
from keion.web.app import app

# Initialize logger
logger = logging.getLogger(__name__)


def create_bot() -> commands.Bot:
    """Create and configure the Discord bot."""
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True

    bot = commands.Bot(
        command_prefix=commands.when_mentioned_or("/", "!"),
        description="Keion music bot",
        intents=intents,
    )

    # Add start_time attribute for uptime tracking
    bot.start_time = datetime.now(UTC)
    return bot


@asynccontextmanager
async def lifespan(app):
    # Create and start the Discord bot
    bot = create_bot()
    app.state.bot = bot  # Store bot instance in app state

    # Register the music cog
    await bot.add_cog(MusicCog(bot))

    # Start the bot in the background
    background_tasks = set()
    task = asyncio.create_task(bot.start(os.getenv("DISCORD_TOKEN")))
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)

    yield

    # Cleanup
    if not bot.is_closed():
        await bot.close()


app.router.lifespan_context = lifespan

if __name__ == "__main__":
    # Use uvloop if available
    try:
        import uvloop

        uvloop.install()
        logger.info("Using uvloop for improved async performance")
    except ImportError:
        logger.info("uvloop not available, using default event loop")

    # Setup logging
    setup_logging()

    # Start the web server
    uvicorn.run(
        app,
        host=os.getenv("WEB_HOST", "0.0.0.0"),
        port=int(os.getenv("WEB_PORT", "8000")),
        log_level="info",
    )
