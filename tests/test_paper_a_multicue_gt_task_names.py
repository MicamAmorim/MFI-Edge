#!/usr/bin/env python3
"""Metadata-only synthetic GT name tests; never opens a ground truth image."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_paper_a_multicue_gt_task_names import check_unit


def fixture():
    import json
    prefix, frame = "5200", 48
    return {
        "capture_prefix": prefix,
        "sequence_id": "5200_left_0048",
        "annotated_left_frame": str(frame),
        "last_left_image": "multicue/images/5200_left_0048.png",
        "h5_anchor_path": "multicue/ground-truth/hdf5/5200_left_0048.h5",
        "left_frame_count": "10",
        "right_frame_count": "10",
        "layout_issues": "",
        "edges_png_names": json.dumps([
            f"multicue/ground-truth/images/edges/5200_left_0048.{i}.png"
            for i in range(6)
        ]),
        "boundaries_png_names": json.dumps([
            f"multicue/ground-truth/images/boundaries/5200_left_0048.{i}.png"
            for i in range(5)
        ]),
    }


class MetadataOnlyContractTests(unittest.TestCase):
    def test_correct_inventory_row(self):
        result = check_unit(fixture())
        self.assertEqual(result["tasks"]["edges"]["file_names"], 6)
        self.assertEqual(result["tasks"]["boundaries"]["file_names"], 5)

    def test_wrong_annotation_frame_fails(self):
        row = fixture()
        row["edges_png_names"] = row["edges_png_names"].replace(
            "5200_left_0048.1", "5200_left_0047.1"
        )
        with self.assertRaises(ValueError):
            check_unit(row)

    def test_duplicate_suffix_fails(self):
        row = fixture()
        row["edges_png_names"] = row["edges_png_names"].replace(
            "5200_left_0048.1", "5200_left_0048.0"
        )
        with self.assertRaises(ValueError):
            check_unit(row)

    def test_bad_original_frame_fails(self):
        row = fixture()
        row["last_left_image"] = "multicue/images/5200_left_0047.png"
        with self.assertRaises(ValueError):
            check_unit(row)


if __name__ == "__main__":
    unittest.main()
