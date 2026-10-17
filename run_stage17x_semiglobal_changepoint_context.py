from __future__ import annotations

"""Stage 17x fixed semi-global scanline change-point context falsification."""

from pathlib import Path
import argparse
import json
import sys
import time

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

import run_stage17h_local_fractal_context as harness
from src.edge_signature import binary_auc, mutual_information_binary, population_masks
from src.semiglobal_changepoint import (
    MAX_WORKING_SIDE,
    SCAN_DIRECTIONS,
    semiglobal_changepoint_evidence,
    synthetic_contract,
)


EXPERIMENT_ID = "stage17x_semiglobal_changepoint_context"
DEFAULT_OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
VARIANTS = ("compact_mfi", "compact_plus_semiglobal_changepoint")
ELIGIBILITY_AUC = 0.56


def _attach_cue_maps(items: list[dict], prefix: str = "STAGE17X_SEMIGLOBAL") -> None:
    for index, item in enumerate(items, start=1):
        print(f"{prefix} {index:03d}/{len(items):03d} {item['id']}", flush=True)
        started = time.perf_counter()
        cue, diagnostics = semiglobal_changepoint_evidence(item["pre_img"])
        elapsed = time.perf_counter() - started
        if not np.all(np.isfinite(cue)) or float(np.min(cue)) < 0.0 or float(np.max(cue)) > 1.0:
            raise RuntimeError(f"invalid semi-global change-point cue for {item['id']}")
        item["local_fractal"] = cue
        item["fractal_diagnostics"] = diagnostics
        item["fractal_runtime_seconds"] = float(elapsed)


def _fit_cue_spec(items: list[dict], seed: int, max_samples: int = 2500) -> dict:
    values, targets = [], []
    for item_no, item in enumerate(items):
        masks = population_masks(item)
        flat = np.asarray(item["local_fractal"], dtype=np.float64).ravel()
        for group_no, (group, target) in enumerate((("edge", True), ("texture", False))):
            ids = np.flatnonzero(np.asarray(masks[group], dtype=bool).ravel())
            if ids.size > int(max_samples):
                rng = np.random.default_rng(int(seed) + 1009 * item_no + 97 * group_no)
                ids = rng.choice(ids, size=int(max_samples), replace=False)
            if ids.size:
                values.append(flat[ids])
                targets.append(np.full(ids.size, target, dtype=bool))
    if not values:
        raise RuntimeError("no semi-global change-point calibration samples were extracted")
    score = np.concatenate(values)
    target = np.concatenate(targets)
    auc = float(binary_auc(score, target))
    information = float(mutual_information_binary(score, target))
    edge_values, texture_values = score[target], score[~target]
    q25, q75 = np.quantile(score, [0.25, 0.75])
    raw_weight = max(auc - 0.5, 0.0) * (1.0 + information)
    eligible = bool(auc >= ELIGIBILITY_AUC and raw_weight > 0.0)
    return {
        "feature": "semiglobal_scanline_changepoint_support",
        "edge_direction": 1.0,
        "midpoint": float(0.5 * (np.median(edge_values) + np.median(texture_values))),
        "scale": float(max(q75 - q25, 1.0e-9)),
        "edge_median": float(np.median(edge_values)),
        "texture_median": float(np.median(texture_values)),
        "texture_auc": auc,
        "mutual_information": information,
        "raw_weight": float(raw_weight if eligible else 0.0),
        "eligible": eligible,
    }


def _diagnostic_row(item: dict) -> dict:
    diagnostics = item["fractal_diagnostics"]
    return {
        "image_id": item["id"],
        **{key: float(value) for key, value in diagnostics.items()},
        "semiglobal_changepoint_runtime_seconds": float(item["fractal_runtime_seconds"]),
    }


def _write_official_manifest(out: Path) -> Path:
    manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [{
            "name": VARIANTS[1],
            "export": {
                "script": "run_stage17x_semiglobal_changepoint_context.py",
                "args": [
                    "--export-bsds", "--image-dir", "{image_dir}",
                    "--output-dir", "{output_dir}", "--split", "{split}",
                ],
                "timeout_minutes": 360,
            },
        }],
    }
    path = out / "official_eval_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def _install_harness_contract() -> None:
    harness.DEFAULT_OUT = DEFAULT_OUT
    harness.VARIANTS = VARIANTS
    harness.ELIGIBILITY_AUC = ELIGIBILITY_AUC
    harness.OFFSETS = SCAN_DIRECTIONS
    harness.SUPPORT_SIZE = "full scanline on fixed working grid"
    harness.local_fractal_edge_evidence = semiglobal_changepoint_evidence
    harness.synthetic_contract = synthetic_contract
    harness._attach_local_fractal_maps = _attach_cue_maps
    harness._fit_cue_spec = _fit_cue_spec
    harness._diagnostic_row = _diagnostic_row
    harness._write_official_manifest = _write_official_manifest


def _rename_if_present(source: Path, target: Path) -> None:
    if source.exists():
        source.replace(target)


def _contract_record() -> dict:
    return {
        "input": "unchanged median-conditioned grayscale image",
        "working_grid_max_side": MAX_WORKING_SIDE,
        "scan_directions": list(SCAN_DIRECTIONS),
        "segment_model": "piecewise-constant least squares",
        "selection": "exact dynamic programming with sigma_hat^2*log(N) Schwarz/BIC penalty",
        "noise_scale": "first-difference MAD with RMS fallback only when MAD is zero",
        "raster_support": "both samples adjacent to each selected change point",
        "direction_merge": "pointwise maximum",
        "normalization": "none",
        "eligibility_auc": ELIGIBILITY_AUC,
    }


def _finalize_development(out: Path) -> None:
    _rename_if_present(out / "fractal_calibration.csv", out / "semiglobal_changepoint_calibration.csv")
    _rename_if_present(out / "fractal_diagnostics.csv", out / "semiglobal_changepoint_diagnostics.csv")
    path = out / "summary.json"
    summary = json.loads(path.read_text(encoding="utf-8"))
    summary.update({
        "stage": "17x-semiglobal-changepoint-context",
        "role": "generation_2_semiglobal_changepoint_context_falsification",
        "mechanism": {
            "description": "one positive context membership from fixed row/column BIC-selected scanline change points",
            "implementation_fidelity": "bounded repository surrogate of Jevnisek-Avidan semi-global scanline segmentation; not exact SGBD",
            "parameters": _contract_record(),
            "unchanged": [
                "five retained memberships",
                "distorted-Choquet gamma 0.55",
                "gate strength 2.0 and floor 0.10",
                "median-conditioned grayscale Scharr+NMS localizer",
            ],
        },
        "files": [
            "summary.json", "variant_ranking.csv", "fold_results.csv",
            "per_image_metrics.csv", "semiglobal_changepoint_calibration.csv",
            "semiglobal_changepoint_diagnostics.csv", "best_method_preview.png",
            "official_eval_manifest.json",
        ],
    })
    summary["visual_preview"]["columns"][-1] = "semiglobal_changepoint_cue"
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def _finalize_export(output_dir: Path) -> None:
    _rename_if_present(output_dir / "fractal_diagnostics.csv", output_dir / "semiglobal_changepoint_diagnostics.csv")
    path = output_dir / "export_manifest.json"
    metadata = json.loads(path.read_text(encoding="utf-8"))
    metadata.pop("fractal_contract", None)
    metadata["method"] = VARIANTS[1]
    metadata["semiglobal_changepoint_contract"] = _contract_record()
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def main() -> int:
    contract = synthetic_contract()
    if not (
        contract["finite"] and contract["bounded"]
        and contract["step_exceeds_checker"] and contract["step_exceeds_noise"]
        and float(contract["flat_max"]) <= 1.0e-12
        and float(contract["repeat_max_abs_delta"]) <= 1.0e-12
        and float(contract["positive_scale_max_abs_error"]) <= 1.0e-9
        and float(contract["offset_max_abs_delta"]) <= 1.0e-9
        and float(contract["polarity_max_abs_delta"]) <= 1.0e-9
    ):
        raise RuntimeError(f"strict semi-global change-point contract failed: {contract}")
    _install_harness_contract()
    parser = argparse.ArgumentParser()
    parser.add_argument("--uded-root", default=str(harness.DEFAULT_UDED))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--max-side", type=int, default=256)
    parser.add_argument("--thresholds", type=int, default=41)
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--max-positive", type=int, default=10)
    parser.add_argument("--max-negative", type=int, default=8)
    parser.add_argument("--max-abs-corr", type=float, default=0.88)
    parser.add_argument("--seed", type=int, default=20261009)
    parser.add_argument("--export-bsds", action="store_true")
    parser.add_argument("--image-dir")
    parser.add_argument("--output-dir")
    parser.add_argument("--split", default="val")
    parser.add_argument("--max-side-development", type=int, default=256)
    args = parser.parse_args()
    if args.export_bsds:
        if not args.image_dir or not args.output_dir:
            parser.error("--export-bsds requires --image-dir and --output-dir")
        result = harness.export_bsds(args)
        _finalize_export(Path(args.output_dir))
        return result
    result = harness.run_experiment(args)
    _finalize_development(Path(args.out))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
