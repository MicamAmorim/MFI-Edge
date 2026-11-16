#!/usr/bin/env python3
"""Only synthetic post-freeze image decoder/auth safety tests; no real GT."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import execute_paper_a_frozen_cohort as task


class FrozenExecutorTests(unittest.TestCase):
    def test_isolated_script_launch_resolves_src(self):
        import subprocess
        run = subprocess.run(
            [sys.executable, "-I", "-c",
             "import runpy, sys; ns=runpy.run_path('scripts/execute_paper_a_frozen_cohort.py'); assert str(ns['ROOT']) in sys.path; from src.paper_a_confirmation_paired_f1 import evaluate_paired_binary; assert callable(evaluate_paired_binary)"],
            cwd=task.ROOT, capture_output=True, text=True,
            timeout=30, check=False)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)

    def test_relative_paths_fail_closed(self):
        for path in ("../gt.png", "/tmp/a.png", "C:\\gt.png", ".\\secret"):
            with self.assertRaises(ValueError):
                task.safe_name(path)

    def test_strict_binary_gt(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "gt.png"
            a = np.zeros((12, 13), dtype=np.uint8)
            a[4:6, 6:8] = 255
            Image.fromarray(a).save(p)
            mask = task.binary_annotation(p, (12, 13))
            self.assertEqual(mask.dtype, bool)
            self.assertEqual(int(mask.sum()), 4)
            a[2, 2] = 127
            Image.fromarray(a).save(p)
            with self.assertRaises(ValueError):
                task.binary_annotation(p, (12, 13))

    def test_no_implicit_resize(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "gt.png"
            a = np.zeros((12, 13), dtype=np.uint8)
            a[0, 0] = 1
            Image.fromarray(a).save(p)
            with self.assertRaises(ValueError):
                task.binary_annotation(p, (10, 10))

    def test_frozen_guard_blocks_before_any_dataset_read(self):
        with patch("paper_a_freeze_guard.validate_files",
                   return_value={"blockers": ["not approved"]}):
            with self.assertRaises(PermissionError):
                task.authorized(Path("unused"))

    def test_valid_gate_without_executor_hash_still_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / "freeze_approval.json").write_text(
                '{"reviewed_by":"reviewer"}', encoding="utf-8")
            with patch("paper_a_freeze_guard.validate_files",
                       return_value={"blockers": []}):
                with self.assertRaises(PermissionError):
                    task.authorized(work)


if __name__ == "__main__":
    unittest.main()
