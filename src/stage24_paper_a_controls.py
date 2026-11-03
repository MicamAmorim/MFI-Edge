from __future__ import annotations
"""Low-cost controls, descriptive variance and rank-equivalence diagnostics.

All baselines are computed at held-out evaluation time; any selected parameter
comes from train fold only. Group-level statistics are descriptive because the
same 14 images appear in repeated folds.
"""
from collections import defaultdict
import csv
import json
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr

from src.stage24_integrity import (
    one_to_one_boundary_counts, aggregate_counts,
)
from src.stage24_recertification_cv import write_csv, memberships_on_split
from src.stage24_recertification_ops import fit_aggregator,apply_aggregator
from src.stage24_recertification_ops import deterministic_seed


def null_and_random_controls(items, train, valid, fold, *, seed=20261104):
    """Full-positive is evaluated exactly analytically; random uses native matcher.

    Random positive density is fixed from the TRAIN GT only. Do not use heldout
    GT support for probability; that would make a trivial control an oracle.
    """
    densities=[float(np.mean(items[int(i)]["gt"])) for i in train]
    d=float(np.mean(densities))
    rows=[]
    for i in valid:
        im=items[int(i)]
        gt=np.asarray(im["gt"],bool)
        N=gt.size;G=int(np.count_nonzero(gt))
        for name,tp,fp,fn,n_pred,status in (
            ("empty",0,0,G,0,"exact_analytic"),
            ("full_image",G,N-G,0,N,"exact_analytic"),
        ):
            p=tp/n_pred if n_pred else 0.
            r=tp/G if G else 1.
            f=(2*p*r/(p+r)) if p+r else 0.
            rows.append({"fold":fold,"image_id":im["id"],
                         "baseline":name,"train_GT_density":d,
                         "tp":tp,"fp":fp,"fn":fn,"precision":p,
                         "recall":r,"F1":f,"status":status})
        rng=np.random.default_rng(deterministic_seed(seed,fold,im["id"]))
        # Limiting random density would invalidate the same-density control.
        # Reject instead of hiding an approximation.
        if int(N*d)>40000:
            rows.append({"fold":fold,"image_id":im["id"],"baseline":"random_same_train_GT_density",
                         "train_GT_density":d,"status":"BLOCKED_OVER_40000_PREDICTIONS"})
        else:
            pred=rng.random(gt.shape)<d
            c=one_to_one_boundary_counts(pred,gt)
            rows.append({"fold":fold,"image_id":im["id"],"baseline":"random_same_train_GT_density",
                         "train_GT_density":d,"tp":c.tp,"fp":c.fp,"fn":c.fn,
                         "precision":c.precision,"recall":c.recall,"F1":c.f1,
                         "status":"one_to_one_native"})
    return rows


def rank_equivalence_on_uded(items,maps,train,valid,fold):
    """Logistic vs nonnegative weighted sum: exact order for same weights."""
    from src.stage24_recertification_cv import clear_group_cache
    from scipy.special import expit
    pair=("gabor4_scale_persistence","halfdisc_distribution_contrast")
    gts=[item["gt"] for item in items]
    mem,ms=memberships_on_split(pair,maps,gts,train)
    model=fit_aggregator("nonnegative_logistic",ms,gts,train,
                          seed=deterministic_seed("rank",fold))
    beta=np.asarray(model["logistic"]["beta"],float)
    nonnegative=np.maximum(beta[1:],0)
    if nonnegative.sum()<=1e-12:
        return [{"fold":fold,"status":"DEGENERATE_ZERO_COEFFICIENTS"}]
    w=nonnegative/nonnegative.sum()
    out=[]
    for i in valid:
        ii=int(i)
        m=np.asarray(ms[ii],float)
        rng=np.random.default_rng(deterministic_seed("rank",fold,items[ii]["id"]))
        n=min(100000,m.shape[0]*m.shape[1])
        ix=rng.choice(m.shape[0]*m.shape[1],size=n,replace=False)
        x=m.reshape(-1,m.shape[-1])[ix]
        log=expit(beta[0]+x@nonnegative)
        weighted=x@w
        # Non-strict correlation near ties due to 32-bit scoring is reported.
        rho=float(spearmanr(log,weighted).statistic)
        out.append({"fold":fold,"image_id":items[ii]["id"],
                    "pair":"|".join(pair),"beta0":float(beta[0]),
                    "weights":"|".join(map(str,w)),
                    "spearman_equal_ranking":rho,"pixels_sampled":int(n),
                    "status":"exploratory_rank_equivalence"})
    return out


def select_best_single(rows,details):
    """Select best single on TRAIN only; never maximize the heldout F1."""
    byfold=defaultdict(list)
    for row in rows:
        if row["train_F1"] is None:continue
        byfold[row["fold"]].append(row)
    chosen={}
    for fold,rr in byfold.items():
        if rr:
            chosen[fold]=sorted(rr,key=lambda z:(-float(z["train_F1"]),
                          z["descriptor_id"],z["thinning"]))[0]
    table=[{"fold":fold,**choice} for fold,choice in chosen.items()]
    images=[{"fold":r["fold"],**r} for r in details if
            r["fold"] in chosen and
            r["descriptor_id"]==chosen[r["fold"]]["descriptor_id"] and
            r["thinning"]==chosen[r["fold"]]["thinning"]]
    return table,images


def variance_decomposition(landscape, mode="raw"):
    """Balanced 2-way sum-of-squares: group, aggregator, interaction.

    Uses mean heldout F1 across repeated splits for each group-operator cell.
    This is a descriptive decomposition, not an independent-sample ANOVA.
    """
    by=defaultdict(list)
    for r in landscape:
        if r.get("thinning")!=mode or r.get("suppressor")!="identity":
            continue
        if r.get("validation_F1") is None:continue
        by[(r["group"],r["aggregator"])].append(float(r["validation_F1"]))
    groups=sorted({k[0] for k in by})
    aggs=sorted({k[1] for k in by})
    if len(groups)<2 or len(aggs)<2:return {"status":"insufficient_cells"}
    # Intersection to avoid silently filling missing group-aggregator cells.
    groups=[g for g in groups if all((g,a) in by for a in aggs)]
    if len(groups)<2:return {"status":"incomplete_factorial"}
    matrix=np.asarray([[np.mean(by[(g,a)]) for a in aggs] for g in groups],float)
    grand=float(np.mean(matrix))
    g_means=matrix.mean(axis=1);a_means=matrix.mean(axis=0)
    ss_g=float(len(aggs)*np.sum((g_means-grand)**2))
    ss_a=float(len(groups)*np.sum((a_means-grand)**2))
    ss_i=float(np.sum((matrix-g_means[:,None]-a_means[None,:]+grand)**2))
    total=ss_g+ss_a+ss_i
    if total==0:return {"status":"zero_variance"}
    return {"status":"descriptive_only","n_groups":len(groups),
            "n_aggregators":len(aggs),
            "fraction_group":ss_g/total,
            "fraction_aggregator":ss_a/total,
            "fraction_interaction":ss_i/total,
            "note":"No inference from folds treated as independent; repeated-image analysis"}


def complementarity_predictive_test(pair_screens,landscape,replicates=2000):
    """Exploratory Spearman with permutation across unique PAIRS."""
    grouped=defaultdict(list); controls=defaultdict(list)
    for r in pair_screens:
        grouped["|".join(sorted((r["a"],r["b"])))].append(float(r["score"]))
    for r in landscape:
        if r.get("arity")!=2 or r.get("thinning")!="raw":
            continue
        if r.get("validation_F1") is None or r.get("suppressor")!="identity":
            continue
        k="|".join(sorted(r["group"].split("|")))
        controls[(k,r["aggregator"])].append(float(r["validation_F1"]))
    observations=[]
    for group,vals in grouped.items():
        mean=controls.get((group,"equal_mean"),[])
        variants=[np.mean(v) for (k,agg),v in controls.items()
                  if k==group and agg!="equal_mean"]
        if not mean or not variants:continue
        observations.append((group,float(np.mean(vals)),
                            float(max(variants)-np.mean(mean)),
                            float(np.mean(mean))))
    if len(observations)<6:
        return {"status":"insufficient_distinct_pairs","n":len(observations)}
    x=np.asarray([a[1] for a in observations])
    y=np.asarray([a[2] for a in observations])
    rho=float(spearmanr(x,y).statistic)
    rng=np.random.default_rng(20261104)
    perm=np.array([spearmanr(x,rng.permutation(y)).statistic for _ in range(replicates)])
    p=float((1+np.count_nonzero(np.abs(perm)>=abs(rho)))/(1+replicates))
    return {"status":"exploratory","n_distinct_pairs":len(observations),
            "spearman":rho,"permutation_p":p,
            "sampling_unit":"pair; rank and gains share UDED data, not independent confirmation",
            "rows":[{"pair":a,"score_mean":b,"max_gain_vs_mean":c,
                     "mean_control_F1":d} for a,b,c,d in observations]}


def scale_audit(items, maxside=256):
    rows=[]
    for item in items:
        h,w=item["gt"].shape
        ih,iw=item["inference_img"].shape[:2]
        rows.append({"image_id":item["id"],"native_h":h,"native_w":w,
                     "inference_h":ih,"inference_w":iw,
                     "pixel_scale_factor":float(np.hypot(h,w)/np.hypot(ih,iw)),
                     "physical_window_25px_at_native_equivalent":
                         float(25*np.hypot(h,w)/np.hypot(ih,iw)),
                     "status":"documented_scaled_implementation_not_native_recomputed"})
    return rows
