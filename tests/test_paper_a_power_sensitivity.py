"""Synthetic sanity checks of the approximate power screen, with no data reads."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from estimate_paper_a_power_sensitivity import approx_power


class SensitivityTests(unittest.TestCase):
    def test_monotone_n(self):
        self.assertLess(approx_power(120, 0.25), approx_power(150, 0.25))
        self.assertLess(approx_power(150, 0.25), approx_power(180, 0.25))

    def test_monotone_effect(self):
        self.assertLess(approx_power(150, 0.20), approx_power(150, 0.30))

    def test_null_nominal_alpha(self):
        self.assertAlmostEqual(approx_power(150, 0), 0.025, places=6)

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            approx_power(3, 0.25)
        with self.assertRaises(ValueError):
            approx_power(150, 1)


if __name__ == "__main__":
    unittest.main()
