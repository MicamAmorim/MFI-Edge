#!/usr/bin/env python3
"""Render original-only comparison sheets with synthetic RGB inputs only."""
import tempfile
import sys
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from render_paper_a_multicue_uded_overlap_review import render_page


class ReviewPageTests(unittest.TestCase):
    def test_synthetic_pair_page(self):
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td)
            left = directory / "uded.png"
            right = directory / "multicue.png"
            Image.new("RGB", (250, 370), "#345678").save(left)
            Image.new("RGB", (640, 360), "#aabbcc").save(right)
            sample = {
                "uded_original_id": "09-MDBD-1C",
                "multicue_sequence_id": "4113_left_0082",
                "capture_prefix": "4113",
                "ratio_matches": "2116",
                "ransac_inliers": "2100",
                "inlier_fraction": "0.99244",
                "uded_path": str(left),
                "multicue_path": str(right),
            }
            output = directory / "sheet.png"
            render_page([sample], output, 1, 1)
            with Image.open(output) as preview:
                self.assertEqual(preview.size, (1180, 503))
                self.assertGreater(output.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
