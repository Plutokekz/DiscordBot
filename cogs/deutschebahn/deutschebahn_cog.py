import asyncio
import logging
import datetime

import httpx
import yaml
from discord.ext import commands, tasks
from sqlalchemy.orm import Session
from sqlalchemy import delete

from cogs.deutschebahn.rs_api.api import RS
from cogs.deutschebahn.station import Station
from database.database import engine
from database.tabels.deutschebahn import RegisteredChannels

logger = logging.getLogger(__name__)


def _load_config():
    with open("config/config.yml", "r", encoding="utf-8") as file:
        return yaml.safe_load(file)["cogs"]["deutschebahn"]


class DeutscheBahnCog(commands.Cog):
    __slots__ = ("bot", "station")

    bot: commands.Bot
    station: Station

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        api = RS(httpx.AsyncClient())
        self.station = Station(api)
        self.session = Session(engine)
        # pylint: disable=no-member
        self.message_of_the_day_task.start()

    @commands.has_permissions(administrator=True)
    @commands.command(name="subscribe")
    async def subscribe_channel(self, ctx: commands.Context):
        """
        Subscribe to the Station of the day message with this channel
        :param ctx:
        :return:
        """
        channel_id = ctx.message.channel.id
        if self.session.query(RegisteredChannels).filter_by(id=channel_id).first():
            logger.warning(
                "Channel %s is already subscribed to station of the day",
                ctx.channel.name,
            )
            await ctx.send(
                f"Kanal {ctx.channel.name} ist schon angemeldet", delete_after=10
            )
        else:
            self.session.add(RegisteredChannels(id=channel_id))
            self.session.commit()
            logger.info("Channel %s subscribed to station of the day", ctx.channel.name)
            await ctx.send(
                f"Kanal {ctx.channel.name} ist angemeldet, für Station des Tages",
                delete_after=10,
            )
        await ctx.message.delete(delay=10)

    @commands.has_permissions(administrator=True)
    @commands.command(name="unsubscribe", alias="abmelden")
    async def unsubscribe_channel(self, ctx: commands.Context):
        """
        Unsubscribe to the Station of the day message with this channel
        :param ctx:
        :return:
        """
        channel_id = ctx.message.channel.id
        if (
            self.session.query(RegisteredChannels).filter_by(id=channel_id).first()
            is None
        ):
            logger.warning(
                "Channel %s is not subscribed to station of the day, unsubscribe not possible",
                ctx.channel.name,
            )
            await ctx.send(
                f"Kanal {ctx.channel.name} ist nicht angemeldet, abmelden nicht möglich",
                delete_after=10,
            )
        else:
            self.session.execute(
                delete(RegisteredChannels).where(RegisteredChannels.id == channel_id)
            )
            self.session.commit()
            logger.info(
                "Channel %s unsubscribed to station of the day", ctx.channel.name
            )
            await ctx.send(
                f"Kanal {ctx.channel.name} ist abgemeldet, für Station des Tages",
                delete_after=10,
            )
        await ctx.message.delete(delay=10)

    @tasks.loop(time=datetime.time(hour=_load_config()["hour"]))
    async def message_of_the_day_task(self):
        logger.info("running station of the day task")
        description, photos = await self.station.get_station_of_the_day()
        for channel_id in self.session.query(RegisteredChannels).all():
            logger.info(channel_id)
            if (channel := self.bot.get_channel(channel_id.id)) is not None:
                logger.info("sending station of the day to: %s", channel)
                await channel.send(embed=description)
                await channel.send(embeds=photos)
        await asyncio.sleep(10)

    @message_of_the_day_task.before_loop
    async def before_my_task(self):
        await self.bot.wait_until_ready()


async def setup(client: commands.Bot) -> None:
    await client.add_cog(DeutscheBahnCog(client))
