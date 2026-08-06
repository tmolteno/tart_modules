import unittest
from unittest import mock

import numpy as np

from tart.simulation import simulator
from tart.util import utc


class TestGetVis(unittest.TestCase):
    def test_simp_mode_uses_correlate_roll(self):
        """get_vis in 'simp' mode should use cor.correlate(obs, mode='roll')."""
        fake_sky = mock.Mock()
        fake_sky.gen_photons_per_src.return_value = []

        n = 8
        rad = mock.Mock()
        rad.baseband_timebase = np.arange(n)
        rad.int_freq = 1.0
        rad.noise_level = np.zeros(2)
        rad.n_samples = 2 ** 8
        rad.ref_freq = 16.368e6
        rad.sampling_rate = rad.ref_freq * 256.0
        rad.sample_duration = 1e-3

        cor = mock.Mock()

        config = mock.Mock()
        config.get_num_antenna.return_value = 2

        obs = mock.Mock()
        rad.get_simplified_obs.return_value = obs

        with mock.patch(
            "tart.simulation.antennas.antennas_simplified_signal",
            return_value=np.zeros((2, n), dtype=complex),
        ):
            simulator.get_vis(
                sky=fake_sky,
                cor=cor,
                rad=rad,
                ants=None,
                ant_models=None,
                config=config,
                timestamp=utc.now(),
                mode="simp",
            )

        cor.correlate.assert_called_once_with(obs, mode="roll")
        cor.correlate_roll.assert_not_called()
