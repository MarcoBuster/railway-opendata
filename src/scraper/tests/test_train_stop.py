import json
import pathlib
from datetime import datetime

import pytest

from src import types
from src.scraper.train_stop import TrainStop, TrainStopTime

DATA_DIR = pathlib.Path("src/scraper/tests/data")


t1 = datetime(year=2023, month=1, day=1, hour=12, minute=00, second=0)
t2 = datetime(year=2023, month=1, day=1, hour=12, minute=5, second=30)
t3 = datetime(year=2023, month=1, day=1, hour=12, minute=6, second=0)


@pytest.mark.parametrize(
    "expected, actual, passed, delay",
    [
        (t1, t2, True, 5.5),
        (t1, None, False, None),
        (t3, t2, True, -0.5),
        (t3, t1, True, -6),
    ],
)
def test_stop_time(
    expected: datetime, actual: datetime | None, passed: bool, delay: int | None
):
    stop_time: TrainStopTime = TrainStopTime(expected=expected, actual=actual)
    assert stop_time.passed() == passed
    assert stop_time.delay() == delay


def test_stop_time_assumption():
    with pytest.raises(AssertionError):
        TrainStopTime(None, actual=t1)  # type: ignore


@pytest.mark.parametrize(
    "data_file, expected_repr",
    [
        ("train-stop_10860.json", "@ Piacenza 09:07 ~ 09:07 +0.5m [5 ~ 5]"),
        ("train-stop_3073.json", "@ Arquata Scrivia 17:43 --> 17:44 [5]"),
        (
            "train-stop_555.json",
            "@ Latina 14:58 ~ 15:01 +3.5m --> 15:00 ~ 15:03 +3.5m [? ~ 2]",
        ),
        ("train-stop_22662.json", "@ Treviglio 17:50 [2 TR Ovest]"),
    ],
)
def test_stop_repr(data_file, expected_repr):
    with open(DATA_DIR / data_file, "r") as f:
        data: types.JSONType = json.load(f)

    stop: TrainStop = TrainStop._from_raw_data(stop_data=data)
    assert repr(stop) == expected_repr
