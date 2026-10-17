from __future__ import annotations

"""Fixed raster adapter for the Stage 18f triangle-partition context cue.

The detector itself remains the immutable MATLAB author implementation.  This
module only maps an arbitrary native raster to the code's documented 129x129
working block and projects its response back to the input support.
"""

from dataclasses import dataclass

import numpy as np
from skimage.transform import resize


WORKING_SIDE = 129
AUTHOR_REPOSITORY = "https://github.com/NatiOfir/TrianglesEdgeDetection.git"
AUTHOR_COMMIT = "19dc4845b26f81b68f40bc2e3e36bfe1c59d01d2"
AUTHOR_TREE = "fa9866f16e8679e77123a2a807978886a9a83595"
AUTHOR_PARAMETER_INDEX = 0


@dataclass(frozen=True)
class ProjectionGeometry:
    source_shape: tuple[int, int]
    resized_shape: tuple[int, int]
    pad_top: int
    pad_bottom: int
    pad_left: int
    pad_right: int


def prepare_author_block(image: np.ndarray) -> tuple[np.ndarray, ProjectionGeometry]:
    """Isotropically fit one finite grayscale raster into a reflected square."""

    values = np.asarray(image, dtype=np.float64)
    if values.ndim != 2 or not np.all(np.isfinite(values)):
        raise ValueError("triangle-partition context requires one finite grayscale raster")
    if float(np.min(values)) < 0.0 or float(np.max(values)) > 1.0:
        raise ValueError("triangle-partition context expects values in [0,1]")
    height, width = values.shape
    scale = WORKING_SIDE / float(max(height, width))
    resized_shape = (
        max(2, min(WORKING_SIDE, int(round(height * scale)))),
        max(2, min(WORKING_SIDE, int(round(width * scale)))),
    )
    resized = resize(
        values,
        resized_shape,
        order=1,
        mode="reflect",
        anti_aliasing=bool(scale < 1.0),
        preserve_range=True,
    )
    dy = WORKING_SIDE - resized_shape[0]
    dx = WORKING_SIDE - resized_shape[1]
    top, bottom = dy // 2, dy - dy // 2
    left, right = dx // 2, dx - dx // 2
    block = np.pad(resized, ((top, bottom), (left, right)), mode="reflect")
    if block.shape != (WORKING_SIDE, WORKING_SIDE):
        raise RuntimeError(f"invalid author working block shape: {block.shape}")
    geometry = ProjectionGeometry(
        source_shape=(height, width),
        resized_shape=resized_shape,
        pad_top=top,
        pad_bottom=bottom,
        pad_left=left,
        pad_right=right,
    )
    return np.clip(block, 0.0, 1.0), geometry


def project_author_response(
    response: np.ndarray, geometry: ProjectionGeometry
) -> np.ndarray:
    """Remove fixed letterboxing and bilinearly restore the native support."""

    values = np.asarray(response, dtype=np.float64)
    if values.shape != (WORKING_SIDE, WORKING_SIDE):
        raise ValueError(f"unexpected author response shape: {values.shape}")
    values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
    y1 = WORKING_SIDE - geometry.pad_bottom
    x1 = WORKING_SIDE - geometry.pad_right
    crop = values[geometry.pad_top:y1, geometry.pad_left:x1]
    if crop.shape != geometry.resized_shape:
        raise RuntimeError(f"invalid response crop shape: {crop.shape}")
    native = resize(
        crop,
        geometry.source_shape,
        order=1,
        mode="reflect",
        anti_aliasing=False,
        preserve_range=True,
    )
    return np.clip(native, 0.0, 1.0).astype(np.float32)


def response_diagnostics(
    evidence: np.ndarray,
    geometry: ProjectionGeometry,
    author_runtime_seconds: float,
) -> dict[str, float]:
    values = np.asarray(evidence, dtype=np.float64)
    return {
        "evidence_mean": float(np.mean(values)),
        "evidence_q90": float(np.quantile(values, 0.9)),
        "evidence_max": float(np.max(values)),
        "positive_fraction": float(np.mean(values > 0.0)),
        "source_height": float(geometry.source_shape[0]),
        "source_width": float(geometry.source_shape[1]),
        "working_height": float(geometry.resized_shape[0]),
        "working_width": float(geometry.resized_shape[1]),
        "author_runtime_seconds": float(author_runtime_seconds),
    }
