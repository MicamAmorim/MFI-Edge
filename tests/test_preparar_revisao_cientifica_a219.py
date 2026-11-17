#!/usr/bin/env python3
"""Synthetic, no-GT tests for unsigned N219 protocol and 219-row signoff preview."""
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import preparar_revisao_cientifica_a219 as prepare


def write_json(path, data):
    path.write_text(json.dumps(data,ensure_ascii=False)+"\n",encoding="utf-8")


def write_csv(path, records):
    stream=io.StringIO(newline="")
    names=("dataset","image_id","relative_path","image_sha256",
           "independence_review","prior_exposure_review","scene_group","notes")
    writer=csv.DictWriter(stream,fieldnames=names,lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    path.write_text(stream.getvalue(),encoding="utf-8")


class CandidateA219PreviewTests(unittest.TestCase):
    def fixture(self, directory):
        p=Path(directory)
        root={name:p/name for name in ("protocol.json","candidate.json","roster.csv",
            "old.csv","readiness.json","power.json","p1.json","stage.json",
            "gt_format.json","gt_detail.json","exe.py")}
        b=[f"RGB_{i:03d}" for i in range(1,126)]
        m=[f"{4100+i}_left_{i+1:04d}" for i in range(94)]
        ob=b[:83]+[f"RGB_{i:03d}" for i in range(150,192)]
        old_m=m+["4586_left_0080"]
        def row(ds,name):
            return {
                "dataset":ds,"image_id":name,
                "relative_path":name+".png",
                "image_sha256":hashlib.sha256((ds+name).encode()).hexdigest(),
                "independence_review":"pending","prior_exposure_review":"pending",
                "scene_group":"NOT_INDEPENDENTLY_ATTESTED_"+name,
                "notes":"REVIEW_ONLY"}
        write_csv(root["old.csv"],[row("BIPED",x) for x in ob]+
                  [row("MultiCue",x) for x in old_m])
        write_csv(root["roster.csv"],[row("BIPED",x) for x in b]+
                  [row("MultiCue",x) for x in m])
        write_json(root["candidate.json"],{
            "status":"PROPOSAL_NOT_FROZEN_NOT_APPROVED",
            "counts":{"BIPED":125,"MultiCue":94,"N":219},
            "images":{"BIPED":",".join(b),"MultiCue":",".join(m)},
            "quarantine_BIPED_ids":",".join(f"RGB_{i:03d}" for i in range(220,236)),
            "source_cohort_sha256":prepare.sha(root["old.csv"].read_bytes()),
            **{k:False for k in (
                "historical_exposure_approved","GT_semantics_approved",
                "independent_scene_approval","power_for_new_domain_mix_approved",
                "freeze_authorized","outcomes_access_authorized")}
        })
        write_json(root["readiness.json"],{
            "status":"A_N219_ORIGINAL_SHA_VERIFIED_SCIENCE_GATES_OPEN",
            "counts":{"BIPED":125,"MultiCue":94,"N":219},
            "review_roster_sha256":prepare.sha(root["roster.csv"].read_bytes()),
            "scientific_signoff":False,"GT_accessed":False,
            "freeze_authorized":False,"H1_H2_executed":False})
        write_json(root["protocol.json"],{
            "status":"draft_not_frozen","freeze_commit":None,
            "confirmatory_outcomes_opened":False,
            "cohort":{"target_n_independent_images":150,"min_n_per_domain":60},
            "measures":{"unit":"independent_original_image"},
            "inference":{"permutations":100000,"alpha_familywise":0.05},
            "hypotheses":[{"id":"H1"},{"id":"H2"}]})
        write_json(root["p1.json"],{
            "all_seven_training_digests_match":True,
            "P1_seven_proofs":[{"fitted_part":str(i)} for i in range(7)]
        })
        write_json(root["stage.json"],{"status":"PREFREEZE_ONLY"})
        write_json(root["gt_format.json"],{"status":"METADATA_NOT_APPROVED"})
        write_json(root["gt_detail.json"],{"status":"METADATA_NOT_APPROVED"})
        root["exe.py"].write_text("# no execution\n",encoding="utf-8")
        effects=[]
        for rho,power in ((.15,.4869),(.20,.815),(.25,.9652)):
            effects.append({
                "assumed_abs_population_Spearman_rho":rho,
                "candidate_A":{"BIPED":125,"MultiCue":94,"N":219,
                               "joint_rejection_rate":power,
                               "mc_95pct_interval":[power-.008,power+.008]},
            })
        write_json(root["power.json"],{
            "schema":"paper_a_A_N219_power_sensitivity_no_protected_outcomes_v1",
            "status":"SYNTHETIC_PLANNING_ONLY_NOT_SCIENTIFICALLY_APPROVED",
            "replicates_per_effect":10000,
            "source_metadata_sha256":{
                "readiness_sha256":prepare.sha(root["readiness.json"].read_bytes()),
                "roster_sha256":prepare.sha(root["roster.csv"].read_bytes())},
            "assumptions":{"true_image_independence_presumed_not_verified":True},
            "scientific_power_approval":False,"freeze_authorized":False,
            "GT_opened":False,"H1_H2_executed":False,
            "effects":effects,
        })
        return dict(protocol=root["protocol.json"],candidate=root["candidate.json"],
            roster=root["roster.csv"],old=root["old.csv"],readiness=root["readiness.json"],
            power=root["power.json"],p1_path=root["p1.json"],stage=root["stage.json"],
            exe=root["exe.py"],fmt=root["gt_format.json"],detail=root["gt_detail.json"])

    def test_draft_all_219_pending_and_source_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            inputs=self.fixture(tmp)
            out=prepare.build(**inputs)
            self.assertEqual(out["draft_protocol"]["status"],"draft_not_frozen")
            self.assertEqual(out["draft_protocol"]["cohort"]["target_n_independent_images"],219)
            self.assertIn("0.8150",out["draft_protocol"]["cohort"]["power_analysis"])
            self.assertIn("254_255",out["draft_protocol"]["measures"]["ground_truth_contract_proposal"]["encoding_proposed_not_approved"])
            with io.StringIO(out["review_sheet_bytes"].decode("utf-8"),newline="") as stream:
                rows=list(csv.DictReader(stream))
            self.assertEqual(len(rows),219)
            self.assertEqual(Counter(r["dataset"] for r in rows),{"BIPED":125,"MultiCue":94})
            self.assertEqual(sum("NEW_BIPED_ALTERNATIVE" in x["historical_attention"] for x in rows),42)
            self.assertTrue(all(r["reviewer_independence_decision"]=="PENDING" and
                                r["reviewer_prior_exposure_decision"]=="PENDING" for r in rows))
            self.assertTrue(all(v is False for v in out["template"]["scientific_approvals"].values()))
            self.assertEqual(len(out["template"]["P1_seven_lineage_reviews"]),7)
            self.assertFalse(out["assessment"]["GT_opened"])
            self.assertFalse(out["assessment"]["scientific_signoff"])
            self.assertEqual(out["assessment"]["counts"]["N"],219)

    def test_fails_closed_when_power_sha_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            inputs=self.fixture(tmp)
            broken=json.loads(inputs["power"].read_text(encoding="utf-8"))
            broken["source_metadata_sha256"]["roster_sha256"]="f"*64
            write_json(inputs["power"],broken)
            with self.assertRaisesRegex(ValueError,"Power assumptions"):
                prepare.build(**inputs)

    def test_fails_closed_when_someone_preapproves_unsigned_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            inputs=self.fixture(tmp)
            bad=json.loads(inputs["readiness"].read_text(encoding="utf-8"))
            bad["scientific_signoff"]=True
            write_json(inputs["readiness"],bad)
            with self.assertRaises(PermissionError):
                prepare.build(**inputs)

    def test_review_previews_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            file=Path(tmp)/"safe.json"
            prepare.write_immutable(file,b'{"freeze":false}')
            prepare.write_immutable(file,b'{"freeze":false}')
            with self.assertRaises(RuntimeError):
                prepare.write_immutable(file,b'{"freeze":true}')


if __name__=="__main__":
    unittest.main()
