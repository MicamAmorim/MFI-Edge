#!/usr/bin/env python3
"""Regression checks for two reproduced Codex findings, synthetic only."""
import hashlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
from test_paper_a_freeze_guard import case
from paper_a_freeze_guard import check_freeze
import execute_paper_a_frozen_cohort as ex
import paper_a_nonconfirmatory_gt_format as fmt


class PostCodexRegression(unittest.TestCase):
    def test_scientific_direction_alpha_mismatch_fails_closed(self):
        p,r,a,c,h=case()
        p["inference"]["alpha_familywise"]=0.01
        p["inference"]["directional_alternative"]={
            "H1":"rho>0","H2":"rho<0"}
        problems=check_freeze(p,r,a,c,h,lambda _:True)
        self.assertTrue(any("alpha" in x for x in problems))
        self.assertTrue(any("directional" in x for x in problems))

    def test_biped_original_must_match_frozen_id(self):
        with tempfile.TemporaryDirectory() as d:
            original=Path(d)/"RGB_001.jpg"
            original.write_bytes(b"synthetic-original-bytes")
            row={"dataset":"BIPED","relative_path":original.name,
                 "image_id":"RGB_999",
                 "image_sha256":hashlib.sha256(original.read_bytes()).hexdigest()}
            with patch.object(ex,"BIPED_IMAGES",Path(d)):
                with self.assertRaisesRegex(ValueError,"ID mismatch"):
                    ex.load_original(row)

    def test_gt_indicator_rejects_three_value_masks(self):
        arr=np.zeros((7,7),dtype=np.uint8)
        arr[0,1]=1;arr[1,0]=255
        output=io.BytesIO()
        Image.fromarray(arr).save(output,format="PNG")
        self.assertFalse(fmt.inspect_png(output.getvalue(),"synthetic.png")[
            "strict_decoder_sample_compatible"])


if __name__=="__main__":
    unittest.main()
