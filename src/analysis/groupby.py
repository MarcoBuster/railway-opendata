import pandas as pd
from pandas.core.groupby.generic import DataFrameGroupBy


def train_number(df: pd.DataFrame) -> DataFrameGroupBy:
    """Group by the dataframe by the train number."""
    return df.groupby("number")


def agg_last(df_grouped: DataFrameGroupBy) -> pd.DataFrame:
    return df_grouped.last()


def agg_mean(df_grouped: DataFrameGroupBy) -> pd.DataFrame:
    return df_grouped.mean()
