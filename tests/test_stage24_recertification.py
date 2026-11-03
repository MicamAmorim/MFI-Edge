from __future__ import annotations
"""Fast synthetic tests for Stage 24G-L: run without UDED, MATLAB or caches."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np

from src.stage24_recertification_ops import (
    AGGREGATORS, capacity_coefficients, capacity_from_mobius,
    choquet, sugeno, fit_aggregator, apply_aggregator,
    thin_score, binary_map, choose_threshold,
)
from src.stage24_integrity import one_to_one_boundary_counts


class PaperARecertificationTests(unittest.TestCase):
    def test_additive_choquet_is_mean(self):
        for n in (2, 3):
            rng = np.random.default_rng(n)
            x = rng.random((7, 11, n))
            cap = np.asarray([int(m).bit_count()/n for m in range(1<<n)])
            self.assertTrue(np.allclose(choquet(x,cap), x.mean(axis=-1),atol=1e-7))

    def test_positive_and_signed_capacities_valid(self):
        for n in (2, 3):
            rng=np.random.default_rng(20+n)
            x=rng.uniform(0,1,(200,n))
            y=(x.mean(axis=-1)>.55).astype(float)
            for signed in (False, True):
                weights=capacity_coefficients(x,y,signed=signed)
                cap=capacity_from_mobius(weights,n)
                self.assertAlmostEqual(cap[0],0.0)
                self.assertAlmostEqual(cap[-1],1.0)
                for mask in range(1<<n):
                    for bit in range(n):
                        if not mask&(1<<bit):
                            self.assertGreaterEqual(cap[mask|(1<<bit)]+1e-5,cap[mask])

    def test_operators_bounded_and_monotone(self):
        rng=np.random.default_rng(17)
        for n in (2,3):
            x=rng.random((20, 13, n),dtype=np.float32)
            z=np.clip(x+.01,0,1)
            cap=np.array([int(mask).bit_count()/n for mask in range(1<<n)])
            for name in ("equal_mean","minimum","maximum","product","median",
                         "owa_optimistic","owa_pessimistic","owa_median",
                         "choquet_distorted_055"):
                params={"family":name,"n_inputs":n}
                a=apply_aggregator(x,params)
                b=apply_aggregator(z,params)
                self.assertEqual(a.shape,x.shape[:-1])
                self.assertTrue(np.isfinite(a).all(),name)
                self.assertGreaterEqual(float(a.min()),0)
                self.assertLessEqual(float(a.max()),1)
                self.assertTrue(np.all(b+1e-6>=a),name)
            self.assertTrue(np.all(sugeno(x,cap)>=0))

    def test_owa_median_two_is_mean_three_is_median(self):
        x=np.array([[[.2,.6],[.8,.9]]],np.float32)
        v=apply_aggregator(x,{"family":"owa_median","n_inputs":2})
        self.assertTrue(np.allclose(v,x.mean(axis=-1)))
        y=np.array([[[.1,.7,.3]]],np.float32)
        v=apply_aggregator(y,{"family":"owa_median","n_inputs":3})
        self.assertAlmostEqual(float(v[0,0]),.3,places=6)

    def test_native_gt_never_modified_by_thinning(self):
        gt=np.zeros((33,33),bool)
        gt[15,5:27]=True
        image=np.repeat(np.arange(33)[:,None],33,axis=1).astype(float)
        score=np.zeros(gt.shape,np.float32)
        score[14:17,5:27]=.8
        snapshot=gt.copy()
        for mode in ("raw","nms_image","binary_thin_diagnostic"):
            s=thin_score(score,mode,image)
            pred=binary_map(s,.5,mode)
            c=one_to_one_boundary_counts(pred,gt,tolerance_px=0)
            self.assertEqual(pred.shape,gt.shape)
            self.assertGreaterEqual(c.tp,0)
            self.assertTrue(np.array_equal(gt,snapshot))
        self.assertLessEqual(np.count_nonzero(binary_map(thin_score(score,"binary_thin_diagnostic",image),.5,"binary_thin_diagnostic")),np.count_nonzero(score>=.5))

    def test_threshold_selected_on_supplied_training_only(self):
        g=np.zeros((12,12),bool);g[5,3:9]=True
        s=np.zeros(g.shape,np.float32);s[5,3:9]=.9
        image=np.zeros(g.shape,np.float32)
        t,c=choose_threshold([s],[g],[image],"raw",count=9)
        self.assertGreater(t,0)
        self.assertEqual(c.tp,6)
        self.assertEqual(c.fp,0)

    def test_same_fitted_aggregation_for_raw_and_nms(self):
        from src.stage24_recertification_cv import fit_and_score, clear_group_cache
        clear_group_cache()
        yy, xx = np.mgrid[:20, :20]
        gt = (yy == 10) & (xx >= 3) & (xx <= 16)
        img = yy.astype(float) / 20
        scores = np.clip(np.exp(-((yy - 10)/2.)**2), 0, 1).astype(np.float32)
        a, b = np.clip(scores + .05, 0, 1), np.clip(scores*.7 + .1, 0, 1)
        items = [{"id": str(i), "gt": gt.copy(), "img": img.copy()} for i in range(3)]
        maps = {"a": [a.copy() for _ in items], "b": [b.copy() for _ in items]}
        raw = fit_and_score(("a","b"),"choquet_positive_2add",items,maps,[0,1],[2],
                            "raw",count=9,seed=17)
        nms = fit_and_score(("a","b"),"choquet_positive_2add",items,maps,[0,1],[2],
                            "nms_image",count=9,seed=99)
        self.assertEqual(raw["model"]["aggregator"], nms["model"]["aggregator"])
        self.assertTrue(np.array_equal(items[0]["gt"], gt))
        clear_group_cache()

    def test_train_only_aggregator_models(self):
        g=np.zeros((13,13),bool);g[4,3:9]=True
        x=np.stack([g.astype(np.float32)*.85+.05,g.astype(np.float32)*.75+.1],axis=-1)
        arr=[x,x.copy()]
        gt=[g,g.copy()]
        for name in ("weighted_mean","nonnegative_logistic","owa_learned",
                     "choquet_additive","choquet_positive_2add",
                     "choquet_signed_2add","choquet_generalized_055",
                     "sugeno_additive","sugeno_positive_2add"):
            state=fit_aggregator(name,arr,gt,[0],seed=12)
            p=apply_aggregator(arr[1],state)
            self.assertEqual(p.shape,g.shape)
            self.assertTrue(np.isfinite(p).all(),name)


if __name__=="__main__":
    unittest.main()
