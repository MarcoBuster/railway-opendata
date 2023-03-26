from dateutil import tz

# Global timezone used in all datetime calls.
TIMEZONE = tz.gettz("GMT+1")

# Intra-day split hour
INTRADAY_SPLIT_HOUR: int = 4
