import argparse
import logging
import sys

import src.analysis.main as analysis
import src.scraper.main as scraper
from src import station_extractor, train_extractor

parser = argparse.ArgumentParser(
    prog="train-scraper",
)
subparsers = parser.add_subparsers(dest="subcommand", required=True)
parser.add_argument("-d", "--debug", action="store_true", help="activate debug logs")

scraper_p = subparsers.add_parser(
    "scraper",
    help="station and train data scraper",
)

# Train extractor arguments
t_extractor = subparsers.add_parser(
    "train-extractor",
    help="convert scraped train data",
)
t_extractor.add_argument(
    "pickle_file",
    help=".pickle file to parse",
    metavar="PICKLE_FILE",
)
t_extractor.add_argument(
    "-f",
    default="csv",
    choices=[
        "csv",
    ],
    help="output file format",
    dest="format",
)
t_extractor.add_argument(
    "-o",
    help="output file name",
    metavar="OUTPUT_FILE",
    dest="output_file",
)

# Station extractor arguments
s_extractor = subparsers.add_parser(
    "station-extractor",
    help="convert scraped station data",
)
s_extractor.add_argument(
    "pickle_file",
    help=".pickle file to parse",
    metavar="PICKLE_FILE",
)
s_extractor.add_argument(
    "-f",
    default="csv",
    choices=["csv", "geojson"],
    help="output file format",
    dest="format",
)
s_extractor.add_argument(
    "-o",
    help="output file name",
    metavar="OUTPUT_FILE",
    dest="output_file",
)

analysis.register_args(
    subparsers.add_parser(
        "analyze",
        help="data analyzer and visualizer",
    )
)


def main():
    args: argparse.Namespace = parser.parse_args()

    logging.basicConfig(
        stream=sys.stdout,
        format="[%(asctime)s - %(levelname)s] %(message)s",
        level=logging.INFO if not args.debug else logging.DEBUG,
    )

    if args.subcommand == "scraper":
        scraper.main()

    if args.subcommand == "train-extractor":
        train_extractor.main(args)

    if args.subcommand == "station-extractor":
        station_extractor.main(args)

    if args.subcommand == "analyze":
        analysis.main(args)


if __name__ == "__main__":
    main()
