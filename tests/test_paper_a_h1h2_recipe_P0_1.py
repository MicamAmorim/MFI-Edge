#!/usr/bin/env python3
"""P0.1 manifest unit tests, without reading any research data/results."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare_paper_a_h1h2_recipe_P0_1 import new_draft, validate, read_protocol

ROOT = Path(__file__).resolve().parents[1]
TEST_HASHES = {"source": "0" * 64}
TEST_COMMIT = "1" * 40


class H1H2ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proto = read_protocol(ROOT)

    def get_template(self):
        return new_draft(self.proto, TEST_HASHES, TEST_COMMIT)

    def test_sanitized_draft_excludes_exploratory_rhos(self):
        draft = self.get_template()
        self.assertNotIn("exploratory_rho", repr(draft))
        self.assertNotIn("fit_all_UDED_F1", repr(draft))
        self.assertEqual(draft["hypotheses"][1]["candidate"]["family"],
                         "choquet_generalized_150")

    def test_template_is_valid_but_incomplete(self):
        result = validate(self.get_template(), self.proto,
                          TEST_HASHES, TEST_COMMIT)
        self.assertEqual(result["status"], "P0_1_DRAFT_INCOMPLETE_NOT_FROZEN")
        self.assertGreater(result["pending_count"], 0)

    def test_unexpected_f1_field_is_rejected(self):
        draft = self.get_template()
        draft["hypotheses"][1]["candidate"]["best_F1"] = 0.99
        with self.assertRaises(ValueError):
            validate(draft, self.proto, TEST_HASHES, TEST_COMMIT)

    def test_preregistered_hypothesis_cannot_change(self):
        draft = self.get_template()
        draft["hypotheses"][1]["candidate"]["family"] = "maximum"
        with self.assertRaises(ValueError):
            validate(draft, self.proto, TEST_HASHES, TEST_COMMIT)

    def test_source_sha_mismatch_rejected(self):
        draft = self.get_template()
        with self.assertRaises(ValueError):
            validate(draft, self.proto, {"source": "9" * 64}, TEST_COMMIT)

    def test_h2_capacity_must_be_monotone_and_consistent(self):
        draft = self.get_template()
        candidate = draft["hypotheses"][1]["candidate"]
        candidate["capacity"] = [0.0, 0.8, 0.2, 0.5, 0.3, 0.7, 0.6, 1.0]
        candidate["mobius"] = [1 / 3] * 3 + [0.0] * 3
        with self.assertRaises(ValueError):
            validate(draft, self.proto, TEST_HASHES, TEST_COMMIT)

    def test_reject_nonpositive_membership_scale(self):
        draft = self.get_template()
        draft["hypotheses"][0]["membership"]["scale"] = [-1, 0.1]
        with self.assertRaises(ValueError):
            validate(draft, self.proto, TEST_HASHES, TEST_COMMIT)

    def test_complete_example_still_requires_independent_audit(self):
        draft = self.get_template()
        proof = {
            "development_dataset_id": "synthetic_development",
            "split_role": "development_train",
            "training_ids_sha256": "a" * 64,
            "fitting_commit": TEST_COMMIT,
            "parameter_export_sha256": "b" * 64,
            "no_confirmatory_overlap_attested": True,
        }
        for case in draft["hypotheses"]:
            n = len(case["group"])
            case["membership"]["midpoint"] = [0.3] * n
            case["membership"]["scale"] = [0.2] * n
            case["membership"]["fit_provenance"] = copy.deepcopy(proof)
            for role in ("candidate", "control"):
                case[role]["threshold"] = 0.5
                case[role]["threshold_fit_provenance"] = copy.deepcopy(proof)
            if case["id"] == "H2":
                case["candidate"]["capacity"] = [
                    0, 1/3, 1/3, 2/3, 1/3, 2/3, 2/3, 1
                ]
                case["candidate"]["mobius"] = [1/3] * 3 + [0] * 3
                case["candidate"]["capacity_fit_provenance"] = copy.deepcopy(proof)
        report = validate(draft, self.proto, TEST_HASHES, TEST_COMMIT)
        self.assertEqual(report["status"],
                         "P0_1_SCHEMA_COMPLETE_INDEPENDENT_AUDIT_REQUIRED")
        self.assertFalse(report["parameter_training_provenance_independently_verified"])


if __name__ == "__main__":
    unittest.main()
