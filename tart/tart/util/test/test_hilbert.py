import unittest

import numpy as np

from tart.util.hilbert import hilbert


class TestHilbert(unittest.TestCase):
    def test_hilbert_phase_shift(self):
        """The Hilbert transform shifts by 90 degrees (H{cos} = sin)."""
        n = 1024
        t = np.arange(n) / float(n)
        f = 8
        x = np.cos(2.0 * np.pi * f * t)
        hx = hilbert(x)
        expected = np.sin(2.0 * np.pi * f * t)
        # Compare away from the signal edges to avoid boundary effects.
        self.assertTrue(np.allclose(hx[50:-50], expected[50:-50], atol=0.05))

    def test_hilbert_odd_length(self):
        """Must handle odd-length inputs (no float-index crash)."""
        x = np.ones(101)
        hx = hilbert(x)
        self.assertEqual(hx.shape, x.shape)
        # The Hilbert transform of a constant is zero.
        self.assertTrue(np.allclose(hx, 0.0, atol=1e-6))
