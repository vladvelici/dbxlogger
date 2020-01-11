import json
import math
import numbers
import datetime

DBXCODE_NAN = "nan"
DBXCODE_INFINITY = "inf"
DBXCODE_NEG_INFINITY = "-inf"

def encode_datetime(dt):
    """ Returns UTC date in ISO 8601 format, with Z at the end instead of
    +00:00.

    If dt has a timezone it is respected. If no timezone given, local timezone
    assumed. All results are in UTC regardless of input timezone.
    """
    stamp = dt.timestamp()
    utcdt = datetime.datetime.fromtimestamp(stamp, tz=datetime.timezone.utc)
    return utcdt.isoformat().replace("+00:00", "Z")

class DBXEncoder(json.JSONEncoder):

    def default(self, obj):

        # handle numbers
        if isinstance(obj, numbers.Number):
            if math.isnan(obj):
                return {"_dbx": DBXCODE_NAN}
            if math.isinf(obj):
                if obj < 0:
                    return {"_dbx": DBXCODE_NEG_INFINITY}
                elif obj > 0:
                    return {"_dbx": DBXCODE_INFINITY}

        # handle dates: make all UTC timestamped with timestamp info removed but encoded with a Z at the end
        if isinstance(obj, datetime.datetime):
            return encode_datetime(obj)

        # many custom loggable objects have a __dbx_encode__ method
        if hasattr(obj, "__dbx_encode__"):
            return obj.__dbx_encode__()

        return super().default(obj)
