#!/usr/bin/env python3
"""Synthetic-only full atlas test. No real Paper A image/GT is accessed."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

import numpy as np
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import build_paper_a_image_only_review_atlas as task


class GtFreeAtlasTests(unittest.TestCase):
    def test_path_rejects_traversal_or_mismatched_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            row={"dataset":"BIPED","image_id":"RGB_111",
                 "relative_path":"../../edges/edge_maps/train/RGB_111.png"}
            with self.assertRaises(ValueError):
                task.safe_source(row,d,d)
            row["relative_path"]="RGB_222.png"
            with self.assertRaises(ValueError):
                task.safe_source(row,d,d)

    def test_220_originals_verified_review_zip_reused_without_gt(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp); b=d/"originals_biped";m=d/"originals_multi"
            b.mkdir();m.mkdir()
            records=[]
            for domain,n,base in (("BIPED",125,b),("MultiCue",95,m)):
                for i in range(n):
                    name=f"RGB_{i:03d}" if domain=="BIPED" else f"{4100+i}_left_0001"
                    rel=name+".png"
                    p=base/rel
                    pixels=np.full((24,32,3),i%256,dtype=np.uint8)
                    pixels[0,0]=[0,1,2]
                    pixels[0,1]=[7,8,9] if domain=="BIPED" else [10,11,12]
                    Image.fromarray(pixels).save(p)
                    records.append({
                        "dataset":domain,"image_id":name,"relative_path":rel,
                        "image_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                        "scene_group":name if domain=="BIPED" else str(4100+i),
                        "independence_review":"pending","prior_exposure_review":"pending",
                        "notes":"","reviewer_independence_decision":"PENDING",
                        "reviewer_prior_exposure_decision":"PENDING",
                        "evidence_for_both_decisions":"","reviewer_name":"","reviewed_utc":"",
                        "historical_attention":"SCENE_REVIEW_PENDING",
                    })
            sheet=d/"review.csv"
            with sheet.open("w",newline="",encoding="utf-8") as f:
                writer=csv.DictWriter(f,fieldnames=task.EXPECTED_COLS)
                writer.writeheader();writer.writerows(records)
            final=d/"atlas";z=d/"atlas.zip"
            a=task.build(sheet=sheet,biped=b,multicue=m,final=final,archive=z)
            self.assertEqual(a["images"],220)
            self.assertFalse(a["GT_opened"])
            self.assertFalse(a["signed_or_frozen"])
            self.assertFalse(a["reused"])
            with zipfile.ZipFile(z) as archive:
                self.assertEqual(len(archive.namelist()),222)
                self.assertNotIn("GT.png",archive.namelist())
            original_digest=hashlib.sha256(z.read_bytes()).hexdigest()
            a2=task.build(sheet=sheet,biped=b,multicue=m,final=final,archive=z)
            self.assertTrue(a2["reused"])
            self.assertEqual(original_digest,a2["atlas_sha256"])


if __name__=="__main__":
    unittest.main()
