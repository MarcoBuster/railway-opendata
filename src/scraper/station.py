# railway-opendata: scrape and analyze italian railway data
# Copyright (C) 2023 Marco Aceti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import logging
import typing as t

import src.scraper.api as api
import src.scraper.train as tr
from src import types
from src.scraper.exceptions import BadRequestException


class Station:
    """A ViaggiaTreno station.

    Attributes:
        code (str): the station code, used in API calls (e.g. S01700)
        region_code (int): the code of the region where the station is located
        name (str | None): the station name (e.g. Milano Centrale)
        short_name (str | None): a shortened version of the name (e.g. Milano C.le)
        position (Tuple[float, float] | None): the latitude and longitude of the station

    Other attributes:
        _phantom (bool): if True, the details of the station can't be fetched
    """

    _cache: dict[str, "Station"] = dict()

    def __init__(
        self,
        code: str,
        region_code: int,
        name: str | None,
        short_name: str | None = None,
        position: t.Tuple[float, float] | None = None,
    ) -> None:
        """Initialize a new station.

        Args:
            code (str): the station code, used in API calls (e.g. S01700)
            region_code (int): the code of the region where the station is located
            name (str | None): the station name (e.g. Milano Centrale)
            short_name (str | None, optional): a shortened version of the name (e.g. Milano C.le)
            position (Tuple[float, float] | None, optional): the latitude and longitude of the station
        """
        self.code: str = code
        self.region_code: int = region_code
        self.name: str | None = None
        if name:
            self.name: str | None = name.title().strip()
            self.short_name: str | None = (
                short_name.title().strip() if short_name else name
            )
        self.position: t.Tuple[float, float] | None = position

        self._phantom: bool = self.name == None

    @classmethod
    def _from_raw(cls, raw_data: dict) -> "Station":
        """Initialize a new station from raw API data, or use the class cache.

        Args:
            station_data (dict): raw data returned by the API.
        """
        station_code = raw_data["codStazione"]

        if station_code not in cls._cache:
            cls._cache[station_code] = cls(
                code=station_code,
                region_code=raw_data["codReg"],
                name=raw_data["localita"]["nomeLungo"],
                short_name=raw_data["localita"]["nomeBreve"],
                position=(raw_data["lat"], raw_data["lon"]),
            )
        else:
            cached: Station = cls._cache[station_code]

            # codReg can have multiple values depending on the request.
            # If an inequality is detected, settle the correct region_code once for all.
            if raw_data["codReg"] != cached.region_code:
                logging.warning(
                    f"Provided region code for {station_code} is different from the cached one"
                )
                cached.region_code = Station._region_code(station_code)

        return cls._cache[station_code]

    def __repr__(self) -> str:
        return f"{self.name} [{self.code}@{self.region_code}]"

    @classmethod
    def by_code(cls, station_code: str) -> "Station":
        """Retrieve a station by its code, or use cache.

        Args:
            station_code (str): the station code

        Returns:
            Station: a station corresponding to the passed station code
        """
        if station_code not in cls._cache:
            try:
                region_code: int = cls._region_code(station_code)
            except BadRequestException as e:
                if e.status_code != 204:
                    raise e

                region_code: int = 0

            try:
                response: str = api.ViaggiaTrenoAPI._raw_request(
                    "dettaglioStazione", station_code, region_code
                )
                raw_data: types.JSONType = api.ViaggiaTrenoAPI._decode_json(response)
                cls._cache[station_code] = cls._from_raw(raw_data)
            except BadRequestException as e:
                if e.status_code != 204:
                    raise e

                cls._cache[station_code] = cls(
                    code=station_code,
                    region_code=region_code,
                    name=None,
                )

        return cls._cache[station_code]

    @staticmethod
    def _region_code(station_code: str) -> int:
        """Retrieve the region code of a given station (by its code).

        Args:
            station_code (str): the code of the station to check

        Raises:
            BadRequestException: if the response is not ok

        Returns:
            int: the region code of the given station
        """
        region_code = api.ViaggiaTrenoAPI._raw_request("regione", station_code)
        return int(region_code)

    @classmethod
    def by_region(cls, region_code: int) -> t.List["Station"]:
        """Retrieve the list of train stations of a given region.

        Args:
            region_code (int): the code of the region to query

        Returns:
            t.List[Station]: a list of train stations
        """
        raw_stations: str = api.ViaggiaTrenoAPI._raw_request(
            "elencoStazioni", region_code
        )
        stations: types.JSONType = api.ViaggiaTrenoAPI._decode_json(raw_stations)
        return list(
            map(
                lambda s: cls._from_raw(s),
                filter(lambda s: s["tipoStazione"] != 4, stations),
            )
        )

    def departures(self) -> t.List["tr.Train"]:
        """Retrieve the departures of a train station.

        Args:
            station_code (str): the code of the considered station

        Returns:
            t.List[Train]: a list of trains departing from the station
        """
        return api.ViaggiaTrenoAPI._station_departures_or_arrivals(
            "partenze", self.code
        )

    def arrivals(self) -> t.List["tr.Train"]:
        """Retrieve the arrivals of a train station.

        Args:
            station_code (str): the code of the considered station

        Returns:
            t.List[Train]: a list of trains departing from the station
        """
        return api.ViaggiaTrenoAPI._station_departures_or_arrivals("arrivi", self.code)

    def __hash__(self) -> int:
        return hash(self.name)
