#!/usr/bin/env python3
"""Only synthetic strings and stat() of fake artifacts. No scientific data."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_paper_a_parameter_provenance_P0 import (
    ALLOWLIST, audit, inspect_source, metadata_only,
)


class ParameterProvenanceP0(unittest.TestCase):
    def test_static_function_recognized(self):
        functions, sections = inspect_source(
            "def f():\n    return helper(1)\n", {"f": ("helper",)})
        self.assertEqual(functions["f"]["status"], "OK")
        self.assertIn("helper(1)", sections["f"])

    def test_missing_expected_call_detected(self):
        functions, _ = inspect_source(
            "def f():\n    return 1\n", {"f": ("helper",)})
        self.assertEqual(functions["f"]["status"], "MISSING_CALL")

    def test_no_artifact_parsing(self):
        with tempfile.TemporaryDirectory() as dirname:
            p = Path(dirname) / "frozen_models.json"
            p.write_text("SENSITIVE_F1=42; NOT JSON", encoding="utf-8")
            status = metadata_only(p, Path(dirname))
            self.assertTrue(status["exists"])
            self.assertFalse(status["bytes_read"])
            self.assertIsNone(status["sha256"])

    def test_missing_artifact_acceptable(self):
        with tempfile.TemporaryDirectory() as dirname:
            status = metadata_only(Path(dirname) / "absent.json", Path(dirname))
            self.assertFalse(status["exists"])

    def test_repository_source_only_contract(self):
        repository = Path(__file__).resolve().parents[1]
        report = audit(repository)
        self.assertEqual(len(report["source_files"]), len(ALLOWLIST))
        self.assertEqual(report["source_contract_mismatches"], [])
        self.assertFalse(report["GT_H5_F1_maps_predictions_opened"])
        self.assertEqual(report["research_artifact_payload_bytes_read"], 0)


if __name__ == "__main__":
    unittest.main()
