#!/usr/bin/env python3
"""No scientific data: validate overnight agent safety constants."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from paper_a_overnight_agent import (ALLOWED_CODEX, ALLOWED_COMMIT, BRANCH, DATA, filter_status_changes)

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

    def test_preexisting_untracked_is_not_staged(self):
        existing = {"resultado_analise_condicional.zip": (120, 9, 0)}
        entries = [("??", "resultado_analise_condicional.zip")]
        self.assertEqual(filter_status_changes(
            entries, existing, lambda _: (120, 9, 0)), [])

    def test_new_untracked_scoped(self):
        existing = {"resultado_analise_condicional.zip": (120, 9, 0)}
        entries = [("??", "resultado_analise_condicional.zip"),
                   ("??", "docs/paper_a_confirmation/NIGHTLY_PROGRESS.md")]
        self.assertEqual(filter_status_changes(
            entries, existing, lambda _: (120, 9, 0)),
            ["docs/paper_a_confirmation/NIGHTLY_PROGRESS.md"])

    def test_preexisting_changed_aborts(self):
        existing = {"results/official_eval/historical.json": (120, 9, 0)}
        with self.assertRaises(RuntimeError):
            filter_status_changes(
                [("??", "results/official_eval/historical.json")],
                existing, lambda _: (121, 9, 0))

    def test_preexisting_deleted_aborts(self):
        existing = {"results/official_eval/historical.json": (120, 9, 0)}
        with self.assertRaises(RuntimeError):
            filter_status_changes([], existing, lambda _: (120, 9, 0))

    def test_tracked_modified_not_ignored(self):
        existing = {"resultado_analise_condicional.zip": (120, 9, 0)}
        entries = [("??", "resultado_analise_condicional.zip"),
                   (" M", "docs/paper_a_confirmation/protocol.json")]
        self.assertIn(
            "docs/paper_a_confirmation/protocol.json",
            filter_status_changes(entries, existing, lambda _: (120, 9, 0)))

if __name__ == "__main__":
    unittest.main()
