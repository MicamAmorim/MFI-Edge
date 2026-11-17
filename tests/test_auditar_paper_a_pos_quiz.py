#!/usr/bin/env python3
"""Run only synthetic post-quiz reconciliation and file-scope tests (NO GT)."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import auditar_paper_a_pos_quiz as mod


def fixture():
    captures=[]
    for i in range(198):
        id=f"RGB_{i+1:03d}"
        captures.append({
            "dataset":"BIPED","image_id":id,"in_initial_cohort":i<125,
            "original_sha256":"a"*64,"scene":"PASS","exposure":"UNCERTAIN",
            "pairReviews":{},"evidence":""})
    for i in range(95):
        id=f"{4100+i}_left_{i+1:04d}"
        captures.append({
            "dataset":"MultiCue","image_id":id,"in_initial_cohort":True,
            "original_sha256":"b"*64,"scene":"PASS","exposure":"UNCERTAIN",
            "pairReviews":{},"evidence":""})
    groups=[{"id":f"CANDIDATE_SCENE_{i+1:02d}","image_ids":[f"RGB_{i+1:03d}",f"RGB_{i+2:03d}"],
             "decision":"UNCERTAIN","evidence":"","sameAsFirst":[],"subgroups":""}
             for i in range(22)]
    doc={
        "schema":mod.REVIEW_SCHEMA,"status":"DRAFT_HUMAN_REVIEW_NOT_SCIENTIFIC_SIGNOFF",
        "scientific_signoff_granted":False,"protected_GT_access_authorized":False,
        "source_sha256":{"cohort_sheet_sha256":"a"*64,"candidate_sha256":"b"*64},
        "capture_reviews":captures,"group_reviews":groups,
        "P1_seven_review":[{"id":f"H1.part{i}","decision":"UNCERTAIN"} for i in range(7)],
        "methodological_review":[{"id":f"S{i}","decision":"UNCERTAIN"} for i in range(10)],
    }
    return doc


class PostQuizAuditTests(unittest.TestCase):
    def test_extract_original_embedded_report(self):
        doc=fixture()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"PaperA_RELATORIO_293_test.html"
            path.write_text('<!doctype html><html><script id="report-data" type="application/json">'+
                            json.dumps(doc)+'</script></html>',encoding="utf-8")
            loaded,sha=mod.load_quiz_report(path)
        self.assertEqual(len(loaded["capture_reviews"]),293)
        self.assertEqual(len(sha),64)

    def test_reconcile_directional_pair_group_and_multicue(self):
        doc=fixture()
        b=doc["capture_reviews"]
        b[0]["pairReviews"]["RGB_002"]="SAME"
        b[1]["pairReviews"]["RGB_001"]="DIFFERENT"
        b[0]["scene"]="GROUP"
        b[2]["pairReviews"]["RGB_004"]="SAME"
        b[3]["pairReviews"]["RGB_003"]="SAME"
        b[3]["scene"]="GROUP"
        multi=[r for r in b if r["dataset"]=="MultiCue"]
        multi[0]["pairReviews"][multi[1]["image_id"]]="SAME"
        multi[1]["pairReviews"][multi[0]["image_id"]]="SAME"
        g=doc["group_reviews"]
        g[0]["decision"]="DISTINCT"
        g[0]["evidence"]="Mesma cena em perspectivas diferentes"
        g[1]["decision"]="SUBGROUPS"
        g[1]["sameAsFirst"]=["RGB_003"]
        g[1]["subgroups"]="RGB_002; RGB_003"
        tasks,info=mod.reconcile_tasks(doc)
        s=info["summary"]
        self.assertEqual(s["directional_pair_conflicts"],1)
        self.assertEqual(s["pass_with_same_comparison"],1)
        self.assertEqual(s["group_question_conflicts"],2)
        self.assertEqual(s["multicue_same_pairs"],1)
        self.assertEqual(len(tasks),5)
        self.assertEqual(s["historical_unchecked_captures"],293)
        self.assertFalse(s["reconciled_or_independent"])
        html=mod.visual_html({"report_sha256":"a"*64,
                              "cohort_sha256":"b"*64,"tasks":tasks})
        self.assertIn("../QUIZ_VISUAL_LOCAL_293/assets/images/",html)
        self.assertIn("RECONCILIATION_NOT_SIGNOFF",html)
        self.assertIn("Exportar reconciliação JSON",html)

    def test_invalid_pair_id_rejected(self):
        doc=fixture()
        doc["capture_reviews"][0]["pairReviews"]["RGB_999"]="SAME"
        with self.assertRaises(ValueError):
            mod.reconcile_tasks(doc)

    def test_reject_unapproved_report_claim(self):
        doc=fixture()
        doc["scientific_signoff_granted"]=True
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"quiz.json"
            path.write_text(json.dumps(doc),encoding="utf-8")
            with self.assertRaises(ValueError):
                mod.load_quiz_report(path)


if __name__=="__main__":
    unittest.main()
