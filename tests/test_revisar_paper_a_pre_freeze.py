#!/usr/bin/env python3
"""Scientific reviewer dossier tests; synthetic metadata, no GT/assets."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import revisar_paper_a_pre_freeze as r


class ReviewSafety(unittest.TestCase):
    def test_direct_script_imports_src_under_python_isolated(self):
        import subprocess
        p = subprocess.run(
            [sys.executable, "-I", "-c",
             "import runpy,sys; x=runpy.run_path('scripts/revisar_paper_a_pre_freeze.py'); assert str(x['ROOT']) in sys.path; from src.paper_a_h1h2_inference_core import validate_fitted_recipe"],
            cwd=r.ROOT, capture_output=True, text=True, timeout=30, check=False)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

    def setUp(self):
        self.p = json.loads(r.PROTOCOL.read_text(encoding="utf-8"))
        self.recipe = json.loads(r.P1.read_text(encoding="utf-8"))
        self.biped = [
            {"image_id": "RGB_%03d" % x,
             "confirmatory_eligibility": "PENDING_HISTORICAL_AND_SCENE_LINEAGE_AUDIT"}
            for x in range(500, 698)]
        self.multi = [
            {"sequence_id": "x%d" % i, "capture_prefix": str(i if i < 96 else 4108)}
            for i in range(100)]
        self.multi[0]["capture_prefix"] = "4113"

    def test_protocol_proposal_is_still_draft(self):
        p = r.proposed_protocol(self.p)
        self.assertEqual(p["status"], "draft_not_frozen")
        self.assertIsNone(p["freeze_commit"])
        self.assertEqual(p["cohort"]["target_n_independent_images"], 220)
        self.assertFalse(p["confirmatory_outcomes_opened"])
        self.assertEqual(self.p["cohort"]["target_n_independent_images"], 150)

    def test_no_automatic_review_approval(self):
        import inspect
        src = inspect.getsource(r.create_dossier)
        self.assertNotIn("freeze_approval.json", src)
        self.assertNotIn("tarfile", src)

    def test_strict_198_95_and_pending(self):
        # Normalize to 96 unique prefix groups including known held 4113.
        self.multi = [
            {"sequence_id": "x%d" % i, "capture_prefix": str(i if i < 96 else 4108)}
            for i in range(100)]
        self.multi[0]["capture_prefix"] = "4113"
        # Prefixes: 4113,1..95,4108 = 97; convert last distinct 95 -> 4108.
        self.multi[95]["capture_prefix"] = "4108"
        review = r.review_metadata(
            self.p, self.recipe, self.biped, self.multi, None, None, None)
        self.assertEqual(review["multi_prefixes_provisionally_usable"], 95)
        self.assertFalse(review["frozen"])

    def test_refuses_promoted_biped(self):
        self.multi = [
            {"sequence_id": "x%d" % i, "capture_prefix": str(i if i < 96 else 4108)}
            for i in range(100)]
        self.multi[0]["capture_prefix"] = "4113"
        self.multi[95]["capture_prefix"] = "4108"
        self.biped[0]["confirmatory_eligibility"] = "approved"
        with self.assertRaises(ValueError):
            r.review_metadata(
                self.p, self.recipe, self.biped, self.multi, None, None, None)


if __name__ == "__main__":
    unittest.main()
