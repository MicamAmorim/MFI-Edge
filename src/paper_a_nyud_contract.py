"""Prospective supplied NYUD object-boundary reference, no file I/O.

Accept the authors' exact native benchmarkData groundTruth.Boundaries only.
No GT resizing, label-derived substitution or ignore-mask invention.
It is one provided reference mask, not four independent annotators.
Caller must prove independent freeze before passing candidate MAT payloads.
"""
from __future__ import annotations
import io
import numpy as np
from scipy.io import loadmat
from src.paper_a_confirmation_paired_f1 import PairedF1,_bool_map,TOLERANCE_RATIO
from src.stage24_integrity import one_to_one_boundary_counts
def decode_nyud_boundaries(payload:bytes,native:tuple[int,int])->tuple[np.ndarray,...]:
    if not isinstance(payload,bytes) or not 0<len(payload)<=20_000_000:raise ValueError('Expected bounded MAT payload')
    mat=loadmat(io.BytesIO(payload),squeeze_me=True,struct_as_record=False)
    gt=mat.get('groundTruth')
    if not hasattr(gt,'Boundaries'):raise ValueError('Expected exactly one supplied NYUD groundTruth struct')
    a=gt.Boundaries
    if hasattr(a,'toarray'):a=a.toarray()
    a=np.asarray(a)
    if a.dtype!=np.uint8 or a.ndim!=2 or a.shape!=tuple(native) or tuple(native)!=(425,560):raise ValueError('Exact native 425x560 uint8 reference required')
    if not set(np.unique(a).tolist()).issubset({0,1}) or not a.any() or a.all():raise ValueError('Expected nondegenerate exact binary 0/1 Boundaries')
    return (a.astype(bool),)
def evaluate_nyud_paired_binary(candidate,control,annotations)->PairedF1:
    if not isinstance(annotations,(list,tuple)) or len(annotations)!=1:raise ValueError('Exactly one provided NYUD reference required')
    p=_bool_map(candidate,'candidate');c=_bool_map(control,'control');g=_bool_map(annotations[0],'annotation')
    if p.shape!=c.shape or p.shape!=g.shape or not g.any() or g.all():raise ValueError('Invalid native NYUD mask geometry/content')
    cf=float(one_to_one_boundary_counts(p,g,tolerance_ratio=TOLERANCE_RATIO).f1);bf=float(one_to_one_boundary_counts(c,g,tolerance_ratio=TOLERANCE_RATIO).f1)
    return PairedF1('NYUDv2',1,(cf,),(bf,),cf,bf,cf-bf)
