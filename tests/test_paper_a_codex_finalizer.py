#!/usr/bin/env python3
"""Only pure orchestration tests. No GT, no Codex invocation."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import paper_a_codex_finalizer as app


class CodexAuditFlowTests(unittest.TestCase):
    def test_exact_read_only_arguments(self):
        import inspect
        src=inspect.getsource(app.codex_audits)
        self.assertIn('"--sandbox","read-only"',src)
        self.assertNotIn("danger-full-access",src)
        self.assertNotIn("--yolo",src)
        self.assertEqual(app.MAX_AUDIT_ROUNDS,2)

    def test_prompts_never_allow_unsigned_scientific_pass(self):
        a=app.prompt_round(1,{"status":"PREFREEZE_SCIENTIFIC_GATES_OPEN","blockers":[]},{},"")
        b=app.prompt_round(2,{"status":"TECHNICAL_ERROR","blockers":[]},{},"prior")
        self.assertIn("Do not mark PASS",a)
        self.assertIn("READ-ONLY",b)
        self.assertIn("Previous Codex audit excerpt",b)

    def test_missing_codex_does_not_impersonate_human_reviewer(self):
        with patch.object(app,"available_codex",return_value=None):
            status=app.codex_audits({"status":"PREFREEZE_SCIENTIFIC_GATES_OPEN"}, {})
        self.assertEqual(status["rounds"],0)
        self.assertNotIn("APPROVED",status["status"])

if __name__=="__main__":
    unittest.main()
