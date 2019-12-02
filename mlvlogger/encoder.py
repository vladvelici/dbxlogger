import json
import math
import numbers
import datetime

from . import mlvtypes


MLVCODE_NAN = "nan"
MLVCODE_INFINITY = "inf"
MLVCODE_NEG_INFINITY = "-inf"

def encode_datetime(dt):
    """ Returns UTC date in ISO 8601 format, with Z at the end instead of
    +00:00.

    If dt has a timezone it is respected. If no timezone given, local timezone
    assumed. All results are in UTC regardless of input timezone.
    """
    stamp = dt.timestamp()
    utcdt = datetime.datetime.fromtimestamp(stamp, tz=datetime.timezone.utc)
    return utcdt.isoformat().replace("+00:00", "Z")

class MLVEncoder(json.JSONEncoder):

    def default(self, obj):

        # handle File MLV objects
        # if isinstance(obj, mlvtypes.File):
        #     return obj.encodable()

        # handle numbers
        if isinstance(obj, numbers.Number):
            if math.isnan(obj):
                return {"_mlv": MLVCODE_NAN}
            if math.isinf(obj):
                if obj < 0:
                    return {"_mlv": MLVCODE_NEG_INFINITY}
                elif obj > 0:
                    return {"_mlv": MLVCODE_INFINITY}

        # handle dates: make all UTC timestamped with timestamp info removed but encoded with a Z at the end
        if isinstance(obj, datetime.datetime):
            return encode_datetime(obj)

        return super().default(obj)
