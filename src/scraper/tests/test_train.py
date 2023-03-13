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


def test_unfetched_repr_1():
    milan: Station = Station.by_code("S01700")
    train: Train = Train(10911, milan)
    assert repr(train) == "Treno [?] ??? 10911 : Milano Centrale [S01700@1] -> ???"


def test_unfetched_repr_2():
    train: Train = Train._from_station_departures_arrivals(
        {
            "numeroTreno": 10911,
            "codOrigine": "S01700",
            "categoriaDescrizione": "REG",
            "nonPartito": False,
            "provvedimento": 0,
        }
    )
    assert repr(train) == "Treno [D] REG 10911 : Milano Centrale [S01700@1] -> ???"


def test_hash():
    milan: Station = Station.by_code("S01700")
    trains: list[Train] = milan.departures()
    if not trains:
        return
    assert hash(trains[0]) is not None
