import itertools
import logging
import os
import pathlib
import pickle
import typing as t
from datetime import date, datetime, timedelta

from tqdm import tqdm

from src.const import TIMEZONE
from src.scraper.station import Station
from src.scraper.train import Train

DATA_DIR = pathlib.Path("data/")


def load_dataset(file_path: pathlib.Path) -> dict[t.Any, t.Any]:
    try:
        with open(file_path, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return dict()


def save_dataset(file_path: pathlib.Path, dataset: dict[t.Any, t.Any]) -> None:
    with open(file_path, "wb") as f:
        pickle.dump(dataset, f)


def main() -> None:
    # Today + ~3 hours
    today: date = (datetime.now(tz=TIMEZONE) - timedelta(hours=3)).date()
    today_path: pathlib.Path = DATA_DIR / today.strftime("%Y-%m-%d")
    try:
        os.mkdir(today_path.absolute())
    except FileExistsError:
        pass

    station_cache: dict[str, Station] = load_dataset(DATA_DIR / "stations.pickle")
    fetched_trains: dict[int, Train] = load_dataset(today_path / "trains.pickle")
    unfetched_trains: dict[int, Train] = load_dataset(today_path / "unfetched.pickle")

    fetched_old_n = len(fetched_trains)
    unfetched_old_n = len(unfetched_trains)
    logging.info(
        f"Loaded {fetched_old_n} already fetched and {unfetched_old_n} unfetched trains"
    )

    # Initialize Station cache
    if len(station_cache) != 0:
        Station._cache = station_cache
    logging.info(f"Initialized station cache with {len(station_cache)} elements")

    # Fetch stations
    stations: set[Station] = set(
        itertools.chain.from_iterable([Station.by_region(r) for r in range(1, 23)])
    )
    logging.info(f"Retrieved {len(stations)} stations")

    # Try to fetch unfetched trains
    logging.info(
        f"Starting fetching {len(unfetched_trains)} previously unfetched trains"
    )
    _fetched_trains_delete_later: list[int] = list()
    for unfetched_train_hash in tqdm(unfetched_trains):
        train = unfetched_trains[unfetched_train_hash]
        try:
            train.fetch()
        except Exception as e:
            logging.exception(e, exc_info=True)
            continue

        if train._phantom or train.arrived():
            fetched_trains[unfetched_train_hash] = train
            logging.debug(f"Saved previously unfetched {train.category} {train.number}")

            # It is not possible to delete dict keys in-place
            _fetched_trains_delete_later.append(unfetched_train_hash)

    for to_delete in _fetched_trains_delete_later:
        del unfetched_trains[to_delete]

    logging.info("Starting fetching departures from all stations")
    for station in tqdm(stations):
        logging.debug(f"Processing {station}")

        departing: list[Train] = station.departures()
        for train in departing:
            if hash(train) in fetched_trains or hash(train) in unfetched_trains:
                continue

            try:
                train.fetch()
            except Exception as e:
                logging.exception(e, exc_info=True)
                continue

            if train._phantom or train.arrived():
                fetched_trains[hash(train)] = train
                logging.debug(f"Saved {train.category} {train.number}")
            else:
                unfetched_trains[hash(train)] = train

    logging.info(f"Retrieved {len(fetched_trains) - fetched_old_n} new trains")
    logging.info(
        f"Unfetched trains: {len(unfetched_trains)} "
        f"({(len(unfetched_trains) - unfetched_old_n):+d})"
    )

    save_dataset(DATA_DIR / "stations.pickle", Station._cache)
    save_dataset(today_path / "trains.pickle", fetched_trains)
    save_dataset(today_path / "unfetched.pickle", unfetched_trains)

    logging.info(f"Trains saved today: {len(fetched_trains)}")
    logging.info(f"Station cache size: {len(Station._cache)}")
