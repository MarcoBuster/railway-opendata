import argparse
import logging
import os
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

train_extractor.register_args(
    subparsers.add_parser(
        "train-extractor",
        help="convert scraped train data",
    )
)
station_extractor.register_args(
    subparsers.add_parser(
        "station-extractor",
        help="convert scraped station data",
    )
)
analysis.register_args(
    subparsers.add_parser(
        "analyze",
        help="data analyzer and visualizer",
    )
)


def main():
    hashseed: str | None = os.getenv("PYTHONHASHSEED")
    if not hashseed or hashseed != "0":
        logging.critical(
            "Hash seed randomization is not disabled. "
            "Please disable it by setting the PYTHONHASHSEED=0 environment variable."
        )
        sys.exit(1)

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
