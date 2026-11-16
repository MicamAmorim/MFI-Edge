#!/usr/bin/env python3
"""Regression test for the image-only MDBD review visualizations.

Operates entirely on synthetic RGB images; never reads dataset/GT/F1 files.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import review_paper_a_multicue_mdbd_lineage as review  # noqa: E402


class ReviewSheetTest(unittest.TestCase):
    def test_render_uses_target_id_schema(self):
        with tempfile.TemporaryDirectory() as root:
            destination = Path(root) / "review.png"
            reference = Image.new("RGB", (320, 160), "#333333")
            sample = Image.new("RGB", (320, 160), "#666666")
            targets = [
                {
                    "id": "4108_left_0082",
                    "path": Path(root) / "never_read.png",
                    "dhash_distance": 9,
                    "phash_distance": 11,
                },
                {
                    "id": "4113_left_0101",
                    "path": Path(root) / "never_read2.png",
                    "dhash_distance": 12,
                    "phash_distance": 13,
                },
            ]
            with patch.object(review, "read_original", return_value=sample) as loader:
                review.render_sheet(
                    reference, targets, "Synthetic regression review",
                    destination, top_k=2,
                )
            self.assertEqual(loader.call_count, 2)
            self.assertTrue(destination.is_file())
            with Image.open(destination) as out:
                self.assertEqual(out.size, (1236, 556))


if __name__ == "__main__":
    unittest.main()
