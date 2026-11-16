#!/usr/bin/env python3
"""Pure in-memory source-manifest tests. Never read images, GT or results."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1] / "scripts"))
import check_paper_a_p1_lineage_prefreeze as task


def fixture():
    items=[{"image_id":f"UDED_{i:02d}",
            "source_sha256":hashlib.sha256(f"uded-{i}".encode()).hexdigest(),
            "excluded":False} for i in range(14)]
    training_hash=task.digest(json.dumps(
        sorted((r["image_id"],r["source_sha256"]) for r in items),
        separators=(",",":"),ensure_ascii=False).encode())
    claim={"training_ids_sha256":training_hash,"fitting_commit":"a"*40,
           "parameter_export_sha256":"f"*64,
           "no_confirmatory_overlap_attested":None}
    def p():return dict(claim)
    recipe={"schema":"paper_a_h1h2_recipe_P1_fitted_development",
            "source_commit":"a"*40,
            "hypotheses":[
                {"id":"H1","membership":{"fit_provenance":p()},
                 "candidate":{"threshold_fit_provenance":p()},
                 "control":{"threshold_fit_provenance":p()}},
                {"id":"H2","membership":{"fit_provenance":p()},
                 "candidate":{"threshold_fit_provenance":p(),"capacity_fit_provenance":p()},
                 "control":{"threshold_fit_provenance":p()}}]}
    cohort=[]
    for domain,n in (("BIPED",125),("MultiCue",95)):
        for i in range(n):
            cohort.append({
                "dataset":domain,"image_id":f"{domain}_{i:03d}",
                "image_sha256":hashlib.sha256(f"{domain}-{i}".encode()).hexdigest(),
                "scene_group":f"{domain}_{i:03d}",
                "independence_review":"pending","prior_exposure_review":"pending"})
    return {"records":items,"ground_truth":"native_never_resized"},recipe,cohort


class LineageTests(unittest.TestCase):
    def test_14_training_digest_reconstructed_and_seven_proofs_match(self):
        a,b,c=fixture()
        report=task.validate_and_compare(a,b,c)
        self.assertTrue(report["all_seven_training_digests_match"])
        self.assertTrue(report["all_seven_provenance_fields_internally_consistent"])
        self.assertEqual(report["cross_domain_exact_source_image_sha256_matches"],[])
        self.assertEqual(report["draft_cohort_domain_counts"],{"BIPED":125,"MultiCue":95})
        self.assertFalse(report["all_seven_externally_attested"])

    def test_reject_fake_220_cohort_overlapping_original_sha(self):
        a,b,c=fixture()
        c[0]["image_sha256"]=a["records"][0]["source_sha256"]
        report=task.validate_and_compare(a,b,c)
        self.assertEqual(len(report["cross_domain_exact_source_image_sha256_matches"]),1)
        self.assertFalse(report["all_seven_externally_attested"])

    def test_recipe_hash_drift_is_not_silently_promoted(self):
        a,b,c=fixture()
        b["hypotheses"][0]["membership"]["fit_provenance"]["training_ids_sha256"]="0"*64
        report=task.validate_and_compare(a,b,c)
        self.assertFalse(report["all_seven_training_digests_match"])

    def test_reject_4113_capture_and_duplicate_groups(self):
        a,b,c=fixture()
        c[-1]["scene_group"]="4113"
        with self.assertRaises(ValueError):
            task.validate_and_compare(a,b,c)
        a,b,c=fixture()
        c[-1]["scene_group"]=c[-2]["scene_group"]
        with self.assertRaises(ValueError):
            task.validate_and_compare(a,b,c)

    def test_missing_14_training_items_fails(self):
        a,b,c=fixture()
        a["records"].pop()
        with self.assertRaises(ValueError):
            task.validate_and_compare(a,b,c)


if __name__=="__main__":
    unittest.main()
