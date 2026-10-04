
from __future__ import annotations
import numpy as np
from scipy import ndimage as ndi

def tolerant_prf(pred, gt, tol=2):
    pred=np.asarray(pred,bool); gt=np.asarray(gt,bool)
    if tol>0:
        dp=ndi.binary_dilation(pred,iterations=tol)
        dg=ndi.binary_dilation(gt,iterations=tol)
    else: dp,dg=pred,gt
    tp_p=np.logical_and(pred,dg).sum()
    tp_r=np.logical_and(gt,dp).sum()
    p=tp_p/max(pred.sum(),1)
    r=tp_r/max(gt.sum(),1)
    f=2*p*r/max(p+r,1e-12)
    return float(p),float(r),float(f)

def best_f1(score, gt, tol=2, n=60):
    vals=score[np.isfinite(score)]
    qs=np.linspace(0.50,0.995,n)
    best=(-1,None,None,None)
    for q in qs:
        t=float(np.quantile(vals,q))
        p,r,f=tolerant_prf(score>=t,gt,tol)
        if f>best[0]: best=(f,t,p,r)
    f,t,p,r=best
    return {"F1":f,"threshold":t,"precision":p,"recall":r}
