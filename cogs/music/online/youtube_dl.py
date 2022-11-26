import asyncio
from typing import Dict, Any
import logging

import discord
import youtube_dl
from discord.ext import commands
from youtube_dl import YoutubeDL

logger = logging.getLogger(__name__)

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ""


class YTDLError(Exception):
    """
    Exception if youtub_dl fails to extract am audio file/url
    """


class AudioSource(discord.PCMVolumeTransformer):
    __slots__ = (
        "requester",
        "channel",
        "title",
        "duration",
        "uploader",
        "uploader_url",
        "thumbnail",
        "url",
        "description",
    )
    requester: discord.Member
    channel: discord.TextChannel
    title: str
    duration: int
    uploader: str
    uploader_url: str
    thumbnail: str
    url: str
    description: str

    def __init__(
        self, original: discord.AudioSource, ctx: commands.Context, data: Dict[str, Any]
    ):
        super().__init__(original, volume=1.0)
        self.title = data.get("title")
        self.duration = data.get("duration")
        self.uploader = data.get("uploader")
        self.uploader_url = data.get("uploader_url")
        self.thumbnail = data.get("thumbnail")
        self.url = data.get("url")
        self.web_page = data.get("webpage_url")
        self.description = data.get("description")
        self.requester = ctx.author
        self.channel = ctx.channel

    def to_embed(self) -> discord.Embed:
        return (
            discord.Embed(
                title="Now playing",
                description=f"```css\n{self.title}\n```",
                color=discord.Color.blurple(),
            )
            .add_field(name="Duration", value=self.duration)
            .add_field(name="Requested by", value=self.requester.mention)
            .add_field(name="Uploader", value=f"[{self.uploader}]({self.uploader_url})")
            .add_field(name="URL", value=f"[Click]({self.web_page})")
            .set_thumbnail(url=self.thumbnail)
        )

    def to_activity(self) -> discord.Activity:
        return discord.Activity(
            type=discord.ActivityType.listening,
            name=self.title,
            details=self.description,
            url=self.web_page,
        )

    @classmethod
    async def _create_source(
        cls,
        *,
        ctx: commands.Context,
        processed_info: dict,
        stream: bool,
        default_info: Dict[str, str],
        ffmpeg_options: Dict[str, str],
        ytdl: YoutubeDL,
    ):
        info = default_info.copy()
        info.update(processed_info)
        filename = (
            processed_info["url"] if stream else ytdl.prepare_filename(processed_info)
        )
        logger.info("Creating new source %s, %s", info.get("title"), filename)
        return cls(
            discord.FFmpegPCMAudio(filename, **ffmpeg_options), ctx=ctx, data=info
        )

    @classmethod
    async def create_sources(
        cls,
        url: str,
        *,
        ctx: commands.Context,
        loop: asyncio.AbstractEventLoop,
        default_info: Dict[str, str],
        ffmpeg_options: Dict[str, str],
        ytdl: YoutubeDL,
        stream: bool = True,
    ):
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream, process=True)
        )
        if data is None:
            raise YTDLError(f"Couldn't find anything that matches `{url}`")

        if "entries" not in data:
            yield await cls._create_source(
                ctx=ctx,
                processed_info=data,
                stream=stream,
                default_info=default_info,
                ffmpeg_options=ffmpeg_options,
                ytdl=ytdl,
            )
        else:
            for entry in data["entries"]:
                yield await cls._create_source(
                    ctx=ctx,
                    processed_info=entry,
                    stream=stream,
                    default_info=default_info,
                    ffmpeg_options=ffmpeg_options,
                    ytdl=ytdl,
                )
