#!/usr/bin/env python3
"""PROPOSAL ONLY: GT decoder candidate from out-of-cohort samples.

Never imported by the frozen evaluator; never authorizes GT access.
No filesystem, TAR, dataset or outcome access. Scientific semantics
must be independently reviewed and frozen prospectively before use.
"""
from __future__ import annotations

import numpy as np

POLICY_ID = "DRAFT_BIPED_0_254_255_MULTICUE_0_65535_v2_NOT_APPROVED"
_ALLOWED = {
    "BIPED": (np.dtype("uint8"), frozenset({0, 254, 255})),
    "MultiCue": (np.dtype("uint16"), frozenset({0, 65535})),
}


def decode_gt_candidate(pixels: np.ndarray, *, dataset: str,
                        native_shape: tuple[int, int]) -> np.ndarray:
    """Draft exact-value mapping only, not a scientifically approved decoder.

    BIPED: 0 -> False, 254/255 -> True (CONDITIONAL meaning of 254).
    MultiCue: uint16 0 -> False, 65535 -> True (CONDITIONAL polarity).
    Any other value, dtype, dimension, empty/full mask or shape: raise.
    """
    if dataset not in _ALLOWED:
        raise ValueError("Unknown dataset (draft decoder)")
    if (not isinstance(pixels, np.ndarray) or pixels.ndim != 2 or
            len(native_shape) != 2 or tuple(pixels.shape) != tuple(native_shape)):
        raise ValueError("Draft decoder requires native 2D grayscale geometry")
    dtype, allowed = _ALLOWED[dataset]
    if pixels.dtype != dtype:
        raise ValueError("GT dtype is not the exact candidate dataset dtype")
    values = set(np.unique(pixels).tolist())
    if not values or not values.issubset(allowed):
        raise ValueError("GT has values not justified even as draft policy")
    if 0 not in values or len(values) == 1:
        raise ValueError("Empty/fully foreground GT requires protocol adjudication")
    if dataset == "BIPED":
        return np.asarray((pixels == 254) | (pixels == 255), dtype=bool)
    return np.asarray(pixels == 65535, dtype=bool)
