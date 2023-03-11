import itertools
import typing as t

import pytest

from src.scraper import BadRequestException, ViaggiaTrenoAPI
from src.scraper.station import Station
from src.scraper.train import Train


def test_bad_request():
    with pytest.raises(BadRequestException):
        ViaggiaTrenoAPI._raw_request("invalid", "method")


def test_ok_request():
    response: str = ViaggiaTrenoAPI._raw_request("regione", "S01700")
    assert type(response) == str
    assert response == "1"


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
def test_station_departures_or_arrivals(kind: str, station_code: str):
    response: t.List[Train] = ViaggiaTrenoAPI._station_departures_or_arrivals(
        kind, station_code
    )
    for train in response:
        assert type(train) == Train
        assert train.number is not None
        assert train.origin is not None


@pytest.mark.skip
def test_train_details():
    station: Station = Station(code="S01700", region_code=1, name="Milano Centrale")
    departing_trains: t.List[Train] = station.departures()
    for raw_train in departing_trains:
        train: Train = ViaggiaTrenoAPI.train_details(
            raw_train._raw["codOrigine"], raw_train._raw["numeroTreno"]
        )
        assert type(train) == Train
        assert train._raw["numeroTreno"] == raw_train._raw["numeroTreno"]
