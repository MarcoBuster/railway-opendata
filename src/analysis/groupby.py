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
