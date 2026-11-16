"""Pre-GT Paper A H1/H2 Stage23 descriptor adapter (candidate, NOT frozen).

Uses the HISTORICAL Stage24 raster protocol: max-side 256, linear reflective
downsampling with anti-aliasing, Stage23 GT-free descriptors, float32 score
registration to ORIGINAL image geometry. Never reads files, GT or F1.
Caller supplies the original image pixels; use only explicitly permitted
development images for exploratory diagnostics until scientific freeze.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import NamedTuple
import numpy as np
from skimage.transform import resize

from src.paper_a_h1h2_inference_core import (
    REQUIRED_MAPS, HypothesisPrediction, predict_from_native_maps,
    validate_fitted_recipe,
)
from src.stage24_integrity import resize_score_to_native

MAX_SIDE = 256
# Fixed order for deterministic caches; set enumeration order has no meaning.
DESCRIPTORS = (
    "halfdisc_distribution_contrast",
    "pmi_dependency_deficit",
    "fh_region_boundary",
    "structure_tensor_coherence",
)


class PreGTResult(NamedTuple):
    predictions: dict[str, HypothesisPrediction]
    original_geometry: tuple[int, int]
    inference_geometry: tuple[int, int]
    descriptors: dict[str, np.ndarray]
    preprocessing: str


def norm_image_256(original: np.ndarray) -> np.ndarray:
    """Identical size policy to run_stage24_residual_campaign.norm_image.

    No GT is needed to obtain original geometry. Preserves intensity range;
    does NOT normalize to 0..1 or alter the researcher's recipe.
    """
    image = np.asarray(original)
    if (image.ndim not in (2, 3) or
            (image.ndim == 3 and image.shape[-1] not in (1, 3)) or
            min(image.shape[:2]) < 8 or
            not np.issubdtype(image.dtype, np.number) or
            not np.isfinite(image).all()):
        raise ValueError("Expected finite native grayscale/RGB original image >=8x8")
    h, w = image.shape[:2]
    scale = min(1.0, MAX_SIDE / max(h, w))
    if scale >= 1:
        return image
    nh, nw = max(8, round(h * scale)), max(8, round(w * scale))
    shape = (nh, nw, image.shape[2]) if image.ndim == 3 else (nh, nw)
    return resize(image, shape, order=1, mode="reflect",
                  anti_aliasing=True, preserve_range=True)


def predict_original_pregt(
    original_image: np.ndarray, recipe: dict, *,
    descriptor_fn: Callable[[str, np.ndarray], np.ndarray] | None = None,
) -> PreGTResult:
    """Generate preoutcome predictions from original image, with ZERO GT access.

    descriptor_fn exists solely to test the adapter on synthetic data without
    importing the full Stage23 stack. For research execution pass None to
    use the pinned src.stage23_descriptors.compute_descriptor function.
    """
    validate_fitted_recipe(recipe)
    image = np.asarray(original_image)
    infer = norm_image_256(image)
    if descriptor_fn is None:
        from src.stage23_descriptors import compute_descriptor
        descriptor_fn = compute_descriptor
    native_maps = {}
    for name in DESCRIPTORS:
        raw = np.asarray(descriptor_fn(name, infer))
        if (raw.shape != infer.shape[:2] or raw.dtype != np.float32 or
                not np.isfinite(raw).all()):
            raise ValueError(name + ": Stage23 returned invalid pre-GT float32 map")
        registered = resize_score_to_native(raw, image.shape[:2])
        if not np.isfinite(registered).all():
            raise ValueError(name + ": registration resulted in nonfinite scores")
        native_maps[name] = registered
    if set(native_maps) != REQUIRED_MAPS:
        raise RuntimeError("Unexpected map inventory")
    predicted = predict_from_native_maps(image, native_maps, recipe)
    return PreGTResult(
        predictions=predicted,
        original_geometry=tuple(int(v) for v in image.shape[:2]),
        inference_geometry=tuple(int(v) for v in infer.shape[:2]),
        descriptors=native_maps,
        preprocessing="downscale_maxside256_then_registered_descriptor_preprocessing_v1",
    )
