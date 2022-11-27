from typing import Dict, Any

import httpx
from cogs.deutschebahn.rs_api.model import CountryList, Model


class RS:
    client: httpx.AsyncClient
    base_url: str = "https://apis.deutschebahn.com/db-api-marketplace/apis/api.railway-stations.org"

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def _send_get_request(self, url: str) -> Dict[str, Any]:
        response = await self.client.get(self.base_url + url)
        if response.status_code == 200:
            return response.json()

    async def get_countries(self) -> CountryList | None:
        """
        List of all supported countries with their configuration
        :return:
        """
        if (response := await self._send_get_request("/countries.json")) is not None:
            return CountryList(__root__=response)

    async def get_photo_station_by_id(self, country: str, _id: int) -> Model | Any:
        """
        Get a railway station of a country by its id with all its photos
        :param country:
        :param _id:
        :return:
        """
        if (response := await self._send_get_request(f"/photoStationById/{country}/{_id}")) is not None:
            return Model(**response)

    async def get_photo_station_by_country(self, country: str, has_photo: bool = False) -> Model | Any:
        """
        List stations by country
        :param has_photo:
        :param country:
        :return:
        """
        if (response := await self._send_get_request(
                f"/photoStationsByCountry/{country}?hasPhoto={has_photo}")) is not None:
            return Model(**response)

    async def get_photo_stations_by_photographer(self, photographer: str):
        """
        List stations with photos by the given photographer
        :param photographer:
        :return:
        """
        if (response := await self._send_get_request(f"/photoStationsByPhotographer/{photographer}")) is not None:
            return Model(**response)

    async def get_photo_stations_by_recent_photo_imports(self, since_hours: int = 10):
        """
        List stations with photos uploaded in the last 24h
        :return:
        """
        if (response := await self._send_get_request(
                f"/photoStationsByRecentPhotoImports?sinceHours={since_hours}")) is not None:
            return Model(**response)

    async def get_photo(self, country: str, filename: str):
        """
        downloads the given photo
        :param country:
        :param filename:
        :return:
        """
        if (response := await self._send_get_request(f"/photos/{country}/{filename}")) is not None:
            return Model(**response)
