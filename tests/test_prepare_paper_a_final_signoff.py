#!/usr/bin/env python3
"""Safe synthetic metadata-only signoff readiness tests; no real GT access."""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import prepare_paper_a_final_signoff as app


class PreReviewTests(unittest.TestCase):
    def test_pending_only_never_promoted(self):
        b=[{"image_id": "RGB_%03d"%k, "sha256": ("%064x"%k), "relative_path":"RGB_%03d.jpg"%k}
           for k in range(1,126)]
        m=[{"sequence_id":"%04d_left_0001"%k,"capture_prefix":str(k),
            "last_left_image":"multicue/images/%04d_left_0001.png"%k} for k in range(1000,1095)]
        proposal = [
            {"dataset":"BIPED","image_id":r["image_id"],"relative_path":r["relative_path"],
            "image_sha256":r["sha256"],"independence_review":"pending",
            "prior_exposure_review":"pending","scene_group":r["image_id"],"notes":""}
            for r in b]
        proposal.extend([
            {"dataset":"MultiCue","image_id":r["sequence_id"],
             "relative_path":Path(r["last_left_image"]).name,
             "image_sha256":("%064x"%(200+k)),"independence_review":"pending",
             "prior_exposure_review":"pending","scene_group":r["capture_prefix"],"notes":""}
            for k,r in enumerate(m)])
        result=app.build_review_rows(proposal,b,m)
        self.assertEqual(len(result),220)
        self.assertTrue(all(r["reviewer_independence_decision"]=="PENDING" for r in result))
        self.assertTrue(all(r["reviewer_prior_exposure_decision"]=="PENDING" for r in result))
        proposal[0]["independence_review"]="pass"
        with self.assertRaises(ValueError):
            app.build_review_rows(proposal,b,m)

    def test_stage13c_no_data_file_does_not_imply_non_exposure(self):
        with patch.object(app,"STAGE13C_SUMMARY",Path("does_not_exist.json")):
            out=app.stage13c_metadata()
        self.assertFalse(out["execution_verified"])
        self.assertFalse(out["independence_attested"])
        self.assertEqual(out["status"],"EXECUTION_EVIDENCE_NOT_FOUND")

    def test_script_never_saves_approved_cohort(self):
        import inspect
        src=inspect.getsource(app.run)
        self.assertIn("REVIEW_220_IMAGES_PENDING.csv",src)
        self.assertNotIn('freeze_approval.json").write_text',src)


if __name__=="__main__":
    unittest.main()
