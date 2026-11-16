#!/usr/bin/env python3
"""One-command freeze review is never self-approved; synthetic-only tests."""
import csv
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import freeze_paper_a_from_independent_review as fr


class ReviewedFreezeTests(unittest.TestCase):
    def test_nonconfirmatory_v2_metadata_binds_exact_3plus12_sources(self):
        def item(label,i,hashval):
            if label=="BIPED":
                name=f"C:\\dataset\\edges\\edge_maps\\test\\rgbr\\RGB_{i:03d}.png"
                values=[0,254,255];dtype="uint8"
            else:
                name=f"multicue/ground-truth/images/edges/4113_left_{i:04d}.1.png"
                values=[0,65535];dtype="uint16"
            old={"source_file":name,"file_sha256":hashval,"shape":[12,13]}
            new={"source_file":name,"sha256":hashval,"shape":[12,13],
                 "dtype":dtype,"all_values_if_at_most_32":values,
                 "scientific_decoding_approved":False}
            return old,new
        b=[item("BIPED",i,hashlib.sha256(f"BIPED{i}".encode()).hexdigest())
           for i in range(3)]
        m=[item("MultiCue",i,hashlib.sha256(f"MultiCue{i}".encode()).hexdigest())
           for i in range(12)]
        previous={
            "schema_version":1,"only_nonconfirmatory_GT_opened":True,
            "protected_confirmatory_GT_opened":False,
            "confirmation_F1_computed":False,
            "scientific_GT_semantics_approval":False,
            "sample_counts":{"BIPED":3,"MultiCue":12},
            "BIPED_samples":[x[0] for x in b],
            "MultiCue_samples":[x[0] for x in m],
        }
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/"format.json"
            d=Path(tmp)/"detail.json"
            a.write_text(json.dumps(previous),encoding="utf-8")
            detail={
                "schema_version":1,
                "source_report_sha256":fr.sha(a),
                "status":"NONCONFIRMATORY_GT_PIXEL_ENCODING_DETAIL_NOT_CERTIFIED",
                "confirmatory_GT_accessed":False,"F1_computed":False,
                "requires_independent_encoding_review":True,
                "sample_counts":{"BIPED_test":3,"MultiCue_excluded_4113":12},
                "BIPED_test":[x[1] for x in b],
                "MultiCue_excluded_4113":[x[1] for x in m],
            }
            d.write_text(json.dumps(detail),encoding="utf-8")
            result=fr.verified_nonconfirmatory_gt_v2_evidence(a,d)
            self.assertEqual(result["nonconfirmatory_gt_format_sha256"],fr.sha(a))
            self.assertEqual(result["nonconfirmatory_gt_detail_sha256"],fr.sha(d))
            detail["MultiCue_excluded_4113"][0]["all_values_if_at_most_32"]=[0,65280]
            d.write_text(json.dumps(detail),encoding="utf-8")
            with self.assertRaises(PermissionError):
                fr.verified_nonconfirmatory_gt_v2_evidence(a,d)

    def test_frozen_proposal_requires_exact_v2_policy(self):
        source=json.loads(fr.PROTOCOL.read_text(encoding="utf-8"))
        if source.get("status")=="draft_not_frozen":
            frozen=fr.freeze_candidate(source)
            self.assertEqual(
                frozen["measures"]["ground_truth_contract"]["encoding"],fr.BIN_POLICY)
            self.assertIn("v2",fr.BIN_POLICY)

    def test_proposed_protocol_remains_not_live(self):
        p=json.loads(fr.PROTOCOL.read_text(encoding="utf-8"))
        if p["status"]=="draft_not_frozen":
            out=fr.freeze_candidate(p)
            self.assertEqual(out["status"],"frozen")
            self.assertIsNone(out["freeze_commit"])
            self.assertEqual(out["cohort"]["target_n_independent_images"],220)
            self.assertEqual(p["status"],"draft_not_frozen")

    def test_rejects_missing_external_authorization_without_touching_gt(self):
        with self.assertRaises(PermissionError):
            fr.validate_signed_decision(
                {"schema_version":1,"approved_for_first_confirmatory_outcome_access":False},
                [],Path("missing"),Path("missing"),Path("missing"),
                Path("missing"),Path("missing"),Path("missing"))

    def test_template_gate_requires_seven_p1_reviews(self):
        import inspect
        s=inspect.getsource(fr.validate_signed_decision)
        self.assertIn("P1_seven_lineage_reviews",s)
        self.assertIn("ground_truth_encoding_evidence",s)
        self.assertIn("stage13c_exposure_evidence",s)

    def test_duplicate_scene_protection_exists(self):
        import inspect
        self.assertIn("Duplicate capture/scene/hash",
                      inspect.getsource(fr.validate_signed_decision))

    def test_gitrepo_not_mutated_by_preview(self):
        import inspect
        s=inspect.getsource(fr.prepare)
        self.assertNotIn('git("commit"',s)
        self.assertNotIn('gt.open(',s)


if __name__=="__main__":
    unittest.main()
