#!/usr/bin/env python3
"""Synthetic image-mask tests only. NEVER opens MultiCue/BIPED GT or image files."""
import sys
import unittest
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.paper_a_confirmation_paired_f1 import evaluate_paired_binary


def mask(x, shape=(64, 64)):
    z = np.zeros(shape, dtype=bool)
    z[12:18, x] = True
    return z


class CandidatePairedF1Tests(unittest.TestCase):
    def test_biped_one_reference_same_pair(self):
        a = mask(12)
        result = evaluate_paired_binary(a, a.copy(), [a],
                                        domain="BIPED")
        self.assertEqual(result.annotation_count, 1)
        self.assertEqual(result.delta_f1, 0)
        self.assertEqual(result.to_dict()["statistical_observation_count"], 1)

    def test_multicue_six_separate_reference_masks(self):
        a = mask(12)
        b = mask(46)
        masks = [a, a.copy(), a.copy(), b, b.copy(), b.copy()]
        result = evaluate_paired_binary(a, b, masks, domain="MultiCue")
        self.assertEqual(result.annotation_count, 6)
        self.assertAlmostEqual(result.candidate_f1_mean, 0.5)
        self.assertAlmostEqual(result.control_f1_mean, 0.5)
        self.assertAlmostEqual(result.delta_f1, 0.0)
        self.assertEqual(len(result.to_dict()["candidate_f1_by_annotation"]), 6)

    def test_multicue_positive_delta(self):
        a, b = mask(12), mask(46)
        result = evaluate_paired_binary(a, b, [a.copy() for _ in range(6)],
                                        domain="MultiCue")
        self.assertAlmostEqual(result.delta_f1, 1.0)

    def test_wrong_reference_count_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_paired_binary(mask(12), mask(12), [mask(12)] * 5,
                                   domain="MultiCue")

    def test_uint8_gt_rejected_without_implicit_binarization(self):
        with self.assertRaises(TypeError):
            evaluate_paired_binary(mask(12), mask(12),
                                   [mask(12).astype(np.uint8) * 255],
                                   domain="BIPED")

    def test_3d_gt_rejected(self):
        gt = np.stack([mask(12), mask(12), mask(12)], axis=-1)
        with self.assertRaises(TypeError):
            evaluate_paired_binary(mask(12), mask(12), [gt], domain="BIPED")

    def test_wrong_native_geometry_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_paired_binary(mask(12), mask(12),
                                   [mask(12, shape=(80, 80))], domain="BIPED")

    def test_empty_gt_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_paired_binary(mask(12), mask(12),
                                   [np.zeros((64, 64), bool)], domain="BIPED")

    def test_score_maps_are_not_accepted_as_binary_predictions(self):
        with self.assertRaises(TypeError):
            evaluate_paired_binary(mask(12).astype(float), mask(12),
                                   [mask(12)], domain="BIPED")

    def test_unrecognized_domain_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_paired_binary(mask(12), mask(12), [mask(12)],
                                   domain="boundaries")


if __name__ == "__main__":
    unittest.main()
