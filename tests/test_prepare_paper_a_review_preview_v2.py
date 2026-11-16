#!/usr/bin/env python3
"""Synthetic/read-only checks of the Windows PowerShell preview entrypoint."""
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import prepare_paper_a_review_preview_v2 as preview


class WindowsPreviewEntrypointTests(unittest.TestCase):
    def test_direct_script_import_isolated_outside_repo_without_data_access(self):
        import subprocess
        import tempfile
        source=ROOT/"scripts"/"prepare_paper_a_review_preview_v2.py"
        # runpy with run_name different from __main__ only imports the
        # entrypoint. This tests Windows-like missing sibling sys.path
        # without invoking real data/protocol preparation.
        with tempfile.TemporaryDirectory() as tmp:
            result=subprocess.run([
                sys.executable, "-I", "-B", "-c",
                "import runpy,sys;runpy.run_path(sys.argv[1],run_name='_import_only_')",
                str(source)],
                cwd=tmp,capture_output=True,text=True,timeout=30,check=False)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_powershell_invokes_real_script_without_python_c_quotes(self):
        p=(ROOT/"scripts/preparar_paper_a_revisao_v2.ps1").read_text(encoding="utf-8")
        self.assertIn("& $python scripts/prepare_paper_a_review_preview_v2.py",p)
        self.assertNotIn("& $python -c",p)

    def test_preview_does_not_issue_or_infer_scientific_approval(self):
        from unittest.mock import patch
        # Patch evidence and template boundaries; no actual source file needed.
        with patch.object(preview,"verified_nonconfirmatory_gt_v2_evidence",
                          return_value={"nonconfirmatory_gt_format_sha256":"a"*64,
                                        "nonconfirmatory_gt_detail_sha256":"b"*64}), \
             patch.object(preview,"prepare",return_value={
                 "status":"REVIEWED_FREEZE_READY_ONLY_WHEN_SIGNED_AND_EVIDENCED",
                 "scientific_signoff_issued":False,
                 "reviewed_protocol_candidate":"preview.json",
                 "review_template":"unsigned.template.json"}):
            self.assertEqual(preview.main(),0)

    def test_approved_or_unexpected_preview_state_rejected(self):
        from unittest.mock import patch
        with patch.object(preview,"verified_nonconfirmatory_gt_v2_evidence",
                          return_value={}), \
             patch.object(preview,"prepare",return_value={
                 "status":"REVIEWED_FREEZE_READY_ONLY_WHEN_SIGNED_AND_EVIDENCED",
                 "scientific_signoff_issued":True}):
            with self.assertRaises(RuntimeError):
                preview.main()


if __name__=="__main__":
    unittest.main()
