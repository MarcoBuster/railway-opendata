import itertools
import logging
import typing as t
import webbrowser
from collections import defaultdict
from datetime import datetime, timedelta
from tempfile import NamedTemporaryFile

import folium
import folium.plugins
import numpy as np
import pandas as pd
from joblib import Parallel, delayed

# The 'length' (in minutes) of a frame
WINDOW_SIZE: int = 2
assert WINDOW_SIZE > 0

# Minimum line weight
MIN_WEIGHT: int = 4
assert MIN_WEIGHT > 0

# Safe values used in sanity checks
MIN_YEAR: int = datetime.now().year - 50
MAX_YEAR: int = datetime.now().year + 10

# Folium map initialization arguments
MAP_KWARGS: dict = {
    "location": (41.890, 12.492),
    "zoom_start": 7,
    "attr": "OSM",
}

# Client code colors
_color_map = {
    "TRENITALIA_REG": "#781504",
    "TRENORD": "#07b836",
    "TRENITALIA_AV": "#ff2600",
    "TRENITALIA_IC": "#0044ff",
    "TPER": "#d8f500",
    "OBB": "#d800f5",
}
_default_color = "#9a8c9c"

COLOR_MAP = defaultdict(lambda: _default_color)
for k in _color_map:
    COLOR_MAP[k] = _color_map[k]


def fill_time(start: datetime, end: datetime) -> t.Generator[datetime, None, None]:
    """Generate a consecutive list of times between the 'start' and 'end' period.

    Args:
        start (datetime): start time
        end (datetime): end time

    Returns:
        Generator[datetime, None, None]: the generated datetimes
    """
    # Fix empty intervals
    if start == end:
        start -= timedelta(minutes=WINDOW_SIZE)

    while start <= end:
        yield start
        start += timedelta(minutes=(WINDOW_SIZE / 2) if WINDOW_SIZE > 1 else 1)


@delayed
def train_stop_geojson(st: pd.DataFrame, train: pd.DataFrame) -> list[dict]:
    """Generate a list of GeoJSON formatted data for train stops.

    Args:
        st (pd.DataFrame): global station data
        train (pd.DataFrame): the train stop data

    Returns:
        Generator[dict, None, None]: a generator of GeoJSON formatted
        dictionaries representing the train _geographic trajectory_.
    """
    ret: list[dict] = list()
    train = train.sort_values(by="stop_number")

    # Iterate the train stops two by two
    for i in range(len(train))[1:]:
        prev = train.iloc[i - 1]
        curr = train.iloc[i]

        try:
            prev_st = st.loc[
                (st.index == prev.stop_station_code)
                & ~st.latitude.isna()
                & ~st.longitude.isna()
            ].iloc[0]
            curr_st = st.loc[
                (st.index == curr.stop_station_code)
                & ~st.latitude.isna()
                & ~st.longitude.isna()
            ].iloc[0]
        except IndexError:
            # The station location can't be retrieved
            continue

        prev_time: datetime | None = prev.departure_expected
        if prev.departure_actual:
            prev_time = prev.departure_actual

        curr_time: datetime | None = curr.arrival_expected
        if curr.arrival_actual:
            curr_time = curr.arrival_actual

        # Sanity check: _time must be not null
        if not prev_time or not curr_time:
            continue

        # Sanity check: a train should arrive in a given station after
        # it departs from the previous one
        if not curr_time >= prev_time:
            continue

        # Sanity check: sometimes the API returns insane year values
        if curr_time.year > MAX_YEAR or prev_time.year < MIN_YEAR:
            continue

        for timestamp in fill_time(prev_time, curr_time):
            ret.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            (prev_st.longitude, prev_st.latitude),
                            (curr_st.longitude, curr_st.latitude),
                        ],
                    },
                    "properties": {
                        "times": [timestamp.isoformat()] * 2,
                        "style": {
                            "color": COLOR_MAP[curr.client_code],
                            "weight": int(curr.crowding / 10)
                            if not np.isnan(curr.crowding)
                            and curr.crowding > MIN_WEIGHT * 10
                            else MIN_WEIGHT,
                        },
                    },
                }
            )

    return ret


def build_map(st: pd.DataFrame, df: pd.DataFrame) -> None:
    """Build a Folium map with train trajectories,
    and open it with a web browser.

    Args:
        st (pd.DataFrame): global station data
        df (pd.DataFrame): the train stop data
    """
    m = folium.Map(**MAP_KWARGS)

    logging.info("Generating GeoJSON features...")
    features = Parallel(n_jobs=-1, verbose=5)(
        train_stop_geojson(st, train_df) for _, train_df in df.groupby("train_hash")
    )

    # Add TimestampedGeoJson plugin
    folium.plugins.TimestampedGeoJson(
        {
            "type": "FeatureCollection",
            "features": list(itertools.chain(*features)),  # type: ignore
        },
        add_last_point=False,
        period=f"PT{WINDOW_SIZE}M",
        duration=f"PT{WINDOW_SIZE}M",
    ).add_to(m)

    # Save the map to a temporary file and open it with a web browser
    outfile = NamedTemporaryFile(delete=False)
    m.save(outfile.file)
    webbrowser.open(outfile.name)
