import typing as t

from src import types


class Station:
    """A ViaggiaTreno station.

    Attributes:
        code (str): the station code, used in API calls (e.g. S01700)
        region_code (int): the code of the region where the station is located
        name (str): the station name (e.g. Milano Centrale)
        short_name (str): a shortened version of the name (e.g. Milano C.le)
        position (Tuple[float, float]): the latitude and longitude of the station
    """

    def __init__(self, station_data: dict) -> None:
        """Initialize a new station from raw API data.

        Args:
            station_data (dict): raw data returned by the API.
        """
        self._raw: types.JSONType = station_data

        self.code: str = self._raw["codStazione"]
        self.region_code: int = self._raw["codReg"]
        self.name: str = self._raw["localita"]["nomeLungo"].title()
        self.short_name: str = self._raw["localita"]["nomeBreve"].title()
        self.position: t.Tuple[float, float] = (self._raw["lat"], self._raw["lon"])
