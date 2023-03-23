import argparse
import csv
import hashlib
import pickle
from datetime import date, datetime, timedelta
from pathlib import Path

from src.const import TIMEZONE
from src.scraper.train import Train
from src.scraper.train_stop import TrainStopTime
from src.utils import parse_input_format_output_args


def load_file(file: Path) -> dict[int, Train]:
    """Load a train data pickle file and return it.

    Args:
        file (Path): the file to load

    Returns:
        dict[int, Train]: the train data contained in the file

    Notes:
        Before commit 48966dfab25553650e3d743a4ecc77db02c4b30,
        departure and arrival timestamps dates of Trenord trains
        were all 1900-01-01.
        This function fixes such incorrect dates.
    """
    with open(file, "rb") as f:
        data: dict[int, Train] = pickle.load(f)

    # Fix departure and arrival timestamps
    def _fix_datetime(train: Train, dt: datetime | None) -> datetime | None:
        if isinstance(dt, datetime) and dt.year < 2000:
            dep_date: date = train.departing_date
            dt = dt.replace(
                year=dep_date.year,
                month=dep_date.month,
                day=dep_date.day,
                tzinfo=TIMEZONE,
            )

            if dt.hour < 4:
                dt += timedelta(days=1)

        return dt

    for train_h in data:
        train: Train = data[train_h]

        for stop in train.stops if isinstance(train.stops, list) else []:
            if isinstance(stop.arrival, TrainStopTime):
                stop.arrival.actual = _fix_datetime(train, stop.arrival.actual)
                stop.arrival.expected = _fix_datetime(train, stop.arrival.expected)  # type: ignore
            if isinstance(stop.departure, TrainStopTime):
                stop.departure.actual = _fix_datetime(train, stop.departure.actual)
                stop.departure.expected = _fix_datetime(train, stop.departure.expected)  # type: ignore

    return data


def to_csv(data: dict[int, Train], output_file: Path) -> None:
    """Convert to CSV train data, one row per stop.

    Args:
        data (dict[int, Train]): the data to convert
        output_file (Path): the file to write
    """
    FIELDS: tuple = (
        "train_hash",
        "number",
        "day",
        "origin",
        "destination",
        "category",
        "client_code",
        "phantom",
        "trenord_phantom",
        "cancelled",
        "stop_number",
        "stop_station_code",
        "stop_type",
        "platform",
        "arrival_expected",
        "arrival_actual",
        "arrival_delay",
        "departure_expected",
        "departure_actual",
        "departure_delay",
        "crowding",
    )

    csvfile = open(output_file, "w+", newline="")
    writer = csv.writer(
        csvfile,
        delimiter=",",
        quotechar="|",
        quoting=csv.QUOTE_MINIMAL,
    )
    writer.writerow(FIELDS)

    for train_h in data:
        train: Train = data[train_h]

        for i, stop in enumerate(train.stops) if isinstance(train.stops, list) else []:
            writer.writerow(
                (
                    hashlib.md5(str(train_h).encode("ascii")).hexdigest(),
                    train.number,
                    train.departing_date.isoformat(),
                    train.origin.code,
                    train.destination.code if train.destination else None,
                    train.category,
                    train.client_code,
                    train._phantom,
                    train._trenord_phantom
                    if hasattr(train, "_trenord_phantom")
                    else False,
                    train.cancelled,
                    i,
                    stop.station.code,
                    stop.stop_type.value,
                    stop.platform_actual or stop.platform_expected,
                    stop.arrival.expected.isoformat()
                    if stop.arrival and stop.arrival.expected
                    else None,
                    stop.arrival.actual.isoformat()
                    if stop.arrival and stop.arrival.actual
                    else None,
                    stop.arrival.delay() if stop.arrival else None,
                    stop.departure.expected.isoformat()
                    if stop.departure and stop.departure.expected
                    else None,
                    stop.departure.actual.isoformat()
                    if stop.departure and stop.departure.actual
                    else None,
                    stop.departure.delay() if stop.departure else None,
                    train.crowding if hasattr(train, "crowding") else None,
                )
            )

    csvfile.close()


def main(args: argparse.Namespace):
    input_f, output_f, format = parse_input_format_output_args(args)

    data: dict[int, Train] = load_file(input_f)
    if format == "csv":
        to_csv(data, output_f)
