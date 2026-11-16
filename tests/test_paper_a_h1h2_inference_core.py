#!/usr/bin/env python3
"""Synthetic-only GT-free prefreeze H1/H2 inference tests."""
import json
from pathlib import Path
import sys
import unittest
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.paper_a_h1h2_inference_core import (
    EXPECTED, REQUIRED_MAPS, preoutcome_features, predict_from_native_maps,
    validate_fitted_recipe,
)
from src.stage24_residual import MembershipModel, apply_membership
from src.stage24_recertification_ops import apply_aggregator, thin_score, binary_map

P1 = ROOT / "docs/paper_a_confirmation/P1_DEVELOPMENT_RECIPE_UNATTESTED.json"


def fixture():
    yy, xx = np.indices((48, 52))
    image = np.zeros((48, 52, 3), dtype=np.float32)
    image[:, 20:30, :] = 1
    image += (yy % 9)[..., None].astype(np.float32) / 50
    maps = {
        "halfdisc_distribution_contrast": (xx / 55.0).astype(np.float32),
        "pmi_dependency_deficit": (yy / 51.0).astype(np.float32),
        "fh_region_boundary": ((xx + yy) / 110.0).astype(np.float32),
        "structure_tensor_coherence": ((xx * 3 - yy + 51) / 210.0).astype(np.float32),
    }
    return image, maps


class PreGTCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads(P1.read_text(encoding="utf-8"))

    def test_original_recipe_has_expected_hypotheses_and_capacity(self):
        cases = validate_fitted_recipe(self.recipe)
        self.assertEqual(list(cases), ["H1", "H2"])
        self.assertEqual(len(cases["H2"]["candidate"]["mobius"]), 6)

    def test_x1_and_x2_are_computed_on_original_float_maps(self):
        _, maps = fixture()
        features = preoutcome_features(maps)
        want_x1 = abs(maps["halfdisc_distribution_contrast"].mean(dtype=np.float64) -
                      maps["pmi_dependency_deficit"].mean(dtype=np.float64))
        want_x2 = np.mean([
            np.corrcoef(maps[a].ravel(), maps[b].ravel())[0, 1]
            for a, b in [("fh_region_boundary", "halfdisc_distribution_contrast"),
                         ("fh_region_boundary", "structure_tensor_coherence"),
                         ("halfdisc_distribution_contrast", "structure_tensor_coherence")]
        ])
        self.assertAlmostEqual(features["X1"], want_x1, places=12)
        self.assertAlmostEqual(features["X2"], want_x2, places=12)

    def test_both_predictions_are_native_boolean_and_no_gt_required(self):
        im, maps = fixture()
        result = predict_from_native_maps(im, maps, self.recipe)
        self.assertEqual(set(result), {"H1", "H2"})
        for hid in result:
            self.assertEqual(result[hid].candidate.shape, im.shape[:2])
            self.assertEqual(result[hid].control.shape, im.shape[:2])
            self.assertEqual(result[hid].candidate.dtype, np.bool_)
            self.assertEqual(result[hid].control.dtype, np.bool_)
            case = next(h for h in self.recipe["hypotheses"] if h["id"] == hid)
            self.assertEqual(result[hid].candidate_threshold, case["candidate"]["threshold"])

    def test_operator_outputs_match_stage24_no_retraining(self):
        im, maps = fixture()
        result = predict_from_native_maps(im, maps, self.recipe)
        for h in self.recipe["hypotheses"]:
            group = h["group"]
            mem = h["membership"]
            m = apply_membership([maps[n] for n in group], MembershipModel(
                np.asarray(mem["midpoint"]), np.asarray(mem["scale"])))
            state = {"family": h["candidate"]["family"], "n_inputs": len(group)}
            if h["id"] == "H2":
                state["capacity"] = h["candidate"]["capacity"]
            expected = binary_map(thin_score(
                apply_aggregator(m, state), "nms_image", im),
                h["candidate"]["threshold"], "nms_image")
            np.testing.assert_array_equal(result[h["id"]].candidate, expected)

    def test_refuse_wrong_image_geometry(self):
        im, maps = fixture()
        with self.assertRaises(ValueError):
            predict_from_native_maps(im[:-1], maps, self.recipe)

    def test_refuse_png_like_map(self):
        im, maps = fixture()
        maps["pmi_dependency_deficit"] = (maps["pmi_dependency_deficit"] * 255).astype(np.uint8)
        with self.assertRaises(TypeError):
            predict_from_native_maps(im, maps, self.recipe)

    def test_refuse_nonfinite_map(self):
        im, maps = fixture()
        maps["halfdisc_distribution_contrast"][0, 0] = np.nan
        with self.assertRaises(ValueError):
            predict_from_native_maps(im, maps, self.recipe)

    def test_refuse_undefined_X2_constant_input(self):
        im, maps = fixture()
        maps["fh_region_boundary"] = np.zeros(im.shape[:2], dtype=np.float32)
        with self.assertRaises(ValueError):
            predict_from_native_maps(im, maps, self.recipe)

    def test_refuse_changed_hypothesis_identity(self):
        im, maps = fixture()
        x = json.loads(json.dumps(self.recipe))
        x["hypotheses"][0]["candidate"]["family"] = "minimum"
        with self.assertRaises(ValueError):
            predict_from_native_maps(im, maps, x)

    def test_refuse_untruthful_p1_metadata(self):
        x = json.loads(json.dumps(self.recipe))
        x["development_GT_and_cached_maps_read"] = False
        with self.assertRaises(ValueError):
            validate_fitted_recipe(x)

    def test_refuse_nonmonotone_capacity(self):
        x = json.loads(json.dumps(self.recipe))
        x["hypotheses"][1]["candidate"]["capacity"][2] = 0.9
        with self.assertRaises(ValueError):
            validate_fitted_recipe(x)

    def test_h2_no_mutation_of_recipe(self):
        im, maps = fixture()
        before = json.dumps(self.recipe, sort_keys=True)
        predict_from_native_maps(im, maps, self.recipe)
        self.assertEqual(json.dumps(self.recipe, sort_keys=True), before)


if __name__ == "__main__":
    unittest.main()
