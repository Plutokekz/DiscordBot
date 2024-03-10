from datetime import datetime
import random
from typing import List, Tuple

import discord
from discord.embeds import Embed
from bot.cogs.deutschebahn.rs_api.api import RS
from bot.cogs.deutschebahn.rs_api.model import Station as ST


class Station:
    api: RS

    def __init__(self, api: RS):
        self.api = api

    async def get_station_of_the_day(self) -> Tuple[Embed, List[Embed]]:
        countries = await self.api.get_countries()
        country = random.choice(list(countries.__root__))

        stations = await self.api.get_photo_station_by_country(
            country.code, has_photo=True
        )
        while len(stations.stations) == 0:
            country = random.choice(list(countries.__root__))
            stations = await self.api.get_photo_station_by_country(
                country.code, has_photo=True
            )
        station: ST = random.choice(stations.stations)
        active = "Die Station ist noch aktiv und wird genutzt."
        if station.inactive:
            active = "Die Station ist leider inaktiv und wird schon länger nicht mehr genutzt."

        short_code = ""
        if (
            station.shortCode is not None
            and station.shortCode != "NULL"
            and station.shortCode != "**"
            and station.shortCode
        ):
            short_code = f"Sie besitzt die Abkürzung **{station.shortCode}**, welche Bahn angestelten genutzt wird."

        station_of_the_day = Embed(
            colour=discord.Colour.dark_red(),
            color=discord.Color.lighter_grey(),
            title=station.title,
            description=f"Diese wunder schöne Station aus {country.name}, ist heute die Station "
            f"des Tages. Sie befindet sich genau [hier](https://www.google.com/maps/"
            f"@{station.lat},{station.lon},15z). {active} {short_code}",
        )
        _photos = []
        for photo in station.photos[: min(4, len(station.photos))]:
            photo_embed = Embed(
                colour=discord.Colour.dark_red(),
                color=discord.Color.lighter_grey(),
                timestamp=datetime.fromtimestamp(photo.createdAt / 1000),
            )
            photo_embed.set_author(name=f"Fotograf: {photo.photographer}")
            photo_embed.set_footer(text=f"LIZENZ: {photo.license}")
            photo_embed.set_image(
                url=f"https://apis.deutschebahn.com/db-api-marketplace/apis/api.railway-stations"
                f".org/photos/{photo.path}"
            )
            _photos.append(photo_embed)
        return station_of_the_day, _photos
