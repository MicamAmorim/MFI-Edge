from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.stage24_integrity import load_float_artifact, one_to_one_boundary_counts, save_float_artifact, select_threshold


class Stage24IntegrityTests(unittest.TestCase):
    def test_perfect(self):
        gt = np.zeros((20, 20), bool); gt[10, 5:15] = True
        c = one_to_one_boundary_counts(gt, gt, tolerance_px=0)
        self.assertEqual((c.tp, c.fp, c.fn), (10, 0, 0)); self.assertEqual(c.f1, 1.0)

    def test_thick_predictions_do_not_get_duplicate_tp(self):
        gt = np.zeros((20, 20), bool); gt[10, 5:15] = True
        pred = np.zeros_like(gt); pred[8:13, 5:15] = True
        c = one_to_one_boundary_counts(pred, gt, tolerance_px=2)
        self.assertEqual(c.tp, 10); self.assertEqual(c.pred_count, 50); self.assertEqual(c.fp, 40)

    def test_threshold_is_train_data_only_api(self):
        gt = np.zeros((8, 8), bool); gt[4, 2:6] = True
        score = np.zeros((8, 8), np.float32); score[4, 2:6] = 0.9
        result = select_threshold([score], [gt], count=11, tolerance_ratio=0.0)
        self.assertGreaterEqual(result["F1"], 0.99)

    def test_float_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.npy"
            arr = np.arange(25, dtype=np.float32).reshape(5, 5) / 24
            identity = {"x": 1}
            save_float_artifact(p, arr, identity)
            self.assertTrue(np.array_equal(arr, load_float_artifact(p, identity)))

    def test_png_rejected(self):
        with self.assertRaises(ValueError):
            load_float_artifact(Path("fake.png"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
