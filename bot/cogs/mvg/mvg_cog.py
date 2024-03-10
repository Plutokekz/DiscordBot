import datetime

import discord
import httpx
from discord.ext import commands, tasks
from mvg_api.v1.schemas.ticker import Ticker
from mvg_api.v1.mvg import AsyncMVG
from sqlalchemy import delete
from sqlalchemy.orm import Session
from markdownify import MarkdownConverter

from bot.database.database import engine
from bot.database.models.mvg import RegisteredChannelWithMessageId
from bot.logger import logger


class MyMarkdownConverter(MarkdownConverter):
    """
    Create a custom MarkdownConverter that adds two newlines after an image
    """

    def convert_li(self, el, text, convert_as_inline):
        return "\n" + super().convert_li(el, text, convert_as_inline)


class TypeOfTransportConverter(commands.Converter):
    async def convert(self, ctx, argument) -> str | None:
        # pylint: disable=unused-argument
        argument = argument.lower()
        if argument in ["s", "sbahn"]:
            return "SBAHN"
        if argument in ["b", "bus"]:
            return "BUS"
        if argument in ["tram", "t"]:
            return "TRAM"
        if argument in ["u", "ubahn", "m", "metro"]:
            return "METRO"
        return None


md = MyMarkdownConverter(bullets=[">"])


class MVGCog(commands.Cog):
    __slots__ = ("bot", "station")

    bot: commands.Bot
    api: AsyncMVG

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api = AsyncMVG()
        self.session = Session(engine)
        # pylint: disable=no-member
        self.update_slim.start()

    @commands.has_permissions(administrator=True)
    @commands.command(name="subscribe-slim")
    async def subscribe_slim(self, ctx: commands.Context):
        """
        Subscribe to the mvg disruption ticker
        :param ctx:
        :return:
        """
        channel_id = ctx.message.channel.id
        if (
            self.session.query(RegisteredChannelWithMessageId)
            .filter_by(id=channel_id)
            .first()
        ):
            logger.warning(
                f"Channel {ctx.channel.name} is already subscribed to station of the day"
            )
            await ctx.send(
                f"Kanal {ctx.channel.name} ist schon angemeldet", delete_after=10
            )
        else:
            message = await ctx.send(embed=await self.generate_slim())
            self.session.add(
                RegisteredChannelWithMessageId(id=channel_id, message_id=message.id)
            )
            self.session.commit()
            logger.info(f"Channel {ctx.channel.name} subscribed to slim message ticker")
            await ctx.send(
                f"Kanal {ctx.channel.name} ist angemeldet, für MVG Störungs Ticker",
                delete_after=10,
            )
        await ctx.message.delete(delay=10)

    @commands.has_permissions(administrator=True)
    @commands.command(name="unsubscribe-slim")
    async def unsubscribe_slim(self, ctx: commands.Context):
        """
        Unsubscribe to the mvg disruption ticker
        :param ctx:
        :return:
        """
        channel_id = ctx.message.channel.id
        if (
            self.session.query(RegisteredChannelWithMessageId)
            .filter_by(id=channel_id)
            .first()
            is None
        ):
            logger.warning(
                f"Channel {ctx.channel.name} is not subscribed to mvg ticker, unsubscribe not possible"
            )
            await ctx.send(
                f"Kanal {ctx.channel.name} ist nicht angemeldet, abmelden nicht möglich",
                delete_after=10,
            )
        else:
            message_from_db = (
                self.session.query(RegisteredChannelWithMessageId)
                .filter_by(id=channel_id)
                .first()
            )
            message = await self.bot.get_channel(channel_id).fetch_message(
                message_from_db.message_id
            )
            await message.delete()
            self.session.execute(
                delete(RegisteredChannelWithMessageId).where(
                    RegisteredChannelWithMessageId.id == channel_id
                )
            )
            self.session.commit()
            logger.info(f"Channel {ctx.channel.name} unsubscribed mvg ticker")
            await ctx.send(
                f"Kanal {ctx.channel.name} ist abgemeldet, für MVG störungs ticker",
                delete_after=10,
            )
        await ctx.message.delete(delay=10)

    async def generate_slim(self) -> discord.Embed:
        try:
            slim_list = await self.api.get_slim()
        except httpx.HTTPError as e:
            logger.error(f"Error while fetching slim list: {e}")
            return discord.Embed(
                colour=discord.Colour.red(),
                color=discord.Color.red(),
                title="Betriebsmeldungen",
                description="Es ist ein Fehler aufgetreten, bitte versuchen sie es später erneut",
                timestamp=datetime.datetime.now(),
                url="https://www.mvg.de/dienste/betriebsaenderungen.html",
            ).set_footer(text="Letzte Aktualisierung")
        if len(slim_list) == 0:
            return discord.Embed(
                colour=discord.Colour.yellow(),
                color=discord.Color.yellow(),
                title="Betriebsmeldungen",
                description="Es liegen momentan keine Störungen oder"
                " Betriebsmeldungen vor, die MVG wünscht ihnen"
                " eine gute fahrt.",
                timestamp=datetime.datetime.now(),
                url="https://www.mvg.de/dienste/betriebsaenderungen.html",
            ).set_footer(text="Letzte Aktualisierung")

        description = (
            f"Es liegen momentan {len(slim_list)} Betriebsmeldungen oder Störungen vor."
        )
        if len(slim_list) == 1:
            description = "Es liegt folgende Betriebsmeldung oder Störung vor"

        embed = discord.Embed(
            colour=discord.Colour.yellow(),
            color=discord.Color.yellow(),
            title="Betriebsmeldungen",
            description=description,
            url="https://www.mvg.de/dienste/betriebsaenderungen.html",
            timestamp=datetime.datetime.now(),
        )
        embed.set_footer(text="Letzte Aktualisierung um")
        for slim in slim_list:
            embed.add_field(name="Störung", value=slim.title)
        return embed

    @commands.command(name="meldungen")
    async def announcements(
        self,
        ctx: commands.Context,
        type_of: TypeOfTransportConverter = None,
        line: str = None,
    ):
        tickers = await self.api.get_ticker()
        for ticker in tickers.__root__:
            if self.check_type_of_transport(type_of, line, ticker):
                embed = self.ticker_to_embed(ticker)
                await ctx.send(embed=embed, delete_after=90)
        await ctx.message.delete(delay=10)

    def check_type_of_transport(self, type_of: str, line_id: str, ticker: Ticker):
        if type_of is None:
            return True
        if ticker.lines is None:
            return False
        for line in ticker.lines:
            return line.typeOfTransport == type_of and (
                line_id is None or line.id == line_id
            )

    def ticker_to_embed(self, ticker: Ticker) -> discord.Embed:
        text = md.convert(ticker.text)
        color = discord.Color.blue()
        if ticker.type is not None:
            if ticker.type == "DISRUPTION":
                color = discord.Color.red()
            elif ticker.type == "PLANED":
                color = discord.Color.yellow()
        embed = discord.Embed(title=ticker.title, description=text, color=color)
        if ticker.links is not None and len(ticker.links) > 0:
            if len(ticker.links) > 1:
                for link in ticker.links[1:]:
                    embed.add_field(name=link.name, value=link.href)
            embed.url = ticker.links[0].href
        if ticker.incidents is not None and "UNKNOWN" not in ticker.incidents:
            name = "Vorfälle"
            if len(ticker.incidents) == 1:
                name = "Vorfall"
            embed.add_field(name=name, value="\n".join(ticker.incidents))
        # if ticker.lines is not None:
        #    for line in ticker.lines:
        #        line.
        if ticker.downloadLinks is not None:
            for download_link in ticker.downloadLinks:
                embed.set_image(
                    url=f"{self.api.api.url}api/ems/tickers/file/{download_link.id}"
                )
        if (
            ticker.activeDuration is not None
            and ticker.activeDuration.fromDate is not None
        ):
            from_date = ticker.activeDuration.fromDate.strftime("%d.%m.%Y, %H:%M:%S")
            to_date = "Ungewiss"
            if ticker.activeDuration.toDate is not None:
                to_date = ticker.activeDuration.toDate.strftime("%d.%m.%Y, %H:%M:%S")
            embed.add_field(name="Aktive dauer", value=f"Von {from_date} bis {to_date}")
        return embed

    @tasks.loop(minutes=30)
    async def update_slim(self):
        logger.info("updating slim")
        slim = await self.generate_slim()
        for channel_id_message_id in self.session.query(
            RegisteredChannelWithMessageId
        ).all():
            channel = self.bot.get_channel(channel_id_message_id.id)
            try:
                message = await channel.fetch_message(channel_id_message_id.message_id)
            except discord.NotFound as e:
                logger.error(
                    f"Error while fetching message {channel_id_message_id.message_id} in channel {channel.id}: {e}"
                )
                continue
            logger.info(
                f"Updating Slim in channel {channel.name} with message {message.id}"
            )
            await message.edit(embed=slim)

    @update_slim.before_loop
    async def before_my_task(self):
        await self.bot.wait_until_ready()


async def setup(client: commands.Bot) -> None:
    await client.add_cog(MVGCog(client))
