from __future__ import annotations
import cogs.music.music_cog as mc
import asyncio
import logging
from typing import Coroutine

from async_timeout import timeout
import discord
from discord.ext import commands

from cogs.music.online.youtube_dl import AudioSource

logger = logging.getLogger(__name__)


class MusicPlayer:
    __slots__ = (
        "bot",
        "guild",
        "channel",
        "cog",
        "queue",
        "next",
        "current",
        "voice_client",
        "player_tasks",
    )
    bot: commands.Bot
    guild: discord.Guild
    channel: discord.VoiceChannel
    cog: mc.Player | None
    queue: asyncio.Queue[AudioSource]
    next: asyncio.Event
    current: AudioSource | None
    voice_client: discord.VoiceClient | None
    player_tasks: set | None

    def __init__(self, ctx: commands.Context):
        self.bot = ctx.bot
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.cog = ctx.cog
        self.queue = asyncio.Queue()
        self.next = asyncio.Event()
        self.player_tasks = set()
        self.creat_referenced_task(self.player_loop())

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
                task = self.destroy(self.guild)
                self.creat_referenced_task(task)
                return task

            self.current = audio_source
            await self.bot.change_presence(activity=audio_source.to_activity())
            if self.voice_client is not None:
                self.voice_client.play(
                    audio_source,
                    after=lambda error: (
                        logger.warning("error while playing: %s", error),
                        self.creat_referenced_task(
                            self.bot.change_presence(activity=discord.Activity())
                        ),
                        self.bot.loop.call_soon_threadsafe(self.next.set),
                    ),
                )
                logger.info("playing %s", self.current.title)
                await self.channel.send(embed=audio_source.to_embed(), delete_after=30)
            await self.next.wait()
            try:
                audio_source.cleanup()
            except ValueError as e:
                logger.error("error while cleaning up audio source: %s", e)
            self.current = None

    def creat_referenced_task(self, coro: Coroutine):
        task = self.bot.loop.create_task(coro)
        self.player_tasks.add(task)
        task.add_done_callback(self.player_tasks.discard)

    async def destroy(self, guild: discord.Guild):
        """Disconnect and cleanup the player."""
        return await self.cog.cleanup(guild)
