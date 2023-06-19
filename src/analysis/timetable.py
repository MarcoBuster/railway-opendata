import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import timple

from src.const import TIMEZONE, TIMEZONE_GMT


def same_line(df: pd.DataFrame) -> bool:
    """Check if the trains in the provided DataFrame are ALL on the same line

    Args:
        df (pd.DataFrame): the trains to check

    Return:
        bool: True if the trains are all on the same line, False otherwise
    """
    return df.nunique().line == 1


def timetable_train(train: pd.DataFrame, expected: bool = False, collapse: bool = True):
    """Generate a timetable graph of a train

    Args:
        train (pd.DataFrame): the train stop data to consider
        expected (bool, optional): determines whatever to consider the 'expected' or 'actual' arrival/departure times. Defaults to False.
        collapse (bool, optional): determines whatever to _collapse_ the times in the graph, relative to the first. Defaults to True.
    """

    if collapse:
        train.value -= train.value.min()

    train_f = train.loc[
        train.variable.str.endswith("expected" if expected else "actual")
    ]
    plt.plot(
        train_f.value,
        train_f.long_name,
        "ko" if expected else "o",
        linestyle="-" if expected else "--",
        linewidth=3 if expected else 2,
        label=f"{train.iloc[0].category} {train.iloc[0].number}"
        if not expected
        else "expected",
        zorder=10 if expected else 5,
    )


def timetable_graph(trains: pd.DataFrame, st: pd.DataFrame, collapse: bool = True):
    """Generate a timetable graph of trains in a line.

    Args:
        trains (pd.DataFrame): the train stop data to consider
        st (pd.DataFrame): the station data
        collapse (bool, optional): determines whatever to _collapse_ the times in the graph, relative to the first. Defaults to True.
    """
    tmpl = timple.Timple()
    tmpl.enable()

    trains_j = (
        trains.sort_values(by="stop_number")
        .join(st, on="stop_station_code")
        .reset_index(drop=True)
    )
    trains_m = (
        pd.melt(
            trains_j,
            id_vars=[
                "long_name",
                "stop_number",
                "train_hash",
                "category",
                "number",
                "origin",
            ],
            value_vars=[
                "departure_expected",
                "departure_actual",
                "arrival_expected",
                "arrival_actual",
            ],
        )
        .sort_values(["stop_number", "variable"])
        .dropna()
    )

    # expected
    if collapse:
        for origin in trains_m.origin.unique():
            train = list(trains_m.loc[trains_m.origin == origin].groupby("train_hash"))[0][1]  # fmt: skip
            timetable_train(train, True)

    # actual
    for _, train in trains_m.groupby("train_hash"):
        timetable_train(train, False, collapse)

    # get station names for proper title
    st_names: pd.DataFrame = st.drop(
        ["region", "latitude", "longitude", "short_name"],
        axis=1,
    )
    line: pd.DataFrame = (
        trains.join(st_names, on="origin")
        .rename({"long_name": "station_a"}, axis=1)
        .join(st_names, on="destination")
        .rename({"long_name": "station_b"}, axis=1)
    )[["station_a", "station_b", "stop_number"]].agg(
        {
            "station_a": lambda s: s.iloc[0],
            "station_b": lambda s: s.iloc[0],
            "stop_number": lambda n: max(n) + 1,
        }
    )

    plt.title(f"{line.station_a} ↔ {line.station_b} [{line.stop_number} stops]")
    start_day, end_day = trains.day.min().date(), trains.day.max().date()
    plt.title(f"{start_day} => {end_day}", loc="left")

    plt.ylabel("Station")
    plt.xlabel("Time")

    ax = plt.gca()
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M", TIMEZONE if not collapse else TIMEZONE_GMT))  # type: ignore

    plt.show()
