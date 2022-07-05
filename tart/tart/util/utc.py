# A UTC class that allows the construction of datetime objects with the timezone of UTC.
# Tim Molteno 2013-2022
#
import pytz

from datetime import tzinfo, timedelta, datetime

UTC = pytz.utc

def utc_datetime(year, month, day, hour=0, minute=0, second=0.0):
    s = int(second)
    us = int((second - int(second)) * 1000000)
    return datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=s, microsecond=us, tzinfo=pytz.utc)


def to_utc(dt):
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(pytz.utc)

def now():
    return to_utc(datetime.utcnow())
