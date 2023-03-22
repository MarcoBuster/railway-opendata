import logging
import os
import sys

hashseed = os.getenv("PYTHONHASHSEED")
if not hashseed or hashseed != "0":
    logging.critical(
        "Hash seed randomization is not disabled. "
        "Please disable it by setting PYTHONHASHSEED=0 environment variable"
    )
    sys.exit(1)

import argparse

import src.scraper.main as scraper
from src import extractor

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
        extractor.main(args)


if __name__ == "__main__":
    main()
