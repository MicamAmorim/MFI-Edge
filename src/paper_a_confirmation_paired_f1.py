"""Proposed PRE-FREEZE paired F1 contract for synthetic-only unit testing.

This module DOES NOT choose a threshold, binarize GT pixels, read a file,
merge annotators, process RGB images, or select a research cohort. It accepts
ONLY pre-binarized boolean, native-resolution 2-D predictions and reference
masks, and delegates exact one-to-one matching to the existing Stage24
matcher. Never call on holdout/confirmatory GT before the protocol is frozen.

This is a candidate metric, NOT the Berkeley official evaluation.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass

import numpy as np

from src.stage24_integrity import one_to_one_boundary_counts

EXPECTED_REFERENCES = {"BIPED": 1, "MultiCue": 6}
TOLERANCE_RATIO = 0.0075


@dataclass(frozen=True)
class PairedF1:
    domain: str
    annotation_count: int
    candidate_f1_by_annotation: tuple[float, ...]
    control_f1_by_annotation: tuple[float, ...]
    candidate_f1_mean: float
    control_f1_mean: float
    delta_f1: float

    def to_dict(self) -> dict:
        out = asdict(self)
        out["candidate_f1_by_annotation"] = list(self.candidate_f1_by_annotation)
        out["control_f1_by_annotation"] = list(self.control_f1_by_annotation)
        out["status"] = "SYNTHETIC_CONTRACT_ONLY_NOT_FROZEN"
        out["statistical_observation_count"] = 1
        return out


def _bool_map(value: np.ndarray, role: str) -> np.ndarray:
    """Fail closed: no implicit 0..255 GT thresholding or 3-D channel take."""
    array = np.asarray(value)
    if array.dtype != np.dtype("bool") or array.ndim != 2:
        raise TypeError(f"{role}: 2-D boolean native-geometry mask required")
    if not array.size or min(array.shape) < 2:
        raise ValueError(f"{role}: empty/degenerate geometry")
    return array


def evaluate_paired_binary(
    candidate: np.ndarray,
    control: np.ndarray,
    annotations: Sequence[np.ndarray],
    *,
    domain: str,
) -> PairedF1:
    """Return ONE image-level paired delta from 1 or 6 separate references.

    Parameters are already-binarized predictions from a separately FROZEN
    recipe/threshold, and independent GT masks of matching image geometry.
    The caller must prove the threshold, annotation decoding and calibration
    were chosen WITHOUT confirmatory GT; this function cannot certify that.
    """
    if domain not in EXPECTED_REFERENCES:
        raise ValueError("Expected domain BIPED or MultiCue; tasks must not be mixed")
    if not isinstance(annotations, (tuple, list)):
        raise TypeError("annotations must be an explicit list/tuple of 2-D masks")
    expected = EXPECTED_REFERENCES[domain]
    if len(annotations) != expected:
        raise ValueError(
            f"{domain}: expected {expected} separate annotation masks, got {len(annotations)}"
        )
    pred = _bool_map(candidate, "candidate")
    ctrl = _bool_map(control, "control")
    if pred.shape != ctrl.shape:
        raise ValueError("Candidate/control native shapes differ")

    f1_candidate: list[float] = []
    f1_control: list[float] = []
    for i, item in enumerate(annotations):
        gt = _bool_map(item, f"annotation[{i}]")
        if gt.shape != pred.shape:
            raise ValueError("GT/native prediction geometry mismatch; never resize GT")
        if not np.any(gt):
            raise ValueError("Empty GT annotation: abort instead of silent filtering")
        f1_candidate.append(float(one_to_one_boundary_counts(
            pred, gt, tolerance_ratio=TOLERANCE_RATIO
        ).f1))
        f1_control.append(float(one_to_one_boundary_counts(
            ctrl, gt, tolerance_ratio=TOLERANCE_RATIO
        ).f1))
    cf = float(np.mean(f1_candidate))
    bf = float(np.mean(f1_control))
    return PairedF1(
        domain=domain,
        annotation_count=expected,
        candidate_f1_by_annotation=tuple(f1_candidate),
        control_f1_by_annotation=tuple(f1_control),
        candidate_f1_mean=cf,
        control_f1_mean=bf,
        delta_f1=cf - bf,
    )
