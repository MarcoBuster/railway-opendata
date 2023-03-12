import itertools
import typing as t

import pytest

from src.scraper.station import Station
from src.scraper.train import Train


@pytest.mark.parametrize(
    "kind, station_code",
    itertools.product(
        ("partenze", "arrivi"),
        [
            "S01700",
            "S08409",
            "S09218",
            "S01608",
        ],
    ),
)
def test_fetch(kind, station_code):
    station: Station = Station.by_code(station_code)
    trains: t.List[Train] = (
        station.departures() if kind == "partenze" else station.arrivals()
    )
    for train in trains:
        train.fetch()
