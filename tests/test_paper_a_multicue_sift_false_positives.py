#!/usr/bin/env python3
"""SIFT matching regression tests, synthetic arrays only; no datasets/GT."""
import sys
import unittest
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from diagnose_paper_a_multicue_sift_false_positives import mutual_match


class MutualMatchTests(unittest.TestCase):
    def test_synthetic_corresponding_descriptors(self):
        rng = np.random.default_rng(17)
        a = rng.uniform(5, 245, (80, 2)).astype(np.float32)
        d = rng.uniform(0, 1, (80, 128)).astype(np.float32)
        b = a + np.array([21., 32.], dtype=np.float32)
        r = mutual_match(a, d, b, d.copy())
        self.assertEqual(r["mutual_bf_matches"], 80)
        self.assertGreaterEqual(r["mutual_ransac_inliers"], 75)
        self.assertTrue(r["mutual_homography_valid"])

    def test_synthetic_independent_descriptors(self):
        rng = np.random.default_rng(18)
        a = rng.uniform(0, 200, (60, 2)).astype(np.float32)
        b = rng.uniform(0, 200, (60, 2)).astype(np.float32)
        d1 = rng.uniform(0, 1, (60, 128)).astype(np.float32)
        d2 = rng.uniform(0, 1, (60, 128)).astype(np.float32)
        r = mutual_match(a, d1, b, d2)
        self.assertLess(r["mutual_ransac_inliers"], 12)


if __name__ == "__main__":
    unittest.main()
