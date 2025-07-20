import unittest
import logging
import numpy as np
from copy import deepcopy

from tart_tools import api_imaging
from tart_tools import api_handler
from tart.util import utc
from tart.util import angle

from tart.imaging import antenna_model
from tart.imaging import radio_source
from tart.imaging import correlator
from tart.imaging import location
from tart.imaging import calibration
from tart.imaging import elaz
from tart.simulation import skymodel
from tart.simulation import antennas
from tart.simulation import radio


logger = logging.getLogger()


class TestApi(unittest.TestCase):

    def setUp(self):
        self.api = 'https://api.elec.ac.nz/tart/nz-dunedin'
        self.pw = 'sharkbait'

        api = api_handler.APIhandler(self.api)

        self.config = api_handler.get_config(api)
        self.ant_pos = self.config.get_antenna_positions()

        gains = api.get("calibration/gain")

        vis_json = api.get("imaging/vis")

        ts = api_imaging.vis_json_timestamp(vis_json)

        cat_url = api.catalog_url(lon=self.config.get_lon(),
                                  lat=self.config.get_lat(),
                                  datestr=utc.to_string(ts))
        self.source_json = api.get_url(cat_url)

        logger.info("Data Download Complete")

        self.cv, self.timestamp = api_imaging.vis_calibrated(
            vis_json, self.config,
            gains["gain"],
            gains["phase_offset"],
            flag_list=[]
        )

    def get_fake_vis(self):

        loc = location.Location(angle.from_dms(self.config.get_lat()),
                                angle.from_dms(self.config.get_lon()),
                                self.config.get_alt())

        ANTS = [antennas.Antenna(loc, pos) for pos in self.ant_pos]
        num_ant = len(ANTS)
        ANT_MODELS = [antenna_model.GpsPatchAntenna() for i in range(num_ant)]
        NOISE_LVLS = np.zeros(num_ant)
        RAD = radio.Max2769B(n_samples=2**12, noise_level=NOISE_LVLS)

        sim_sky = skymodel.Skymodel(0, location=loc, gps=0, thesun=0, known_cosmic=0)

        timestamp = utc.now()

        # ############## HOUR HAND ###########################
        #
        # The pattern rotates once every 12 hours
        #
        hour_hand = timestamp.hour*30.0 + timestamp.minute/2.0

        self.hour_sources = [{'el': el, 'az': -hour_hand} for el in [85, 75, 65, 55]]
        for m in self.hour_sources:
            sim_sky.add_src(radio_source.ArtificialSource(loc, timestamp, r=1e6, el=m['el'], az=m['az']))

        # ############## MINUTE HAND ###########################
        #
        # The pattern rotates once every 1 hour
        #
        minute_hand = timestamp.minute*6.0 + timestamp.second/10.0

        self.minute_sources = [{'el': el, 'az': -minute_hand} for el in [90, 80, 70, 60, 50, 40, 30]]
        for m in self.minute_sources:
            sim_sky.add_src(radio_source.ArtificialSource(loc, timestamp, r=1e6, el=m['el'], az=m['az']))

        sources = sim_sky.gen_photons_per_src(timestamp, radio=RAD,
                                              config=self.config, n_samp=1)

        v_sim = antennas.antennas_simp_vis(
            ANTS, ANT_MODELS, sources, timestamp, self.config, RAD.noise_level
        )

        cv = calibration.CalibratedVisibility(v_sim)

        return cv

    def test_imaging(self):

        cv = self.get_fake_vis()
        rotation = 0.0
        api_imaging.rotate_vis(
            rotation, cv, reference_positions=deepcopy(self.ant_pos)
        )
        n_bin = 2 ** 8

        cal_ift, cal_extent, n_fft, bin_width = api_imaging.image_from_calibrated_vis(
            cv, nw=n_bin / 4, num_bin=n_bin
        )

        img = np.abs(cal_ift)
        max_p = np.max(img)
        min_p = np.min(img)
        mad_p = np.std(img)
        ift_scaled = (img - min_p) / mad_p

        import matplotlib.pyplot as plt

        for m in self.minute_sources:
            src = elaz.ElAz(m['el'], m['az'])
            x, y = src.get_px(n_bin)
            print(x, y)
            ift_scaled[x, y] = -1
        plt.imshow(ift_scaled)

        plt.show()

        for m in self.minute_sources:
            src = elaz.ElAz(m['el'], m['az'])
            x, y = src.get_px(n_bin)
            self.assertGreater(img[y, x], max_p/3)
