# railway-opendata: scrape and analyze italian railway data
# Copyright (C) 2023 Marco Aceti
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


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
