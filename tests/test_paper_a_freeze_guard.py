#!/usr/bin/env python3
"""No GT read: synthetic guard tests for scientific freeze authorization."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from paper_a_freeze_guard import check_freeze

H = "a"*64
C = "b"*40


def case():
    protocol = {
        "status": "frozen", "confirmatory_outcomes_opened": False,
        "exploratory_source": {"discovery_images": ["excluded"]},
        "cohort": {"no_GT_until_lock": True, "dataset_names": ["BIPED","MultiCue"],
                   "target_n_independent_images": 4, "min_n_per_domain": 2},
        "hypotheses": [
            {"id":"H1","candidate":"maximum","control":"equal_mean"},
            {"id":"H2","candidate":"choquet_generalized_150","control":"equal_mean"}],
        "inference":{"multiplicity":"Holm two hypotheses","permutations":100000},
        "freeze_commit": None,
    }
    recipe = {"schema": "paper_a_h1h2_recipe_P1_fitted_development",
              "development_GT_and_cached_maps_read":True,
              "no_scientific_artifacts_or_outcomes_read":False,
              "hypotheses":[
        {"id":"H1","group":["a","b"],"membership":{"midpoint":[0,0],"scale":[1,1]},
         "candidate":{"threshold":0.3},"control":{"threshold":0.4}},
        {"id":"H2","group":["a","b","c"],"membership":{"midpoint":[0,0,0],"scale":[1,1,1]},
         "candidate":{"threshold":0.3,"capacity":[0,0.3,0.3,0.5,0.3,0.6,0.5,1.0],
                      "mobius":[0.3,0.3,0.3,-0.1,0,0]},
         "control":{"threshold":0.4}}
    ]}
    approve = {
        "schema_version":1, "approved_for_first_confirmatory_outcome_access":True,
        "reviewed_by":"Independent methodological reviewer",
        "approved_utc":"2026-11-16T10:00:00Z",
        "freeze_commit":C, "protocol_sha256":H,
        "recipe_sha256":H, "cohort_sha256":H,
        "scientific_approvals":{n:True for n in (
            "training_lineage","capacity_and_thresholds","ground_truth_semantics",
            "independent_scenes_and_exposure","sample_size_and_inference",
            "independent_protocol_review")},
        "review_notes":"Independently reviewed source, cohort, frozen parameters, tests and annotations.",
    }
    rows=[]
    for d in ("BIPED","MultiCue"):
        for n in range(2):
            rows.append({
                "dataset":d,"image_id":f"{d}-{n}","relative_path":f"{d}/{n}.png",
                "image_sha256":f"{len(rows)+1:064x}",
                "independence_review":"pass","prior_exposure_review":"pass",
                "scene_group":f"{d}-scene-{n}","notes":"reviewed"
            })
    return protocol,recipe,approve,rows,dict(protocol_sha256=H,recipe_sha256=H,cohort_sha256=H)


class FreezeSafetyTests(unittest.TestCase):
    def test_valid_synthetic(self):
        p,r,a,c,h=case()
        self.assertEqual(check_freeze(p,r,a,c,h,lambda _:True), [])

    def test_unfrozen_fails(self):
        p,r,a,c,h=case();p["status"]="draft_not_frozen"
        self.assertIn("Protocol still draft_not_frozen",
                      check_freeze(p,r,a,c,h,lambda _:True))

    def test_bad_approval_fails(self):
        p,r,a,c,h=case();a["approved_for_first_confirmatory_outcome_access"]=False
        self.assertTrue(check_freeze(p,r,a,c,h,lambda _:True))

    def test_wrong_hash_fails(self):
        p,r,a,c,h=case();a["recipe_sha256"]="d"*64
        self.assertTrue(check_freeze(p,r,a,c,h,lambda _:True))

    def test_overlap_scene_fails(self):
        p,r,a,c,h=case();c[1]["scene_group"]=c[0]["scene_group"]
        self.assertTrue(check_freeze(p,r,a,c,h,lambda _:True))

    def test_unreviewed_fails(self):
        p,r,a,c,h=case();c[0]["prior_exposure_review"]="PENDING"
        self.assertTrue(check_freeze(p,r,a,c,h,lambda _:True))

    def test_missing_choquet_fails(self):
        p,r,a,c,h=case();r["hypotheses"][1]["candidate"]["capacity"]=None
        self.assertTrue(check_freeze(p,r,a,c,h,lambda _:True))

    def test_ancestry_fails(self):
        p,r,a,c,h=case()
        self.assertTrue(check_freeze(p,r,a,c,h,lambda _:False))


    def test_disallow_false_GT_free_claim_in_fitted_recipe(self):
        p,r,a,c,h=case()
        r["no_scientific_artifacts_or_outcomes_read"]=True
        self.assertTrue(check_freeze(p,r,a,c,h,lambda _:True))

    def test_reject_old_metadata_only_P0_1_as_fitted(self):
        p,r,a,c,h=case()
        r["schema"]="paper_a_h1h2_recipe_P0_1"
        self.assertTrue(check_freeze(p,r,a,c,h,lambda _:True))


if __name__ == "__main__":
    unittest.main()
