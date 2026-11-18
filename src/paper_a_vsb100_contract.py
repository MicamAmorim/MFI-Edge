"""Prospective VSB100 annotation adapter, not a freeze authorization.

Caller must pass bytes only AFTER an independently reviewed prospective
freeze, except the expressly excluded training video used for format QA.
This module has no file I/O and does not fit, resize, merge or threshold GT.
The full-frame General benchmark is perceptual segmentation boundaries;
its four references do not increase the number of scene observations.
"""
from __future__ import annotations
import io
import numpy as np
from scipy.io import loadmat
from src.paper_a_confirmation_paired_f1 import PairedF1, _bool_map, TOLERANCE_RATIO
from src.stage24_integrity import one_to_one_boundary_counts

def decode_vsb100_boundaries(payload: bytes, native: tuple[int,int]) -> tuple[np.ndarray,...]:
    if not isinstance(payload,bytes) or not 0<len(payload)<=20_000_000:
        raise ValueError('Expected bounded lossless MAT annotation bytes')
    mat=loadmat(io.BytesIO(payload),squeeze_me=True,struct_as_record=False)
    if 'groundTruth' not in mat:
        raise ValueError('Missing VSB100 groundTruth')
    refs=np.asarray(mat['groundTruth'],dtype=object).ravel()
    if len(refs)!=4:
        raise ValueError('Exactly four VSB100 annotators are required')
    decoded=[]
    for ref in refs:
        if not hasattr(ref,'Boundaries'):
            raise ValueError('Missing annotated Boundaries; never derive them from labels')
        arr=ref.Boundaries
        if hasattr(arr,'toarray'):arr=arr.toarray()
        arr=np.asarray(arr)
        if arr.dtype!=np.uint8 or arr.ndim!=2 or arr.shape!=tuple(native):
            raise ValueError('Expected native uint8 2-D annotation; no GT resize')
        if not set(np.unique(arr).tolist()).issubset({0,1}) or not arr.any() or arr.all():
            raise ValueError('Expected nondegenerate exact binary {0,1} Boundaries')
        decoded.append(arr.astype(bool))
    return tuple(decoded)

def evaluate_vsb100_paired_binary(candidate:np.ndarray,control:np.ndarray,
                                 annotations:tuple[np.ndarray,...]) -> PairedF1:
    pred=_bool_map(candidate,'candidate');ctrl=_bool_map(control,'control')
    if pred.shape!=ctrl.shape or not isinstance(annotations,(tuple,list)) or len(annotations)!=4:
        raise ValueError('Four separate native annotations and aligned predictions required')
    cf=[];bf=[]
    for item in annotations:
        gt=_bool_map(item,'annotation')
        if gt.shape!=pred.shape or not gt.any() or gt.all():
            raise ValueError('Invalid native reference; abort without filtering')
        cf.append(float(one_to_one_boundary_counts(pred,gt,tolerance_ratio=TOLERANCE_RATIO).f1))
        bf.append(float(one_to_one_boundary_counts(ctrl,gt,tolerance_ratio=TOLERANCE_RATIO).f1))
    cm=float(np.mean(cf));bm=float(np.mean(bf))
    return PairedF1('VSB100',4,tuple(cf),tuple(bf),cm,bm,cm-bm)
