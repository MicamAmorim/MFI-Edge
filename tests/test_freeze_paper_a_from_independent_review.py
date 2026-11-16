#!/usr/bin/env python3
"""One-command freeze review is never self-approved; synthetic-only tests."""
import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import freeze_paper_a_from_independent_review as fr


class ReviewedFreezeTests(unittest.TestCase):
    def test_proposed_protocol_remains_not_live(self):
        p=json.loads(fr.PROTOCOL.read_text(encoding="utf-8"))
        if p["status"]=="draft_not_frozen":
            out=fr.freeze_candidate(p)
            self.assertEqual(out["status"],"frozen")
            self.assertIsNone(out["freeze_commit"])
            self.assertEqual(out["cohort"]["target_n_independent_images"],220)
            self.assertEqual(p["status"],"draft_not_frozen")

    def test_rejects_missing_external_authorization_without_touching_gt(self):
        with self.assertRaises(PermissionError):
            fr.validate_signed_decision(
                {"schema_version":1,"approved_for_first_confirmatory_outcome_access":False},
                [],Path("missing"),Path("missing"),Path("missing"),
                Path("missing"),Path("missing"),Path("missing"))

    def test_template_gate_requires_seven_p1_reviews(self):
        import inspect
        s=inspect.getsource(fr.validate_signed_decision)
        self.assertIn("P1_seven_lineage_reviews",s)
        self.assertIn("ground_truth_encoding_evidence",s)
        self.assertIn("stage13c_exposure_evidence",s)

    def test_duplicate_scene_protection_exists(self):
        import inspect
        self.assertIn("Duplicate capture/scene/hash",
                      inspect.getsource(fr.validate_signed_decision))

    def test_gitrepo_not_mutated_by_preview(self):
        import inspect
        s=inspect.getsource(fr.prepare)
        self.assertNotIn('git("commit"',s)
        self.assertNotIn('gt.open(',s)


if __name__=="__main__":
    unittest.main()
