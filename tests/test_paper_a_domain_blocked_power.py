#!/usr/bin/env python3
"""Synthetic tests only; no dataset, GT or F1 reads."""
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from simulate_paper_a_domain_blocked_power import (
    ranks_z, holm_two, null_distribution, synthetic_sample,
    pooled_within_domain, simulate_design, SCENARIOS,
)


class BlockedPowerTests(unittest.TestCase):
    def test_rank_center_and_scale(self):
        r = ranks_z(np.array([3., 1., 2., 4.]))
        self.assertAlmostEqual(float(np.mean(r)), 0., places=6)
        self.assertAlmostEqual(float(np.std(r, ddof=1)), 1., places=6)

    def test_holm(self):
        self.assertEqual(holm_two(.01, .04), (True, True))
        self.assertEqual(holm_two(.03, .04), (False, False))

    def test_permutation_null(self):
        null = null_distribution(25, 25, 1500, np.random.default_rng(5))
        self.assertEqual(len(null), 1500)
        self.assertGreater(float(np.std(null)), 0.)

    def test_effect_direction(self):
        data = synthetic_sample(100, 100, .4, .4, .3, np.random.default_rng(2))
        t1, t2 = pooled_within_domain(*data, 100)
        self.assertGreater(t1, .1)
        self.assertGreater(t2, .1)

    def test_null_domain_shift_type_i(self):
        original = SCENARIOS.copy()
        try:
            SCENARIOS.clear()
            SCENARIOS["null"] = (0., 0., 1.2)
            out = simulate_design(45, 45, 300, 3000, 13)[0]
            self.assertLess(out["probability_any_rejection"], .10)
        finally:
            SCENARIOS.clear()
            SCENARIOS.update(original)


if __name__ == "__main__":
    unittest.main()
