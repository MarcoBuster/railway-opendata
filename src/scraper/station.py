import typing as t

from src import types
from src.scraper import ViaggiaTrenoAPI
from src.scraper.train import Train


class Station:
    """A ViaggiaTreno station.

    Attributes:
        code (str): the station code, used in API calls (e.g. S01700)
        region_code (int): the code of the region where the station is located
        name (str): the station name (e.g. Milano Centrale)
        short_name (str): a shortened version of the name (e.g. Milano C.le)
        position (Tuple[float, float] | None): the latitude and longitude of the station
    """

    _cache: dict[str, "Station"] = dict()

    def __init__(
        self,
        code: str,
        region_code: int,
        name: str,
        short_name: str | None = None,
        position: t.Tuple[float, float] | None = None,
    ) -> None:
        """Initialize a new station.

        Args:
            code (str): the station code, used in API calls (e.g. S01700)
            region_code (int): the code of the region where the station is located
            name (str): the station name (e.g. Milano Centrale)
            short_name (str, optional): a shortened version of the name (e.g. Milano C.le)
            position (Tuple[float, float] | None, optional): the latitude and longitude of the station
        """
        self.code: str = code
        self.region_code: int = region_code
        self.name: str = name.title().strip()
        self.short_name: str = short_name.title().strip() if short_name else name
        self.position: t.Tuple[float, float] | None = position

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
                cached.region_code = Station._region_code(station_code)

        return cls._cache[station_code]

    def __repr__(self) -> str:
        return f"Stazione di {self.name} [{self.code}@{self.region_code}]"

    @classmethod
    def by_code(cls, station_code: str) -> "Station":
        """Retrieve a station by its code, or use cache.

        Args:
            station_code (str): the station code

        Returns:
            Station: a station corresponding to the passed station code
        """
        if station_code not in cls._cache:
            region_code: int = cls._region_code(station_code)
            response: str = ViaggiaTrenoAPI._raw_request(
                "dettaglioStazione", station_code, region_code
            )
            raw_data: types.JSONType = ViaggiaTrenoAPI._decode_json(response)
            cls._cache[station_code] = cls._from_raw(raw_data)

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
        region_code = ViaggiaTrenoAPI._raw_request("regione", station_code)
        return int(region_code)

    @classmethod
    def by_region(cls, region_code: int) -> t.List["Station"]:
        """Retrieve the list of train stations of a given region.

        Args:
            region_code (int): the code of the region to query

        Returns:
            t.List[Station]: a list of train stations
        """
        raw_stations: str = ViaggiaTrenoAPI._raw_request("elencoStazioni", region_code)
        stations: types.JSONType = ViaggiaTrenoAPI._decode_json(raw_stations)
        return list(
            map(
                lambda s: cls._from_raw(s),
                filter(lambda s: s["tipoStazione"] != 4, stations),
            )
        )

    def departures(self) -> t.List[Train]:
        """Retrieve the departures of a train station.

        Args:
            station_code (str): the code of the considered station

        Returns:
            t.List[Train]: a list of trains departing from the station
        """
        return ViaggiaTrenoAPI._station_departures_or_arrivals("partenze", self.code)

    def arrivals(self) -> t.List[Train]:
        """Retrieve the arrivals of a train station.

        Args:
            station_code (str): the code of the considered station

        Returns:
            t.List[Train]: a list of trains departing from the station
        """
        return ViaggiaTrenoAPI._station_departures_or_arrivals("arrivi", self.code)
