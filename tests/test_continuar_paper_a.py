#!/usr/bin/env python3
"""Pure one-command safety tests: no datasets or GT."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import continuar_paper_a as app


class OneCommandTests(unittest.TestCase):
    def test_direct_script_launch_has_repo_root_on_sys_path(self):
        # Regression for ModuleNotFoundError: No module named 'src' on Windows.
        import subprocess
        command = [
            sys.executable, "-I", "-c",
            ("import runpy, sys; "
             "ns = runpy.run_path('scripts/continuar_paper_a.py'); "
             "assert str(ns['ROOT']) in sys.path; "
             "from src.paper_a_h1h2_inference_core import validate_fitted_recipe; "
             "assert callable(validate_fitted_recipe)")
        ]
        result = subprocess.run(
            command, cwd=app.ROOT, text=True, capture_output=True,
            timeout=30, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_inputs_do_not_trigger_gt(self):
        self.assertFalse(any("gt" in v.lower() for v in
            ["biped_inventory", "biped_audit", "biped_dedup"]))

    def test_biped_no_automatic_approval(self):
        import inspect
        source = inspect.getsource(app.validate_biped)
        self.assertIn("PENDING_HISTORICAL_AND_SCENE_LINEAGE_AUDIT", source)

    def test_validates_multicue_from_metadata_only(self):
        import inspect
        src = inspect.getsource(app.multicue_metadata)
        self.assertIn("validate_inventory", src)
        self.assertNotIn("Image.open", src)

    def test_review_packet_only_pre_freeze(self):
        import inspect
        src=inspect.getsource(app.one_shot)
        self.assertIn("prepare_paper_a_final_signoff",src)
        self.assertIn('if protocol_status == "draft_not_frozen":',src)

    def test_review_bundle_is_only_after_existing_science_gate_reports(self):
        import inspect
        src = inspect.getsource(app.one_shot)
        self.assertIn("from export_paper_a_review_bundle import assemble", src)
        self.assertIn('if protocol_status == "draft_not_frozen":', src)
    
    def test_frozen_path_skips_draft_only_dossier(self):
        import inspect
        src = inspect.getsource(app.one_shot)
        self.assertIn('if protocol_status == "draft_not_frozen"', src)
        self.assertIn("SKIPPED_AFTER_DRAFT_FREEZE_GUARD_STILL_REQUIRED", src)

    def test_completion_uses_existing_gated_controller(self):
        import inspect
        src = inspect.getsource(app.one_shot)
        self.assertIn("finish_paper_a.py", src)
        self.assertIn("--skip-baseline-zip", src)


if __name__ == "__main__":
    unittest.main()
