import json
import pathlib
import typing as t

import pytest

from src import types
from src.scraper import BadRequestException, Station

DATA_DIR = pathlib.Path("src/scraper/tests/data")


@pytest.mark.parametrize(
    "station_file, expected",
    [
        (
            "station_S01700.json",
            {
                "code": "S01700",
                "region_code": 1,
                "name": "Milano Centrale",
                "short_name": "Milano Centrale",
                "position": (45.486347, 9.204528),
            },
        ),
        (
            "station_S01608.json",
            {
                "code": "S01608",
                "region_code": 1,
                "name": "Arcene",
                "short_name": "Arcene",
                "position": (45.577162, 9.606652),
            },
        ),
    ],
)
def test_init(station_file: str, expected: dict):
    with open(DATA_DIR / station_file, "r") as f:
        data: types.JSONType = json.load(f)

    station = Station._from_raw(data)
    assert station.code == expected["code"]
    assert station.region_code == expected["region_code"]
    assert station.name == expected["name"]
    assert station.short_name == expected["short_name"]
    assert station.position == expected["position"]


@pytest.mark.parametrize("region_code", range(0, 22 + 1))
def test_assumptions(region_code):
    """For each station returned by the API, we assume there is no None field."""
    response: t.List[Station] = Station.by_region(region_code)
    for station in response:
        assert station.code is not None
        assert station.region_code == region_code
        assert station.name is not None
        assert station.short_name is not None
        assert station.position is not None


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
    response: int = Station._region_code(station_code)
    assert type(response) == int
    assert response == region_code


def test_station_region_code_invalid():
    with pytest.raises(BadRequestException):
        Station._region_code("S00000")


@pytest.mark.parametrize("region_code", range(0, 22 + 1))
def test_by_region(region_code):
    response: t.List[Station] = Station.by_region(region_code)
    for station in response:
        assert type(station) == Station
        assert station.region_code == region_code
