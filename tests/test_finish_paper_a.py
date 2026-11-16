#!/usr/bin/env python3
"""No datasets/GT: pure tests of the resumable Paper A completion plan."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from finish_paper_a import good_audit,count_recipe_missing,approval_template


class CompletionSafetyTests(unittest.TestCase):
    def test_successful_cache_audit_recognized(self):
        audit={"status":"TECHNICAL_AUDITS_OK_SCIENTIFIC_GATES_STILL_OPEN",
               "failures":[],"GT_H5_F1_or_confirmatory_data_opened":False,
               "new_training_or_descriptor_reprocessing":False,
               "phases":{"P0_4_cache_SHA256":{"matched":56}}}
        self.assertTrue(good_audit(audit))
        audit["phases"]["P0_4_cache_SHA256"]["matched"]=55
        self.assertFalse(good_audit(audit))

    def test_auto_approval_is_never_issued(self):
        item=approval_template()
        self.assertFalse(item["approved_for_first_confirmatory_outcome_access"])
        self.assertFalse(any(item["scientific_approvals"].values()))

    def test_missing_recipe_rejected(self):
        self.assertTrue(count_recipe_missing({}))

    def test_partial_recipe_reports_missing(self):
        recipe={"schema":"paper_a_h1h2_recipe_P0_1",
                "hypotheses":[{"id":"H1","membership":{"midpoint":None},
                               "candidate":{},"control":{}},
                              {"id":"H2","membership":{"midpoint":None},
                               "candidate":{},"control":{}}]}
        missing=count_recipe_missing(recipe)
        self.assertIn("H2.choquet.capacity_and_mobius",missing)
        self.assertIn("H1.candidate.threshold",missing)

    def test_audit_never_accepts_GT_access(self):
        audit={"status":"TECHNICAL_AUDITS_OK_SCIENTIFIC_GATES_STILL_OPEN",
               "failures":[],"GT_H5_F1_or_confirmatory_data_opened":True,
               "new_training_or_descriptor_reprocessing":False,
               "phases":{"P0_4_cache_SHA256":{"matched":56}}}
        self.assertFalse(good_audit(audit))


if __name__=="__main__":
    unittest.main()
