import typing as t

import pytest

from src.scraper import BadRequestException, Station, ViaggiaTrenoAPI


def test_bad_request():
    with pytest.raises(BadRequestException):
        ViaggiaTrenoAPI._raw_request("invalid", "method")


def test_ok_request():
    response: str = ViaggiaTrenoAPI._raw_request("regione", "S01700")
    assert type(response) == str
    assert response == "1"


@pytest.mark.parametrize(
    "station_code, region_code",
    [
        ("S01700", 1),  # Milano Centrale
        ("S08409", 5),  # Roma Termini
        ("S09218", 18),  # Napoli Centrale
        ("S01608", 1),  # Arcene
    ],
)
def test_station_region_code(station_code, region_code):
    response: int = ViaggiaTrenoAPI.station_region_code(station_code)
    assert type(response) == int
    assert response == region_code


def test_station_region_code_invalid():
    with pytest.raises(BadRequestException):
        ViaggiaTrenoAPI.station_region_code("S00000")


@pytest.mark.parametrize("region_code", range(0, 22 + 1))
def test_list_stations(region_code):
    response: t.List[Station] = ViaggiaTrenoAPI.list_stations(region_code)
    for station in response:
        assert type(station) == Station
        assert station._raw["codReg"] == region_code
        assert station._raw["tipoStazione"] != 4
