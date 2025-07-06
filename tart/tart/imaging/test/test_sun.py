"""
Solar Radio Source

Calculate the position in horizontal coordinates for the sun.
"""
#
# Copyright (c) Tim Molteno 2013. tim@elec.ac.nz
#
import datetime
import unittest

from tart.imaging import location, sun
from tart.util import angle, utc


class TestSun(unittest.TestCase):
    def setUp(self):
        self.t = utc.utc_datetime(2002, 10, 31, 0, 2, 2)
        self.s = sun.Sun()

    def test_horizontal(self):
        el, az = self.s.to_horizontal(location.Dunedin, self.t)
        print("El %f    Az %f" % (el.to_degrees(), az.to_degrees()))
        self.assertAlmostEqual(el.to_degrees(), 57.848294, 3)
        self.assertAlmostEqual(az.to_degrees(), 8.943156, 1)

    def test_now_horizontal(self):
        t = utc.now()
        s = sun.Sun()
        el, az = s.to_horizontal(location.Dunedin, t)
        print("El %f    Az %f" % (el.to_degrees(), az.to_degrees()))

    def test_radec(self):
        Dunedin = location.Dunedin
        import ephem

        dnd = ephem.Observer()
        dnd.lon = str(Dunedin.lon.to_degrees())
        dnd.lat = str(Dunedin.lat.to_degrees())
        dnd.elevation = Dunedin.alt
        dnd.pressure = 0.0
        datee = utc.now()
        for delta in range(24):
            timedelta = datetime.timedelta(hours=delta)
            dnd.date = datee + timedelta

            j = ephem.Sun()
            j.compute(dnd)
            ra = angle.from_rad(j.ra.real)
            dec = angle.from_rad(j.dec.real)
            s = sun.Sun()
            sra, sdec = s.radec(datee + timedelta)
            self.assertAlmostEqual(sra.to_degrees(), ra.to_degrees(), 2)
            self.assertAlmostEqual(sdec.to_degrees(), dec.to_degrees(), 2)
