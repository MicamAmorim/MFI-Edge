#!/usr/bin/env python3
"""Synthetic, offline-only end-to-end test for the Paper A 293-photo review UI."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import build_paper_a_review_quiz as q


class OfflineReviewTests(unittest.TestCase):
    def test_objective_review_questions_and_json_roundtrip_contract(self):
        ui=(ROOT/"tools/paper_a_revisao/app.js").read_text(encoding="utf-8")
        html=(ROOT/"tools/paper_a_revisao/index.template.html").read_text(encoding="utf-8")
        for text in (
            "Sim, todas mostram o mesmo lugar",
            "Apenas algumas mostram o mesmo lugar",
            "Não, mostram lugares diferentes",
            "Não consigo decidir",
            "Qual detalhe fixo você usou para comparar?",
            "Os mesmos prédios/fachadas",
            "As mesmas ruas, placas ou postes",
            "data-group-same",
            "S.groups[g.id]={decision:g.decision,representative:g.representative,subgroups:g.subgroups,evidence:g.evidence,cue:g.cue",
            "sameAsFirst:Array.isArray(g.sameAsFirst)",
            "data-pair-value",
            "v.pairReviews[pair.dataset.pairTarget]=pair.dataset.pairValue",
            "pairReviews:i.pairReviews",
            "comparisons_summary",
            "Não consegui conferir / não sei",
            "O que ainda não podemos afirmar:",
            "a.decision===\"UNCERTAIN\"",
            "scientific_signoff_granted:false",
            "protected_GT_access_authorized:false",
        ):
            with self.subTest(text=text):
                self.assertIn(text,ui)
        self.assertIn("não precisa escrever uma justificativa longa",html)
        self.assertIn("Não consegui conferir",html)
        self.assertNotIn(
            "Estas capturas correspondem a quantas cenas independentes?",ui)
        self.assertNotIn(
            "É uma observação visualmente independente das demais?",ui)

    def test_frontend_javascript_syntax_when_node_available(self):
        import shutil
        import subprocess
        node=shutil.which("node")
        if node is None:
            self.skipTest("Node.js not installed; skip supplemental JS parsing")
        proc=subprocess.run(
            [node,"--check",str(ROOT/"tools/paper_a_revisao/app.js")],
            cwd=ROOT,capture_output=True,text=True,timeout=30,check=False)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)

    def test_all_293_originals_and_22_panels_sha_checked_without_gt(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)
            b=d/"biped";m=d/"multi";b.mkdir();m.mkdir()
            flagged=list(dict.fromkeys(x for g in q.EXPECTED_GROUPS for x in g))
            universe=sorted(set(flagged+[f"RGB_{i:03d}" for i in range(1,259)]))[:]
            # All flagged IDs MUST survive synthetic 198-item truncation.
            extras=[x for x in universe if x not in flagged][:198-len(flagged)]
            ids=sorted(flagged+extras)
            self.assertEqual(len(ids),198)
            chosen=set(flagged+extras[:73])
            self.assertEqual(len(chosen),125)
            candidates=[];cohort=[]
            for n,iid in enumerate(ids):
                rel=iid+".jpg";p=b/rel
                img=Image.new("RGB",(48,30),(n%255,(n*13)%255,(n*7)%255))
                ImageDraw.Draw(img).text((1,1),iid,fill="white")
                img.save(p,format="JPEG",quality=88)
                sha=q.sha_bytes(p.read_bytes())
                candidates.append({
                    "dataset":"BIPEDv2_train","image_id":iid,"relative_path":rel,
                    "sha256":sha,
                    "near_image_flags":"","historical_id_warning":"false",
                })
                if iid in chosen:
                    cohort.append({
                        "dataset":"BIPED","image_id":iid,"relative_path":rel,
                        "image_sha256":sha,"independence_review":"pending",
                        "prior_exposure_review":"pending","scene_group":iid,
                        "notes":"PENDING",
                        "reviewer_independence_decision":"PENDING",
                        "reviewer_prior_exposure_decision":"PENDING",
                        "evidence_for_both_decisions":"","reviewer_name":"",
                        "reviewed_utc":"","historical_attention":"BIPED_REVIEW_PENDING",
                    })
            for n in range(95):
                iid=f"{4100+n}_left_{n+1:04d}"
                path=m/(iid+".png")
                img=Image.new("RGB",(48,30),(n%255,(n*11)%255,(n*19)%255))
                ImageDraw.Draw(img).text((1,1),str(n),fill="white")
                img.save(path,format="PNG")
                cohort.append({
                    "dataset":"MultiCue","image_id":iid,"relative_path":path.name,
                    "image_sha256":q.sha_bytes(path.read_bytes()),
                    "independence_review":"pending","prior_exposure_review":"pending",
                    "scene_group":str(4100+n),"notes":"PENDING",
                    "reviewer_independence_decision":"PENDING",
                    "reviewer_prior_exposure_decision":"PENDING",
                    "evidence_for_both_decisions":"","reviewer_name":"",
                    "reviewed_utc":"","historical_attention":"MULTICUE_REVIEW_PENDING",
                })
            candfile=d/"candidate.csv";cohortfile=d/"review.csv"
            with candfile.open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=list(candidates[0]));w.writeheader();w.writerows(candidates)
            with cohortfile.open("w",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,fieldnames=q.REVIEW_COLUMNS);w.writeheader();w.writerows(cohort)
            auditfile=d/"p1.json";templatefile=d/"template.json"
            proof=[{"hypothesis":"H1" if i<3 else "H2",
                    "fitted_part":str(i),
                    "fitting_commit":"a"*40,
                    "training_ids_sha256":"b"*64} for i in range(7)]
            auditfile.write_text(json.dumps({
                "all_seven_training_digests_match":True,
                "P1_seven_proofs":proof,
                "training_ids_hash_recomputed":"b"*64
            }),encoding="utf-8")
            templatefile.write_text(json.dumps({
                "reviewed_cohort_sheet_sha256":q.sha_bytes(cohortfile.read_bytes()),
                "approved_for_first_confirmatory_outcome_access":False,
                "approved_runtime_sources_sha256":{"fake.py":"a"*64}
            }),encoding="utf-8")
            source=q.inspect_sources(candidates=candfile,review=cohortfile,p1=auditfile,template=templatefile)
            self.assertEqual(len(source["items"]),293)
            self.assertEqual(len(source["groups"]),22)
            self.assertEqual(len(source["p1"]),7)
            self.assertEqual(sum(x["in_initial_cohort"] for x in source["items"]),220)
            out=d/"out"
            result=q.generate(biped=b,multicue=m,output=out,frontend=ROOT/"tools/paper_a_revisao",sources=source)
            self.assertEqual(result["status"],"LOCAL_293_IMAGE_QUIZ_READY_NOT_SIGNED")
            self.assertFalse(result["GT_opened"])
            self.assertFalse(result["freeze_authorized"])
            self.assertEqual(len(list((out/"assets/images").glob("*.jpg"))),293)
            self.assertEqual(len(list((out/"assets/groups").glob("*.jpg"))),22)
            manifest=json.loads((out/"MANIFEST.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["images"]),293)
            self.assertTrue(all(len(r["original_sha256"])==64 for r in manifest["images"]))
            html=(out/"index.html").read_text(encoding="utf-8")
            self.assertIn("198 candidatas BIPED",html)
            self.assertIn('"visual_candidates_n":293',html)
            self.assertNotIn("__REVIEW_DATA_JSON__",html)
            # Every visual eligibility question must now have real references
            # from its own dataset, including all 73 alternative BIPED images.
            label='<script type="application/json" id="review-data">'
            browser=json.loads(html.split(label,1)[1].split("</script>",1)[0])
            self.assertEqual(len(browser["items"]),293)
            for record in browser["items"]:
                refs=record["visual_references"]
                self.assertGreaterEqual(len(refs),4)
                self.assertEqual(len(refs),len(set(r["id"] for r in refs)))
                for reference in refs:
                    self.assertEqual(reference["dataset"],record["dataset"])
                    self.assertNotEqual(reference["id"],record["id"])
                    self.assertIn(reference["reason"],(
                        "suspected_shared_scene","approximate_visual_similarity"))
            first_group=q.EXPECTED_GROUPS[0]
            group_item=next(x for x in browser["items"]
                if x["dataset"]=="BIPED" and x["id"]==first_group[0])
            self.assertTrue(set(first_group[1:]).issubset(
                {x["id"] for x in group_item["visual_references"]}))
            self.assertIn("comparison-card",(
                ROOT/"tools/paper_a_revisao/app.js").read_text(encoding="utf-8"))

            again=q.generate(biped=b,multicue=m,output=out,frontend=ROOT/"tools/paper_a_revisao",sources=source)
            self.assertTrue(again["reused_sha_checked_thumbnails"])
            # A reused slim MANIFEST must not strip selection flags and
            # original file URI links from the browser's full data model.
            reused_html=(out/"index.html").read_text(encoding="utf-8")
            self.assertIn('"in_initial_cohort":true',reused_html)
            self.assertIn('"in_initial_cohort":false',reused_html)
            self.assertIn('"original_href":"file://',reused_html)
            self.assertIn('"visual_candidates_n":293',reused_html)
            # Corrupting a generated image must fail rather than silently reusing.
            (out/"assets/images"/("BIPED_"+ids[0]+".jpg")).write_bytes(b"bad")
            with self.assertRaises(RuntimeError):
                q.generate(biped=b,multicue=m,output=out,frontend=ROOT/"tools/paper_a_revisao",sources=source)


if __name__=="__main__":
    unittest.main()
