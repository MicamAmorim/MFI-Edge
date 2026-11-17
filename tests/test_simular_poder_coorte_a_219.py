#!/usr/bin/env python3
"""Synthetic-only N219 joint-power planning tests. No GT, no actual cohort."""
import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import simular_poder_coorte_a_219 as power


class CandidateAPowerTests(unittest.TestCase):
    def test_holm_two_hypothesis_rule(self):
        p=np.array([[.01,.03],[.03,.03],[.001,.09],[.02,.05]])
        self.assertEqual(power.both_holm(p).tolist(),[True,False,False,True])

    def test_one_sided_directions_respected(self):
        p=power.pvalues_from_weighted_rho(np.array([[-100.,100.],
                                                     [100.,-100.]]),(125,94))
        self.assertTrue((p[0]<.00001).all())
        self.assertTrue((p[1]>.99999).all())

    def test_spearman_simple_no_tie_cases(self):
        x=np.arange(6,dtype=float).reshape((1,1,6))
        self.assertAlmostEqual(float(power.correlation_of_ranks(x,x)[0,0]),1)
        self.assertAlmostEqual(float(power.correlation_of_ranks(x,x[:,:,::-1])[0,0]),-1)

    def test_seeded_reproducible_planning_simulation(self):
        a=power.simulate(replicates=300,seed=20261117,abs_rho=.20,batch=100)
        b=power.simulate(replicates=300,seed=20261117,abs_rho=.20,batch=100)
        self.assertEqual(a,b)
        self.assertEqual(a["candidate_A"]["N"],219)
        self.assertEqual(a["former_legacy_mix_comparison_only"]["N"],220)
        self.assertTrue(0<a["candidate_A"]["joint_rejection_rate"]<1)
        self.assertTrue(0<=a["candidate_A"]["mc_95pct_interval"][0]<
                        a["candidate_A"]["mc_95pct_interval"][1]<=1)

    def test_source_status_and_sha_guard(self):
        with tempfile.TemporaryDirectory() as td:
            d=Path(td)
            csvpath=d/"review.csv"
            sio=io.StringIO()
            writer=csv.DictWriter(sio,fieldnames=["dataset","image_id",
                "independence_review","prior_exposure_review"])
            writer.writeheader()
            for dataset,n in (("BIPED",125),("MultiCue",94)):
                for i in range(n):
                    writer.writerow({
                        "dataset":dataset,"image_id":dataset+str(i),
                        "independence_review":"pending",
                        "prior_exposure_review":"pending"
                    })
            csvpath.write_bytes(sio.getvalue().encode("utf-8"))
            rpt=d/"status.json"
            meta={
                "schema":"paper_a_A_219_metadata_readiness_v1",
                "status":"A_N219_ORIGINAL_SHA_VERIFIED_SCIENCE_GATES_OPEN",
                "counts":{"BIPED":125,"MultiCue":94,"N":219},
                "GT_accessed":False,"scientific_signoff":False,
                "freeze_authorized":False,
                "roster_sha256":"78cc7c4b36e0fc6faf9996c3dd760cbc8b97f21cfe23c18e26d4f31f7e8ae1d2",
                "review_roster_sha256":power.sha(csvpath)
            }
            rpt.write_text(json.dumps(meta),encoding="utf-8")
            answer=power.read_inputs(readiness=rpt,cohort=csvpath)
            self.assertEqual(answer["roster_sha256"],power.sha(csvpath))
            csvpath.write_text("tampered\n",encoding="utf-8")
            with self.assertRaises(ValueError):
                power.read_inputs(readiness=rpt,cohort=csvpath)


if __name__=="__main__":
    unittest.main()
