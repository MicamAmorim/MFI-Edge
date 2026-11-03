"""Synthetic diagnostic: offset lines must not alter the frozen v2 defaults."""
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from synthetic_v2 import _region, make_sample


class SyntheticOffsetContract(unittest.TestCase):
    def test_default_remains_exactly_centered(self):
        default, angle, _ = _region("line", 81, np.random.default_rng(2), angle=0)
        zero, _, _ = _region("line", 81, np.random.default_rng(2),
                             angle=0, line_offset_px=0)
        np.testing.assert_array_equal(default, zero)
        self.assertEqual(angle, 0)
        self.assertFalse(default[40, 40])
        self.assertTrue(default[41, 40])

    def test_explicit_line_offset_shifts_boundary(self):
        central, _, _ = _region("line", 81, np.random.default_rng(4), angle=0)
        shifted, _, _ = _region("line", 81, np.random.default_rng(4),
                                angle=0, line_offset_px=14)
        self.assertTrue(central[48, 40])
        self.assertFalse(shifted[48, 40])
        self.assertTrue(shifted[55, 40])
        self.assertFalse(np.array_equal(central, shifted))

    def test_historical_generation_is_unchanged(self):
        cfg = {"primitive":"line", "n":81, "seed":7, "angle":22.,
               "noise":"none", "blur":0., "contrast":.5}
        a, ga = make_sample(cfg)
        b, gb = make_sample({**cfg, "line_offset_px":0.})
        np.testing.assert_array_equal(a,b)
        np.testing.assert_array_equal(ga,gb)

    def test_bad_offset_rejected(self):
        with self.assertRaises(ValueError):
            _region("line", 81, np.random.default_rng(8),
                    angle=0, line_offset_px=40)


if __name__ == "__main__":
    unittest.main(verbosity=2)
