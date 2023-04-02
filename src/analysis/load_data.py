from pathlib import Path

import pandas as pd

from src.const import RailwayCompany


def read_train_csv(file: Path) -> pd.DataFrame:
    """Load train CSV to a pandas dataframe

    Args:
        file (Path): the train CSV file path

    Returns:
        pd.DataFrame: the loaded dataframe
    """

    df: pd.DataFrame = pd.read_csv(
        file,
        parse_dates=[
            "day",
            "arrival_expected",
            "arrival_actual",
            "departure_expected",
            "departure_actual",
        ],
        infer_datetime_format=True,
    )
    df.client_code = df.client_code.apply(RailwayCompany.from_code)  # type: ignore
    df.day = pd.to_datetime(df.day.apply(lambda dt: dt.date()))
    return df.loc[(df.phantom == False) & (df.trenord_phantom == False)].drop(
        ["phantom", "trenord_phantom"], axis=1
    )


def read_station_csv(file: Path) -> pd.DataFrame:
    """Load station CSV to a pandas dataframe

    Args:
        file (Path): the station CSV file path

    Returns:
        pd.DataFrame: the loaded dataframe
    """

    return pd.read_csv(file)
