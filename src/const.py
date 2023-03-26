from enum import Enum

from dateutil import tz

# Global timezone used in all datetime calls.
TIMEZONE = tz.gettz("GMT+1")

# Intra-day split hour
INTRADAY_SPLIT_HOUR: int = 4


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
    def from_code(cls, code: int) -> "RailwayCompany":
        try:
            return cls(code)
        except ValueError:
            return cls.OTHER
