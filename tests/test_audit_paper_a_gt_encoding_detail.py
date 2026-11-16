#!/usr/bin/env python3
"""Synthetic-only GT diagnostic tests: NEVER open repository datasets."""
import hashlib
import io
import json
import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_paper_a_gt_encoding_detail as audit


def sample_png(arr):
    buffer = io.BytesIO()
    Image.fromarray(arr).save(buffer, format="PNG")
    raw = buffer.getvalue()
    with Image.open(io.BytesIO(raw)) as im:
        return raw, {
            "file_sha256": hashlib.sha256(raw).hexdigest(),
            "shape": list(np.asarray(im).shape),
            "dtype": str(np.asarray(im).dtype),
            "pil_mode": im.mode,
            "source_file": "synthetic.png",
        }


def previous_fixture():
    biped = [{"source_file":f"C:\\dataset\\edges\\edge_maps\\test\\rgbr\\RGB_{i:03}.png",
              "file_sha256":"a"*64} for i in range(1,4)]
    multi = [{"source_file":
              f"multicue/ground-truth/images/edges/4113_left_{i:04}.1.png",
              "file_sha256":"b"*64} for i in range(1,13)]
    return {
        "schema_version":1,
        "status":"GT_FORMAT_SAMPLE_OBSERVED_NOT_INDEPENDENTLY_CERTIFIED",
        "only_nonconfirmatory_GT_opened":True,
        "protected_confirmatory_GT_opened":False,
        "confirmation_F1_computed":False,
        "BIPED_samples":biped, "MultiCue_samples":multi,
    }


class NonconfirmatoryEncodingTests(unittest.TestCase):
    def test_biped_254_kept_exact_without_threshold(self):
        a = np.array([[0,254,255],[0,0,255],[0,254,0]] * 5, dtype=np.uint8)
        raw, item = sample_png(a)
        result = audit.pixel_summary(raw,item)
        self.assertEqual(result["selected_counts"]["254"],2*5)
        self.assertEqual(result["selected_counts"]["255"],2*5)
        self.assertFalse(result["scientific_decoding_approved"])

    def test_uint16_values_not_silently_scaled(self):
        a = np.zeros((12,13),dtype=np.uint16)
        a[0,0],a[0,1],a[0,2] = 256,65280,65535
        raw,item = sample_png(a)
        result = audit.pixel_summary(raw,item)
        self.assertEqual(result["dtype"],"uint16")
        self.assertEqual(result["max_value"],65535)
        self.assertEqual(result["selected_counts"]["256"],1)
        self.assertEqual(result["selected_counts"]["65280"],1)

    def test_rejects_mismatched_previous_checksum(self):
        raw,item = sample_png(np.zeros((12,13),dtype=np.uint8))
        item["file_sha256"]="0"*64
        with self.assertRaises(ValueError):
            audit.pixel_summary(raw,item)

    def test_record_allowlist_only_test_and_excluded_4113(self):
        item = previous_fixture()
        b,m = audit.select_previous_samples(json.dumps(item).encode())
        self.assertEqual((len(b),len(m)),(3,12))
        item["BIPED_samples"][0]["source_file"] = (
            r"C:\dataset\edges\edge_maps\train\rgbr\RGB_001.png")
        with self.assertRaises(ValueError):
            audit.select_previous_samples(json.dumps(item).encode())
        item=previous_fixture()
        item["MultiCue_samples"][0]["source_file"] = (
            "multicue/ground-truth/images/edges/4108_left_0001.1.png")
        with self.assertRaises(ValueError):
            audit.select_previous_samples(json.dumps(item).encode())


if __name__=="__main__":
    unittest.main()
