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


import argparse
import csv
import pickle
from pathlib import Path

from geojson import Feature, FeatureCollection, Point

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
    csvfile.close()


def to_geojson(data: dict[str, Station], output_file: Path) -> None:
    feature_list: list[Feature] = list()

    for station_c in data:
        station: Station = data[station_c]
        if not station.position:
            continue

        feature: Feature = Feature(
            geometry=Point((station.position[1], station.position[0])),
            properties={
                "code": station.code,
                "name": station.name,
                "short_name": station.short_name
                if hasattr(station, "short_name")
                else None,
                "region": station.region_code,
            },
        )
        feature_list.append(feature)

    collection: FeatureCollection = FeatureCollection(feature_list)
    with open(output_file, "w+") as f:
        f.write(str(collection))


def register_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "pickle_file",
        help=".pickle file to parse",
        metavar="PICKLE_FILE",
    )
    parser.add_argument(
        "-f",
        default="csv",
        choices=["csv", "geojson"],
        help="output file format",
        dest="format",
    )
    parser.add_argument(
        "-o",
        help="output file name",
        metavar="OUTPUT_FILE",
        dest="output_file",
    )


def main(args: argparse.Namespace):
    input_f, output_f, format = parse_input_format_output_args(args)

    data: dict[str, Station] = load_file(input_f)

    if format == "csv":
        to_csv(data, output_f)

    if format == "geojson":
        to_geojson(data, output_f)
