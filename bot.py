import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
from loguru import logger


def setup_logger():
    """
    Sets up the logger with two sinks: one for errors and one for info messages.
    """
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)

    error_file = os.path.join(log_dir, "error.log")
    logger.add(error_file, format="{time} {level} {message}", level="ERROR")

    info_file = os.path.join(log_dir, "info.log")
    logger.add(info_file, format="{time} {level} {message}", level="INFO", filter=logger_only_level("INFO"))
    logger.debug("logger setup complete")


def logger_only_level(level):
    """
    Filter for logger to write down only one log level.
    """
    def is_level(record): return record['level'].name == level
    return is_level


async def load_cogs(bot):
    """
    Loads all cogs for the bot.
    """
    logger.debug(f"Loading cogs")
    cogs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cogs")
    for filename in os.listdir(cogs_dir):
        if filename.endswith(".py"):
            try:
                cog_name = filename[:-3]
                cog_path = f'cogs.{cog_name}'
                await bot.load_extension(cog_path)
                logger.debug(f"Loaded cog '{cog_name}'")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                logger.error(f"Failed to load cog {cog_name}\n{exception}")


def main():
    setup_logger()

    load_dotenv()
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN environment variable not set.")
        return

    bot = commands.Bot(command_prefix='>', intents=discord.Intents.all())

    asyncio.run(load_cogs(bot))

    try:
        bot.run(token)
    except discord.LoginFailure:
        logger.error("Invalid DISCORD_TOKEN provided.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == '__main__':
    main()
