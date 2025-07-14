import datetime
import unittest

from astropy import time

from tart.util import utc


class TestUTC(unittest.TestCase):

    def compare(self, utcd, utcd2):
        self.assertEqual(utcd2.year, utcd.year)
        self.assertEqual(utcd2.month, utcd.month)
        self.assertEqual(utcd2.day, utcd.day)
        self.assertEqual(utcd2.hour, utcd.hour)
        self.assertEqual(utcd2.minute, utcd.minute)
        self.assertEqual(utcd2.second, utcd.second)
        self.assertAlmostEqual((utcd2 - utcd).total_seconds(), 0.0, 3)


    def test_basic(self):
        utcd = utc.utc_datetime(year=2009, month=7, day=22, hour=5, minute=9, second=50.3)
        apyt = time.Time('2009-07-22 05:09:50.3', format='iso', scale='utc')
        apyt2 = time.Time(utcd, scale='utc')

        utcd2 = apyt.to_datetime(utc.UTC)
        obstime = apyt2.to_datetime(utc.UTC)

        self.compare(utcd2, utcd)

        self.assertEqual((utcd - obstime).total_seconds(), 0.0)


    def test_now(self):
        self.assertRaises(RuntimeError, utc.to_utc, datetime.datetime.now())

    def test_parsing(self):
        now = utc.now()

        # As used by create_direct_vis_dict
        rep = utc.to_string(now)

        # As used by observation.from_hdf5
        timestamp = utc.from_string(rep)

        self.compare(timestamp, now)
        self.assertEqual(timestamp.isoformat(), now.isoformat())
