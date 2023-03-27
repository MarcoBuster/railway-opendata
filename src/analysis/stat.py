import pandas as pd


def describe(df: pd.DataFrame) -> pd.DataFrame:
    """Call pandas.DataFrame.describe()"""
    return df[
        [
            "arrival_delay",
            "departure_delay",
            "crowding",
        ]
    ].describe()
