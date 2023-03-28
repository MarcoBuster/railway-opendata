from dateutil import tz

# Global timezone used in all datetime calls.
TIMEZONE = tz.gettz("Europe/Rome")
TIMEZONE_GMT = tz.gettz("GMT")

# Intra-day split hour
INTRADAY_SPLIT_HOUR: int = 4
