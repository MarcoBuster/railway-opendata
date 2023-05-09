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

    # Fix incorrect origin and destination
    df["origin"] = (df.groupby("train_hash").transform("first"))["stop_station_code"]
    df["destination"] = df.groupby("train_hash").transform("last")["stop_station_code"]

    return df


def read_station_csv(file: Path) -> pd.DataFrame:
    """Load station CSV to a pandas dataframe

    Args:
        file (Path): the station CSV file path

    Returns:
        pd.DataFrame: the loaded dataframe
    """

    st: pd.DataFrame = pd.read_csv(file, index_col="code")

    # Some stations (like 'Brescia') have MULTIPLE codes,
    # but only one associated row has useful (non-NaN) information.
    for idx, station in st.iterrows():
        # Search other stations with the same name
        other: pd.DataFrame = st.loc[st.long_name == station.long_name]
        if len(other) == 1:
            continue

        # If 'this' station has useful information, don't perform any actions
        if not np.isnan(station.latitude) and not np.isnan(station.longitude):
            continue

        # If present, select the 'oracle' station with information
        other = other.loc[~np.isnan(other.latitude)]
        if len(other) == 0:
            continue
        oracle = other.iloc[0]

        # Fill missing information using the oracle data
        st.loc[st.index == idx, ["short_name", "latitude", "longitude"]] = (  # type: ignore
            oracle.short_name,
            oracle.latitude,
            oracle.longitude,
        )

    return st


def tag_lines(df: pd.DataFrame, stations: pd.DataFrame) -> pd.DataFrame:
    """Add 'railway line' information to the 'trains' dataframe.

    Args:
        trains (pd.DataFrame): the considered dataframe
        stations (pd.DataFrame): the station data

    Returns:
        pd.DataFrame: the tagged dataframe

    Notes:
        Two trains (t_1, t_2) are considered of the same 'railway line' iff:
        - t_1.railway_company == t_2.railway_company;
        - t_1.origin == t_2.origin and t_1.destination == t_2.destination or viceversa;
        - t_1.stop_set == t_2.stop_set (*).

        (*): can be simplified in t_1.stop_count == t_2.stop_count.

        The above definition is just a convenient approximation.
        More precise considerations can only be made on a case-by-case basis.
    """

    df = df.sort_values(["train_hash", "stop_number"])
    df["stop_set"] = df.groupby("train_hash").stop_station_code.transform(
        lambda stops: hash(frozenset(stops.unique()))
    )
    df["track"] = df.apply(
        lambda r: (r.origin + "_" + r.destination)
        if r.origin > r.destination
        else (r.destination + "_" + r.origin),
        axis=1,
    )
    df["line"] = df.apply(
        lambda r: f"{r.client_code}_{r.track}_{r.stop_set}",
        axis=1,
    )
    return df
