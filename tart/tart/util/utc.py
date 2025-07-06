# A UTC class that allows the construction of datetime objects with the timezone of UTC.
# Tim Molteno 2013-2022
#
from datetime import datetime, timezone

from dateutil import parser

UTC = timezone.utc

def utc_datetime(year, month, day, hour=0, minute=0, second=0.0):
    s = int(second)
    us = int((second - int(second)) * 1000000)
    return datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=s, microsecond=us, tzinfo=timezone.utc)

def to_utc(dt):
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if dt.tzinfo.utcoffset(dt).total_seconds() != 0:
        raise RuntimeError(f"Attempting to convert non-utc timezone ({dt}) to utc: {dt.tzinfo}")
    return dt

def now():
    return datetime.now(timezone.utc)

def parse(timestamp):
    return to_utc(parser.parse(timestamp))

def as_string(timestamp):
    return timestamp.isoformat()
