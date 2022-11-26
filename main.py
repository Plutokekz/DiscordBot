import asyncio
import logging
import os
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)
discord.utils.setup_logging(level=logging.INFO, root=True)


TOKEN = os.environ["DiscordToken"]
intents = discord.Intents.all()

client = commands.Bot(".", intents=intents)


@client.event
async def on_ready():
    logger.info("We have logged in as %s", client.user.name)


async def main():
    for extension in ["cogs.music.music_cog"]:
        await client.load_extension(extension)
        logger.info("loaded extension: %s", extension)
    await client.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
