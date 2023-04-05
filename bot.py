import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio
from loguru import logger

def only_level(level):
    def is_level(record): return record['level'].name == level
    return is_level

logger.add(f"{os.path.realpath(os.path.dirname(__file__))}/logs/error.log", format="{time} {level} {message}", level="ERROR")
logger.add(f"{os.path.realpath(os.path.dirname(__file__))}/logs/info.log", format="{time} {level} {message}", level="INFO", filter=only_level("INFO"))

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

async def load_cogs():
    """
    This code registers all cogs for the bot. This function is run when the bot starts.
    """
    logger.debug(f"Loading cogs")
    for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/cogs"):
        if file.endswith(".py"):
            filename = file[::]
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                logger.debug(f"Loaded cog '{filename}'")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                logger.error(f"Failed to load cog {filename}\n{exception}")


asyncio.run(load_cogs())
bot.run(TOKEN)