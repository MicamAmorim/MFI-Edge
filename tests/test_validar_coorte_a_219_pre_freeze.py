#!/usr/bin/env python3
"""Synthetic-only A-N219 original SHA and fail-closed signoff tests."""
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
import validar_coorte_a_219_pre_freeze as a


def write_csv(path,items):
    out=io.StringIO(newline="")
    writer=csv.DictWriter(out,fieldnames=list(items[0]))
    writer.writeheader();writer.writerows(items)
    path.write_text(out.getvalue(),encoding="utf-8")


class CandidateATests(unittest.TestCase):
    def build(self,d):
        b=d/"b";m=d/"m";b.mkdir();m.mkdir()
        inv=[];old=[];sha_map={}
        selected_b=[f"RGB_{i:03d}" for i in range(1,126)]
        old_b=selected_b[:83]+[f"RGB_{i:03d}" for i in range(151,193)]
        multi=[f"{4600+i}_left_{i+1:04d}" for i in range(93)]+[
            "4582_left_0020","4586_left_0080"]
        selected_m=multi[:-1]
        for i in range(1,199):
            name=f"RGB_{i:03d}"
            payload=f"BIPED/{name}".encode("utf-8")
            path=b/(name+".png");path.write_bytes(payload)
            hash=hashlib.sha256(payload).hexdigest();sha_map[("BIPED",name)]=hash
            inv.append({"dataset":"BIPEDv2_train","image_id":name,
                        "sha256":hash,"relative_path":path.name})
            if name in old_b:
                old.append({"dataset":"BIPED","image_id":name,
                            "relative_path":path.name,"image_sha256":hash})
        for name in multi:
            payload=f"MultiCue/{name}".encode("utf-8")
            path=m/(name+".png");path.write_bytes(payload)
            hash=hashlib.sha256(payload).hexdigest();sha_map[("MultiCue",name)]=hash
            old.append({"dataset":"MultiCue","image_id":name,
                        "relative_path":path.name,"image_sha256":hash})
        self.assertEqual(len(old),220)
        config=d/"config.json";inventory=d/"candidate.csv";previous=d/"old.csv"
        write_csv(inventory,inv);write_csv(previous,old)
        roster=sorted(f"{ds}|{name}|{sha_map[(ds,name)]}\n"
            for ds,chosen in (("BIPED",selected_b),("MultiCue",selected_m))
            for name in chosen)
        q=','.join(f"RGB_{i:03d}" for i in range(130,146))
        config.write_text(json.dumps({
            "schema":"paper_a_candidate_A_219_pre_freeze_v1",
            "status":"PROPOSAL_NOT_FROZEN_NOT_APPROVED",
            "counts":{"BIPED":125,"MultiCue":94,"N":219},
            "images":{"BIPED":','.join(selected_b),"MultiCue":','.join(selected_m)},
            "quarantine_BIPED_ids":q,
            "excluded_MultiCue_possible_repeated_capture":"4586_left_0080",
            "source_cohort_sha256":a.digest(previous),
            "roster_sha256_sorted_dataset_id_source_sha":
               hashlib.sha256(''.join(roster).encode("utf-8")).hexdigest(),
            **{k:False for k in (
              "historical_exposure_approved","GT_semantics_approved",
              "independent_scene_approval","power_for_new_domain_mix_approved",
              "freeze_authorized","outcomes_access_authorized")}
        }),encoding="utf-8")
        p1=d/"P1.json";p1.write_text(json.dumps({
            "all_seven_training_digests_match":True,
            "all_seven_provenance_fields_internally_consistent":True,
            "P1_seven_proofs":[{"id":i} for i in range(7)]
        }),encoding="utf-8")
        protocol=d/"protocol.json"
        protocol.write_text(json.dumps({
            "status":"draft_not_frozen",
            "cohort":{"target_n_independent_images":220}
        }),encoding="utf-8")
        return dict(config=config,inventory=inventory,selected_old=previous,
                    p1_path=p1,protocol=protocol,biped_base=b,multicue_base=m)

    def test_synthetic_exact_125_plus_94_sources_and_no_freeze(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=self.build(Path(tmp))
            status,rows=a.audit(**args)
            self.assertEqual(len(rows),219)
            self.assertEqual(status["counts"],{"BIPED":125,"MultiCue":94,"N":219})
            self.assertEqual(status["retained_BIPED"],83)
            self.assertEqual(status["replacement_BIPED"],42)
            powers=status["illustrative_normal_approx_joint_power_not_validated"]
            self.assertGreater(powers["scenario_A_N219"],0.80)
            self.assertLess(powers["scenario_A_N219"],
                            powers["legacy_mix_N220_same_approximation"])
            self.assertTrue(powers["cannot_authorize_power_or_freeze"])
            self.assertTrue(status["P1_lineage_metadata_consistent"])
            self.assertFalse(status["scientific_signoff"])
            self.assertFalse(status["GT_accessed"])
            self.assertFalse(status["freeze_authorized"])
            self.assertEqual(len(set(x["image_sha256"] for x in rows)),219)
            self.assertTrue(all(x["independence_review"]=="pending" for x in rows))
            broken=args["biped_base"]/"RGB_084.png"
            broken.write_bytes(b"altered_original")
            with self.assertRaisesRegex(ValueError,"Original SHA mismatch"):
                a.audit(**args)

    def test_fails_closed_on_quarantined_selected_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=self.build(Path(tmp))
            cfg=json.loads(args["config"].read_text(encoding="utf-8"))
            cfg["quarantine_BIPED_ids"]+=","+"RGB_001"
            args["config"].write_text(json.dumps(cfg),encoding="utf-8")
            with self.assertRaises(ValueError):
                a.audit(**args)

    def test_existing_report_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"report.json"
            a.write_unchanged(path,b'{"safe":false}')
            a.write_unchanged(path,b'{"safe":false}')
            with self.assertRaises(RuntimeError):
                a.write_unchanged(path,b'{"safe":true}')


if __name__=="__main__":
    unittest.main()
