#!/usr/bin/env python3
"""Synthetic nonconfirmatory GT test only; no archive or dataset access."""
import io
import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import paper_a_nonconfirmatory_gt_format as gt


def png(array):
    tmp=io.BytesIO()
    Image.fromarray(array).save(tmp,format="PNG")
    return tmp.getvalue()


class FormatAuditTests(unittest.TestCase):
    def test_binary_sample_is_compatible(self):
        a=np.zeros((12,13),dtype=np.uint8)
        a[1:3,2:5]=255
        self.assertTrue(gt.inspect_png(png(a),"synthetic.png")[
            "strict_decoder_sample_compatible"])

    def test_nonbinary_sample_rejected_without_threshold(self):
        a=np.zeros((12,13),dtype=np.uint8)
        a[1:3,2:5]=127
        self.assertFalse(gt.inspect_png(png(a),"synthetic.png")[
            "strict_decoder_sample_compatible"])

    def test_different_rgb_channels_not_accepted(self):
        a=np.zeros((12,13,3),dtype=np.uint8)
        a[1:3,2:5,0]=255
        self.assertFalse(gt.inspect_png(png(a),"synthetic.png")[
            "strict_decoder_sample_compatible"])

    def test_selection_allowlist_excludes_candidate_prefixes(self):
        self.assertTrue(gt.TARGET.fullmatch("multicue/ground-truth/images/edges/4113_left_0082.1.png"))
        self.assertFalse(gt.TARGET.fullmatch("multicue/ground-truth/images/edges/4108_left_0082.1.png"))
        self.assertFalse(gt.TARGET.fullmatch("multicue/ground-truth/images/boundaries/4113_left_0082.1.png"))

if __name__=="__main__":
    unittest.main()
