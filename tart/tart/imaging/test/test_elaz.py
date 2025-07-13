"""
Solar Radio Source

Calculate the position in horizontal coordinates for the sun.
"""
#
# Copyright (c) Tim Molteno 2013. tim@elec.ac.nz
#
# import datetime
# import math
# from tart.util import angle


import unittest
import numpy as np

from tart.imaging.elaz import ElAz


class TestElaz(unittest.TestCase):

    def test_elaz_lmn_vertical(self):
        elaz = ElAz(90,0)
        elaz2 = ElAz(90,90)

        self.assertAlmostEqual(elaz.l, 0)
        self.assertAlmostEqual(elaz.m, 0)
        self.assertAlmostEqual(elaz2.l, 0)
        self.assertAlmostEqual(elaz2.m, 0)


    def test_elaz_lmn_horizontal(self):
        elaz = ElAz(0,0)    # Due north (straight up) 0, 1
        elaz2 = ElAz(0,90)  # Due west (-1,0)

        self.assertAlmostEqual(elaz.l, 0)
        self.assertAlmostEqual(elaz.m, 1)
        self.assertAlmostEqual(elaz2.l, -1)
        self.assertAlmostEqual(elaz2.m, 0)


    def test_elaz_px_window(self):
        elaz = ElAz(90,0)

        x_min, x_max, y_min, y_max, area = elaz.get_px_window(num_bins=128, window_deg=6)
        self.assertAlmostEqual(x_min, 61)
        self.assertAlmostEqual(x_max, 67)
        x_min, x_max, y_min, y_max, area = elaz.get_px_window(num_bins=128, window_deg=3)
        self.assertAlmostEqual(x_min, 62)
        self.assertAlmostEqual(x_max, 66)

        self.assertAlmostEqual(y_min, 62)
        self.assertAlmostEqual(y_max, 66)

    def test_elaz_px_vertical(self):

        elaz = ElAz(90,0)
        elaz2 = ElAz(90,90)

        x,y = elaz.get_px(num_bins=128)
        self.assertAlmostEqual(x, 64)
        self.assertAlmostEqual(y, 64)

        x,y = elaz2.get_px(num_bins=128)
        self.assertAlmostEqual(x, 64)
        self.assertAlmostEqual(y, 64)


    def test_elaz_px_horizontal(self):

        elaz = ElAz(0,0)    # Due north (straight up, center) 0, 1
        elaz2 = ElAz(0,90)  # Due west (-1,0)

        x,y = elaz.get_px(num_bins=128)
        self.assertAlmostEqual(x, 64)
        self.assertAlmostEqual(y, 0)

        x,y = elaz2.get_px(num_bins=128)
        self.assertAlmostEqual(x, 0)
        self.assertAlmostEqual(y, 64)

    def test_round_trip(self):
        num_bins = 256
        for i in range(100):
            elaz = ElAz(np.random.uniform(0,90),
                        np.random.uniform(0,360))
            l, m = elaz.get_lm()
            x, y = elaz.get_px(num_bins)

            # Now construct elaz from x,y

            elaz2 = ElAz.from_pixels(x,y, num_bins)

            self.assertAlmostEqual(elaz.el_r, elaz2.el_r)
            self.assertAlmostEqual(elaz.az_r, elaz2.az_r)
