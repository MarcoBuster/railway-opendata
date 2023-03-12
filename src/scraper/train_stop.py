from datetime import datetime
from enum import Enum

import src.scraper.api as api
import src.scraper.station as st


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
            station=st.Station.by_code(stop_data["id"]),
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

    def __repr__(self) -> str:
        ret = f"@ {self.station.name} "
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
