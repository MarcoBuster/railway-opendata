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
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        df = df.loc[df.day >= start_date]
    if isinstance(end_date, datetime):
        end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        df = df.loc[df.day <= end_date]
    return df
