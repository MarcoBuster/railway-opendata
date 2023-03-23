import argparse
import csv
import pickle
from pathlib import Path

from src.scraper.station import Station
from src.utils import parse_input_format_output_args


def load_file(file: Path) -> dict[str, Station]:
    """Load a station data pickle file and return it.

    Args:
        file (Path): the file to load

    Returns:
        dict[str, Station]: the station data contained in the file
    """
    with open(file, "rb") as f:
        data: dict[str, Station] = pickle.load(f)

    return data


def to_csv(data: dict[str, Station], output_file: Path) -> None:
    """Convert to CSV station data, one row per station.

    Args:
        data (dict[int, Station]): the data to convert
        output_file (Path): the file to write
    """
    FIELDS: tuple = (
        "code",
        "region",
        "long_name",
        "short_name",
        "latitude",
        "longitude",
    )

    csvfile = open(output_file, "w+", newline="")
    writer = csv.writer(
        csvfile,
        delimiter=",",
        quotechar="|",
        quoting=csv.QUOTE_MINIMAL,
    )
    writer.writerow(FIELDS)

    for station_c in data:
        station: Station = data[station_c]
        writer.writerow(
            (
                station.code,
                station.region_code,
                station.name,
                station.short_name if hasattr(station, "short_name") else None,
                station.position[0] if station.position else None,
                station.position[1] if station.position else None,
            )
        )


def main(args: argparse.Namespace):
    input_f, output_f, format = parse_input_format_output_args(args)

    data: dict[str, Station] = load_file(input_f)
    if format == "csv":
        to_csv(data, output_f)
