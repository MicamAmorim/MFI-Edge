#!/usr/bin/env python3
"""Synthetic unit tests for SIFT/RANSAC overlap screening; no research data read."""
import importlib
import sys
import unittest
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
geo = importlib.import_module("audit_paper_a_multicue_mdbd_geometry")


class LocalFeatureTest(unittest.TestCase):
    def test_synthetic_unrelated_has_no_support(self):
        a = np.random.default_rng(12).integers(0, 255, (256, 256), dtype=np.uint8)
        b = np.random.default_rng(44).integers(0, 255, (256, 256), dtype=np.uint8)
        n1, n2, matches, inliers, fraction, valid = geo.match_pair(a, b)
        self.assertGreater(n1, 0)
        self.assertGreater(n2, 0)
        self.assertLess(inliers, 12)

    def test_synthetic_geometric_alignment(self):
        rng = np.random.default_rng(77)
        a = rng.integers(0, 256, (400, 500), dtype=np.uint8)
        crop = a[50:350, 70:430]
        # Same pixel structure, different canvas/position; no ground truth.
        b = np.pad(crop, ((35, 20), (24, 20)), mode="constant")
        n1, n2, matches, inliers, fraction, valid = geo.match_pair(crop, b)
        self.assertGreaterEqual(matches, 15)
        self.assertGreaterEqual(inliers, 12)
        self.assertTrue(valid)


if __name__ == "__main__":
    unittest.main()
