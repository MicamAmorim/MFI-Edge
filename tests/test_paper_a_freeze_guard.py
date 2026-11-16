#!/usr/bin/env python3
"""No GT read: synthetic guard tests for scientific freeze authorization."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from paper_a_freeze_guard import check_freeze,GT_POLICY_V2

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
        "inference":{"multiplicity":"Holm two hypotheses","permutations":100000,
                  "alpha_familywise":0.05,
                  "directional_alternative":{"H1":"rho<0","H2":"rho>0"},
                  "permutation_seed":20261115,
                  "test":"domain-blocked one-sided Spearman permutation"},
        "measures":{"ground_truth_contract":{"encoding":GT_POLICY_V2}},
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
        "gt_binary_decoding_contract":GT_POLICY_V2,
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

    def test_reject_changed_direction_and_alpha_before_outcomes(self):
        p,r,a,c,h=case()
        p["inference"].update({
            "alpha_familywise":0.01,
            "directional_alternative":{"H1":"rho>0","H2":"rho<0"}})
        problems=check_freeze(p,r,a,c,h,lambda _:True)
        self.assertTrue(any("alpha" in v for v in problems))
        self.assertTrue(any("directional" in v for v in problems))

    def test_mismatched_gt_decoder_policy_rejected(self):
        p,r,a,c,h=case()
        p["measures"]["ground_truth_contract"]["encoding"]="STRICT_BINARY_0_1_OR_0_255_NATIVE_v1"
        self.assertTrue(any("GT encoding policy" in x
            for x in check_freeze(p,r,a,c,h,lambda _:True)))
        p,r,a,c,h=case()
        a["gt_binary_decoding_contract"]="STRICT_BINARY_0_1_OR_0_255_NATIVE_v1"
        self.assertTrue(any("GT binary decoding approval" in x
            for x in check_freeze(p,r,a,c,h,lambda _:True)))

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


    def test_pinned_windows_crlf_equivalence_is_restricted(self):
        import hashlib
        from unittest.mock import Mock, patch
        from paper_a_freeze_guard import source_sha256_at_pinned_commit
        from prepare_paper_a_h1h2_recipe_P0_1 import CODE_FILES, PROTOCOL
        rev="b5a79ec6bb5f9a1fbd38477cd2900b19e98b8d46"
        raw=b"line_one\nline_two\n"
        crlf=raw.replace(b"\n",b"\r\n")
        valid={p:hashlib.sha256(crlf).hexdigest() for p in (PROTOCOL,*CODE_FILES)}
        with patch("paper_a_freeze_guard.ancestor",return_value=True), \
             patch("paper_a_freeze_guard.subprocess.run",
                   return_value=Mock(returncode=0,stdout=raw)):
            observed=source_sha256_at_pinned_commit(Path("."),rev,valid)
            self.assertEqual(observed,valid)
            wrong=dict(valid)
            wrong[PROTOCOL]=hashlib.sha256(b"modified").hexdigest()
            with self.assertRaises(ValueError):
                source_sha256_at_pinned_commit(Path("."),rev,wrong)

    def test_pinned_provenance_reads_original_git_blob_bytes(self):
        import hashlib
        from unittest.mock import patch, Mock
        from paper_a_freeze_guard import source_sha256_at_pinned_commit
        from prepare_paper_a_h1h2_recipe_P0_1 import CODE_FILES, PROTOCOL
        revision = "b5a79ec6bb5f9a1fbd38477cd2900b19e98b8d46"
        with patch("paper_a_freeze_guard.ancestor", return_value=True), \
             patch("paper_a_freeze_guard.subprocess.run") as proc:
            def show(args, **kwargs):
                self.assertEqual(args[0:2], ["git", "show"])
                return Mock(returncode=0, stdout=args[2].encode())
            proc.side_effect = show
            d = source_sha256_at_pinned_commit(Path(__file__).resolve().parents[1], revision)
        self.assertEqual(set(d), set((PROTOCOL, *CODE_FILES)))
        self.assertEqual(d[PROTOCOL], hashlib.sha256((revision+":"+PROTOCOL).encode()).hexdigest())


    def test_git_freeze_manifest_checks_signed_hashes_and_public_copy(self):
        import json
        import tempfile
        from unittest.mock import patch
        from paper_a_freeze_guard import (RUNTIME_SOURCES, sha256,
            verify_versioned_freeze_inputs)
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp)
            folder=repo/"docs"/"paper_a_confirmation"
            folder.mkdir(parents=True)
            protocol=folder/"protocol.json"
            recipe=repo/"recipe.json"
            cohort=repo/"cohort.csv"
            recipe_git=folder/"FROZEN_H1_H2_RECIPE_P1.json"
            public=folder/"FROZEN_COHORT_IDS_PUBLIC.csv"
            protocol.write_text('{"status":"frozen"}',encoding="utf-8")
            recipe.write_text('{"test":1}',encoding="utf-8")
            cohort.write_text("dataset,image_id\nBIPED,RGB_01\n",encoding="utf-8")
            recipe_git.write_bytes(recipe.read_bytes())
            public.write_text("dataset,image_id\nBIPED,RGB_01\n",encoding="utf-8")
            approval={
                "review_decision_sha256":"a"*64,
                "review_sheet_sha256":"b"*64,
                "approved_executor_source_sha256":"c"*64,
                "freeze_commit":"b"*40,
                "approved_runtime_sources_sha256":{p:"d"*64 for p in RUNTIME_SOURCES},
            }
            manifest={
                "status":"REVIEWED_PRE_GT_CONFIRMATORY_LOCK",
                "schema_version":1,
                "protocol_sha256":sha256(protocol),
                "local_frozen_recipe_sha256":sha256(recipe),
                "public_frozen_recipe_sha256":sha256(recipe_git),
                "local_frozen_cohort_sha256":sha256(cohort),
                "public_frozen_cohort_sha256":sha256(public),
                "external_signed_decision_sha256":approval["review_decision_sha256"],
                "external_review_sheet_sha256":approval["review_sheet_sha256"],
                "executor_source_sha256":approval["approved_executor_source_sha256"],
                "approved_runtime_sources_sha256":approval["approved_runtime_sources_sha256"],
                "no_GT_opened_by_freeze_step":True,
            }
            (folder/"FROZEN_FREEZE_INPUTS_MANIFEST.json").write_text(
                json.dumps(manifest),encoding="utf-8")
            # This synthetic fixture has no Git repository and no real runtime
            # sources. Mock those boundaries, but validate all real manifests.
            with patch("paper_a_freeze_guard.runtime_source_hashes",
                       return_value=approval["approved_runtime_sources_sha256"]), \
                 patch("paper_a_freeze_guard.check_commit_blob_integrity",
                       return_value=[]):
                self.assertEqual(
                    verify_versioned_freeze_inputs(repo,protocol,recipe,cohort,approval),[])
                public.write_text("modified",encoding="utf-8")
                self.assertTrue(
                    verify_versioned_freeze_inputs(repo,protocol,recipe,cohort,approval))
                public.write_text("dataset,image_id\nBIPED,RGB_01\n",encoding="utf-8")
                approval["approved_runtime_sources_sha256"] = {
                    p:"e"*64 for p in RUNTIME_SOURCES}
                self.assertTrue(any(
                    "runtime sources disagree" in msg.lower()
                    for msg in verify_versioned_freeze_inputs(
                        repo,protocol,recipe,cohort,approval)))


if __name__ == "__main__":
    unittest.main()
