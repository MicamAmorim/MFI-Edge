#!/usr/bin/env python3
"""Synthetic-only tests of second-pass scene graph; no GT or datasets."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import consolidar_reconciliacao_paper_a as audit
import auditar_paper_a_pos_quiz as first


def row(name, partners, selected=True):
    return {"dataset":"BIPED","image_id":name,"pairReviews":partners,
            "in_initial_cohort":selected,"scene":"PASS","exposure":"UNCERTAIN",
            "original_sha256":"a"*64}


def sample(rows,groups=None):
    return {"capture_reviews":rows, "group_reviews":groups or [],
            "source_sha256":{"cohort_sheet_sha256":"b"*64}}


def group(names,decision):
    return {"id":"CANDIDATE_SCENE_01","image_ids":names,
            "decision":decision,"sameAsFirst":[],"evidence":""}


class ConsolidateReconciliationTests(unittest.TestCase):
    def test_direct_launcher_imports_sibling_helper_with_isolated_python(self):
        import subprocess
        script=ROOT/"scripts/consolidar_reconciliacao_paper_a.py"
        helper=ROOT/"scripts/auditar_paper_a_pos_quiz.py"
        self.assertTrue(helper.is_file())
        with tempfile.TemporaryDirectory() as tmp:
            # -I removes inherited PYTHONPATH and current-folder imports;
            # runpy with a non-main name verifies import without reading data.
            process=subprocess.run(
                [sys.executable,"-I","-B","-c",
                 "import runpy,sys;runpy.run_path(sys.argv[1],run_name='_import_only_')",
                 str(script)],
                cwd=tmp,capture_output=True,text=True,timeout=30,check=False)
        self.assertEqual(process.returncode,0,process.stdout+process.stderr)

    def test_transitive_negative_does_not_certify_independence(self):
        doc=sample([
            row("RGB_001",{"RGB_002":"SAME","RGB_003":"DIFFERENT"}),
            row("RGB_002",{"RGB_001":"SAME","RGB_003":"SAME"}),
            row("RGB_003",{"RGB_002":"SAME","RGB_001":"DIFFERENT"})
        ])
        result=audit.analyze(doc,{"answers":[]})
        self.assertEqual(result["conflict_count"],1)
        case=result["remaining_conflicts"][0]
        self.assertEqual(case["images"],["RGB_001","RGB_003"])
        self.assertEqual(case["reason"],"TRANSITIVE_GROUP_CONFLICT")
        self.assertEqual(case["positive_path"],["RGB_001","RGB_002","RGB_003"])
        self.assertFalse(result["scientific_signoff"])
        self.assertFalse(result["cohort_modified"])

    def test_conflicting_reviewer_decisions_in_same_revision(self):
        doc=sample([
            row("RGB_001",{"RGB_002":"SAME"}),
            row("RGB_002",{"RGB_001":"DIFFERENT"})
        ],[group(["RGB_001","RGB_002"],"DISTINCT")])
        rec={"answers":[
            {"kind":"PAIR_CONFLICT","dataset":"BIPED",
             "images":["RGB_001","RGB_002"],"decision":"DIFFERENT","id":"pair"},
            {"kind":"GROUP_CONTRADICTION","dataset":"BIPED",
             "images":["RGB_001","RGB_002"],"decision":"ONE","id":"group"}
        ]}
        result=audit.analyze(doc,rec)
        self.assertEqual(result["conflict_count"],1)
        self.assertTrue(result["remaining_conflicts"][0]["latest_group_vs_pair_conflict"])
        self.assertEqual(result["remaining_conflicts"][0]["reason"],"CONFLICT_IN_SAME_ROUND")

    def test_later_group_adjudication_supersedes_only_old_votes(self):
        doc=sample([
            row("RGB_001",{"RGB_002":"DIFFERENT"}),
            row("RGB_002",{"RGB_001":"DIFFERENT"})
        ],[group(["RGB_001","RGB_002"],"DISTINCT")])
        result=audit.analyze(doc,{"answers":[{
            "kind":"GROUP_CONTRADICTION","dataset":"BIPED",
            "images":["RGB_001","RGB_002"],"decision":"ONE","id":"group"}]})
        self.assertEqual(result["conflict_count"],0)
        self.assertEqual(len(result["historical_votes_overridden_by_later_group_review"]),1)
        self.assertEqual(result["provisional_scene_counts"]["BIPED"]
                         ["provisional_components_among_selected"],1)

    def test_full_answer_validation_rejects_fabricated_scientific_approval(self):
        doc=first_fixture()
        doc["capture_reviews"][0]["pairReviews"]["RGB_002"]="SAME"
        doc["capture_reviews"][1]["pairReviews"]["RGB_001"]="DIFFERENT"
        tasks,_=first.reconcile_tasks(doc)
        responses=[{
            "id":t["id"],"kind":t["type"],"dataset":t["dataset"],
            "images":t["images"],"decision":t["choices"][-1][0],
            "note":""} for t in tasks]
        rec={"schema":audit.SCHEMA,"source_report_sha256":"a"*64,
             "source_cohort_sha256":doc["source_sha256"]["cohort_sheet_sha256"],
             "scientific_signoff_granted":False,
             "protected_gt_access_authorized":False,
             "status":"RECONCILIATION_NOT_SIGNOFF","answers":responses}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"rec.json"
            p.write_text(json.dumps(rec),encoding="utf-8")
            restored,_=audit.load_reconciliation(p,doc,"a"*64)
            self.assertEqual(len(restored["answers"]),len(tasks))
            rec["scientific_signoff_granted"]=True
            p.write_text(json.dumps(rec),encoding="utf-8")
            with self.assertRaises(ValueError):
                audit.load_reconciliation(p,doc,"a"*64)
            rec["scientific_signoff_granted"]=False
            rec["answers"][0]["decision"]="NOT_A_REAL_ANSWER"
            p.write_text(json.dumps(rec),encoding="utf-8")
            with self.assertRaises(ValueError):
                audit.load_reconciliation(p,doc,"a"*64)

    def test_review_export_never_issues_freeze(self):
        report={"source_report_sha256":"a"*64,"reconciliation_sha256":"b"*64,
                "source_cohort_sha256":"c"*64,
                "remaining_conflicts":[{"id":"BIPED__RGB_001__RGB_003",
                "dataset":"BIPED","images":["RGB_001","RGB_003"],
                "reason":"TRANSITIVE_GROUP_CONFLICT",
                "positive_path":["RGB_001","RGB_002","RGB_003"],
                "prior_votes":{},"later_pair_decisions":[],
                "latest_group_vs_pair_conflict":False,
                "positive_evidence":[],"negative_evidence":[]}]}
        html=audit.review_page(report)
        self.assertIn('"positive_path":["RGB_001","RGB_002","RGB_003"]',html)
        self.assertIn("c.positive_path.join",html)
        self.assertIn("scientific_signoff:false",html)
        self.assertIn("protected_gt_access:false",html)
        self.assertNotIn("grant_approval",html)


def first_fixture():
    import importlib.util
    filename=ROOT/"tests/test_auditar_paper_a_pos_quiz.py"
    spec=importlib.util.spec_from_file_location("previous_test_fixture",filename)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.fixture()


if __name__=="__main__":
    unittest.main()
