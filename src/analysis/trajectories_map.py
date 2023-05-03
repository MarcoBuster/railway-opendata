import itertools
import logging
import pathlib
import typing as t
import webbrowser
from collections import defaultdict
from datetime import datetime, timedelta
from tempfile import NamedTemporaryFile

import folium
import folium.plugins
import numpy as np
import pandas as pd
from colour import Color
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

# Assets path (marker icons)
ASSETS_PATH = pathlib.Path("./src/analysis/assets/").resolve()

# Delay color range: (lower_bound, color)
_color_map: list[tuple[float, Color]] = [
    (-5, Color("#34ebc0")),
    (0, Color("green")),
    (10, Color("orange")),
    (30, Color("red")),
    (120, Color("black")),
]

# Statically populate COLORS dict
COLORS: dict[int | float, Color] = defaultdict(lambda: Color("gray"))
for i, (lower_bound, color) in enumerate(_color_map[1:]):
    prev_bound, prev_color = _color_map[i + 1 - 1]
    n_range: range = range(round(prev_bound), round(lower_bound) + 1)
    scale: list[Color] = list(prev_color.range_to(color, len(n_range)))
    for j, n in enumerate(n_range):
        COLORS[n] = scale[j]


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


def icon_marker(railway_company: str, category: str) -> str:
    """Select a proper marker (from the src/analysis/assets/ directory)
    by railway_company and category.

    Args:
        railway_company (str): a railway company
        category (str): a category

    Returns:
        str: filename of the proper marker
    """

    category = category.replace("MET", "REG").replace("EC FR", "EC")
    railway_company = railway_company.lower()

    if railway_company.startswith("trenitalia") and category in [
        "EC",
        "FA",
        "FB",
        "FR",
        "IC",
        "ICN",
        "REG",
    ]:
        return f"trenitalia_{category.lower()}.svg"

    if railway_company in ["trenord", "tper"] and category == "REG":
        return f"{railway_company}_reg.svg"

    if railway_company == "obb" and category == "EC":
        return "obb_ec.svg"

    return "other.svg"


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

        prev_time: datetime | None = prev.departure_actual or prev.departure_expected
        curr_time: datetime | None = curr.arrival_actual or curr.arrival_expected
        delay: float = (
            round(prev.departure_delay)
            if not np.isnan(prev.departure_delay)
            else np.nan
        )

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
            ret.extend(
                [
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
                                "color": COLORS[delay].get_hex(),
                                "weight": int(curr.crowding / 10)
                                if not np.isnan(curr.crowding)
                                and curr.crowding > MIN_WEIGHT * 10
                                else MIN_WEIGHT,
                            },
                        },
                    },
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": (curr_st.longitude, curr_st.latitude),
                        },
                        "properties": {
                            "icon": "marker",
                            "iconstyle": {
                                "iconUrl": str(
                                    ASSETS_PATH
                                    / icon_marker(curr.client_code, curr.category)
                                ),
                                "iconSize": [24, 24],
                                "fillOpacity": 1,
                            },
                            "tooltip": (
                                f"<b>{curr.client_code}</b> &#8729; <b>{curr.category}</b> <b>{curr.number}</b>"
                                f"<dd>{prev_st.long_name} "
                                f"{f'({round(prev.departure_delay, 1):+g} min)' if not np.isnan(prev.departure_delay) else ''}"
                                f" &rarr; "
                                f"{curr_st.long_name} "
                                f"{f' ({round(prev.arrival_delay, 1):+g} min)' if not np.isnan(prev.arrival_delay) else ''}"
                            ),
                            "name": "",
                            "times": [timestamp.isoformat()],
                        },
                    },
                ]
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
