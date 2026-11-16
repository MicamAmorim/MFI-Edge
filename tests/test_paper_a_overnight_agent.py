#!/usr/bin/env python3
"""No scientific data: validate overnight agent safety constants."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from paper_a_overnight_agent import ALLOWED_CODEX, ALLOWED_COMMIT, BRANCH, DATA

class OvernightSafety(unittest.TestCase):
    def test_branch(self):
        self.assertEqual(BRANCH, "experiment/paper-a-conditional-confirmation")
    def test_protocol_protected(self):
        self.assertNotIn("docs/paper_a_confirmation/protocol.json", ALLOWED_CODEX)
    def test_research_source_protected(self):
        self.assertNotIn("src/stage24_recertification_ops.py", ALLOWED_CODEX)
    def test_controller_status_can_commit(self):
        self.assertIn("docs/paper_a_confirmation/NIGHTLY_PROGRESS.md", ALLOWED_COMMIT)
        self.assertNotIn("docs/paper_a_confirmation/NIGHTLY_PROGRESS.md", ALLOWED_CODEX)
    def test_output_on_data_drive(self):
        self.assertTrue(str(DATA).startswith("F:"))
    def test_no_broad_git_permission(self):
        self.assertNotIn("tests/test_stage24_math_contracts.py", ALLOWED_COMMIT)

if __name__ == "__main__":
    unittest.main()
