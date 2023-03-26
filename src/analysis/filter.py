from datetime import datetime

import pandas as pd


def date_filter(
    df: pd.DataFrame, start_date: datetime | None, end_date: datetime | None
) -> pd.DataFrame:
    """Filter dataframe by date (day).

    Args:
        df (pd.DataFrame): the considered dataframe
        start_date (datetime | None): the start date
        end_date (datetime | None): the end date

    Returns:
        pd.DataFrame: the filtered dataframe
    """
    if isinstance(start_date, datetime):
        df = df.loc[df.day >= start_date.date()]
    if isinstance(end_date, datetime):
        df = df.loc[df.day <= end_date.date()]
    return df
