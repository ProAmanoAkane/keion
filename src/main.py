import os
import asyncio
from keion import setup_bot

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", None)

if DISCORD_TOKEN is None:
    raise ValueError("DISCORD_TOKEN environment variable is not set")

async def main():
    """Main entry point for the bot."""
    bot = await setup_bot()
    
    async with bot:
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())