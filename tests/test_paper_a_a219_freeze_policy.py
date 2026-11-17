#!/usr/bin/env python3
"""Synthetic A219 freeze source and group-validation tests; no GT/H5/F1."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import paper_a_a219_freeze_policy as policy


def write_json(path, obj):
    path.write_text(json.dumps(obj,ensure_ascii=False),encoding="utf-8")


def manifest(path,rows):
    with path.open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=(
            "dataset","image_id","relative_path","image_sha256",
            "independence_review","prior_exposure_review","scene_group","notes"))
        writer.writeheader();writer.writerows(rows)


class A219FreezeBindingTests(unittest.TestCase):
    def test_standalone_preview_import_from_different_working_directory(self):
        import subprocess
        script=ROOT/"scripts"/"gerar_preview_freeze_a219.py"
        with tempfile.TemporaryDirectory() as other_directory:
            proc=subprocess.run(
                [sys.executable,"-B",str(script),"--check-import-only"],
                cwd=other_directory,capture_output=True,text=True,
                timeout=30,check=False)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
        self.assertIn("A219_PREVIEW_IMPORTS_OK_NO_ACTION",proc.stdout)

    def test_standalone_preview_never_invokes_freeze(self):
        import ast
        script=ROOT/"scripts"/"gerar_preview_freeze_a219.py"
        tree=ast.parse(script.read_text(encoding="utf-8"))
        calls={n.func.id for n in ast.walk(tree)
               if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
        self.assertIn("prepare",calls)
        self.assertNotIn("attempt_freeze",calls)

    def fixture(self,base):
        p=Path(base)
        ids={"BIPED":[f"RGB_{i:03d}" for i in range(1,126)],
             "MultiCue":[f"{i+4200}_left_{i:04d}" for i in range(94)]}
        rows=[]
        for ds,names in ids.items():
            for name in names:
                rows.append({
                    "dataset":ds,"image_id":name,"relative_path":name+".png",
                    "image_sha256":hashlib.sha256(f"{ds}/{name}".encode()).hexdigest(),
                    "independence_review":"pending","prior_exposure_review":"pending",
                    "scene_group":"NOT_INDEPENDENTLY_ATTESTED_"+name,
                    "notes":"PRE-FREEZE ONLY",
                })
        cfg=p/"candidate.json";roster=p/"roster.csv";old=p/"old.csv"
        read=p/"readiness.json";power=p/"power.json";preview=p/"preview.json"
        manifest(roster,rows)
        manifest(old,rows[:83]+rows[125:]+[
            {**r,"image_id":"OLD_BIPED_"+str(i), "relative_path":"OLD_BIPED_"+str(i)+".png"}
            for i,r in enumerate(rows[83:125])]+[
            {**rows[-1],"image_id":"EXTRA_MULTICUE","relative_path":"EXTRA_MULTICUE.png"}
        ])
        write_json(cfg,{
            "schema":"paper_a_candidate_A_219_pre_freeze_v1",
            "status":"PROPOSAL_NOT_FROZEN_NOT_APPROVED",
            "counts":{"BIPED":125,"MultiCue":94,"N":219},
            "source_cohort_sha256":policy.sha(old),
            "images":{ds:','.join(names) for ds,names in ids.items()},
            "quarantine_BIPED_ids":','.join(f"RGB_{i:03d}" for i in range(150,166)),
            **{k:False for k in (
             "historical_exposure_approved","GT_semantics_approved",
             "independent_scene_approval","power_for_new_domain_mix_approved",
             "freeze_authorized","outcomes_access_authorized")}
        })
        write_json(read,{
            "status":"A_N219_ORIGINAL_SHA_VERIFIED_SCIENCE_GATES_OPEN",
            "counts":{"BIPED":125,"MultiCue":94,"N":219},
            "review_roster_sha256":policy.sha(roster),
            "scientific_signoff":False,"freeze_authorized":False,
            "GT_accessed":False,"H1_H2_executed":False
        })
        write_json(preview,{
            "status":"draft_not_frozen",
            "cohort":{"target_n_independent_images":219},
            "confirmatory_outcomes_opened":False,"freeze_commit":None
        })
        write_json(power,{
            "schema":"paper_a_A_N219_power_sensitivity_no_protected_outcomes_v1",
            "status":"SYNTHETIC_PLANNING_ONLY_NOT_SCIENTIFICALLY_APPROVED",
            "replicates_per_effect":10000,
            "source_metadata_sha256":{
                "readiness_sha256":policy.sha(read),
                "roster_sha256":policy.sha(roster),
            },
            "assumptions":{"true_image_independence_presumed_not_verified":True},
            "effects":[{"assumed_abs_population_Spearman_rho":rho} for rho in (.15,.20,.25)],
            "scientific_power_approval":False,"freeze_authorized":False,
            "GT_opened":False,"H1_H2_executed":False,
        })
        args={"candidate":cfg,"roster":roster,"readiness":read,
              "power":power,"preview":preview,"old":old}
        return args,rows

    def test_exact_hash_and_all_219_images(self):
        with tempfile.TemporaryDirectory() as tmp:
            args,rows=self.fixture(tmp)
            status=policy.validate_sources(**args)
            self.assertEqual(len(status["baseline_rows"]),219)
            policy.validate_reviewed_rows(rows,status["baseline_rows"])
            self.assertTrue(status["not_a_scientific_signoff"])

    def test_fails_if_first_image_changed_or_fake_scene_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            args,rows=self.fixture(tmp)
            original=policy.validate_sources(**args)["baseline_rows"]
            with self.assertRaisesRegex(PermissionError,"scene group"):
                policy.validate_reviewed_rows(rows,original,require_groups=True)
            fixed=[{**r,"scene_group":"REVIEWED_SCENE_"+r["image_id"]} for r in rows]
            policy.validate_reviewed_rows(fixed,original,require_groups=True)
            fixed[17]["image_sha256"]="f"*64
            with self.assertRaisesRegex(PermissionError,"ID/path/SHA"):
                policy.validate_reviewed_rows(fixed,original,require_groups=True)

    def test_fails_on_undocumented_same_scene_repetition(self):
        with tempfile.TemporaryDirectory() as tmp:
            args,rows=self.fixture(tmp)
            original=policy.validate_sources(**args)["baseline_rows"]
            fixed=[{**r,"scene_group":"REVIEWED_SCENE_"+r["image_id"]} for r in rows]
            fixed[1]["scene_group"]=fixed[0]["scene_group"]
            with self.assertRaisesRegex(PermissionError,"Repeated independent scene"):
                policy.validate_reviewed_rows(fixed,original,require_groups=True)

    def test_stale_power_and_claim_of_approval_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            args,rows=self.fixture(tmp)
            power=json.loads(args["power"].read_text())
            power["scientific_power_approval"]=True
            write_json(args["power"],power)
            with self.assertRaisesRegex(PermissionError,"may not authorize"):
                policy.validate_sources(**args)
            power["scientific_power_approval"]=False
            power["source_metadata_sha256"]["roster_sha256"]="a"*64
            write_json(args["power"],power)
            with self.assertRaisesRegex(PermissionError,"Power sensitivity"):
                policy.validate_sources(**args)


if __name__=="__main__":
    unittest.main()
