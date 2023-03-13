import itertools
import logging
import os
import pathlib
import typing as t
from datetime import datetime

import jsonpickle
from tqdm import tqdm

from src.const import TIMEZONE
from src.scraper.station import Station
from src.scraper.train import Train

DATA_DIR = pathlib.Path("data/")


def load_dataset(file_path: pathlib.Path) -> dict[t.Any, t.Any]:
    os.system(f"touch {file_path.absolute()}")
    with open(file_path, "r") as f:
        contents: str = "\n".join(f.readlines())
        dataset: dict[t.Any, t.Any]
        if len(contents) > 0:
            dataset = jsonpickle.loads(contents)  # type: ignore
        else:
            dataset = dict()
    return dataset


def save_dataset(file_path: pathlib.Path, dataset: dict[t.Any, t.Any]) -> None:
    os.system(f"touch {file_path.absolute()}")
    frozen = jsonpickle.encode(dataset)
    with open(file_path, "w") as f:
        f.write(str(frozen))


def main() -> None:
    today_path: pathlib.Path = DATA_DIR / datetime.now(tz=TIMEZONE).strftime("%Y-%m-%d")
    try:
        os.mkdir(today_path.absolute())
    except FileExistsError:
        pass

    station_cache: dict[str, Station] = load_dataset(DATA_DIR / "stations.json")
    fetched_trains: dict[int, Train] = load_dataset(today_path / "trains.json")
    unfetched_trains: dict[int, Train] = load_dataset(today_path / "unfetched.json")

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
            logging.exception(e)
            continue

        if train._phantom or train.arrived():
            fetched_trains[unfetched_train_hash] = train
            logging.debug(f"Saved previously unfetched {train.category} {train.number}")

            # It is not possible to delete dict keys in-place
            _fetched_trains_delete_later.append(unfetched_train_hash)

    for to_delete in _fetched_trains_delete_later:
        del unfetched_trains[to_delete]

    logging.info("Starting fetch departures from all stations")
    for station in tqdm(stations):
        logging.debug(f"Processing {station}")

        departing: list[Train] = station.departures()
        for train in departing:
            if hash(train) in fetched_trains or hash(train) in unfetched_trains:
                continue

            try:
                train.fetch()
            except Exception as e:
                logging.exception(e)
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

    save_dataset(DATA_DIR / "stations.json", Station._cache)
    save_dataset(today_path / "trains.json", fetched_trains)
    save_dataset(today_path / "unfetched.json", unfetched_trains)

    logging.info(f"Trains saved today: {len(fetched_trains)}")
    logging.info(f"Station cache size: {len(Station._cache)}")
