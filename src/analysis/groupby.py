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


import pandas as pd
from pandas.core.groupby.generic import DataFrameGroupBy

from src.const import LOCALE


def train_hash(df: pd.DataFrame) -> DataFrameGroupBy:
    """Group the dataframe by the train hash."""
    return df.groupby("train_hash")


def client_code(df: pd.DataFrame) -> DataFrameGroupBy:
    """Group the dataframe by the client code."""
    df = df.loc[df.client_code != "OTHER"]
    return df.groupby("client_code")


def weekday(df: pd.DataFrame) -> DataFrameGroupBy:
    """Group the dataframe by the (departure) weekday"""
    df["weekday"] = df.day.dt.day_name(locale=LOCALE)
    return df.groupby("weekday")


def agg_last(df_grouped: DataFrameGroupBy) -> pd.DataFrame:
    return df_grouped.last()


def agg_mean(df_grouped: DataFrameGroupBy) -> pd.DataFrame:
    return df_grouped.mean()
