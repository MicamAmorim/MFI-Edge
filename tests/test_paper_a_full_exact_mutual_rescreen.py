#!/usr/bin/env python3
"""Synthetic tests of exact mutual screen triage and checkpoint validation."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from rescreen_paper_a_multicue_uded_exact_mutual import (
    POLICY, check_resume, screen_flag,
)


class ExactMutualScreenTests(unittest.TestCase):
    def test_expected_flags(self):
        positive = {"mutual_bf_matches": 2100,
                    "mutual_ransac_inliers": 2100,
                    "mutual_inlier_fraction": 1.0,
                    "mutual_homography_valid": True}
        negative = {"mutual_bf_matches": 1,
                    "mutual_ransac_inliers": 0,
                    "mutual_inlier_fraction": 0.0,
                    "mutual_homography_valid": False}
        self.assertEqual(screen_flag(positive), "REVIEW_STRONG")
        self.assertEqual(screen_flag(negative), "NO_MATCHING_FLAG")

    def test_resume_rejects_new_dataset(self):
        valid = {
            "status": "PARTIAL_EXACT_MUTUAL_BF_IMAGE_ONLY",
            "policy": POLICY,
            "sift_cache_algorithm": "other",
            "opencv": "other",
            "reference_id": "01-0843x4",
            "reference_sha256": "a" * 64,
            "target_manifest_digest": "b" * 64,
            "gt_h5_f1_accessed": False,
            "pairs": [],
        }
        with self.assertRaises(ValueError):
            check_resume(valid, {"id": "01-0843x4", "sha256": "a" * 64},
                         "CHANGED_DIGEST", set())


if __name__ == "__main__":
    unittest.main()
