from __future__ import annotations
import numpy as np
from scipy import ndimage as ndi

EPS=1e-12

def tolerant_counts(pred, gt, tol=2):
    pred=np.asarray(pred,bool); gt=np.asarray(gt,bool)
    if tol>0:
        base=ndi.generate_binary_structure(2,1)
        dp=ndi.binary_dilation(pred,structure=base,iterations=int(tol))
        dg=ndi.binary_dilation(gt,structure=base,iterations=int(tol))
    else:
        dp,dg=pred,gt
    return int(np.logical_and(pred,dg).sum()), int(pred.sum()), int(np.logical_and(gt,dp).sum()), int(gt.sum())

def counts_to_prf(mp,npred,mg,ngt,beta=1.0):
    p=mp/max(npred,1); r=mg/max(ngt,1); b2=beta*beta
    f=(1+b2)*p*r/max(b2*p+r,EPS)
    return float(p),float(r),float(f)

def tolerant_prf(pred,gt,tol=2,beta=1.0):
    return counts_to_prf(*tolerant_counts(pred,gt,tol),beta=beta)

def _thresholds_from_scores(scores,n=99):
    vals=np.concatenate([np.asarray(s,float)[np.isfinite(s)].ravel() for s in scores])
    if vals.size==0:
        return np.array([0.0])
    return np.unique(np.quantile(vals,np.linspace(0.01,0.995,n)))

def _prepared_threshold_counts(score,gt,tol=2):
    """Precompute exact equivalents of the prototype dilation-based tolerant counts."""
    score=np.asarray(score,float); gt=np.asarray(gt,bool)
    finite=np.isfinite(score)
    all_scores=np.sort(score[finite].ravel())
    if tol>0:
        base=ndi.generate_binary_structure(2,1)
        dg=ndi.binary_dilation(gt,structure=base,iterations=int(tol))
        footprint=ndi.iterate_structure(base,int(tol))
        near_max=ndi.maximum_filter(np.where(finite,score,-np.inf),footprint=footprint,
                                    mode="constant",cval=-np.inf)
    else:
        dg=gt; near_max=score
    correct_scores=np.sort(score[finite & dg].ravel())
    gtmax_scores=np.sort(near_max[gt & np.isfinite(near_max)].ravel())
    return all_scores,correct_scores,gtmax_scores,int(gt.sum())

def _count_ge(sorted_vals,thresholds):
    if sorted_vals.size==0:
        return np.zeros(len(thresholds),dtype=np.int64)
    return sorted_vals.size-np.searchsorted(sorted_vals,thresholds,side="left")

def pr_curve(scores,gts,tol=2,n_thresholds=99,beta=1.0):
    thresholds=_thresholds_from_scores(scores,n_thresholds)
    mp=np.zeros(len(thresholds),dtype=np.int64)
    npred=np.zeros(len(thresholds),dtype=np.int64)
    mg=np.zeros(len(thresholds),dtype=np.int64)
    ngt=0
    for score,gt in zip(scores,gts):
        all_s,corr_s,gtmax_s,n_gt=_prepared_threshold_counts(score,gt,tol)
        npred += _count_ge(all_s,thresholds)
        mp += _count_ge(corr_s,thresholds)
        mg += _count_ge(gtmax_s,thresholds)
        ngt += n_gt
    p=mp/np.maximum(npred,1); r=mg/max(ngt,1); b2=beta*beta
    f=(1+b2)*p*r/np.maximum(b2*p+r,EPS)
    return np.column_stack([thresholds,p,r,f]).astype(float)

def average_precision_from_pr(precision,recall):
    order=np.argsort(recall)
    r=np.asarray(recall)[order]; p=np.asarray(precision)[order]
    p=np.maximum.accumulate(p[::-1])[::-1]
    r=np.concatenate([[0.0],r,[1.0]])
    p=np.concatenate([[p[0] if p.size else 0.0],p,[0.0]])
    return float(np.trapezoid(p,r))

def roc_auc(scores,gts):
    y=np.concatenate([np.asarray(g,bool).ravel() for g in gts]).astype(np.uint8)
    s=np.concatenate([np.asarray(x,float).ravel() for x in scores])
    pos=s[y==1]; neg=s[y==0]
    if pos.size==0 or neg.size==0:
        return float("nan")
    from scipy.stats import rankdata
    ranks=rankdata(np.concatenate([pos,neg]),method="average")
    rpos=ranks[:pos.size].sum()
    return float((rpos-pos.size*(pos.size+1)/2.0)/(pos.size*neg.size))

def benchmark_metrics(scores,gts,tol=2,n_thresholds=99,beta=1.0):
    curve=pr_curve(scores,gts,tol=tol,n_thresholds=n_thresholds,beta=beta)
    bi=int(np.nanargmax(curve[:,3]))
    ods_t,ods_p,ods_r,ods=curve[bi]
    image_best=[]
    for s,g in zip(scores,gts):
        c=pr_curve([s],[g],tol=tol,n_thresholds=n_thresholds,beta=beta)
        image_best.append(float(np.max(c[:,3])))
    ap=average_precision_from_pr(curve[:,1],curve[:,2])
    eligible=curve[:,1]>=0.5
    r50=float(np.max(curve[eligible,2])) if np.any(eligible) else 0.0
    return {
        "ODS":float(ods),"ODS_threshold":float(ods_t),
        "ODS_precision":float(ods_p),"ODS_recall":float(ods_r),
        "OIS":float(np.mean(image_best)),"AP":ap,"R50":r50,
        "ROC_AUC":roc_auc(scores,gts),"curve":curve,
    }

def best_f1(score,gt,tol=2,n=60):
    m=benchmark_metrics([score],[gt],tol=tol,n_thresholds=n)
    return {"F1":m["ODS"],"threshold":m["ODS_threshold"],
            "precision":m["ODS_precision"],"recall":m["ODS_recall"]}
