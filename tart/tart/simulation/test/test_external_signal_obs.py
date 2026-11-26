import os
import tempfile
import unittest

import numpy as np

from tart.operation import observation, settings
from tart.simulation.radio import Max2769B
from tart.util import utc


class TestExternalSignalObs(unittest.TestCase):
    """Test creation of a raw observation file (.h5) from an externally
    simulated 1.57542 GHz time series passed through the Max2769B radio model.
    """

    def setUp(self):
        self.config = settings.from_file("./tart/test/test_telescope_config.json")
        self.num_ant = self.config.get_num_antenna()
        self.n_samples = 2**12
        noiselvls = 0.1 * np.ones(self.num_ant)
        self.rad = Max2769B(noise_level=noiselvls, n_samples=self.n_samples)

        # externally simulated 1.57542 GHz time series, one row per antenna,
        # sampled at the full rate rad.sampling_rate = ref_freq * freq_mult
        self.timebase = np.arange(
            0, self.rad.sample_duration, 1.0 / self.rad.sampling_rate
        )
        self.ant_sigs = np.array(
            [
                np.cos(2 * np.pi * 1575.42e6 * self.timebase + phase)
                for phase in np.linspace(0.0, np.pi, self.num_ant)
            ]
        )
        self.tmpdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_external_signal_to_h5_observation(self):
        timestamp = utc.now()
        obs = self.rad.get_full_obs(
            self.ant_sigs, timestamp, self.config, self.timebase
        )

        # the radio produces one boolean (1-bit) data stream per antenna
        self.assertEqual(obs.data.shape, (self.num_ant, self.n_samples))
        self.assertEqual(obs.data.dtype, np.bool_)

        filename = os.path.join(self.tmpdir.name, "sim_obs.h5")
        obs.to_hdf5(filename)

        loaded = observation.Observation_Load(filename)

        self.assertEqual(loaded.get_julian_date(), obs.get_julian_date())
        self.assertEqual(loaded.get_sampling_rate(), self.rad.ref_freq)
        for ant in range(self.num_ant):
            self.assertTrue((loaded.get_antenna(ant) == obs.get_antenna(ant)).all())

    def test_external_signal_to_hdf_observation(self):
        # the .hdf extension must keep working alongside .h5
        obs = self.rad.get_full_obs(
            self.ant_sigs, utc.now(), self.config, self.timebase
        )
        filename = os.path.join(self.tmpdir.name, "sim_obs.hdf")
        obs.to_hdf5(filename)

        loaded = observation.Observation_Load(filename)
        self.assertTrue((loaded.get_antenna(0) == obs.get_antenna(0)).all())


if __name__ == "__main__":
    unittest.main()
