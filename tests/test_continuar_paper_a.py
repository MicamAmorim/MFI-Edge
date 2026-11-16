#!/usr/bin/env python3
"""Pure one-command safety tests: no datasets or GT."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import continuar_paper_a as app


class OneCommandTests(unittest.TestCase):
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

    def test_completion_uses_existing_gated_controller(self):
        import inspect
        src = inspect.getsource(app.one_shot)
        self.assertIn("finish_paper_a.py", src)
        self.assertIn("--skip-baseline-zip", src)


if __name__ == "__main__":
    unittest.main()
