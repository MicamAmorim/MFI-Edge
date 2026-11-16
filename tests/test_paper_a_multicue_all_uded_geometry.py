#!/usr/bin/env python3
"""Purely synthetic tests of cached MultiCue/UDED SIFT geometry: no source data."""
import sys
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_paper_a_multicue_all_uded_geometry import compare, features, flann_index


class GeometricLineageTest(unittest.TestCase):
    def test_translation_recognized(self):
        rng = np.random.default_rng(123)
        a = rng.integers(0, 256, (480, 640), dtype=np.uint8)
        B = cv2.warpAffine(
            a, np.float32([[1., 0., 23.], [0., 1., 17.]]), (640, 480))
        detector = cv2.SIFT_create(nfeatures=3500)
        ka, da = detector.detectAndCompute(a, None)
        kb, db = detector.detectAndCompute(B, None)
        x = np.asarray([kp.pt for kp in ka], np.float32).reshape(-1, 2)
        y = np.asarray([kp.pt for kp in kb], np.float32).reshape(-1, 2)
        matches, inliers, fraction, valid = compare(x, da, y, db, flann_index(db))
        self.assertGreater(matches, 100)
        self.assertGreater(inliers, 90)
        self.assertGreater(fraction, 0.9)
        self.assertTrue(valid)

    def test_cache_provenance_and_reuse(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / "synthetic.png"
            img = np.random.default_rng(19).integers(
                0, 256, (256, 256, 3), dtype=np.uint8)
            self.assertTrue(cv2.imwrite(str(path), img))
            import hashlib
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            record = {"path": path, "sha256": digest}
            sift = cv2.SIFT_create(nfeatures=3500)
            first = features(record, root, sift)
            second = features(record, root, sift)
            self.assertTrue(np.array_equal(first[0], second[0]))
            self.assertTrue(np.array_equal(first[1], second[1]))
            self.assertEqual(len(list(root.glob("sift_*.npz"))), 1)


if __name__ == "__main__":
    unittest.main()
