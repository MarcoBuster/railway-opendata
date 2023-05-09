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

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pandas.core.groupby.generic import DataFrameGroupBy

from src.const import RAILWAY_COMPANIES_PALETTE, WEEKDAYS


def describe(df: pd.DataFrame | DataFrameGroupBy) -> None:
    """Call pandas.DataFrame.describe()"""
    print(df.describe())


def prepare_mpl(df: pd.DataFrame, args: argparse.Namespace) -> None:
    """Prepare matplotlib params"""
    if args.stat not in [
        "delay_boxplot",
        "day_train_count",
    ]:
        return

    mpl.rcParams["figure.figsize"] = (12, 12 * 5 / 7)
    sns.set_theme(style="whitegrid", palette="pastel")

    plt.title(args.stat)

    start_day, end_day = df.day.min().date(), df.day.max().date()
    plt.title(f"{start_day} => {end_day}", loc="left")

    if args.group_by != "none":
        grouped_str = f" grouped by {args.group_by}"
        if args.agg_func == "none":
            grouped_str += ", unaggregated"
        else:
            grouped_str += f", aggr. with '{args.agg_func}' func"
        plt.title(grouped_str, loc="right")


def delay_boxplot(df: pd.DataFrame | DataFrameGroupBy) -> None:
    """Show a seaborn boxplot of departure and arrival delays"""

    if isinstance(df, DataFrameGroupBy):
        grouped_by: str = df.any().index.name
        group_melt = pd.DataFrame()

        grouped: list = list(df)  # type: ignore
        if grouped_by == "weekday":
            # Re-order fields
            grouped.sort(key=lambda t: WEEKDAYS[t[0]])

        for group in grouped:  # type: ignore
            melt = pd.melt(
                group[1],
                id_vars=[
                    col
                    for col in df.obj.columns
                    if col
                    not in [
                        "arrival_delay",
                        "departure_delay",
                    ]
                ],
                value_name="value",
            )
            group_melt = pd.concat([group_melt, melt])

        ax = sns.boxplot(
            group_melt[[grouped_by, "variable", "value"]],
            x=grouped_by,
            y="value",
            hue="variable",
            showfliers=False,
        )
        ax.set(xlabel=grouped_by, ylabel="Delay (minutes)")

    elif isinstance(df, pd.DataFrame):
        ax = sns.boxplot(
            df[["arrival_delay", "departure_delay"]],
            showfliers=False,
        )
        ax.set(xlabel="Variable", ylabel="Delay (minutes)")

    plt.show()


def day_train_count(df: pd.DataFrame | DataFrameGroupBy) -> None:
    """Show a seaborn barplot of unique train count, grouped by day"""

    if isinstance(df, DataFrameGroupBy):
        grouped_by: str = df.any().index.name

        palette: None | dict[str, str] = None
        hue_order: None | list[str] = None

        if grouped_by == "client_code":
            palette = RAILWAY_COMPANIES_PALETTE
            hue_order = (
                df.train_hash.nunique().sort_values(ascending=False).index.to_list()
            )

        grouped = df.obj.groupby(["day", grouped_by]).nunique().reset_index()
        grouped["day"] = grouped["day"].apply(lambda d: d.date().isoformat())

        ax = sns.barplot(
            data=grouped,
            x="day",
            y="train_hash",
            hue=grouped_by,
            palette=palette,
            hue_order=hue_order,
        )

    elif isinstance(df, pd.DataFrame):
        grouped = df.groupby("day").nunique().reset_index()
        grouped["day"] = grouped["day"].apply(lambda d: d.date().isoformat())

        ax = sns.barplot(
            data=grouped,
            x="day",
            y="train_hash",
        )

    ax.set(xlabel="Day", ylabel="Train count")
    plt.show()
