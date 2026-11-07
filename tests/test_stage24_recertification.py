from __future__ import annotations
"""Fast synthetic tests for Stage 24G-L: run without UDED, MATLAB or caches."""
from pathlib import Path
import sys
import unittest
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np

from src.stage24_recertification_ops import (
    AGGREGATORS, capacity_coefficients, capacity_from_mobius,
    choquet, sugeno, fit_aggregator, apply_aggregator,
    thin_score, binary_map, choose_threshold,
)
from src.stage24_integrity import one_to_one_boundary_counts, prepare_boundary_reference


class PaperARecertificationTests(unittest.TestCase):
    def test_long_checkpoint_atomic_write_resume_and_archive(self):
        import shutil
        import zipfile
        from src.stage24_recertification_cv import native_path, _checkpoint_piece, write_json
        from scripts.build_stage24gl_repro_package import create_shards
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            long_root = root / ("group_" + "a" * 70)
            target = long_root / ("b" * 70) / ("c" * 70) / "checkpoint.json"
            self.assertGreater(len(str(target)), 260)
            try:
                self.assertEqual(_checkpoint_piece(target, {"v": 1}, lambda: {"F1": 0.}), {"F1": 0.})
                self.assertEqual(_checkpoint_piece(target, {"v": 1}, lambda: self.fail("recomputed")), {"F1": 0.})
                write_json(target, {"spec": {"v": 1}, "value": {"F1": .5}})
                with patch("scripts.build_stage24gl_repro_package.ROOT", root):
                    entries, archives = create_shards([target], root / "zip", "test", root, 100000)
                self.assertEqual(len(entries), 1)
                with zipfile.ZipFile(root / "zip" / archives[0]["archive"]) as z:
                    self.assertIsNone(z.testzip())
            finally:
                if native_path(long_root).exists():
                    shutil.rmtree(native_path(long_root))

    def test_preflight_rejects_normalized_nonmonotone_capacity(self):
        from run_stage24_paper_a_recertification import preflight_math
        with patch("src.stage24_recertification_ops.capacity_from_mobius",
                   return_value=np.array([0., 1.2, .5, 1.])):
            with self.assertRaisesRegex(RuntimeError, "Non-monotone"):
                preflight_math()
        self.assertTrue(all(type(row["passed"]) is bool for row in preflight_math()))

    def test_zero_f1_is_retained_in_image_bootstrap(self):
        from src.stage24_paper_a_controls import image_level_bootstrap_deltas
        rows = [{"group": "a|b", "aggregator": operator, "image_id": str(i),
                 "thinning": "raw", "suppressor": "identity", "F1": score}
                for i in range(6)
                for operator, score in (("equal_mean", .5), ("minimum", 0.))]
        result = image_level_bootstrap_deltas(rows, reps=20)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["delta_F1_mean"], -.5)
        self.assertEqual(result[0]["n_unique_images"], 6)

    def test_skipped_official_or_runtime_is_not_complete(self):
        from argparse import Namespace
        from run_stage24_paper_a_recertification import campaign_complete
        import json
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            args = Namespace(phase="all", max_folds=15, skip_official=False, skip_runtime=False)
            self.assertFalse(campaign_complete(args, path))
            (path / "official_bsds_summary.json").write_text(json.dumps({"status": "completed"}))
            self.assertTrue(campaign_complete(args, path))
            args.skip_official = True
            self.assertFalse(campaign_complete(args, path))
            args.skip_official, args.skip_runtime = False, True
            self.assertFalse(campaign_complete(args, path))

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
                         "owa_optimistic","owa_pessimistic","owa_median","lukasiewicz",
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

    def test_zero_anchored_membership_calibration(self):
        from src.stage24_recertification_ops import calibrate_memberships, CALIBRATION_MODES
        from src.stage24_residual import MembershipModel
        from scipy.special import expit
        m=MembershipModel(np.array([0.,.25]),np.array([.1,.2]))
        inp=np.zeros((3,4,2),np.float32)
        scores=np.broadcast_to(expit(-m.midpoint/m.scale),inp.shape).copy()
        anchored=calibrate_memberships(scores,m,"zero_anchored")
        self.assertTrue(np.allclose(anchored,0.,atol=1e-6))
        self.assertTrue(np.allclose(calibrate_memberships(scores,m,"legacy_sigmoid"),scores))
        self.assertEqual(len(CALIBRATION_MODES),2)

    def test_quantile_mapping_is_monotone(self):
        from src.stage24_recertification_ops import (
            quantile_mapping_fit,quantile_mapping_apply,
        )
        x=np.linspace(0.,1.,121,dtype=np.float32).reshape(11,11)
        model=quantile_mapping_fit([x],n=32)
        f=quantile_mapping_apply(x,model)
        self.assertEqual(f.shape,x.shape)
        self.assertTrue(np.all(np.diff(f.ravel())>=-1e-7))
        self.assertGreaterEqual(f.min(),0)
        self.assertLessEqual(f.max(),1)

    def test_paired_berkeley_count_bootstrap_synthetic(self):
        from src.stage24_paper_a_berkeley_bootstrap import (
            synthetic_contract,_curve_metrics,
        )
        self.assertTrue(synthetic_contract())
        x=np.zeros((3,99,5),dtype=np.float64)
        x[:,:,0]=np.arange(1,100)[None,:]/100.
        x[:,:,2]=100.
        x[:,:,4]=100.
        x[:,:,1]=40
        x[:,:,3]=40
        m=_curve_metrics(x)
        self.assertAlmostEqual(m["ODS"],.4,places=5)
        self.assertAlmostEqual(m["OIS"],.4,places=5)

    def test_historical_stage23d_formula_contract(self):
        from src.stage24_paper_a_historical import synthetic_contract
        self.assertTrue(synthetic_contract())

    def test_full_positive_analytic_baseline(self):
        from src.stage24_paper_a_controls import null_and_random_controls
        gt=np.zeros((18,20),bool)
        gt[6,2:14]=True
        a=[{"id":str(i),"gt":gt.copy()} for i in range(4)]
        rows=null_and_random_controls(a,[0,1],[2,3],"f1")
        full=[x for x in rows if x["baseline"]=="full_image"]
        self.assertEqual(len(full),2)
        self.assertEqual(full[0]["tp"],int(gt.sum()))
        self.assertEqual(full[0]["fp"],gt.size-int(gt.sum()))
        self.assertEqual(full[0]["fn"],0)
        self.assertTrue(np.array_equal(a[0]["gt"],gt))

    def test_train_only_aggregator_models(self):
        g=np.zeros((13,13),bool);g[4,3:9]=True
        x=np.stack([g.astype(np.float32)*.85+.05,g.astype(np.float32)*.75+.1],axis=-1)
        arr=[x,x.copy()]
        gt=[g,g.copy()]
        for name in ("weighted_mean","nonnegative_logistic","owa_learned",
                     "choquet_additive","choquet_positive_2add",
                     "choquet_signed_2add","choquet_generalized_055",
                     "sugeno_additive","sugeno_positive_2add",
                     "gcf_tp_tp","gcf_cl_cl","gcf_tp_tl",
                     "gcf_tm_fna","gcf_gm_gm"):
            state=fit_aggregator(name,arr,gt,[0],seed=12)
            p=apply_aggregator(arr[1],state)
            self.assertEqual(p.shape,g.shape)
            self.assertTrue(np.isfinite(p).all(),name)


    def test_bipartite_matching_preserves_exact_maximum_cardinality(self):
        """Independent sparse-graph oracle, including dense and uncovered GT."""
        from scipy.sparse import csr_matrix
        from scipy.sparse.csgraph import maximum_bipartite_matching
        rng = np.random.default_rng(20261104)
        for size in ((7, 9), (13, 11)):
            for tol in (0, 1, 2, 3):
                for probability in (0., .05, .3, .8, 1.):
                    for _ in range(3):
                        gt = rng.random(size) < .2
                        pred = rng.random(size) < probability
                        pxy, gxy = np.argwhere(pred), np.argwhere(gt)
                        if not len(pxy) or not len(gxy):
                            expected = 0
                        else:
                            d2 = ((pxy[:, None, :] - gxy[None, :, :])**2).sum(axis=2)
                            edges = csr_matrix((d2 <= tol**2).astype(np.uint8))
                            expected = int(np.count_nonzero(
                                maximum_bipartite_matching(edges, perm_type="column") >= 0))
                        reference = prepare_boundary_reference(gt, tolerance_px=tol)
                        old = one_to_one_boundary_counts(pred, gt, tolerance_px=tol)
                        cached = one_to_one_boundary_counts(pred, gt, reference=reference)
                        self.assertEqual(old.tp, expected)
                        self.assertEqual(cached, old)
                        self.assertEqual(old.fp, int(pred.sum()) - expected)
                        self.assertEqual(old.fn, int(gt.sum()) - expected)

    def test_threshold_prepared_reference_matches_uncached_oracle(self):
        from src.stage24_recertification_ops import canonical_threshold_candidates
        from src.stage24_integrity import aggregate_counts
        rng = np.random.default_rng(17)
        gts = [rng.random((15, 17)) < .18 for _ in range(3)]
        scores = [rng.random((15, 17)).astype(np.float32) for _ in range(3)]
        images = [np.zeros((15, 17), dtype=np.float32) for _ in range(3)]
        candidates = [float(t) for t in canonical_threshold_candidates(scores, count=9)
                      if t > 1e-7]
        if not candidates:
            candidates = [.5]
        old = []
        for threshold in candidates:
            counts = aggregate_counts([
                one_to_one_boundary_counts(score >= threshold, gt)
                for score, gt in zip(scores, gts)
            ])
            old.append(((counts.f1, counts.precision, counts.recall, threshold),
                        counts, threshold))
        oracle = max(old, key=lambda item: item[0])
        steps = []
        selected, counts = choose_threshold(scores, gts, images, "raw", count=9,
                                            progress=lambda done, total: steps.append((done, total)))
        self.assertEqual(selected, oracle[2])
        self.assertEqual(counts, oracle[1])
        self.assertEqual(steps[0][0], 0)
        self.assertEqual(steps[-1], (len(candidates), len(candidates)))

    def test_parallel_threshold_search_is_identical_to_serial(self):
        import os
        rng = np.random.default_rng(921)
        gts = [rng.random((31, 28)) < .2 for _ in range(4)]
        images = [rng.random((31, 28)).astype(np.float32) for _ in range(4)]
        scores = [rng.random((31, 28)).astype(np.float32) for _ in range(4)]
        from unittest.mock import patch
        for mode in ("raw", "nms_image"):
            with patch.dict(os.environ, {"STAGE24GL_MATCH_WORKERS": "1"}):
                a = choose_threshold(scores, gts, images, mode, count=11)
            with patch.dict(os.environ, {"STAGE24GL_MATCH_WORKERS": "4"}):
                b = choose_threshold(scores, gts, images, mode, count=11)
            self.assertEqual(a, b)
        with patch.dict(os.environ, {"STAGE24GL_MATCH_WORKERS": "0"}):
            with self.assertRaises(ValueError):
                choose_threshold(scores, gts, images, "raw", count=3)

    def test_individual_descriptor_parts_resume_without_recomputation(self):
        import src.stage24_recertification_cv as cv
        gt = np.zeros((13, 13), dtype=bool)
        gt[6, 3:11] = True
        score = gt.astype(np.float32) * .8 + .1
        image = np.tile(np.arange(13, dtype=np.float32), (13, 1))
        items = [{"id": str(j), "gt": gt.copy(), "img": image.copy()}
                 for j in range(3)]
        maps = {"toy": [score.copy() for _ in items]}
        counts = one_to_one_boundary_counts(score >= .5, gt, tolerance_px=0)
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(cv, "DESCRIPTOR_IDS", ("toy",)), \
                 patch.object(cv, "fit_membership", return_value=object()), \
                 patch.object(cv, "apply_membership",
                              side_effect=lambda cues, model: cues[0][..., None]), \
                 patch.object(cv, "choose_threshold", return_value=(.5, counts)):
                first = cv.individual_descriptor_baselines(
                    items, maps, [0, 1], [2], "r1_f1",
                    checkpoint_dir=directory, count=5,
                )
                self.assertEqual(len(first[0]), 2)
                self.assertEqual(len(list(Path(directory).glob("*.json"))), 2)
                with patch.object(cv, "choose_threshold",
                                  side_effect=AssertionError("should use checkpoint")):
                    resumed = cv.individual_descriptor_baselines(
                        items, maps, [0, 1], [2], "r1_f1",
                        checkpoint_dir=directory, count=5,
                    )
                self.assertEqual(first, resumed)
                with self.assertRaises(RuntimeError):
                    cv.individual_descriptor_baselines(
                        items, maps, [0, 1], [2], "r1_f1",
                        checkpoint_dir=directory, count=7,
                    )

    def test_group_piece_is_signature_guarded(self):
        from src.stage24_recertification_cv import _checkpoint_piece
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.json"
            spec = {"signature": "approved", "fold": "r1_f1"}
            self.assertEqual(_checkpoint_piece(path, spec, lambda: {"count": 2}),
                             {"count": 2})
            self.assertEqual(_checkpoint_piece(path, spec,
                             lambda: (_ for _ in ()).throw(AssertionError("recalculated"))),
                             {"count": 2})
            with self.assertRaises(RuntimeError):
                _checkpoint_piece(path, {"signature": "other"},
                                  lambda: {"count": 9})


if __name__=="__main__":
    unittest.main()
