from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from src.const import RailwayCompany


def read_train_csv(file: Path) -> pd.DataFrame:
    """Load train CSV to a pandas dataframe

    Args:
        file (Path): the train CSV file path

    Returns:
        pd.DataFrame: the loaded dataframe
    """

    df: pd.DataFrame = pd.read_csv(file)

    @np.vectorize
    def _parse_dt(_string: str | None) -> datetime | None:
        try:
            if not isinstance(_string, str):
                return None
            return datetime.fromisoformat(_string)
        except ValueError:
            return None

    # Parse datetimes
    for dt_field in [
        "arrival_expected",
        "arrival_actual",
        "departure_expected",
        "departure_actual",
    ]:
        df[dt_field] = (
            df[dt_field]
            .apply(_parse_dt)
            .astype("object")
            .where(df[dt_field].notnull(), None)
        )

    df.day = pd.to_datetime(df.day)

    # Map client codes
    df.client_code = df.client_code.apply(RailwayCompany.from_code)  # type: ignore

    # Exclude phantom data
    df = df.loc[(df.phantom == False) & (df.trenord_phantom == False)].drop(
        ["phantom", "trenord_phantom"], axis=1
    )
    return df


def read_station_csv(file: Path) -> pd.DataFrame:
    """Load station CSV to a pandas dataframe

    Args:
        file (Path): the station CSV file path

    Returns:
        pd.DataFrame: the loaded dataframe
    """

    return pd.read_csv(file)
