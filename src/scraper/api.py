import json
import typing as t
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter, Retry

from src import types
from src.const import TIMEZONE
from src.scraper import Station, Train


class BadRequestException(Exception):
    """Bad request to ViaggiaTreno API."""

    def __init__(
        self, url: str, status_code: int, response: str, *args: object
    ) -> None:
        """Creates a BadRequestException.

        Args:
            url (str): the request URL
            status_code (int): the response status code
            response (str): the response data
        """
        self.url = url
        self.status_code = status_code
        self.response = response
        super().__init__(*args)


class ViaggiaTrenoAPI:
    BASE_URL: str = "http://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/"

    # Initialize requests session with auto-retry and exponential backoff
    _session: requests.Session = requests.Session()
    _session.mount(
        "http://",
        HTTPAdapter(
            max_retries=Retry(
                total=10,
                read=5,
                status=10,
                status_forcelist=[500, 502, 503, 504],
                backoff_factor=0.2,
            )
        ),
    )

    @classmethod
    def _raw_request(cls, method: str, *parameters: t.Any) -> str:
        """Perform a HTTP request to ViaggiaTreno API and return a raw string,
        if the request has been successful.

        Args:
            method (str): the method to be called
            parameters (tuple[str]): a list of parameters

        Raises:
            BadRequestException: if the response is not ok

        Returns:
            str: the raw response from the API
        """
        response: requests.Response = cls._session.get(
            f"{ViaggiaTrenoAPI.BASE_URL}{method}/"
            f"{'/'.join(map(lambda p: str(p), parameters))}"
        )

        if response.status_code != 200 or "Error" in response.text:
            raise BadRequestException(
                url=response.url,
                status_code=response.status_code,
                response=response.text,
            )

        return response.text

    @staticmethod
    def _decode_json(string: str) -> types.JSONType:
        """Decode a JSON string.

        Args:
            string (str): the string to decode

        Returns:
            types.JSONType: the decoded JSON value
        """
        return json.loads(string)

    @staticmethod
    def station_region_code(station_code: str) -> int:
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

    @staticmethod
    def list_stations(region_code: int) -> t.List[Station]:
        """Retrieve the list of train stations of a given region.

        Args:
            region_code (int): the code of the region to query

        Returns:
            t.List[Station]: a list of train stations
        """
        raw_stations: str = ViaggiaTrenoAPI._raw_request("elencoStazioni", region_code)
        stations: types.JSONType = ViaggiaTrenoAPI._decode_json(raw_stations)
        return list(
            filter(
                # stations with tipoStazione == 4 are just placeholders
                lambda s: s._raw["tipoStazione"] != 4,
                map(lambda s: Station(s), list(stations)),
            )
        )

    @staticmethod
    def _station_departures_or_arrivals(kind: str, station_code: str) -> t.List[Train]:
        """Helper function to .station_departures and .station_arrivals methods.

        Args:
            kind (str): either 'partenze' (departures) or 'arrivi' (arrivals)
            station_code (str): the code of the considered station

        Returns:
            t.List[Train]: a list of trains departing o arriving to the station
        """
        assert kind in ["partenze", "arrivi"]

        now: str = datetime.now(tz=TIMEZONE).strftime("%a %b %d %Y %H:%M:%S %Z%z")
        raw_trains: str = ViaggiaTrenoAPI._raw_request(kind, station_code, now)
        trains: types.JSONType = ViaggiaTrenoAPI._decode_json(raw_trains)
        return list(map(lambda t: Train(t), trains))

    @staticmethod
    def station_departures(station_code: str) -> t.List[Train]:
        """Retrieve the departures of a train station.

        Args:
            station_code (str): the code of the considered station

        Returns:
            t.List[Train]: a list of trains departing from the station
        """
        return ViaggiaTrenoAPI._station_departures_or_arrivals("partenze", station_code)

    @staticmethod
    def station_arrivals(station_code: str) -> t.List[Train]:
        """Retrieve the arrivals of a train station.

        Args:
            station_code (str): the code of the considered station

        Returns:
            t.List[Train]: a list of trains departing from the station
        """
        return ViaggiaTrenoAPI._station_departures_or_arrivals("arrivi", station_code)

    @staticmethod
    def train_details(departing_station_code: str, train_number: int) -> Train:
        """Retreive the details of a train.

        Args:
            departing_station_code (str): the code of the departure station of the train
            train_number (int): the train number to check

        Returns:
            Train: the details of the train

        Notes:
            A train number alone DOES NOT uniquely identify a train.
        """

        # Calculate midnight of today
        now: datetime = datetime.now()
        midnight: datetime = datetime(
            year=now.year, month=now.month, day=now.day, hour=0, minute=0, second=0
        )

        raw_details: str = ViaggiaTrenoAPI._raw_request(
            "andamentoTreno",
            departing_station_code,
            train_number,
            int(midnight.timestamp() * 1000),
        )
        train_details: types.JSONType = ViaggiaTrenoAPI._decode_json(raw_details)
        return Train(train_details)
