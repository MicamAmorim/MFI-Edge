#!/usr/bin/env python3
"""Synthetic Spearman/permutation unit tests; no real GT or F1 accessed."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from analyze_paper_a_confirmed import (rho,aggregate_domain_rho,
    permutation_test,holm2,check_outcomes)


class InferentialTests(unittest.TestCase):
    def fixture(self):
        rows=[]
        for d in ("BIPED","MultiCue"):
            for i in range(12):
                rows.append({"dataset":d,"image_id":f"{d}-{i}",
                  "scene_group":f"{d}-scene-{i}",
                  "image_sha256":f"{len(rows)+1:064x}",
                  "X1":i/12,"Y1":(12-i)/12-0.5,
                  "X2":i/12,"Y2":i/12-0.5})
        return rows

    def test_midrank_spearman(self):
        self.assertAlmostEqual(rho([1,2,2,3],[3,2,2,1]),-1)

    def test_constant_variable_fails(self):
        with self.assertRaises(ValueError):
            rho([1,1,1],[0,1,2])

    def test_domain_statistic(self):
        rows=self.fixture()
        stat,domains=aggregate_domain_rho(rows,"X1","Y1")
        self.assertAlmostEqual(stat,-1)
        self.assertEqual(len(domains),2)

    def test_negative_direction(self):
        rows=self.fixture()
        result=permutation_test(rows,"H1",99,2026)
        self.assertAlmostEqual(result["statistic_within_domain"],-1)
        self.assertLessEqual(result["p_one_sided"],0.05)

    def test_positive_direction(self):
        rows=self.fixture()
        result=permutation_test(rows,"H2",99,2026)
        self.assertAlmostEqual(result["statistic_within_domain"],1)
        self.assertLessEqual(result["p_one_sided"],0.05)

    def test_holm_preserves_order(self):
        self.assertEqual(holm2(0.01,0.04),(0.02,0.04))
        self.assertEqual(holm2(0.07,0.01),(0.07,0.02))

    def test_matching_cohort(self):
        rows=self.fixture()
        cohort=[{key:r[key] for key in ("dataset","image_id","scene_group","image_sha256")} for r in rows]
        self.assertEqual(len(check_outcomes([{k:str(v) for k,v in r.items()} for r in rows],cohort)),24)

    def test_outcome_missing_rejected(self):
        rows=self.fixture()
        cohort=[{key:r[key] for key in ("dataset","image_id","scene_group","image_sha256")} for r in rows]
        with self.assertRaises(ValueError):
            check_outcomes([{k:str(v) for k,v in r.items()} for r in rows[:-1]],cohort)


if __name__=="__main__":
    unittest.main()
