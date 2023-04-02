import argparse
import logging
import pathlib
from datetime import datetime

import pandas as pd
from dateparser import parse
from pandas.core.groupby.generic import DataFrameGroupBy
from tqdm import tqdm

from src.analysis import groupby, stat
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
        "--group-by",
        help="group by stops by a value",
        choices=(
            "none",
            "train_hash",
            "client_code",
            "weekday",
        ),
        default="none",
    )
    parser.add_argument(
        "--agg-func",
        help="group by aggregation function",
        choices=(
            "none",
            "mean",
            "last",
        ),
        default="last",
    )
    parser.add_argument(
        "--stat",
        help="the stat to calculate",
        choices=(
            "describe",
            "delay_boxplot",
        ),
        default="describe",
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
    df.reset_index(drop=True, inplace=True)

    stations: pd.DataFrame = read_station_csv(args.station_csv)
    original_length: int = len(df)

    # Apply filters
    df: pd.DataFrame | DataFrameGroupBy = date_filter(df, start_date, end_date)
    logging.info(f"Loaded {len(df)} data points ({original_length} before filtering)")

    stat.set_plot_title(df, args)

    if args.group_by != "none":
        df_grouped: DataFrameGroupBy | None = None

        if args.group_by == "train_hash":
            df_grouped = groupby.train_hash(df)
        elif args.group_by == "client_code":
            df_grouped = groupby.client_code(df)
        elif args.group_by == "weekday":
            df_grouped = groupby.weekday(df)

        assert df_grouped is not None

        if args.agg_func == "last":
            df = df_grouped.last()
        elif args.agg_func == "mean":
            df = df_grouped.mean(numeric_only=True)
        elif args.agg_func == "none":
            df = df_grouped

    if args.stat == "describe":
        stat.describe(df)
    elif args.stat == "delay_boxplot":
        stat.delay_boxplot(df)
