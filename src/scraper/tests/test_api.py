import itertools
import typing as t

import pytest

from src.scraper import BadRequestException, Station, Train, ViaggiaTrenoAPI


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
        assert train._raw["numeroTreno"] is not None
        assert train._raw["codOrigine"] is not None


def test_train_details():
    departing_trains: t.List[Train] = ViaggiaTrenoAPI.station_departures("S01700")
    for raw_train in departing_trains:
        train: Train = ViaggiaTrenoAPI.train_details(
            raw_train._raw["codOrigine"], raw_train._raw["numeroTreno"]
        )
        assert type(train) == Train
        assert train._raw["numeroTreno"] == raw_train._raw["numeroTreno"]
