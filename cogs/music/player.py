import asyncio
import logging

from async_timeout import timeout
import discord
from discord.ext import commands

# from cogs.music.music_cog import Player
from cogs.music.online.youtube_dl import AudioSource

logger = logging.getLogger(__name__)


class MusicPlayer:
    __slots__ = ("bot", "guild", "channel", "cog", "queue", "next", "current")
    bot: commands.Bot
    guild: discord.Guild
    channel: discord.VoiceChannel
    cog: commands.Cog | None
    queue: asyncio.Queue
    next: asyncio.Event
    current: AudioSource | None

    def __init__(self, ctx: commands.Context):
        self.bot = ctx.bot
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.cog = ctx.cog
        self.queue = asyncio.Queue()
        self.next = asyncio.Event()
        self.bot.loop.create_task(self.player_loop())

    async def get_playlist(self):
        size = self.queue.qsize()
        play_list = []
        for _ in range(size):
            source = await self.queue.get()
            play_list.append(source)
            await self.queue.put(source)
        return play_list

    async def player_loop(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()
            try:
                async with timeout(100):
                    audio_source = await self.queue.get()
            except asyncio.TimeoutError as e:
                logger.error("cant get audio source from queue Timeout: %s", e)
                return self.destroy(self.guild)

            self.current = audio_source
            await self.bot.change_presence(activity=audio_source.to_activity())
            if self.guild.voice_client is not None:
                self.guild.voice_client.play(
                    audio_source,
                    after=lambda error: (
                        logger.warning("error while playing: %s", error),
                        self.bot.loop.create_task(
                            self.bot.change_presence(activity=discord.Activity())
                        ),
                        self.bot.loop.call_soon_threadsafe(self.next.set),
                    ),
                )
                logger.info("playing %s", self.current.title)
                await self.channel.send(embed=audio_source.to_embed(), delete_after=30)
            await self.next.wait()

            audio_source.cleanup()
            self.current = None

    def destroy(self, guild: discord.Guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self.cog.cleanup(guild))
