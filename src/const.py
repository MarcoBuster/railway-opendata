from enum import Enum

from dateutil import tz

# Global timezone used in all datetime calls.
TIMEZONE = tz.gettz("Europe/Rome")
TIMEZONE_GMT = tz.gettz("GMT")

# Intra-day split hour
INTRADAY_SPLIT_HOUR: int = 4

# Pandas locale
LOCALE: str = "it_IT.utf-8"

# Italian weekdays - see 'LOCALE'
WEEKDAYS = {
    "Lunedì": 1,  # Monday
    "Martedì": 2,  # Tuesday
    "Mercoledì": 3,  # Wednesday
    "Giovedì": 4,  # Thursday
    "Venerdì": 5,  # Friday
    "Sabato": 6,  # Saturday
    "Domenica": 7,  # Sunday
}

# Railway company palette
RAILWAY_COMPANIES_PALETTE = {
    "TRENITALIA_REG": "#fa1b0f",
    "TRENORD": "#298044",
    "TPER": "#d014fa",
    "TRENITALIA_AV": "#c2152e",
    "TRENITALIA_IC": "#1b48f2",
    "OBB": "#464644",
    "OTHER": "#858585",
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
