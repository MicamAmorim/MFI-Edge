#!/usr/bin/env python3
"""No dataset; exercise metadata-only review ZIP on isolated temp directories."""
import json
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import export_paper_a_review_bundle as task


class ReviewBundleTests(unittest.TestCase):
    def test_current_status_and_gt_evidence_are_explicit_metadata_only(self):
        expected = {
            "review/LAST_STATUS.json":
                ("work", "LAST_STATUS.json"),
            "review/signoff/NONCONFIRMATORY_GT_ENCODING_EVIDENCE.json":
                ("work", "scientific_signoff/NONCONFIRMATORY_GT_ENCODING_EVIDENCE.json"),
            "science/PARECER_CODEX_DUPLA_AUDITORIA_20261116.md":
                ("root", "docs/paper_a_confirmation/PARECER_CODEX_DUPLA_AUDITORIA_20261116.md"),
        }
        for destination, source in expected.items():
            self.assertEqual(task.FILES.get(destination), source)
            self.assertNotIn(destination, task.REQUIRED)

    def test_curated_bundle_contains_only_explicit_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            data = Path(tmp) / "data"
            work = Path(tmp) / "work"
            for d in (root, data, work):
                d.mkdir()
            mock_paths = {
                "a/first.json": ("root", "a.json"),
                "b/second.csv": ("data", "b.csv"),
            }
            (root / "a.json").write_text('{"x":1}', encoding="utf-8")
            (data / "b.csv").write_text("id\n1\n", encoding="utf-8")
            (data / "ground-truth.png").write_bytes(b"fake GT must not enter")
            with mock.patch.object(task, "FILES", mock_paths), \
                 mock.patch.object(task, "REQUIRED", set(mock_paths)):
                result = task.assemble(root, data, work)
            with zipfile.ZipFile(result["path"]) as f:
                self.assertEqual(set(f.namelist()), set(mock_paths) | {"MANIFEST.json"})
                report = json.loads(f.read("MANIFEST.json"))
                self.assertTrue(report["no_scientific_approval"])
                self.assertTrue(report["no_GT_H5_original_images_descriptor_maps_or_F1_included"])
            
    def test_missing_required_review_metadata_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            data = Path(tmp) / "data"
            work = Path(tmp) / "work"
            for d in (root, data, work):
                d.mkdir()
            with mock.patch.object(task, "FILES", {"a": ("root", "missing.txt")}), \
                 mock.patch.object(task, "REQUIRED", {"a"}):
                with self.assertRaises(ValueError):
                    task.assemble(root, data, work)


if __name__ == "__main__":
    unittest.main()
