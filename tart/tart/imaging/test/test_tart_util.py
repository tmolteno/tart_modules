import unittest

from astropy import time

from tart.imaging.tart_util import *
from tart.util.utc import now


class TestTartUtil(unittest.TestCase):
    def test_astropy(self):
        utcd = now()
        obstime = time.Time(utcd, scale="utc")

        jd = JulianDay(utcd)

        self.assertAlmostEqual(obstime.jd, jd, 4)
