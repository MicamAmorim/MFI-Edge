from __future__ import annotations
"""Research math regressions: copulas, CF1F2 Eq9 and tie reduction."""
import unittest
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
import numpy as np

from src.operators import FUNCTIONS, cf1f2_integral
from src.stage24_strict_generalized_cf1f2 import (
    VALID_PAIRS, generalized_cf1f2, apply_registered_gcf, check_pseudo_pair,
)
from src.stage24_math_contracts import (
    COPULA_THEORETICAL_CANDIDATES, numerical_copula_contract,
)


class StrictGeneralizedIntegralTests(unittest.TestCase):
    def test_candidate_copulas_and_legacy_misnomers(self):
        for name in COPULA_THEORETICAL_CANDIDATES:
            out=numerical_copula_contract(FUNCTIONS[name],n=81)
            self.assertTrue(out["margins_pass"],name)
            self.assertTrue(out["two_increasing_grid_pass"],name)
        for name in ("TDP","OmM","GM","HM","S","ORS"):
            out=numerical_copula_contract(FUNCTIONS[name],n=81)
            self.assertFalse(out["margins_pass"] and out["two_increasing_grid_pass"],name)

    def test_pseudo_pairs_pass_numerical_screen(self):
        for name,fn in VALID_PAIRS.items():
            a,b=(FUNCTIONS[x] for x in fn)
            self.assertTrue(all(check_pseudo_pair(a,b,grid=61).values()),name)

    def test_right_neutral_shortcut_failure_gm(self):
        val=apply_registered_gcf(np.array([.25]),np.array([0.,1.]),"gcf_gm_gm")
        self.assertAlmostEqual(float(val),.5,places=6)
        # The historical x_(1) shortcut yields 0.25 instead: do not regress.
        self.assertNotAlmostEqual(float(val),.25,places=6)

    def test_ties_reduce_dimension(self):
        cap=np.array([0.,1/3,1/3,2/3,1/3,2/3,2/3,1.],float)
        x=np.array([[.4,.4,.8],[.8,.4,.4],[.4,.8,.4]],float)
        for name in VALID_PAIRS:
            v=apply_registered_gcf(x,cap,name)
            self.assertTrue(np.allclose(v,v[0],rtol=0,atol=1e-6),name)

    def test_non_symmetric_tie_capacity_determinism(self):
        # Same coordinates, ties admitted; stable or unstable sorting of
        # equal keys must be irrelevant thanks to set-based tails.
        cap=np.array([0.,.1,.2,.35,.45,.62,.75,1.],float)
        x=np.array([.4,.4,.8],float)
        expected=float(apply_registered_gcf(x,cap,"gcf_gm_gm"))
        # Reimplement with alternative equal-tie permutations, but
        # the set of indices active at each DISTINCT y remains unchanged.
        def direct(y):
            previous=0.;total=0.
            for level in np.unique(y):
                subset=sum(1<<i for i,val in enumerate(y) if val>=level)
                mu=cap[subset]
                total+=np.sqrt(level*mu)-np.sqrt(previous*mu)
                previous=level
            return min(1,total)
        self.assertAlmostEqual(expected,direct(x),places=6)

    def test_hamacher_n_ary_associativity(self):
        from src.fuzzy_measures import adaptive_q_from_features
        x=np.array([.2,.4,.6,.8])
        exact=1./(sum(1./x)-3.)
        new=float(adaptive_q_from_features(x,mode="hamacher",q_min=0.,q_max=1.))
        legacy=float(adaptive_q_from_features(x,mode="hamacher_legacy",q_min=0.,q_max=1.))
        self.assertAlmostEqual(new,exact,places=6)
        self.assertGreater(abs(new-legacy),.05)
        self.assertEqual(float(adaptive_q_from_features(
            np.array([.0,.5,.5]),mode="hamacher",q_min=0.,q_max=1.)),0.)

    def test_pseudo_pair_is_not_proof(self):
        x=np.array([.3,.5,.9],float)
        cap=np.array([0.,.2,.2,.5,.3,.6,.7,1.],float)
        out=apply_registered_gcf(x,cap,"gcf_tp_tl")
        self.assertGreaterEqual(float(out),0)
        self.assertLessEqual(float(out),1)


if __name__=="__main__":
    unittest.main()
