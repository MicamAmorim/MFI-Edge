#!/usr/bin/env python3
"""GT-free Stage23 preflight with diagnostic-rich synthetic original image.

No BIPED/MultiCue/UDED original image or GT file is opened. A constant map
must remain a hard error for H2 pending the prespecified scientific policy.
"""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.paper_a_prefreeze_map_adapter import DESCRIPTORS, predict_original_pregt


def synthetic_original() -> np.ndarray:
    """Deterministic multi-region texture avoids an uninformative stripe-only fixture.

    Intended for TEST coverage, not tuning a candidate or setting thresholds.
    """
    h, w = 160, 192
    yy, xx = np.indices((h, w))
    rng = np.random.default_rng(20261116)
    base = np.full((h, w), 0.13, dtype=np.float64)
    base[:, w // 2:] = 0.82
    base[h // 4:3 * h // 4, w // 4:3 * w // 4] = 0.45
    base[h // 3:h // 3 + 25, w // 3:w // 3 + 25] = 0.97
    base += 0.035 * rng.standard_normal((h, w))
    base = np.clip(base, 0.0, 1.0)
    rgb = np.stack([
        base,
        np.clip(base * 0.92 + 0.04 * (yy / h), 0.0, 1.0),
        np.clip(base * 0.88 + 0.04 * (xx / w), 0.0, 1.0),
    ], axis=-1)
    return np.asarray(rgb, dtype=np.float32)


def descriptor_statistics(descriptor: np.ndarray) -> dict:
    """Observable test diagnostic; does not silently impute constant Pearson."""
    m = np.asarray(descriptor)
    return {
        "shape": list(m.shape),
        "min": float(np.min(m)),
        "max": float(np.max(m)),
        "mean": float(np.mean(m, dtype=np.float64)),
        "std": float(np.std(m, dtype=np.float64)),
        "nonzero_pixels": int(np.count_nonzero(m)),
        "unique_values": int(np.unique(m).size),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--real-stage23", action="store_true",
                        help="Compute four real Stage23 maps on a rich SYNTHETIC image")
    args = parser.parse_args()
    original = synthetic_original()
    recipe = json.loads((ROOT / "docs/paper_a_confirmation" /
                         "P1_DEVELOPMENT_RECIPE_UNATTESTED.json").read_text(encoding="utf-8"))
    diagnostics = {}
    if args.real_stage23:
        from src.stage23_descriptors import compute_descriptor

        def maker(name, frame):
            output = compute_descriptor(name, frame)
            diagnostics[name] = descriptor_statistics(output)
            return output
    else:
        def maker(name, frame):
            y, x = np.indices(frame.shape[:2], dtype=np.float64)
            idx = DESCRIPTORS.index(name)
            output = ((x * (idx + 1) + y * (3 - idx)) /
                      (frame.shape[0] * 4 + frame.shape[1] * 4)).astype(np.float32)
            diagnostics[name] = descriptor_statistics(output)
            return output
    try:
        r = predict_original_pregt(original, recipe, descriptor_fn=maker)
    except (ValueError, TypeError) as exc:
        print(json.dumps({
            "status": "SYNTHETIC_PREGT_DIAGNOSTIC_FAILED",
            "reason": str(exc),
            "used_real_images_or_GT": False,
            "not_a_confirmatory_result": True,
            "descriptor_diagnostics": diagnostics,
        }, indent=2, ensure_ascii=False), flush=True)
        return 2
    print(json.dumps({
        "status": "SYNTHETIC_ORIGINAL_IMAGE_PREGT_NO_CONFIRMATORY_GT",
        "actual_stage23_implementation_invoked": args.real_stage23,
        "synthetic_scene": "deterministic multi-region RGB with mild texture",
        "used_real_images_or_GT": False,
        "development_fit_rerun": False,
        "original_geometry": r.original_geometry,
        "inference_geometry": r.inference_geometry,
        "descriptor_diagnostics": diagnostics,
        "hypotheses": {key: {
            "X": round(v.feature, 8),
            "candidate_pixels": int(v.candidate.sum()),
            "control_pixels": int(v.control.sum()),
        } for key, v in r.predictions.items()},
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
