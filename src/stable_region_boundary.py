from __future__ import annotations

"""Fixed component-tree-inspired region-boundary stability support.

This is a transparent repository-specific surrogate for the mechanism in
Donoser, Riemenschneider, and Bischof (CVPR 2010), not an exact reproduction of
their unpublished component-tree implementation.  It operates only on an
already serialized soft edge score and contains no ground-truth-dependent
logic.
"""

from dataclasses import dataclass

import numpy as np
from scipy import ndimage


QUANTIZATION_LEVELS = 255
REGION_AREA_MIN = 400
LEVEL_DELTA = 5
CHAMFER_DISTANCE_MAX = 10.0
FRAGMENT_LENGTH_MIN = 70
REGION_CONNECTIVITY = ndimage.generate_binary_structure(2, 1)
FRAGMENT_CONNECTIVITY = ndimage.generate_binary_structure(2, 2)


@dataclass(frozen=True)
class StabilityDiagnostics:
    evaluated_levels: int
    supported_pixels: int
    supported_fraction: float
    mean_positive_support: float
    max_support: float


def _area_filtered_regions(mask: np.ndarray) -> np.ndarray:
    labels, count = ndimage.label(mask, structure=REGION_CONNECTIVITY)
    if count == 0:
        return np.zeros_like(mask, dtype=bool)
    sizes = np.bincount(labels.ravel(), minlength=count + 1)
    keep = sizes >= REGION_AREA_MIN
    keep[0] = False
    return keep[labels]


def _inner_boundary(mask: np.ndarray) -> np.ndarray:
    if not np.any(mask):
        return np.zeros_like(mask, dtype=bool)
    eroded = ndimage.binary_erosion(
        mask, structure=REGION_CONNECTIVITY, border_value=0
    )
    return mask & ~eroded


def _retain_fragments(mask: np.ndarray) -> tuple[np.ndarray, np.ndarray, int]:
    labels, count = ndimage.label(mask, structure=FRAGMENT_CONNECTIVITY)
    if count == 0:
        return np.zeros_like(mask, dtype=bool), labels, 0
    sizes = np.bincount(labels.ravel(), minlength=count + 1)
    keep = sizes >= FRAGMENT_LENGTH_MIN
    keep[0] = False
    return keep[labels], labels, int(np.count_nonzero(keep))


def stable_region_boundary_support(
    score: np.ndarray,
) -> tuple[np.ndarray, StabilityDiagnostics]:
    """Return fixed multilevel region-boundary shape-stability support.

    The score is quantized once to the registered 8-bit lattice.  At every
    cutoff, low-response regions large enough to supply boundary context are
    compared with their enlarged regions five levels later.  Ancestor-boundary
    fragments within the published ten-pixel chamfer radius are retained only
    when at least seventy pixels long.  Their support is the product of the
    threshold saliency and normalized inverse mean chamfer distance.

    The global boundary matching is the declared surrogate step: it avoids
    claiming access to the authors' unpublished component-tree node-selection
    code.  All numerical constants are fixed before benchmark execution.
    """
    x = np.clip(np.asarray(score, dtype=np.float32), 0.0, 1.0)
    if x.ndim != 2 or not np.all(np.isfinite(x)):
        raise ValueError("stable boundary support requires a finite 2-D score")
    quantized = np.rint(x * QUANTIZATION_LEVELS).astype(np.uint8)
    support = np.zeros_like(x, dtype=np.float32)
    evaluated = 0

    # A boundary changes only when the current cutoff or its delta-shifted
    # ancestor crosses an occupied quantized level.  Evaluating those change
    # points is equivalent to scanning all 251 possible cutoffs while avoiding
    # redundant connected-component and distance-transform work.
    occupied = np.unique(quantized).astype(int)
    cutoffs = {0}
    cutoffs.update(int(v) for v in occupied if 0 <= v <= QUANTIZATION_LEVELS - LEVEL_DELTA)
    cutoffs.update(
        int(v - LEVEL_DELTA)
        for v in occupied
        if LEVEL_DELTA <= v <= QUANTIZATION_LEVELS
    )

    for cutoff in sorted(cutoffs):
        current = _area_filtered_regions(quantized <= cutoff)
        ancestor = _area_filtered_regions(quantized <= cutoff + LEVEL_DELTA)
        current_boundary = _inner_boundary(current)
        ancestor_boundary = _inner_boundary(ancestor)
        if not np.any(current_boundary) or not np.any(ancestor_boundary):
            continue
        evaluated += 1
        distance = ndimage.distance_transform_edt(~current_boundary)
        matched = ancestor_boundary & (distance <= CHAMFER_DISTANCE_MAX)
        retained, labels, count = _retain_fragments(matched)
        if count == 0:
            continue
        threshold_saliency = (QUANTIZATION_LEVELS - float(cutoff)) / QUANTIZATION_LEVELS
        for label_id in np.unique(labels[retained]):
            fragment = labels == int(label_id)
            mean_distance = float(np.mean(distance[fragment]))
            shape_stability = max(
                0.0, 1.0 - mean_distance / CHAMFER_DISTANCE_MAX
            )
            value = float(threshold_saliency * shape_stability)
            # Region boundaries lie immediately inside low-response regions,
            # whereas the serialized NMS response occupies the separating
            # lattice sites. Project each stable fragment by one 4-neighbor
            # step onto those separator sites before using it as a score gate.
            separator = ndimage.binary_dilation(
                fragment, structure=REGION_CONNECTIVITY
            ) & (quantized > cutoff)
            support[separator] = np.maximum(support[separator], value)

    positive = quantized > 0
    supported = support > 0
    diagnostics = StabilityDiagnostics(
        evaluated_levels=evaluated,
        supported_pixels=int(np.count_nonzero(supported)),
        supported_fraction=float(np.mean(supported)),
        mean_positive_support=float(np.mean(support[positive])) if np.any(positive) else 0.0,
        max_support=float(np.max(support)) if support.size else 0.0,
    )
    return support, diagnostics
