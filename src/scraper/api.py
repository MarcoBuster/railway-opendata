import json
import typing as t

import requests

from src import types
from src.scraper import Station


class BadRequestException(Exception):
    """Bad request to ViaggiaTreno API."""

    def __init__(self, status_code: int, response: str, *args: object) -> None:
        """Creates a BadRequestException.

        Args:
            status_code (int): the response status code
            response (str): the response data
        """
        self.status_code = status_code
        self.response = response
        super().__init__(*args)


class ViaggiaTrenoAPI:
    BASE_URL: str = "http://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/"

    @staticmethod
    def _raw_request(method: str, *parameters: str) -> str:
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
        response: requests.Response = requests.get(
            f"{ViaggiaTrenoAPI.BASE_URL}{method}/"
            f"{'/'.join(map(lambda p: str(p), parameters))}"
        )

        if response.status_code != 200 or "Error" in response.text:
            raise BadRequestException(
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
        return map(lambda s: Station(s), list(stations))
