
from __future__ import annotations
import numpy as np
from scipy import ndimage as ndi
from dataclasses import dataclass
from .features import extract_features
from .operators import FUNCTIONS, cf_integral, cc_integral, cf1f2_integral

@dataclass
class ScaleResult:
    window:int
    raw:np.ndarray
    bits:np.ndarray
    active:np.ndarray
    heterogeneity:np.ndarray

def empirical_surprisal(raw, background_mask=None, eps=1e-9, max_samples=250000, seed=0):
    raw=np.asarray(raw,dtype=float)
    if background_mask is None:
        cutoff=np.quantile(raw,0.60)
        background_mask=raw<=cutoff
    vals=raw[background_mask & np.isfinite(raw)]
    if vals.size<100:
        vals=raw[np.isfinite(raw)].ravel()
    if vals.size>max_samples:
        rng=np.random.default_rng(seed)
        vals=rng.choice(vals,size=max_samples,replace=False)
    vals=np.sort(vals)
    flat=raw.ravel()
    idx=np.searchsorted(vals,flat,side="left")
    tail=(len(vals)-idx+1)/(len(vals)+1.0)
    bits=-np.log2(np.maximum(tail,eps))
    return bits.reshape(raw.shape)

def aggregate_features(X, family="CF1F2", F="TP", F1="TP", F2="TL", q=0.1):
    if family.upper()=="CF":
        return cf_integral(X,FUNCTIONS[F],q=q)
    if family.upper()=="CC":
        return cc_integral(X,FUNCTIONS[F],q=q)
    if family.upper()=="CF1F2":
        return cf1f2_integral(X,FUNCTIONS[F1],FUNCTIONS[F2],q=q)
    raise ValueError(f"Unknown family: {family}")

def precompute_multiscale_features(img, scales=(33,17,9)):
    out=[]
    names=None
    for w in scales:
        X,names,hetero=extract_features(img,int(w))
        out.append((int(w),X,hetero))
    return out,names

def multiscale_from_precomputed(precomputed, image_shape, family="CF1F2", F="TP", F1="TP", F2="TL",
                                q=0.1, refine_quantile=0.82, heterogeneity_quantile=0.82,
                                dilation_radius=3, eps=1e-9):
    results=[]
    active=np.ones(image_shape,dtype=bool)
    struct=ndi.generate_binary_structure(2,1)
    scales=[w for w,_,_ in precomputed]
    for k,(w,X,hetero) in enumerate(precomputed):
        raw=aggregate_features(X,family=family,F=F,F1=F1,F2=F2,q=q)
        bits=empirical_surprisal(raw,eps=eps)
        if k>0:
            bits=np.where(active,bits,0.0)
            raw=np.where(active,raw,0.0)
        if active.any():
            hot = bits >= np.quantile(bits[active],refine_quantile)
            hetero_thr=np.quantile(hetero[active],heterogeneity_quantile)
        else:
            hot=np.zeros_like(active)
            hetero_thr=1.0
        hetero_hot=hetero>=hetero_thr
        next_active=(hot | hetero_hot) & active
        if dilation_radius>0:
            next_active=ndi.binary_dilation(next_active,structure=struct,iterations=dilation_radius)
        results.append(ScaleResult(int(w),raw,bits,next_active,hetero))
        active=next_active
    stack=np.stack([r.bits for r in results],axis=-1)
    final_bits=np.max(stack,axis=-1)
    best_scale_idx=np.argmax(stack,axis=-1)
    best_scale=np.take(np.asarray(scales),best_scale_idx)
    return results, final_bits, best_scale

def multiscale_detect(img, scales=(33,17,9), family="CF1F2", F="TP", F1="TP", F2="TL",
                      q=0.1, refine_quantile=0.82, heterogeneity_quantile=0.82,
                      dilation_radius=3, eps=1e-9):
    pre,names=precompute_multiscale_features(img,scales)
    results,final_bits,best_scale=multiscale_from_precomputed(
        pre,np.asarray(img).shape[:2],family=family,F=F,F1=F1,F2=F2,q=q,
        refine_quantile=refine_quantile,
        heterogeneity_quantile=heterogeneity_quantile,
        dilation_radius=dilation_radius,eps=eps)
    return results,final_bits,best_scale,names
