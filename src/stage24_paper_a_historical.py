from __future__ import annotations
"""Re-apply the EXACT Stage23D complementarity SCORE formula train-only.

This is a historical-measure diagnostic, not a corrected Berkeley metric.
Old Stage23D thresholds/GT geometry differed. We hold threshold values fixed
between geometry variants to isolate, as far as possible, representation effects.
"""
from itertools import combinations
import math
import numpy as np
from skimage.transform import resize
from scipy.stats import rankdata

from run_stage23d_cached_complementarity_map import (
    FAMILIES, _pair_masks, _corr,
)
from src.stage24_recertification_ops import choose_threshold
from src.stage24_integrity import tolerance_pixels


def _stage23d_formula(metrics,mean_spearman,family_a,family_b):
    redundancy=min(abs(float(mean_spearman)),1.)
    unique_gt=np.clip(metrics["unique_gt_a"]+metrics["unique_gt_b"],0.,1.)
    conditional=np.clip(.5*(metrics["p_a_correct_given_b_wrong"]+
                            metrics["p_b_correct_given_a_wrong"]),0.,1.)
    unique_fp=np.clip(.5*(metrics["unique_fp_a"]+metrics["unique_fp_b"]),0.,1.)
    stability=float(metrics["bilateral_unique_stability"])
    score=float(.25*(1.-redundancy)+.25*unique_gt+
                .20*conditional+.15*stability+.15*(1.-unique_fp))
    eligible=(family_a!=family_b and redundancy<=.95)
    return score,eligible


def historical_score_comparison(items,maps,train,fold,groups):
    """Compare SAME Stage23D score implementation under two GT geometries.

    Train-only thresholds are calibrated with the current one-to-one matcher
    at NATIVE GT, reused unchanged for legacy-resized variant.
    Hence the delta is not a causal GT-only effect: cue resampling changes too.
    """
    gts=[np.asarray(x["gt"],bool) for x in items]
    raw_shapes=[x["inference_img"].shape[:2] for x in items]
    seen=sorted({d for group in groups for d in group})
    images=[x["img"] for x in items]
    thresholds={}
    down={}
    reduced_gts=[resize(g.astype(np.uint8),shape,order=0,
                        anti_aliasing=False,preserve_range=True)>.5
                 for g,shape in zip(gts,raw_shapes)]
    for d in seen:
        t,_=choose_threshold([maps[d][int(i)] for i in train],
                             [gts[int(i)] for i in train],
                             [images[int(i)] for i in train],
                             "raw",count=21)
        thresholds[d]=t
        down[d]=[resize(np.asarray(v,np.float32),shape,order=1,
                        anti_aliasing=True,preserve_range=True)
                 for v,shape in zip(maps[d],raw_shapes)]
    rows=[]
    for group in groups:
        a,b=sorted(group)
        for geometry in ("native_GT","legacy_resized_GT_and_evidence"):
            data=[]
            vals=[]
            for k in train:
                i=int(k)
                gt=gts[i] if geometry=="native_GT" else reduced_gts[i]
                src=maps if geometry=="native_GT" else down
                aa,bb=np.asarray(src[a][i]),np.asarray(src[b][i])
                pred_a=aa>=thresholds[a];pred_b=bb>=thresholds[b]
                component=_pair_masks(pred_a,pred_b,gt,tolerance_pixels(gt.shape))
                component["bilateral_unique_stability"]=float(
                    component["unique_gt_a"]>0 and component["unique_gt_b"]>0)
                data.append(component)
                vals.append(_corr(aa,bb)[1])
            mean={col:float(np.mean([r[col] for r in data])) for col in data[0]}
            score,eligible=_stage23d_formula(mean,float(np.mean(vals)),
                                             FAMILIES[a],FAMILIES[b])
            rows.append({"fold":fold,"a":a,"b":b,"geometry":geometry,
                         "score_stage23d_exact_formula":score,
                         "eligible":eligible,"threshold_a_native_fit":thresholds[a],
                         "threshold_b_native_fit":thresholds[b],
                         "mean_spearman":float(np.mean(vals)),
                         "matched_training_images":len(train),
                         "scientific_caution":"same historical score coefficients but legacy resize alters evidence; not isolated causal GT effect"})
    return rows


def synthetic_contract():
    r={"unique_gt_a":.2,"unique_gt_b":.1,
       "p_a_correct_given_b_wrong":.8,"p_b_correct_given_a_wrong":.6,
       "unique_fp_a":.1,"unique_fp_b":.2,
       "bilateral_unique_stability":.75}
    score,elig=_stage23d_formula(r,.3,"curvature","texture")
    return elig and 0<=score<=1
