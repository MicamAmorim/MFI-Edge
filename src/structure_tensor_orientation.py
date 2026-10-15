from __future__ import annotations

"""Fixed structure-tensor orientation evidence for Stage 16z.

The construction follows the scalar second-moment matrix described by Bigun,
Granlund and Wiklund (TPAMI 1991) and the noise/integration-scale formulation
made explicit by Weickert (Image and Vision Computing 1999).  Stage 16z uses
only the tensor analysis; it does not run coherence-enhancing diffusion.
"""

import numpy as np
from scipy import ndimage as ndi

from src.classical_detectors import gray01


NOISE_SIGMA = 0.5
INTEGRATION_SIGMA = 4.0


def structure_tensor_orientation_evidence(
    image: np.ndarray,
    *,
    noise_sigma: float = NOISE_SIGMA,
    integration_sigma: float = INTEGRATION_SIGMA,
) -> np.ndarray:
    """Return ``lambda_max - lambda_min`` of the scalar structure tensor.

    The eigenvalue difference is zero in a perfectly flat or locally isotropic
    neighborhood and positive when one gradient orientation dominates.  Unlike
    normalized coherence, it also tends continuously to zero with contrast,
    avoiding an unstable unit response in nearly flat regions.
    """
    gray = gray01(image).astype(np.float64, copy=False)
    gx = ndi.gaussian_filter(
        gray, sigma=float(noise_sigma), order=(0, 1), mode="reflect"
    )
    gy = ndi.gaussian_filter(
        gray, sigma=float(noise_sigma), order=(1, 0), mode="reflect"
    )
    rho = float(integration_sigma)
    jxx = ndi.gaussian_filter(gx * gx, sigma=rho, mode="reflect")
    jyy = ndi.gaussian_filter(gy * gy, sigma=rho, mode="reflect")
    jxy = ndi.gaussian_filter(gx * gy, sigma=rho, mode="reflect")
    evidence = np.sqrt(np.maximum((jxx - jyy) ** 2 + 4.0 * jxy * jxy, 0.0))
    return np.clip(np.nan_to_num(evidence), 0.0, 1.0).astype(np.float32)


def synthetic_contract() -> dict[str, float | bool]:
    """Deterministic edge-versus-isotropic-texture contract."""
    step = np.zeros((64, 64), dtype=np.float32)
    step[:, 32:] = 1.0
    yy, xx = np.indices(step.shape)
    checker = ((yy // 2 + xx // 2) % 2).astype(np.float32)

    first = structure_tensor_orientation_evidence(step)
    second = structure_tensor_orientation_evidence(step)
    isotropic = structure_tensor_orientation_evidence(checker)
    repeat_delta = float(np.max(np.abs(first - second)))
    step_band = float(np.mean(first[:, 27:38]))
    remote = float(np.mean(np.concatenate([first[:, :12], first[:, -12:]], axis=1)))
    checker_mean = float(np.mean(isotropic))
    return {
        "finite": bool(np.all(np.isfinite(first)) and np.all(np.isfinite(isotropic))),
        "bounded": bool(
            np.min(first) >= 0.0
            and np.max(first) <= 1.0
            and np.min(isotropic) >= 0.0
            and np.max(isotropic) <= 1.0
        ),
        "repeat_max_abs_delta": repeat_delta,
        "step_band_mean": step_band,
        "remote_band_mean": remote,
        "checkerboard_mean": checker_mean,
        "step_exceeds_remote": bool(step_band > remote),
        "step_exceeds_checkerboard": bool(step_band > checker_mean),
    }
