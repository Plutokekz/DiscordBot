from typing import Dict, Any, List
import logging

import discord
import yaml
import youtube_dl.YoutubeDL
from discord.ext import commands
from discord.ext.commands import MissingAnyRole, CommandNotFound
from discord.utils import get

from cogs.music.player import MusicPlayer
from cogs.music.online.youtube_dl import AudioSource, YTDLError
from cogs.utlis import check_roles
from database.database import engine
from database.tabels.musicplayer import SongRequest
import datetime
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class VoiceConnectionError(commands.CommandError):
    """Custom Exception class for connection errors."""


class InvalidVoiceChannel(VoiceConnectionError):
    """Exception for cases of invalid Voice Channels."""


def _load_config():
    with open("config.yml", "r") as fp:
        return yaml.safe_load(fp)['cogs']['music']


class Player(commands.Cog):
    __slots__ = ('bot', 'players', 'voice_client', 'config')

    bot: commands.Bot
    players: Dict[int, MusicPlayer]
    voice_client: discord.VoiceClient | None
    config: Dict[str, Any]

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players = {}
        self.voice_client = None
        self.config = _load_config()
        self.session = Session(engine)

    @commands.command(name='play')
    async def play(self, ctx: commands.Context, *, search: str):
        """Plays a song.
        If there are songs in the queue, this will be queued until the
        other songs finished playing.
        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
        """
        logger.info(f"{ctx.message.author.name} trying to play {search} in {ctx.message.channel.name}")
        if not ctx.voice_client:
            await self.connect(ctx)
        player = self.get_player(ctx)

        async with ctx.typing():
            async for source in AudioSource.create_sources(search, ctx=ctx, loop=ctx.bot.loop,
                                                           ffmpeg_options=self.config['online']['ffmpeg_options'],
                                                           ytdl=youtube_dl.YoutubeDL(
                                                               self.config['online']['ytdl_format_options']),
                                                           default_info=self.config['online']['default_info']):
                logger.info(f"{ctx.message.author.name} is queuing {source.title}")
                await player.queue.put(source)
                await self.add_request_to_database(ctx, source)
        await ctx.message.delete(delay=10)

    @commands.command(name="queue")
    async def queue(self, ctx: commands.Context):
        player = self.get_player(ctx)
        play_list: List[AudioSource] = await player.get_playlist()
        message = "\n**Durchsagenlist**\n"
        message += "\n".join(
            [f"__{index + 1:01n}__. **{source.title}**" for index, source in
             enumerate(play_list)])
        await ctx.message.delete(delay=10)
        await ctx.send(message, delete_after=30)

    async def connect(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None) -> None:
        """Connect the Bot to the voice channel of the author."""
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                raise VoiceConnectionError(f'{ctx.message.author.name} is not in a Voice channel')
        if ctx.voice_client is None or self.voice_client is None:
            self.voice_client = await channel.connect()
            logger.info(f"{self.bot.user.name} connect with {channel}")
            await ctx.send(f'Is am Bahnsteig **{channel}** erschienen', delete_after=10)
            return
        if self.voice_client.channel.id == channel.id:
            return
        await self.voice_client.move_to(channel)
        logger.info(f"{self.bot.user.name} moved to {channel}")
        await ctx.send(f'Gleis wechsel zu: **{channel}**', delete_after=10)

    @commands.command(name='pause')
    async def pause(self, ctx: commands.Context) -> None:
        """Pauses the currently playing song."""
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            emoji = get(self.bot.emojis, name='DarksideDeutscheBahn')
            await ctx.message.add_reaction(emoji)
            logger.info(f"{ctx.message.author.name} paused")
        await ctx.message.delete(delay=10)

    @commands.command(name='resume')
    async def resume(self, ctx: commands.Context) -> None:
        """Resumes a currently paused song."""
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            emoji = get(self.bot.emojis, name='DeutscheBahn')
            await ctx.message.add_reaction(emoji)
            logger.info(f"{ctx.message.author.name} resumed")
        await ctx.message.delete(delay=10)

    @commands.command(name='skip')
    async def skip(self, ctx: commands.Context) -> None:
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            logger.info(f"{ctx.message.author.name} skipped")
        await ctx.message.delete(delay=10)

    @commands.command(name='stop')
    async def stop(self, ctx: commands.Context) -> None:
        """Stops the playing or paused song."""
        if self.voice_client and self.voice_client.is_connected():
            emoji = get(self.bot.emojis, name='SaltyCaptin')
            logger.info(f"{ctx.message.author.name} stopped")
            await ctx.message.add_reaction(emoji)
            await self.cleanup(ctx.guild)
            await self.bot.change_presence(activity=discord.Activity())
        await ctx.message.delete()

    async def cleanup(self, guild: discord.Guild) -> None:
        try:
            await guild.voice_client.disconnect(force=True)
        except AttributeError as e:
            logger.warning(f"Error in cleanup, disconnection the client: {e}")

        try:
            del self.players[guild.id]
        except KeyError as e:
            logger.warning(f"Error in cleanup, removing the player from Players: {e}")

    async def cog_check(self, ctx: commands.Context) -> bool:
        """A local check which applies to all commands in this cog."""
        if not ctx.guild:
            raise commands.NoPrivateMessage
        if not check_roles(ctx, ['@everyone']):
            raise MissingAnyRole(['@everyone'])
        return True

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> None:
        """A local error handler for all errors arising from commands in this cog."""
        name = ctx.message.author.name
        logger.error(f"An error {error}")
        if isinstance(error, commands.NoPrivateMessage):
            logger.error(f"{name} is trying to run a command in Private chat {error}")
            return await self._send_error_msg(ctx, 'Sie können diesen befehl nur in der Deutschen Bahn nutzen')
        elif isinstance(error, MissingAnyRole):
            logger.error(f"{name} is missing a role: {error}")
            return await self._send_error_msg(ctx, f"{name} you have no permission for that command")
        elif isinstance(error, VoiceConnectionError):
            logger.error(f"{name} is currently not in a voice channel")
            return await self._send_error_msg(ctx, f'{name}, Sie befinden sich nicht ein einem Sprach Kanal')
        elif isinstance(error, YTDLError):
            logger.error(f"An error occurred while processing this youtube_dl query: {error}")
            await self._send_error_msg(ctx, f"Durchsage nicht möglich")
        elif isinstance(error, CommandNotFound):
            logger.error(f"Command not found: {error}")
        await ctx.message.delete(delay=10)

    def get_player(self, ctx: commands.Context) -> MusicPlayer:
        """Retrieve the guild player, or generate one."""
        if (player := self.players.get(ctx.guild.id)) is not None:
            return player
        player = MusicPlayer(ctx)
        self.players[ctx.guild.id] = player
        return player

    async def add_request_to_database(self, ctx: commands.Context, source: AudioSource):
        request = SongRequest(date=datetime.datetime.today(), title=source.title, requester_id=ctx.message.author.id,
                              web_page=source.web_page)
        self.session.add(request)
        self.session.commit()

    async def _send_error_msg(self, ctx: commands.Context, message: str) -> None:
        send_message = await ctx.send(message, delete_after=20)
        emoji = get(self.bot.emojis, name='AMBOS')
        await send_message.add_reaction(emoji)
        emoji = get(self.bot.emojis, name='4923_bettermissingping')
        await send_message.add_reaction(emoji)

    async def cog_unload(self) -> None:
        self.session.close()


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Player(client))