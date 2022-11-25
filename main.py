import asyncio
import logging
import os
import discord
from discord.ext import commands

logger = logging.getLogger(__name__)
discord.utils.setup_logging(level=logging.INFO, root=True)


TOKEN = os.environ['DiscordToken']
intents = discord.Intents.default()
intents.message_content = True

client = commands.Bot(".", intents=intents)


@client.event
async def on_ready():
    logger.info(f'We have logged in as {client.user}')


async def main():
    for extension in ['cogs.music.music_cog']:
        await client.load_extension(extension)
        logger.info(f"loaded extension: {extension}")
    await client.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
