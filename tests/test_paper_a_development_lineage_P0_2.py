#!/usr/bin/env python3
"""P0.2 synthetic metadata tests only; no images, GT, maps or F1 access."""
import csv
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_paper_a_development_lineage_P0_2 import source_metadata

ROOT = Path(__file__).resolve().parents[1]
IDS = [f"seq_{i:02d}" for i in range(14)]
DS = ("halfdisc_distribution_contrast", "pmi_dependency_deficit",
      "fh_region_boundary", "structure_tensor_coherence")


def fake():
    from audit_paper_a_development_lineage_P0_2 import EXPECTED_DESCRIPTORS
    manifest = {"ground_truth": "native_never_resized",
                "inference": "maxside256_score_registered_to_native",
                "records": [{"image_id": x, "excluded": False,
                             "gt_resized": False, "source_sha256": "a" * 64,
                             "bytes_read": True} for x in IDS] + [
                    {"image_id": "03-35028", "excluded": True}]}
    descriptors = list(EXPECTED_DESCRIPTORS) + [
        f"other_{i}" for i in range(9)]
    rows = [{"image_id": img, "descriptor_id": desc, "source": "stage24_cache",
             "sha256": "b" * 64, "gt_resized": "False", "dtype": "float32"}
            for img in IDS for desc in descriptors]
    return manifest, rows


class MetadataP02Tests(unittest.TestCase):
    def test_matching_metadata(self):
        manifest, rows = fake()
        result = source_metadata(manifest, rows, set(IDS))
        self.assertEqual(result["development_image_count"], 14)
        self.assertEqual(result["H1_H2_required_descriptor_metadata_rows"], 56)
        self.assertFalse(result["any_GT_payload_loaded"])

    def test_unlisted_discovery_ids_rejected(self):
        manifest, rows = fake()
        with self.assertRaises(ValueError):
            source_metadata(manifest, rows, set(IDS[:-1]))

    def test_missing_required_descriptor_rejected(self):
        manifest, rows = fake()
        rows = [r for r in rows if not (
            r["image_id"] == IDS[0] and r["descriptor_id"] == DS[0])]
        with self.assertRaises(ValueError):
            source_metadata(manifest, rows, set(IDS))

    def test_nonfloat_descriptor_rejected(self):
        manifest, rows = fake()
        rows[0]["dtype"] = "uint8"
        with self.assertRaises(ValueError):
            source_metadata(manifest, rows, set(IDS))

    def test_duplicate_rows_rejected(self):
        manifest, rows = fake()
        rows[-1] = dict(rows[0])
        with self.assertRaises(ValueError):
            source_metadata(manifest, rows, set(IDS))

    def test_protected_original_not_selected(self):
        manifest, rows = fake()
        manifest["records"][-1]["image_id"] = "14-not-protected"
        with self.assertRaises(ValueError):
            source_metadata(manifest, rows, set(IDS))


if __name__ == "__main__":
    unittest.main()
