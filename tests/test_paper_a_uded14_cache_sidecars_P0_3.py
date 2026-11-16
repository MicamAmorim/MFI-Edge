#!/usr/bin/env python3
"""P0.3 synthetic metadata validations; no scientific cache bytes or GT read."""
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_paper_a_uded14_cache_sidecars_P0_3 import validate_sidecar

SHA = "a" * 64


def fixture():
    image = {
        "image_id": "DEV001",
        "source_sha256": "b" * 64,
        "inference_shape": [120, 256],
        "native_gt_shape": [240, 512],
    }
    meta = {
        "schema_version": 1,
        "artifact_sha256": SHA,
        "shape": [120, 256],
        "dtype": "float32",
        "identity": {
            "schema_version": 1,
            "dataset": "UDED",
            "split": "selection_overlap_clean",
            "image_id": "DEV001",
            "source_sha256": "b" * 64,
            "descriptor_id": "halfdisc_distribution_contrast",
            "parameters": {"radius_fraction": 0.02},
            "code_hash": "c" * 64,
            "preprocessing": "downscale_maxside256_then_registered_descriptor_preprocessing_v1",
            "inference_shape": [120, 256],
            "native_shape": [240, 512],
            "dtype": "float32",
            "gt_used": False,
        },
    }
    return meta, image


class CacheSidecarTests(unittest.TestCase):
    def test_matching_sidecar(self):
        m, i = fixture()
        self.assertEqual(validate_sidecar(m, i, SHA)[0], "METADATA_MATCH_ONLY")

    def test_wrong_source_detected(self):
        m, i = fixture()
        m["identity"]["source_sha256"] = "d" * 64
        self.assertEqual(validate_sidecar(m, i, SHA)[0], "IDENTITY_DRIFT")

    def test_gt_used_refused(self):
        m, i = fixture()
        m["identity"]["gt_used"] = True
        self.assertEqual(validate_sidecar(m, i, SHA)[0], "IDENTITY_DRIFT")

    def test_geometry_drift_detected(self):
        m, i = fixture()
        m["shape"] = [256, 256]
        self.assertEqual(validate_sidecar(m, i, SHA)[0], "GEOMETRY_OR_FORMAT_DRIFT")

    def test_manifest_sha_disagreement_detected(self):
        m, i = fixture()
        self.assertEqual(validate_sidecar(m, i, "d" * 64)[0],
                         "MANIFEST_SHA_DISAGREEMENT")

    def test_unexpected_metadata_keys_rejected(self):
        m, i = fixture()
        m["F1"] = 0.99
        self.assertEqual(validate_sidecar(m, i, SHA)[0], "INVALID_SCHEMA")


if __name__ == "__main__":
    unittest.main()
