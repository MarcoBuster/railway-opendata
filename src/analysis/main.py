import argparse
import logging
import pathlib
from datetime import datetime

import pandas as pd
from dateparser import parse
from tqdm import tqdm

from src.analysis import stat
from src.analysis.filter import date_filter
from src.analysis.load_data import read_station_csv, read_train_csv


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
        choices=("describe",),
        default="describe",
    )
    parser.add_argument(
        "--format",
        help="output format",
        choices=(
            "human",
            "csv",
        ),
        default="human",
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

    # Load dataset
    df = pd.DataFrame()
    logging.info("Loading datasets...")
    for train_csv in (
        tqdm(args.trains_csv)
        if logging.root.getEffectiveLevel() > logging.DEBUG
        else args.trains_csv
    ):
        path = pathlib.Path(train_csv)
        train_df: pd.DataFrame = read_train_csv(pathlib.Path(train_csv))
        df = pd.concat([df, train_df], axis=0)
        logging.debug(f"Loaded {len(train_df)} data points @ {path}")

    stations: pd.DataFrame = read_station_csv(args.station_csv)
    original_length: int = len(df)

    # Apply filters
    df = date_filter(df, start_date, end_date)
    logging.info(f"Loaded {len(df)} data points ({original_length} before filtering)")

    if args.stat == "describe":
        df = stat.describe(df)

    if args.format == "human":
        print(df)
    elif args.format == "csv":
        print(df.to_csv())
