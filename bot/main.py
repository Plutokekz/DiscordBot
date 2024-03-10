import asyncio
import logging
import os
import discord
from discord.ext import commands
from bot.logger import logger

discord.utils.setup_logging(level=logging.INFO, root=True)


TOKEN = os.environ["DiscordToken"]
intents = discord.Intents.all()
# test the integration
client = commands.Bot("!", intents=intents)


@client.event
async def on_ready():
    logger.info(f"We have logged in as {client.user.name}")


async def main():
    for extension in [
        "bot.cogs.music.music_cog",
        "bot.cogs.deutschebahn.deutschebahn_cog",
        "bot.cogs.mvg.mvg_cog",
    ]:
        await client.load_extension(extension)
        logger.info(f"loaded extension: {extension}")
    await client.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
