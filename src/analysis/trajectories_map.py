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
from branca.colormap import LinearColormap
from branca.element import MacroElement, Template
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
        start += timedelta(minutes=WINDOW_SIZE)


def icon_marker(railway_company: str, category: str) -> str:
    """Select a proper marker (from the src/analysis/assets/markers/ directory)
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

        # Tooltip pop up display
        tooltip: str = (
            f"<b>{curr.client_code}</b> &#8729; <b>{curr.category}</b> <b>{curr.number}</b>"
            f"<dd>{prev_st.long_name} "
            f"{f'({round(prev.departure_delay, 1):+g} min)' if not np.isnan(prev.departure_delay) else ''}"
            f" &rarr; "
            f"{curr_st.long_name} "
            f"{f' ({round(prev.arrival_delay, 1):+g} min)' if not np.isnan(prev.arrival_delay) else ''}"
        )

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
                            "tooltip": tooltip,
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
                                    / "markers"
                                    / icon_marker(curr.client_code, curr.category)
                                ),
                                "iconSize": [24, 24],
                                "fillOpacity": 1,
                            },
                            "tooltip": tooltip,
                            "name": "",
                            "times": [timestamp.isoformat()],
                        },
                    },
                ]
            )

    return ret


class StatsChart(MacroElement):
    """Helper class to compute and embed the train count chart."""

    def __init__(self, df: pd.DataFrame, *args, **kwargs):
        """Initialize a new object.

        Args:
            df (pd.DataFrame): the train stop data
        """
        super().__init__(*args, **kwargs)

        # Prepare dataset
        trains = df.groupby("train_hash")
        self.data = pd.DataFrame(index=df.train_hash.unique())
        self.data["departure"] = trains.first()["departure_actual"].fillna(
            trains.first()["departure_expected"]
        )
        self.data["arrival"] = trains.last()["arrival_actual"].fillna(
            trains.first()["arrival_expected"]
        )
        self.data["delay"] = trains.mean(numeric_only=True)["departure_delay"].fillna(
            trains.mean(numeric_only=True)["arrival_delay"]
        )

    def get_train_count_data(self) -> list[dict[str, str | int]]:
        """Return circulating train count in a JS-likable format."""
        ret: list[dict[str, str | int]] = []
        for time in fill_time(self.data.departure.min(), self.data.arrival.max()):
            subset: pd.DataFrame = self.data.loc[
                (time >= self.data.departure) & (time <= self.data.arrival)
            ]
            ret.append(
                {
                    "x": time.isoformat(),
                    "y": len(subset),
                }
            )
        return ret

    def get_delays_data(self) -> list[dict[str, str | float]]:
        ret: list[dict[str, str | float]] = []
        for time in fill_time(self.data.departure.min(), self.data.arrival.max()):
            subset: pd.DataFrame = self.data.loc[
                (time >= self.data.departure) & (time <= self.data.arrival)
            ]
            ret.append(
                {
                    "x": time.isoformat(),
                    "y": subset.delay.mean() if len(subset) > 20 else "NaN",
                }
            )
        return ret


class MarkerLegend(MacroElement):
    """Helper class to embed the marker legend"""

    @staticmethod
    def get_markers_path() -> str:
        """Return the absolute path of assets"""
        return str(ASSETS_PATH / "markers")


def build_map(st: pd.DataFrame, df: pd.DataFrame) -> None:
    """Build a Folium map with train trajectories,
    and open it with a web browser.

    Args:
        st (pd.DataFrame): global station data
        df (pd.DataFrame): the train stop data
    """
    m = folium.Map(**MAP_KWARGS)

    # Drop cancelled stops and trains
    df = df.loc[(df.stop_type != "C") & (df.cancelled == False)].copy()

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

    # Add delay legend
    LinearColormap(
        colors=list(map(lambda c: c.get_rgb(), COLORS.values())),
        index=COLORS.keys(),
        vmin=min(COLORS.keys()),
        vmax=min(60, max(COLORS.keys())),
        max_labels=50,
        tick_labels=list(range(-5, 61, 5)),
        caption="Departure delay",
    ).add_to(m)

    # Add marker legend
    legend = MarkerLegend()
    with open(ASSETS_PATH / "templates" / "marker_legend.html", "r") as f:
        legend._template = Template("\n".join(f.readlines()))
    m.get_root().add_child(legend)

    # Add train count chart
    macro = StatsChart(df)
    with open(ASSETS_PATH / "templates" / "stats_chart.html", "r") as f:
        macro._template = Template("\n".join(f.readlines()))
    m.get_root().add_child(macro)

    # Save the map to a temporary file and open it with a web browser
    outfile = NamedTemporaryFile(delete=False, suffix=".html")
    m.save(outfile.file)

    webbrowser.open(outfile.name)
