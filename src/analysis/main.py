import argparse
from datetime import datetime

from dateparser import parse


def register_args(parser: argparse.ArgumentParser):
    parser.add_argument(
        "--start-date",
        help="the start date in a 'dateparser'-friendly format",
    )
    parser.add_argument(
        "--end-date",
        help="the end date in a 'dateparser'-friendly format",
    )
    parser.add_argument(
        "--stat",
        help="the stat to calculate",
    )
    parser.add_argument(
        "station_csv",
        help="exported station CSV",
    )
    parser.add_argument(
        "trains_csv",
        nargs="+",
        help="exported train CSV",
    )


def main(args: argparse.Namespace):
    start_date: datetime | None = parse(args.start_date if args.start_date else "")
    if args.start_date and not start_date:
        raise argparse.ArgumentTypeError("invalid start_date")

    end_date: datetime | None = parse(args.end_date if args.end_date else "")
    if args.end_date and not end_date:
        raise argparse.ArgumentTypeError("invalid end_date")

    raise NotImplementedError()
