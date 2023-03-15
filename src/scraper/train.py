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

    Meta attributes:
        _phantom (bool): true if no more data can be fetched (e.g. train is cancelled)
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

        self._phantom: bool = False
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

        if len(self.stops) == 0 and self.cancelled:
            self._phantom = True
            return

        # Assertion: there should always be at least two stops - the first and the last.
        assert len(self.stops) >= 2

        # ViaggiaTreno bug: sometimes, the last stop is not marked as last

        if len(list(filter(lambda s: s.stop_type == tr_st.TrainStopType.LAST, self.stops))) == 0:  # fmt: skip
            self.stops[len(self.stops) - 1].stop_type = tr_st.TrainStopType.LAST

    def arrived(self) -> bool | None:
        """Return True if the train has arrived (no more information to fetch),
        False otherwise.

        Returns:
            bool | None: True if the train has arrived, False otherwise.
            None if the train has never been fetched.
        """
        if not self._fetched or self._phantom:
            return None

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
