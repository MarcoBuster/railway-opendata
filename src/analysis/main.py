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
import logging
import pathlib
import warnings
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
from dateparser import parse
from joblib import Parallel, delayed
from pandas.core.groupby.generic import DataFrameGroupBy

from src.analysis import groupby, stat, timetable, trajectories_map
from src.analysis.filter import *
from src.analysis.load_data import read_station_csv, read_train_csv, tag_lines


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
        "--railway-companies",
        help="comma-separated list of railway companies to include. If not set, all companies will be included.",
        dest="client_codes",
    )
    parser.add_argument(
        "--railway-lines",
        help=(
            "comma-separated list of railway lines to include. "
            "If not set, all lines will be include. "
            "Use --stat detect_lines to see available lines."
        ),
        dest="railway_lines",
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
        default="none",
    )
    parser.add_argument(
        "--stat",
        help="the stat to calculate",
        choices=(
            "describe",
            "delay_boxplot",
            "day_train_count",
            "trajectories_map",
            "detect_lines",
            "timetable",
        ),
        default="describe",
    )
    parser.add_argument(
        "--save-fig",
        metavar="FILENAME",
        help="save the output figure to a file if using delay_boxplot or day_train_count stats. If not specified, use pyplot.show()",
        default=None,
    )
    parser.add_argument(
        "--timetable-collapse",
        help="collapse the train stop times in the graph, relative to the first (only for 'timetable' stat). Defaults to False",
        action=argparse.BooleanOptionalAction,
        default=False,
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


@delayed
def _load_train_dataset(train_csv: str) -> pd.DataFrame:
    path = pathlib.Path(train_csv)
    train_df: pd.DataFrame = read_train_csv(pathlib.Path(train_csv))
    logging.debug(f"Loaded {len(train_df)} data points @ {path}")
    return train_df


def main(args: argparse.Namespace):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

        start_date: datetime | None = parse(args.start_date if args.start_date else "")
        if args.start_date and not start_date:
            raise argparse.ArgumentTypeError("invalid start_date")

        end_date: datetime | None = parse(args.end_date if args.end_date else "")
        if args.end_date and not end_date:
            raise argparse.ArgumentTypeError("invalid end_date")

    railway_companies: str | None = args.client_codes
    railway_lines: str | None = args.railway_lines

    # Load dataset
    df: pd.DataFrame | DataFrameGroupBy = pd.DataFrame()
    logging.info("Loading datasets...")

    for train_df in Parallel(n_jobs=-1, verbose=5)(
        _load_train_dataset(train_csv) for train_csv in args.trains_csv  # type: ignore
    ):
        df = pd.concat([df, train_df], axis=0)

    df.reset_index(drop=True, inplace=True)

    stations: pd.DataFrame = read_station_csv(args.station_csv)
    original_length: int = len(df)

    # Tag lines
    df = tag_lines(df, stations)

    # Apply filters
    df = date_filter(df, start_date, end_date)
    df = railway_company_filter(df, railway_companies)
    df = railway_lines_filter(df, railway_lines)
    logging.info(f"Loaded {len(df)} data points ({original_length} before filtering)")

    # Prepare graphics
    stat.prepare_mpl(df, args)

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

    if args.stat in [
        "trajectories_map",
        "detect_lines",
        "timetable",
    ] and not isinstance(df, pd.DataFrame):
        raise ValueError(f"can't use {args.stat} with unaggregated data")

    if args.stat == "describe":
        stat.describe(df)
    elif args.stat == "delay_boxplot":
        stat.delay_boxplot(df)
    elif args.stat == "day_train_count":
        stat.day_train_count(df)
    elif args.stat == "trajectories_map":
        trajectories_map.build_map(stations, df)
    elif args.stat == "detect_lines":
        stat.detect_lines(df, stations)
    elif args.stat == "timetable":
        if not timetable.same_line(df):
            raise ValueError(
                f"can't use timetable if --railway-lines filter is not used"
            )
        timetable.timetable_graph(df, stations, args.timetable_collapse)

    # Visualizations only
    if args.stat in ["delay_boxplot", "day_train_count", "timetable"]:
        if args.save_fig:
            plt.savefig(args.save_fig)
        else:
            plt.show()
