import typing as t
from datetime import date, datetime, timedelta
from enum import Enum

import src.scraper.api as api
import src.scraper.station as st
from src.scraper.exceptions import IncompleteTrenordStopDataException


class TrainStopType(Enum):
    """A train stop type."""

    FIRST = "P"
    STOP = "F"
    LAST = "A"
    CANCELLED = "C"


class TrainStopTime:
    """Helper class to handle arrival and departures times.

    Attributes:
        expected (datetime): expected departing or arrival time
        actual (datetime | None): actual departing or arrival time
    """

    def __init__(self, expected: datetime, actual: datetime | None) -> None:
        """Initialize a new TrainStopTime object.

        Args:
            expected (datetime): expected departing or arrival time
            actual (datetime | None): actual departing or arrival time
        """
        assert expected is not None

        self.expected: datetime = expected
        self.actual: datetime | None = actual

    def passed(self) -> bool:
        """Return if the train actually arrived or departed from the station.

        Returns:
            bool: True if the actual time is not None
        """
        return self.actual is not None

    def delay(self) -> float | None:
        """Return the delay in minutes.

        Returns:
            int | None: delay in minutes, None if not .passed().
        """
        if not self.passed():
            return None

        assert isinstance(self.actual, datetime)
        assert isinstance(self.expected, datetime)

        if self.actual >= self.expected:
            return (self.actual - self.expected).seconds / 60
        else:
            return -(self.expected - self.actual).seconds / 60

    def __repr__(self) -> str:
        hm = lambda d: d.strftime("%H:%M")

        ret: str = hm(self.expected)
        if not self.passed():
            return ret

        ret += f" ~ {hm(self.actual)}"
        if self.delay() == 0:
            return ret

        delay: float | None = self.delay()
        assert isinstance(delay, float)

        sign: str = "+" if delay > 0 else "-"
        ret += f" {sign}{round(abs(delay), 1)}m"

        return ret


class TrainStop:
    """A ViaggiaTreno train stop.

    Attributes:
        station (st.Station): the station the train is stopping by
        stop_type (TrainStopType): the type of stop (first, last, stop)
        platform_expected (str | None): expected platform
        platform_actual (str | None): actual platform
        arrival (TrainStopTime | None): arrival time, can be None if it's the first stop
        departure (TrainStopTime | None): departure time, can be None if it's the last stop
    """

    def __init__(
        self,
        station: st.Station,
        stop_type: TrainStopType,
        platform_expected: str | None,
        platform_actual: str | None,
        arrival_expected: datetime | None,
        arrival_actual: datetime | None,
        departure_expected: datetime | None,
        departure_actual: datetime | None,
    ) -> None:
        """Initialize a new TrainStop object.

        Args:
            station (st.Station): the station the train is stopping by
            stop_type (TrainStopType): the type of stop (first, last, stop)
            platform_expected (str | None): expected platform
            platform_actual (str | None): actual platform
            arrival_expected (datetime | None): expected arrival time
            arrival_actual (datetime | None): actual arrival time
            departure_expected (datetime | None): expected departure time
            departure_actual (datetime | None): actual departure time
        """
        self.station: st.Station = station
        self.stop_type: TrainStopType = stop_type

        self.platform_expected: str | None = platform_expected
        self.platform_actual: str | None = platform_actual

        self.arrival: TrainStopTime | None = None
        self.departure: TrainStopTime | None = None

        if self.stop_type == TrainStopType.CANCELLED:
            return

        if self.stop_type != TrainStopType.FIRST:
            assert isinstance(arrival_expected, datetime)
            self.arrival = TrainStopTime(arrival_expected, arrival_actual)

        if self.stop_type != TrainStopType.LAST:
            assert isinstance(departure_expected, datetime)
            self.departure = TrainStopTime(departure_expected, departure_actual)

    @classmethod
    def _from_raw_data(cls, stop_data: dict) -> "TrainStop":
        """Initialize a new train stop from the data processed by Train.fetch()

        Args:
            stop_data (dict): the data to initialize the class with

        Returns:
            TrainStop: a constructed TrainStop object
        """
        station = st.Station.by_code(stop_data["id"])
        if station._phantom:
            station.name = stop_data["stazione"].title().strip()

        stop_type: TrainStopType
        if stop_data["tipoFermata"] == "P":
            stop_type = TrainStopType.FIRST
        elif stop_data["tipoFermata"] == "A":
            stop_type = TrainStopType.LAST
        elif stop_data["tipoFermata"] == "F":
            stop_type = TrainStopType.STOP
        else:
            stop_type = TrainStopType.CANCELLED

        _to_dt = api.ViaggiaTrenoAPI._to_datetime

        return cls(
            station=station,
            stop_type=stop_type,
            platform_expected=(
                stop_data["binarioProgrammatoArrivoDescrizione"]
                or stop_data["binarioProgrammatoPartenzaDescrizione"]
            ),
            platform_actual=(
                stop_data["binarioEffettivoArrivoDescrizione"]
                or stop_data["binarioEffettivoPartenzaDescrizione"]
            ),
            arrival_expected=_to_dt(stop_data["arrivo_teorico"]),
            arrival_actual=_to_dt(stop_data["arrivoReale"]),
            departure_expected=_to_dt(stop_data["partenza_teorica"]),
            departure_actual=_to_dt(stop_data["partenzaReale"]),
        )

    @classmethod
    def _from_trenord_raw_data(
        cls, stop_data: dict, today: date = date.today()
    ) -> t.Union["TrainStop", None]:
        """Initialize a new train stop from data processed by Train.trenord_fetch()

        Args:
            stop_data (dict): the data to initialize the class with
            today (date): the date of the train, used to parse datetimes

        Returns:
            TrainStop: a constructed TrainStop object
        """

        def _hhmmss_to_dt(hhmmss: str | None) -> datetime | None:
            """Parse and return a Trenord time string into a datetime object.

            Args:
                hhmmss (str | None): the string to parse

            Returns:
                datetime | None: the parsed datetime object.
            """
            if not hhmmss:
                return None

            computed: datetime = datetime.strptime(hhmmss, "%H:%M:%S").replace(
                year=today.year,
                month=today.month,
                day=today.day,
                tzinfo=api.TIMEZONE,
            )
            if computed.hour < 4:
                computed += timedelta(days=1)
            return computed

        if not stop_data["actual_data"]:
            return None

        station_code: str | None = (
            stop_data["station"].get("station_id")
            or stop_data["actual_data"]["actual_station_mir"]
        )
        try:
            assert isinstance(station_code, str) and len(station_code) > 0
        except AssertionError:
            raise IncompleteTrenordStopDataException

        station = st.Station.by_code(station_code)
        if station._phantom and stop_data.get("station", {}).get("station_ori_name"):
            station.name = stop_data["station"]["station_ori_name"].title().strip()

        stop_type: TrainStopType
        stop_type_raw = (
            stop_data["actual_data"].get("actual_type", None) or stop_data["type"]
        )
        if stop_type_raw == "O":
            stop_type = TrainStopType.FIRST
        elif stop_type_raw == "F":
            stop_type = TrainStopType.STOP
        elif stop_type_raw == "D":
            stop_type = TrainStopType.LAST
        else:
            stop_type = TrainStopType.CANCELLED

        if stop_data["cancelled"]:
            stop_type = TrainStopType.CANCELLED

        return cls(
            station=station,
            stop_type=stop_type,
            platform_expected=stop_data.get("platform", None),
            platform_actual=None,
            arrival_expected=_hhmmss_to_dt(stop_data.get("arr_time")),
            arrival_actual=_hhmmss_to_dt(
                stop_data["actual_data"].get("arr_actual_time")
            ),
            departure_expected=_hhmmss_to_dt(stop_data.get("dep_time")),
            departure_actual=_hhmmss_to_dt(
                stop_data["actual_data"].get("dep_actual_time")
            ),
        )

    def __repr__(self) -> str:
        ret = f"@ ({self.stop_type.value}) {self.station.name} "
        if self.stop_type == TrainStopType.FIRST:
            ret += f"{self.departure}"
        elif self.stop_type == TrainStopType.LAST:
            ret += f"{self.arrival}"
        else:
            ret += f"{self.arrival} --> {self.departure}"

        platform_exp: str = self.platform_expected if self.platform_expected else "?"

        if self.platform_actual:
            return ret + f" [{platform_exp} ~ {self.platform_actual}]"
        else:
            return ret + f" [{platform_exp}]"
