# A UTC class that allows the construction of datetime objects with the timezone of UTC.
# Tim Molteno 2013-2022
#
from datetime import datetime, timezone

from dateutil import parser

UTC = timezone.utc


def utc_datetime(year, month, day, hour=0, minute=0, second=0.0):
    s = int(second)
    us = int((second - int(second)) * 1000000)
    return datetime(year=year, month=month, day=day,
                    hour=hour, minute=minute, second=s,
                    microsecond=us, tzinfo=timezone.utc)


def to_utc(dt):
    if dt.tzinfo is None:
        err = f"Attempting to convert non-utc timezone ({dt}) to utc: {dt.tzinfo}"
        raise RuntimeError(err)
    if dt.tzinfo.utcoffset(dt).total_seconds() != 0:
        err = f"Attempting to convert non-utc timezone ({dt}) to utc: {dt.tzinfo}"
        raise RuntimeError(err)
    return dt


def now():
    return datetime.now(timezone.utc)


def from_string(repr):
    return to_utc(parser.parse(repr))


def to_string(timestamp):
    return timestamp.isoformat()
