import unittest
import math

from astropy import time 
from astropy.time import Time 
from datetime import datetime

import tart.util.utc as utc

class TestUTC(unittest.TestCase):

    def test_basic(self):
        utcd = utc.utc_datetime(year=2009, month=7, day=22, hour=5, minute=9, second=50.3)
        apyt = time.Time('2009-07-22 05:09:50.3', format='iso', scale='utc')
        apyt2 = time.Time(utcd, scale='utc')

        utcd2 = apyt.to_datetime(utc.UTC)
        obstime = apyt2.to_datetime(utc.UTC)

        self.assertEqual(utcd2.year, utcd.year)
        self.assertEqual(utcd2.month, utcd.month)
        self.assertEqual(utcd2.day, utcd.day)
        self.assertEqual(utcd2.hour, utcd.hour)
        self.assertEqual(utcd2.minute, utcd.minute)
        self.assertEqual(utcd2.second, utcd.second)

        self.assertEqual((utcd - obstime).total_seconds(), 0.0)


    def test_now(self):
        now = utc.to_utc(datetime.utcnow())
        
        now_utc = utc.now()
        print(now, now_utc)
        self.assertAlmostEqual((now - now_utc).total_seconds(), 0.0, 3)
