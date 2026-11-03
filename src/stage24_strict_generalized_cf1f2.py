from __future__ import annotations
"""Generalized gC(F1,F2) equation (9) with dimension reduction on ties.

Dimuro et al., Fuzzy Sets and Systems 378 (2020), 44-67, Definition 4.2:
  min(1, sum_{j=1}^k F1(y_j, mu(B_j)) - F2(y_{j-1},mu(B_j)))
with y_0=0, y_j DISTINCT increasing input values, and
B_j = {criterion index i: x_i >= y_j}.

This is separate from the historical prototype's x_(1) shortcut and
from quasi-arithmetic Choquet operators. Do NOT conflate the families.
"""
import numpy as np
from src.operators import FUNCTIONS

VALID_PAIRS = {
    "gcf_tp_tp": ("TP","TP"),
    "gcf_cl_cl": ("CL","CL"),
    "gcf_tp_tl": ("TP","TL"),
    "gcf_tm_fna": ("TM","FNA"),
    "gcf_gm_gm": ("GM","GM"),
}


def check_pseudo_pair(f1, f2, grid=101, tol=1e-9):
    """Numeric screening, not a formal proof of (DI, BC0, BC1, DM)."""
    t=np.linspace(0,1,grid,dtype=float)
    xx,yy=np.meshgrid(t,t,indexing="ij")
    a=np.asarray(f1(xx,yy))
    b=np.asarray(f2(xx,yy))
    checks={
        "f1_first_increasing":bool(np.all(np.diff(a,axis=0)>=-tol)),
        "f1_dominates_f2":bool(np.all(a+tol>=b)),
        "zero_agreement":bool(np.allclose(a[0,:],b[0,:],atol=tol)),
        "zero_at_mu_N":bool(abs(float(f1(0,1)))<tol),
        "one_at_mu_N":bool(abs(float(f1(1,1))-1)<tol),
    }
    return checks


def generalized_cf1f2(x, capacity, f1, f2):
    """Correct gCF1F2 with tie-reduced tails and explicit baseline F2(0,mu(N)).

    Shape (...,n) -> (...). Supports n in [1,3] so pair/triple capacities
    remain directly inspectable. Does not assert a pseudo-pair theorem for an
    arbitrary supplied F1,F2; callers must check their formal admissibility.
    """
    m=np.asarray(x,dtype=float)
    if m.ndim<1 or m.shape[-1]<1 or m.shape[-1]>3:
        raise ValueError("Only 1-3 descriptor inputs supported")
    n=m.shape[-1]
    cap=np.asarray(capacity,dtype=float)
    if cap.shape!=(1<<n,) or not np.all(np.isfinite(cap)):
        raise ValueError("Capacity size/finite contract mismatch")
    if abs(cap[0])>1e-8 or abs(cap[-1]-1)>1e-8:
        raise ValueError("Capacity not normalized")
    for mask in range(1<<n):
        for j in range(n):
            if not mask&(1<<j) and cap[mask|(1<<j)]+1e-8<cap[mask]:
                raise ValueError("Capacity is not monotone")
    if not np.isfinite(m).all() or np.min(m)<-1e-7 or np.max(m)>1+1e-7:
        raise ValueError("Inputs outside unit interval")
    order=np.argsort(m,axis=-1,kind="stable")
    sorted_x=np.take_along_axis(m,order,axis=-1)
    out=np.zeros(m.shape[:-1],dtype=np.float64)
    for j in range(n):
        # FIRST index of each run of tied values. All tied criteria are in
        # its tail set, making the formula invariant to tie permutations.
        if j==0:
            active=np.ones_like(out,dtype=bool)
            prev=np.zeros_like(out)
        else:
            active=sorted_x[...,j]>sorted_x[...,j-1]
            prev=sorted_x[...,j-1]
        mask=np.zeros(m.shape[:-1],dtype=np.int32)
        for k in range(j,n):
            mask|=1<<order[...,k]
        mu=cap[mask]
        term=np.asarray(f1(sorted_x[...,j],mu),float)-np.asarray(f2(prev,mu),float)
        out+=np.where(active,term,0.)
    if np.min(out)<-1e-6 or not np.isfinite(out).all():
        raise RuntimeError("Generalized integral violated lower bound")
    return np.asarray(np.minimum(1.,np.maximum(0.,out)),dtype=np.float32)


def apply_registered_gcf(membership_map, capacity, operator):
    if operator not in VALID_PAIRS:
        raise KeyError(operator)
    f1,f2=(FUNCTIONS[name] for name in VALID_PAIRS[operator])
    return generalized_cf1f2(membership_map,capacity,f1,f2)


def synthetic_contract():
    for key,pair in VALID_PAIRS.items():
        f1,f2=(FUNCTIONS[k] for k in pair)
        chk=check_pseudo_pair(f1,f2,grid=51)
        if not all(chk.values()):
            return {"passed":False,"pair":key,"checks":chk}
    # Same input x, different tie permutations must be identical.
    cap=np.array([0,.2,.3,.65,.4,.7,.8,1.],float)
    a=np.array([.4,.4,.8])
    b=np.array([.4,.8,.4])
    for key in VALID_PAIRS:
        aa=apply_registered_gcf(a,cap,key)
        bb=apply_registered_gcf(b,cap,key)
        # Relabeling criteria requires relabeling capacity too; for the
        # symmetric equality test use a symmetric capacity instead.
        sym=np.array([0,1/3,1/3,2/3,1/3,2/3,2/3,1.])
        aa=apply_registered_gcf(a,sym,key)
        bb=apply_registered_gcf(b,sym,key)
        if not np.allclose(aa,bb,atol=1e-6):
            return {"passed":False,"reason":"tie permutation", "pair":key}
    # Explicit n=1 GM reveals the historical x_(1) shortcut error.
    val=float(apply_registered_gcf(np.array([.25]),np.array([0.,1.]),"gcf_gm_gm"))
    if abs(val-.5)>1e-6:
        return {"passed":False,"reason":"GM baseline not respected","observed":val}
    return {"passed":True,"pairs":list(VALID_PAIRS)}
