from __future__ import annotations

"""Frozen raw evidence maps for the first Stage-23 landscape."""

import numpy as np
from scipy import ndimage as ndi
from skimage import color

from benchmark_uded import SCALES
from src.classical_detectors import detector_score, robust01
from src.conditioning import apply_conditioning
from src.features import extract_features
from src.fh_region_boundary import fh_region_boundary_evidence
from src.phase_congruency import phase_congruency_edge_moment
from src.pmi_dependency_context import pmi_dependency_context
from src.semiglobal_changepoint import semiglobal_changepoint_evidence
from src.structure_tensor_orientation import structure_tensor_orientation_evidence
from src.texture_gradient import lbp_half_disc_texture_gradient


DESCRIPTOR_IDS = (
    "scharr_pre_nms_magnitude", "lab_dizenzo_tensor_gradient", "gabor4_s5",
    "hessian_s7", "gabor4_s13", "hessian_s13", "gabor4_scale_persistence",
    "structure_tensor_coherence", "phase_congruency_max_moment",
    "halfdisc_distribution_contrast", "pmi_dependency_deficit",
    "semiglobal_changepoint", "fh_region_boundary",
)

_SCHARR_X = np.asarray(
    [[-3.0, 0.0, 3.0], [-10.0, 0.0, 10.0], [-3.0, 0.0, 3.0]], dtype=float
) / 32.0
_SCHARR_Y = _SCHARR_X.T


def _rgb01(image: np.ndarray) -> np.ndarray:
    source = np.asarray(image)
    if source.ndim != 3 or source.shape[-1] < 3:
        raise ValueError("Stage-23 CIELAB evidence requires RGB input")
    out = source[..., :3].astype(float)
    if np.issubdtype(source.dtype, np.integer):
        out /= float(np.iinfo(source.dtype).max)
    elif np.nanmax(out) > 1.0:
        out /= 255.0
    return np.clip(out, 0.0, 1.0)


def _lab_dizenzo_pre_nms(image: np.ndarray) -> np.ndarray:
    lab = color.rgb2lab(_rgb01(image)).astype(float) / 100.0
    lab = ndi.median_filter(lab, size=(3, 3, 1), mode="reflect")
    dx = np.stack([ndi.correlate(lab[..., c], _SCHARR_X, mode="reflect") for c in range(3)], axis=-1)
    dy = np.stack([ndi.correlate(lab[..., c], _SCHARR_Y, mode="reflect") for c in range(3)], axis=-1)
    gxx, gyy, gxy = np.sum(dx * dx, axis=-1), np.sum(dy * dy, axis=-1), np.sum(dx * dy, axis=-1)
    disc = np.sqrt(np.maximum((gxx - gyy) ** 2 + 4.0 * gxy * gxy, 0.0))
    return robust01(np.sqrt(np.maximum(0.5 * (gxx + gyy + disc), 0.0))).astype(np.float32)


def _single_scale(pre_img: np.ndarray, window: int, feature: str) -> np.ndarray:
    tensor, names, _ = extract_features(pre_img, window, mode="oriented_ms")
    return np.asarray(tensor[..., names.index(feature)], dtype=np.float32)


def _gabor_persistence(pre_img: np.ndarray) -> np.ndarray:
    stack = np.stack([_single_scale(pre_img, int(window), "gabor4") for window in SCALES], axis=-1)
    return np.clip(np.mean(stack, axis=-1) / np.maximum(np.max(stack, axis=-1), 1.0e-12), 0.0, 1.0).astype(np.float32)


def descriptor_parameters(descriptor_id: str) -> dict[str, object]:
    specs: dict[str, dict[str, object]] = {
        "scharr_pre_nms_magnitude": {"conditioning": "median3_reflect", "sigma": 1.0},
        "lab_dizenzo_tensor_gradient": {"color_space": "CIELAB", "conditioning": "channel_median3_reflect", "nms": False},
        "gabor4_s5": {"window": 5, "mode": "oriented_ms", "orientations": 4},
        "hessian_s7": {"window": 7, "mode": "oriented_ms"},
        "gabor4_s13": {"window": 13, "mode": "oriented_ms", "orientations": 4},
        "hessian_s13": {"window": 13, "mode": "oriented_ms"},
        "gabor4_scale_persistence": {"scales": list(SCALES), "mode": "oriented_ms", "definition": "mean_over_max"},
        "structure_tensor_coherence": {"noise_sigma": 0.5, "integration_sigma": 4.0},
        "phase_congruency_max_moment": {"nscale": 4, "norient": 6, "min_wavelength": 3.0, "mult": 2.1, "sigma_on_f": 0.55, "k": 2.0, "cutoff": 0.5, "spread_gain": 10.0},
        "halfdisc_distribution_contrast": {"radius_fraction": 0.02, "minimum_radius": 3, "lbp_points": 8, "lbp_radius": 1.0, "orientations": 8, "comparison": "chi_square"},
        "pmi_dependency_deficit": {"levels": 256, "rho": 1.25, "pair_axes": 4},
        "semiglobal_changepoint": {"max_side": 256, "directions": ["row", "column"], "penalty": "BIC"},
        "fh_region_boundary": {"sigma": 0.8, "scale": 300.0, "connectivity": 8, "min_size_cleanup": False},
    }
    if descriptor_id not in specs:
        raise KeyError(descriptor_id)
    return specs[descriptor_id]


def compute_descriptor(descriptor_id: str, image: np.ndarray) -> np.ndarray:
    """Compute one GT-free frozen evidence map from a registered image raster."""
    pre = apply_conditioning(image, "median", size=3)
    if descriptor_id == "scharr_pre_nms_magnitude": value = detector_score(pre, "scharr", 1.0)
    elif descriptor_id == "lab_dizenzo_tensor_gradient": value = _lab_dizenzo_pre_nms(image)
    elif descriptor_id == "gabor4_s5": value = _single_scale(pre, 5, "gabor4")
    elif descriptor_id == "hessian_s7": value = _single_scale(pre, 7, "hessian")
    elif descriptor_id == "gabor4_s13": value = _single_scale(pre, 13, "gabor4")
    elif descriptor_id == "hessian_s13": value = _single_scale(pre, 13, "hessian")
    elif descriptor_id == "gabor4_scale_persistence": value = _gabor_persistence(pre)
    elif descriptor_id == "structure_tensor_coherence": value = structure_tensor_orientation_evidence(pre)
    elif descriptor_id == "phase_congruency_max_moment": value = phase_congruency_edge_moment(pre)
    elif descriptor_id == "halfdisc_distribution_contrast": value, _ = lbp_half_disc_texture_gradient(pre)
    elif descriptor_id == "pmi_dependency_deficit": value, _ = pmi_dependency_context(pre)
    elif descriptor_id == "semiglobal_changepoint": value, _ = semiglobal_changepoint_evidence(pre)
    elif descriptor_id == "fh_region_boundary": value, _ = fh_region_boundary_evidence(pre)
    else: raise KeyError(descriptor_id)
    out = np.asarray(value, dtype=np.float32)
    if out.shape != np.asarray(image).shape[:2] or not np.all(np.isfinite(out)):
        raise RuntimeError(f"invalid Stage-23 descriptor output {descriptor_id}: {out.shape}")
    return out


def synthetic_contract() -> dict[str, object]:
    image = np.zeros((65, 67, 3), dtype=np.float32)
    image[:, 33:, :] = 1.0
    maxima = {descriptor_id: float(np.max(compute_descriptor(descriptor_id, image))) for descriptor_id in DESCRIPTOR_IDS}
    return {"count": len(maxima), "all_finite": all(np.isfinite(value) for value in maxima.values()), "maxima": maxima}
