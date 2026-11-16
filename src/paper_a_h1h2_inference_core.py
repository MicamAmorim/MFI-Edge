"""Paper A H1/H2 GT-free inference core — PRE-FREEZE candidate implementation.

Pure in-memory operations on externally supplied ORIGINAL-image rasters and
native-size float32 descriptor maps. No file I/O, data selection, labels,
fitting, re-thresholding, or confirmatory F1 analysis occurs in this module.
The source image and maps MUST be from the SAME original geometry.
This module is NOT a certified image/GT confirmatory evaluator.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Mapping

import numpy as np

from src.stage24_residual import MembershipModel, apply_membership
from src.stage24_recertification_ops import apply_aggregator, binary_map, thin_score

H1_GROUP = ("halfdisc_distribution_contrast", "pmi_dependency_deficit")
H2_GROUP = ("fh_region_boundary", "halfdisc_distribution_contrast",
            "structure_tensor_coherence")
REQUIRED_MAPS = frozenset(H1_GROUP + H2_GROUP)
EXPECTED = {"H1": (H1_GROUP, "maximum"),
            "H2": (H2_GROUP, "choquet_generalized_150")}


@dataclass(frozen=True)
class HypothesisPrediction:
    """One pre-outcome X value and two independently-thresholded boolean maps."""
    feature: float
    candidate: np.ndarray
    control: np.ndarray
    candidate_threshold: float
    control_threshold: float


def validate_fitted_recipe(recipe: dict) -> dict:
    """Structural safety check; NOT scientific approval or lineage attestation."""
    if not isinstance(recipe, dict) or recipe.get("schema") != (
            "paper_a_h1h2_recipe_P1_fitted_development"):
        raise ValueError("Expected exact P1 fitted-development recipe schema")
    if (recipe.get("development_GT_and_cached_maps_read") is not True or
            recipe.get("no_scientific_artifacts_or_outcomes_read") is not False):
        raise ValueError("Recipe must disclose development GT and map access")
    method = recipe.get("fixed_method_choices", {})
    required = {"thinning": "nms_image", "calibration": "legacy_sigmoid",
                "suppressor": "identity", "suppression_strength": 1.0,
                "H2_gamma": 1.5, "map_dtype": "float32"}
    if any(method.get(k) != v for k, v in required.items()):
        raise ValueError("Unsupported or changed pre-freeze operator contract")
    cases = recipe.get("hypotheses", [])
    if not isinstance(cases, list) or [x.get("id") for x in cases] != ["H1", "H2"]:
        raise ValueError("H1/H2 identity and order must be fixed")
    by_id = {}
    for h in cases:
        hid = h["id"]
        group, candidate_kind = EXPECTED[hid]
        if tuple(h.get("group", [])) != group:
            raise ValueError(hid + ": cue identity/order changed")
        mem = h.get("membership", {})
        if mem.get("mode") != "legacy_sigmoid":
            raise ValueError(hid + ": wrong membership mode")
        for key in ("midpoint", "scale"):
            vals = mem.get(key)
            if (not isinstance(vals, list) or len(vals) != len(group) or
                    any(type(z) not in (float, int) or not np.isfinite(z)
                        for z in vals)):
                raise ValueError(hid + ": malformed " + key)
        if any(z <= 0 for z in mem["scale"]):
            raise ValueError(hid + ": scale must be strictly positive")
        cand, ctrl = h.get("candidate", {}), h.get("control", {})
        if (cand.get("family") != candidate_kind or
                ctrl.get("family") != "equal_mean" or
                cand.get("n_inputs") != len(group) or
                ctrl.get("n_inputs") != len(group)):
            raise ValueError(hid + ": operator/control identity mismatch")
        for op in (cand, ctrl):
            t = op.get("threshold")
            if type(t) not in (int, float) or not np.isfinite(t) or not (0 < t <= 1):
                raise ValueError(hid + ": missing/invalid development threshold")
        by_id[hid] = h
    capacity = by_id["H2"]["candidate"].get("capacity")
    mobius = by_id["H2"]["candidate"].get("mobius")
    if (not isinstance(capacity, list) or len(capacity) != 8 or
            not isinstance(mobius, list) or len(mobius) != 6):
        raise ValueError("H2: 8-subset capacity and 6 Möbius terms required")
    if not np.isfinite(capacity).all() or not np.isfinite(mobius).all():
        raise ValueError("H2: nonfinite Choquet coefficients")
    if abs(capacity[0]) > 1e-8 or abs(capacity[7] - 1) > 1e-8:
        raise ValueError("H2: capacity not normalized")
    pairs = list(combinations(range(3), 2))
    for mask in range(8):
        reconstructed = sum(mobius[j] for j in range(3) if mask & (1 << j))
        reconstructed += sum(mobius[j + 3] for j, (a, b) in enumerate(pairs)
                             if (mask & (1 << a)) and (mask & (1 << b)))
        if abs(reconstructed - capacity[mask]) > 1e-7:
            raise ValueError("H2: Möbius and capacity disagree")
        for j in range(3):
            if not mask & (1 << j) and capacity[mask] > capacity[mask | (1 << j)] + 1e-8:
                raise ValueError("H2: nonmonotone capacity")
    return by_id


def _native_maps(image: np.ndarray, maps: Mapping[str, np.ndarray]) -> dict:
    im = np.asarray(image)
    if im.ndim not in (2, 3) or min(im.shape[:2]) < 4:
        raise ValueError("Original image must have a nondegenerate 2-D geometry")
    if not isinstance(maps, Mapping) or not REQUIRED_MAPS.issubset(maps):
        raise ValueError("One or more of four required descriptor maps are missing")
    out = {}
    for name in REQUIRED_MAPS:
        value = np.asarray(maps[name])
        if value.dtype != np.dtype("float32") or value.ndim != 2:
            raise TypeError(name + ": original GT-free float32 score map required")
        if value.shape != im.shape[:2]:
            raise ValueError(name + ": map must be registered to original image, never GT")
        if not np.all(np.isfinite(value)):
            raise ValueError(name + ": nonfinite descriptor map")
        out[name] = value
    return out


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    """A tied/constant-map policy must be approved BEFORE scientific freeze."""
    x, y = a.ravel().astype(np.float64), b.ravel().astype(np.float64)
    x -= x.mean()
    y -= y.mean()
    denom = np.linalg.norm(x) * np.linalg.norm(y)
    if denom <= 1e-12:
        raise ValueError("Constant/degenerate X2 descriptor correlation: fail closed")
    return float(np.clip(np.dot(x, y) / denom, -1.0, 1.0))


def preoutcome_features(maps: Mapping[str, np.ndarray]) -> dict[str, float]:
    """No GT used; maps must be independently checked for native geometry."""
    if not REQUIRED_MAPS.issubset(maps):
        raise ValueError("Missing descriptor map")
    for name in REQUIRED_MAPS:
        m = np.asarray(maps[name])
        if m.dtype != np.float32 or m.ndim != 2 or not np.isfinite(m).all():
            raise ValueError(name + ": finite float32 descriptor required")
    if len({np.asarray(maps[n]).shape for n in REQUIRED_MAPS}) != 1:
        raise ValueError("Descriptor geometries differ")
    dh, dp = maps[H1_GROUP[0]], maps[H1_GROUP[1]]
    x1 = abs(float(np.mean(dh, dtype=np.float64)) -
             float(np.mean(dp, dtype=np.float64)))
    x2 = float(np.mean([_pearson(maps[a], maps[b])
                        for a, b in combinations(H2_GROUP, 2)]))
    return {"X1": x1, "X2": x2}


def predict_from_native_maps(image: np.ndarray,
                             maps: Mapping[str, np.ndarray],
                             recipe: dict) -> dict[str, HypothesisPrediction]:
    """Predict H1/H2 WITHOUT GT. No training, image I/O or stats are performed.

    Important: this code assumes already-computed native-registered float32
    descriptor scores. Source image loading, 256px descriptor preprocessing,
    resizing, scene certification, GT decoding and frozen approval are all
    responsibilities of a separate reviewed executor.
    """
    fixed = validate_fitted_recipe(recipe)
    original = _native_maps(image, maps)
    features = preoutcome_features(original)
    result = {}
    for hid, case in fixed.items():
        group = tuple(case["group"])
        mem = case["membership"]
        fitted = MembershipModel(np.asarray(mem["midpoint"], dtype=float),
                                 np.asarray(mem["scale"], dtype=float))
        memberships = apply_membership([original[k] for k in group], fitted)
        candidate = dict(case["candidate"])
        control = dict(case["control"])
        cs = apply_aggregator(memberships, {
            "family": candidate["family"],
            "n_inputs": len(group),
            **({"capacity": candidate["capacity"]}
               if hid == "H2" else {}),
        })
        bs = apply_aggregator(memberships, {
            "family": "equal_mean", "n_inputs": len(group),
        })
        # Match Stage24 train-only NMS-image and separately fitted thresholds.
        # No threshold tuning or leakage via GT here.
        candidate_mask = binary_map(
            thin_score(cs, "nms_image", image), candidate["threshold"], "nms_image")
        control_mask = binary_map(
            thin_score(bs, "nms_image", image), control["threshold"], "nms_image")
        result[hid] = HypothesisPrediction(
            feature=features["X1" if hid == "H1" else "X2"],
            candidate=np.asarray(candidate_mask, dtype=bool),
            control=np.asarray(control_mask, dtype=bool),
            candidate_threshold=float(candidate["threshold"]),
            control_threshold=float(control["threshold"]),
        )
    return result
