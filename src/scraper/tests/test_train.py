import itertools
import json
import pathlib
import typing as t
from datetime import date, datetime

import pytest

from src import types
from src.scraper.station import Station
from src.scraper.train import Train
from src.scraper.train_stop import TrainStop, TrainStopTime

DATA_DIR = pathlib.Path("src/scraper/tests/data")


@pytest.mark.parametrize(
    "kind, station_code",
    itertools.product(
        ("partenze", "arrivi"),
        [
            "S01700",
            "S08409",
            "S09218",
            "S01608",
            "N00001",
            "N00005",
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
        if (
            not train.departed
            and not train._phantom
            and not train._trenord_phantom
            and not train.cancelled
        ):
            assert not train.arrived()


def test_unfetched_repr_1():
    milan: Station = Station.by_code("S01700")
    train: Train = Train(10911, milan, datetime.now().date())
    assert repr(train) == "Treno [?] ??? 10911 : Milano Centrale [S01700@1] -> ???"


def test_unfetched_repr_2():
    train: Train = Train._from_station_departures_arrivals(
        {
            "numeroTreno": 10911,
            "codOrigine": "S01700",
            "categoriaDescrizione": "REG",
            "dataPartenzaTreno": 1678662000000,
            "codiceCliente": 1,
            "nonPartito": False,
            "provvedimento": 0,
            "compImgCambiNumerazione": "",
        }
    )
    assert repr(train) == "Treno [D] REG 10911 : Milano Centrale [S01700@1] -> ???"


def test_hash():
    milan: Station = Station.by_code("S01700")
    trains: list[Train] = milan.departures()
    if not trains:
        return
    assert hash(trains[0]) is not None


def test_fix_intraday_datetimes():
    milan: Station = Station.by_code("S01700")
    mock_train: Train = Train(2647, milan, date(year=2023, month=3, day=25))

    mock_train.category = "REG"
    mock_train.destination = Station.by_code("S02430")
    mock_train._phantom = False
    mock_train._trenord_phantom = False
    mock_train.cancelled = False
    mock_train._fetched = datetime.now()

    with open(DATA_DIR / "train-stops_2647.json") as f:
        stops: list[types.JSONType] = json.load(f)

    mock_train.stops = list()
    for stop in stops:
        fetched_stop = TrainStop._from_trenord_raw_data(
            stop, day=mock_train.departing_date
        )
        if fetched_stop:
            mock_train.stops.append(fetched_stop)

    assert len(mock_train.stops) == 11

    mock_train._fix_intraday_datetimes()

    for i, stop in enumerate(mock_train.stops):
        expected_day = 25 if i < 4 else 26

        if i != 0:
            assert isinstance(stop.arrival, TrainStopTime)
            assert stop.arrival.expected.day == expected_day
            if isinstance(stop.arrival.actual, datetime):
                assert stop.arrival.actual.day == expected_day

        if i != len(mock_train.stops) - 1:
            assert isinstance(stop.departure, TrainStopTime)
            assert stop.departure.expected.day == expected_day
            if isinstance(stop.departure.actual, datetime):
                assert stop.departure.actual.day == expected_day
