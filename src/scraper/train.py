import logging
import typing as t
from datetime import date, datetime

import src.scraper.api as api
import src.scraper.station as st
import src.scraper.train_stop as tr_st
from src import types
from src.const import TIMEZONE


class Train:
    """A ViaggiaTreno train.

    Attributes:
        number (int): the train number
        origin (Station): the departing station
        departing_date (datetime.date | None): the departing date
        destination (Station | None): the arriving station
        category (str | None): e.g. REG, FR, IC...
        client_code (int | None): the train operator
        departed (bool | None): true if the train departed
        cancelled (bool | None): true if the train has been cancelled (partially or totally)

    Extended attributes: these attributes are updated by the fetch() method.
        stops (List[TrainStop] | None): the train stops; see TrainStop for more details
        delay (int | None): instantaneous delay of the train, based on last detection
        last_detection_place (str | None): place of last detection, it can be a station (or a stop)
        last_detection_time (datetime | None): time of last detection
        crowding (float | None): crowding level (only for trains operated by Trenord)
        crowding_source (str | None): source confidence for crowding parameter (only for trains operated by Trenord)

    Meta attributes:
        _phantom (bool): true if no more data can be fetched (e.g. train is cancelled)
        _trenord_phantom (bool): true if the train is Trenord's and no data can be fetched using its API
        _fetched (datetime | None): the last time the data has been fetched successfully
    """

    def __init__(self, number: int, origin: st.Station, departing_date: date) -> None:
        """Initialize a new train.

        Args:
            number (int): the train number
            origin (Station): the departing station
            departing_date (date): the departing date

        Notes:
            Other fields can be set manually or using the fetch() method.
        """
        self.number: int = number
        self.origin: st.Station = origin
        self.departing_date: date = departing_date
        self.destination: st.Station | None = None
        self.category: str | None = None
        self.client_code: int | None = None
        self.departed: bool | None = None
        self.cancelled: bool | None = None

        # Extended attributes
        self.stops: t.List[tr_st.TrainStop] | None = None
        self.delay: int | None = None
        self.last_detection_place: str | None = None
        self.last_detection_time: datetime | None = None
        self.crowding: float | None = None
        self.crowding_source: float | None = None

        self._phantom: bool = False
        self._trenord_phantom: bool = False
        self._fetched: datetime | None = None

    @classmethod
    def _from_station_departures_arrivals(cls, train_data: dict) -> "Train":
        """Initialize a new train from the data returned by
        ViaggiaTrenoAPI._station_departures_or_arrival().

        Args:
            train_data (dict): the data to initialize the train with

        Returns:
            Train: the initialized train
        """
        departing_date_midnight = api.ViaggiaTrenoAPI._to_datetime(
            train_data["dataPartenzaTreno"]
        )
        assert isinstance(departing_date_midnight, datetime)

        train: Train = cls(
            number=train_data["numeroTreno"],
            origin=st.Station.by_code(train_data["codOrigine"]),
            departing_date=departing_date_midnight.date(),
        )

        train.category = train_data["categoriaDescrizione"].upper().strip()
        train.client_code = train_data["codiceCliente"]
        train.departed = not train_data["nonPartito"]
        train.cancelled = (
            train_data["provvedimento"] != 0
            or "cancellazione.png" in train_data["compImgCambiNumerazione"]
        )
        return train

    def fetch(self):
        """Try fetch more details about the train.

        Notes:
            Some trains (especially cancelled or partially cancelled ones)
            can't be fetched with this API. If so, self._phantom is set to True.
        """
        try:
            raw_details: str = api.ViaggiaTrenoAPI._raw_request(
                "andamentoTreno",
                self.origin.code,
                self.number,
                int(
                    datetime.combine(
                        self.departing_date.today(),
                        datetime.min.time(),
                        tzinfo=TIMEZONE,
                    ).timestamp()
                    * 1000
                ),
            )
            train_data: types.JSONType = api.ViaggiaTrenoAPI._decode_json(raw_details)
        except api.BadRequestException:
            self._phantom = True
            return

        try:
            self.destination = st.Station.by_code(train_data["idDestinazione"])
        except api.BadRequestException:
            # No destination available or destination station not found
            pass

        if (
            (category := train_data["categoria"].upper().strip())
            and len(category) > 0
            and not self.category
        ):
            self.category = category

        self.departed = not train_data["nonPartito"]
        self.cancelled = train_data["provvedimento"] != 0

        self.delay = train_data["ritardo"] if self.departed else None
        self.last_detection_place = (
            train_data["stazioneUltimoRilevamento"]
            if train_data["stazioneUltimoRilevamento"] != "--"
            else None
        )
        self.last_detection_time = api.ViaggiaTrenoAPI._to_datetime(
            train_data["oraUltimoRilevamento"]
        )

        self.stops = list()
        for raw_stop in train_data["fermate"]:
            stop: tr_st.TrainStop = tr_st.TrainStop._from_raw_data(raw_stop)
            self.stops.append(stop)

        self._fetched = datetime.now()

        if self.client_code == api.TrenordAPI.TRENORD_CLIENT_CODE:
            self.fetch_trenord()

        if len(self.stops) == 0 and self.cancelled:
            self._phantom = True
            return

        # Assertion: there should always be at least two stops - the first and the last.
        assert len(self.stops) >= 2

        # API bug: sometimes, the last stop is not marked as last
        logging.warning(f"{self.category} {self.number} has not a last stop.")
        if len(list(filter(lambda s: s.stop_type == tr_st.TrainStopType.LAST, self.stops))) == 0:  # fmt: skip
            i = len(self.stops) - 1
            while i > 0:
                if self.stops[i] != tr_st.TrainStopType.CANCELLED and isinstance(
                    self.stops[i].arrival, tr_st.TrainStopTime
                ):
                    break
                i -= 1
            if i < 2:
                self.cancelled = True
                return

            self.stops[i].stop_type = tr_st.TrainStopType.LAST

    def fetch_trenord(self) -> None:
        """Try fetch more details about the train, using Trenord API."""

        if (
            self.client_code != api.TrenordAPI.TRENORD_CLIENT_CODE
            or self._trenord_phantom
        ):
            return

        assert self._fetched

        # Sometimes, ViaggiaTreno returns "trains" operated by Trenord
        # that don't really operate any passenger services.
        # On the other hand, such trains are not returned by Trenord API
        # which is more precise.
        try:
            trenord_details_raw = api.TrenordAPI._raw_request("train", self.number)
            trenord_details = api.ViaggiaTrenoAPI._decode_json(trenord_details_raw)
            assert len(trenord_details) > 0
        except AssertionError:
            self._trenord_phantom = True
            logging.debug(
                f"Trenord train {self.number} is not present in Trenord API. Marked as phantom."
            )
            return
        except api.BadRequestException as e:
            logging.warning(e, exc_info=True)
            return

        # Trenord returns multiple trains and possible journeys.
        # This algorithm selects the correct train actual data.
        actual_train_info: types.JSONType | None = None
        actual_stop_info: types.JSONType | None = None
        for data in trenord_details:
            for journey in data.get("journey_list", []):
                train_info: types.JSONType = journey["train"]
                stop_info: types.JSONType = journey["pass_list"]

                if train_info["date"] != datetime.now().strftime("%Y%m%d"):
                    continue

                if len(stop_info) == 0:
                    continue

                if not any([stop.get("actual_data") for stop in stop_info]):
                    continue

                actual_train_info = train_info
                actual_stop_info = stop_info
                break

        if not actual_train_info or not actual_stop_info:
            logging.warning(
                f"Can't update info about {self.category} {self.number} using Trenord API: no actual data found."
            )
            return

        self.departed = bool(actual_train_info.get("actual_time", False))
        self.crowding = actual_train_info.get("crowding", {}).get("percentage", None)
        self.crowding_source = actual_train_info.get("crowding", {}).get("source", None)

        old_stops = self.stops
        self.stops = list()
        for i, raw_stop in enumerate(actual_stop_info):
            stop: tr_st.TrainStop
            try:
                stop = tr_st.TrainStop._from_trenord_raw_data(raw_stop)
            except AssertionError:
                # The stop - for some unknown reason - has no 'station' information
                # in Trenord database. Use old stop data.
                logging.warning(
                    f"Incomplete Trenord stop data for {self.category} {self.number} stop #{i}."
                )
                stop = old_stops[i]
            self.stops.append(stop)

    def arrived(self) -> bool | None:
        """Return True if the train has arrived (no more information to fetch),
        False otherwise.

        Returns:
            bool | None: True if the train has arrived, False otherwise.
            None if the train has never been fetched.
        """
        if not self._fetched or self._phantom:
            return None

        if self.cancelled:
            return True

        assert isinstance(self.stops, list)
        arriving_stop: tr_st.TrainStop = next(
            filter(lambda s: s.stop_type == tr_st.TrainStopType.LAST, self.stops)
        )
        assert isinstance(arriving_stop.arrival, tr_st.TrainStopTime)
        return arriving_stop.arrival.actual is not None

    def __repr__(self) -> str:
        if not self._fetched:
            if self.departed and self.category:
                return f"Treno [{'D' if self.departed else 'S'}] {self.category} {self.number} : {self.origin} -> ???"
            else:
                return f"Treno [?] ??? {self.number} : {self.origin} -> ???"

        if self._phantom:
            return f"Treno [?] {self.category} {self.number} : {self.origin} -> ?"

        assert isinstance(self.stops, list)
        return (
            f"Treno [{'D' if self.departed else 'S'}{'X' if self.cancelled else ''}] "
            f"{self.category} {self.number} : {self.origin} -> {self.destination}"
            f"{f' ({round(self.crowding, 2)}%)' if self.crowding else ''}"
            f"\n{chr(10).join([str(stop) for stop in self.stops])}"
        )

    def __hash__(self) -> int:
        """Return the hash code.

        Notes:
            Trains with the same number and origin but departing in different days
            will have a different hash code.
        """
        return (
            hash(self.number)
            + hash(self.origin.code)
            + hash(self.departing_date if self.departing_date else date.today())
        )
