import json
import typing as t
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter, Retry

import src.scraper.train as tr
from src import types
from src.const import TIMEZONE, TIMEZONE_GMT
from src.scraper.exceptions import BadRequestException


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
                status_forcelist=[403, 500, 502, 503, 504],
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
    def _to_datetime(time: int | None) -> datetime | None:
        """Convert a UNIX timestamp with milliseconds to datetime.
        If None is passed, None is returned.

        Args:
            time (int | None): the UNIX timestamp to convert

        Returns:
            datetime | None: the resulting datetime object
        """
        if not time:
            return None

        return datetime.fromtimestamp(time / 1000, tz=TIMEZONE)

    @staticmethod
    def _station_departures_or_arrivals(
        kind: str, station_code: str
    ) -> t.List["tr.Train"]:
        """Helper function to Station.departures and Station.arrivals methods.

        Args:
            kind (str): either 'partenze' (departures) or 'arrivi' (arrivals)
            station_code (str): the code of the considered station

        Returns:
            t.List[Train]: a list of trains departing o arriving to the station
        """
        assert kind in ["partenze", "arrivi"]

        now: str = datetime.now(tz=TIMEZONE_GMT).strftime("%a %b %d %Y %H:%M:%S %Z%z")
        raw_trains: str = ViaggiaTrenoAPI._raw_request(kind, station_code, now)
        trains: types.JSONType = ViaggiaTrenoAPI._decode_json(raw_trains)
        return list(
            map(
                lambda t: tr.Train._from_station_departures_arrivals(t),
                trains,
            )
        )


class TrenordAPI:
    BASE_URL: str = "https://admin.trenord.it/store-management-api/mia/"

    TRENORD_CLIENT_CODE: int = 63

    # Initialize requests session with auto-retry and exponential backoff
    _session: requests.Session = requests.Session()
    _session.mount(
        "http://",
        HTTPAdapter(
            max_retries=Retry(
                total=10,
                read=5,
                status=10,
                status_forcelist=[403, 500, 502, 503, 504],
                backoff_factor=0.2,
            )
        ),
    )

    @classmethod
    def _raw_request(cls, method: str, *parameters: t.Any) -> str:
        """Perform a HTTP request to Trenord API and return a raw string,
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
            f"{TrenordAPI.BASE_URL}{method}/"
            f"{'/'.join(map(lambda p: str(p), parameters))}"
        )

        if response.status_code != 200 or "Error" in response.text:
            raise BadRequestException(
                url=response.url,
                status_code=response.status_code,
                response=response.text,
            )

        return response.text
