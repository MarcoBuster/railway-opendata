import locale
import logging
from enum import Enum

from dateutil import tz

# Global timezone used in all datetime calls.
TIMEZONE = tz.gettz("GMT+1")

# Intra-day split hour
INTRADAY_SPLIT_HOUR: int = 4

# Pandas locale
LOCALE: str = "it_IT.utf-8"
try:
    locale.setlocale(locale.LC_ALL, LOCALE)
except locale.Error:
    logging.warning(
        f"Can't set locale {LOCALE}. "
        f"Using the default one: {locale.getdefaultlocale()[0]}"
    )


# Weekdays
def _w(weekday_number: int) -> str:
    return locale.nl_langinfo(getattr(locale, f"DAY_{weekday_number}")).title()


WEEKDAYS = {
    _w(2): 1,  # Monday
    _w(3): 2,  # Tuesday
    _w(4): 3,  # Wednesday
    _w(5): 4,  # Thursday
    _w(6): 5,  # Friday
    _w(7): 6,  # Saturday
    _w(1): 7,  # Sunday
}


class RailwayCompany(Enum):
    """Italian railway companies codes."""

    TRENITALIA_AV = 1
    TRENITALIA_REG = 2
    TRENITALIA_IC = 4
    TPER = 18
    TRENORD = 63
    OBB = 64
    OTHER = -1

    @classmethod
    def from_code(cls, code: int) -> str:
        try:
            instance: "RailwayCompany" = cls(code)
        except ValueError:
            instance: "RailwayCompany" = cls.OTHER
        return instance.name
