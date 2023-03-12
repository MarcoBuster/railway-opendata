import itertools
import typing as t

import pytest

from src.scraper import BadRequestException, ViaggiaTrenoAPI
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
