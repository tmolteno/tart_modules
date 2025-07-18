import unittest
import logging
import os

import numpy as np
from copy import deepcopy

from tart.util import utc
from tart.util import angle

from tart.imaging import antenna_model
from tart.imaging import radio_source
from tart.imaging import location
from tart.imaging import calibration
from tart.imaging import elaz
from tart.imaging import imaging
from tart.simulation import skymodel
from tart.simulation import antennas
from tart.simulation import radio
from tart.operation import settings


logger = logging.getLogger()

TESTCONFIG_FILENAME = os.path.join(os.path.dirname(__file__), '../../test/test_telescope_config.json')
ANT_POS_FILE = os.path.join(os.path.dirname(__file__), '../../test/test_calibrated_antenna_positions.json')


class TestSettings(unittest.TestCase):

    def setUp(self):
        self.config = settings.from_file(TESTCONFIG_FILENAME)
        self.config.load_antenna_positions(
            cal_ant_positions_file=ANT_POS_FILE
        )

    def get_clock_sources(self, timestamp):
        # ############## HOUR HAND ###########################
        #
        # The pattern rotates once every 12 hours
        #
        hour_hand = timestamp.hour*30.0 + timestamp.minute/2.0

        hour_sources = [{'el': el, 'az': -hour_hand} for el in [85, 75, 65, 55]]

        # ############## MINUTE HAND ###########################
        #
        # The pattern rotates once every 1 hour
        #
        minute_hand = timestamp.minute*6.0 + timestamp.second/10.0

        minute_sources = [{'el': el, 'az': -minute_hand} for el in [90, 80, 70, 60, 50, 40, 30]]

        return hour_sources, minute_sources

    def get_clock_vis(self, config, timestamp):

        loc = location.Location(angle.from_dms(config.get_lat()),
                                angle.from_dms(config.get_lon()),
                                config.get_alt())

        ant_pos = config.get_antenna_positions()
        num_ant = len(ant_pos)

        ANTS = [antennas.Antenna(loc, pos) for pos in ant_pos]
        ANT_MODELS = [antenna_model.GpsPatchAntenna() for i in range(num_ant)]
        RAD = radio.Max2769B(n_samples=2**12, noise_level=np.zeros(num_ant))

        hour_sources, minute_sources = self.get_clock_sources(timestamp)

        sim_sky = skymodel.Skymodel(0, location=loc, gps=0,
                                    thesun=0, known_cosmic=0)

        for m in hour_sources + minute_sources:
            src = radio_source.ArtificialSource(loc, timestamp, r=1e6,
                                                el=m['el'], az=m['az'])
            sim_sky.add_src(src)

        sources = sim_sky.gen_photons_per_src(timestamp, radio=RAD,
                                              config=self.config, n_samp=1)

        v_sim = antennas.antennas_simp_vis(
            ANTS, ANT_MODELS, sources, timestamp, self.config, RAD.noise_level
        )

        cv = calibration.CalibratedVisibility(v_sim)

        return cv, hour_sources, minute_sources

    def test_imaging(self):

        cv, hour_sources, minute_sources = \
            self.get_clock_vis(timestamp=utc.now(), config=self.config)

        n_bin = 2 ** 8

        cal_ift, cal_extent, n_fft, bin_width = imaging.image_from_calibrated_vis(
            cv, nw=n_bin / 4, num_bin=n_bin
        )

        img = np.abs(cal_ift)
        max_p = np.max(img)
        min_p = np.min(img)
        mad_p = np.std(img)
        ift_scaled = (img - min_p) / mad_p

        import matplotlib.pyplot as plt

        for m in minute_sources:
            src = elaz.ElAz(m['el'], m['az'])
            x, y = src.get_px(n_bin)
            print(x, y)
            ift_scaled[x, y] = -1
        plt.imshow(ift_scaled)

        plt.show()

        for m in minute_sources:
            src = elaz.ElAz(m['el'], m['az'])
            x, y = src.get_px(n_bin)
            self.assertGreater(img[x, y], max_p/3)
