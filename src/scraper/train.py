import typing as t
from datetime import datetime

import src.scraper.api as api
import src.scraper.station as st
import src.scraper.train_stop as tr_st
from src import types


class Train:
    """A ViaggiaTreno train.

    Attributes:
        number (int): the train number
        origin (Station): the departing station
        destination (Station | None): the arriving station
        category (str | None): e.g. REG, FR, IC...
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

    def __init__(self, number: int, origin: st.Station) -> None:
        """Initialize a new train.

        Args:
            number (int): the train number
            origin (Station): the departing station

        Notes:
            Other fields can be set manually or using the fetch() method.
        """
        self.number: int = number
        self.origin: st.Station = origin
        self.destination: st.Station | None = None
        self.category: str | None = None
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
        train: Train = cls(
            number=train_data["numeroTreno"],
            origin=st.Station.by_code(train_data["codOrigine"]),
        )
        train.category = train_data["categoriaDescrizione"].upper().strip()
        train.departed = not train_data["nonPartito"]
        train.cancelled = train_data["provvedimento"] != 0
        return train

    def fetch(self):
        """Try fetch more details about the train.

        Notes:
            Some trains (especially cancelled or partially cancelled ones)
            can't be fetched with this API. If so, self._phantom is set to True.
        """
        # Calculate midnight of today
        now: datetime = datetime.now()
        midnight: datetime = datetime(
            year=now.year, month=now.month, day=now.day, hour=0, minute=0, second=0
        )

        try:
            raw_details: str = api.ViaggiaTrenoAPI._raw_request(
                "andamentoTreno",
                self.origin.code,
                self.number,
                int(midnight.timestamp() * 1000),
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

        # There should always be at least two stops: the first and the last.
        assert len(self.stops) >= 2

        self._fetched = datetime.now()

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
