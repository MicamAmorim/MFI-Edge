from __future__ import annotations
import numpy as np
from scipy import ndimage as ndi

def percentile_confidence(score):
    """Convert an MFI score map to an empirical within-image percentile in [0,1].

    This is a confidence/rank map, not a calibrated posterior probability.
    """
    x=np.asarray(score,float)
    order=np.argsort(x.ravel(),kind="mergesort")
    ranks=np.empty_like(order,dtype=float)
    ranks[order]=np.linspace(0.0,1.0,len(order),endpoint=True)
    return ranks.reshape(x.shape)

def mfi_roi(score_or_confidence, q=0.70, dilation=0, already_confidence=False):
    conf=np.asarray(score_or_confidence,float)
    if not already_confidence:
        conf=percentile_confidence(conf)
    roi=conf>=float(q)
    if dilation>0:
        roi=ndi.binary_dilation(roi,iterations=int(dilation))
    return roi,conf

def hard_gate(detector_score, roi):
    return np.asarray(detector_score,float)*np.asarray(roi,bool)

def soft_gate(detector_score, roi, confidence):
    return np.asarray(detector_score,float)*np.asarray(roi,bool)*np.asarray(confidence,float)
