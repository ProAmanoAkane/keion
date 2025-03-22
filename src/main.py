"""Main entry point for the Keion Discord bot."""

import os
import asyncio
import discord
from keion import setup_bot

# Add performance intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

# Add connection pooling
discord.utils.setup_logging()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if DISCORD_TOKEN is None:
    raise ValueError("DISCORD_TOKEN environment variable is not set")

async def main() -> None:
    """Main entry point for the bot."""
    try:
        
        bot = await setup_bot()
        
        async with bot:
            print(f"Starting bot with version {discord.__version__}")
            await bot.start(DISCORD_TOKEN)
    except Exception as e:
        print(f"Error starting bot: {e}")
        raise

if __name__ == "__main__":
    # Use uvloop if available for better async performance
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass
        
    asyncio.run(main())