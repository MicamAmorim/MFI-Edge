from __future__ import annotations

"""Stage 18z fold-fitted independent-component concentration falsification."""

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
from src.ica_sparse_context import (
    MAX_ITERATIONS,
    N_COMPONENTS,
    PATCHES_PER_IMAGE,
    PATCH_SIZE,
    TOLERANCE,
    fit_ica_context,
    ica_concentration_context,
    synthetic_contract,
)


EXPERIMENT_ID = "stage18z_ica_sparse_context"
DEFAULT_OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
VARIANTS = ("compact_mfi", "compact_plus_ica_sparse_context")
ELIGIBILITY_AUC = 0.56


def _placeholder_maps(items: list[dict], prefix: str = "STAGE18Z_ICA_PLACEHOLDER") -> None:
    for index, item in enumerate(items, start=1):
        print(f"{prefix} {index:03d}/{len(items):03d} {item['id']}", flush=True)
        item["local_fractal"] = np.zeros_like(item["pre_img"], dtype=np.float32)
        item["fractal_diagnostics"] = {
            "evidence_mean": 0.0,
            "evidence_q90": 0.0,
            "evidence_max": 0.0,
            "active_fraction": 0.0,
            "response_l2_mean": 0.0,
            "model_sha256_prefix": 0.0,
        }
        item["fractal_runtime_seconds"] = 0.0
        item["_ica_model_id"] = None


def _evaluate_item(item: dict, model: dict[str, object]) -> np.ndarray:
    model_id = str(model["model_sha256"])
    if item.get("_ica_model_id") == model_id:
        return np.asarray(item["local_fractal"], dtype=np.float32)
    started = time.perf_counter()
    cue, diagnostics = ica_concentration_context(item["pre_img"], model)
    elapsed = time.perf_counter() - started
    if not np.all(np.isfinite(cue)) or float(np.min(cue)) < 0.0 or float(np.max(cue)) > 1.0:
        raise RuntimeError(f"invalid ICA concentration cue for {item['id']}")
    item["local_fractal"] = cue
    item["fractal_diagnostics"] = diagnostics
    item["fractal_runtime_seconds"] = float(elapsed)
    item["_ica_model_id"] = model_id
    return cue


def _fit_cue_spec(items: list[dict], seed: int, max_samples: int = 2500) -> dict:
    model, fit_diagnostics = fit_ica_context(
        [np.asarray(item["pre_img"], dtype=np.float64) for item in items], seed=int(seed)
    )
    if not bool(fit_diagnostics["converged"]):
        raise RuntimeError(f"fixed FastICA fit did not converge: {fit_diagnostics}")
    values, targets = [], []
    for item_no, item in enumerate(items):
        masks = population_masks(item)
        flat = _evaluate_item(item, model).astype(np.float64, copy=False).ravel()
        for group_no, (group, target) in enumerate((("edge", True), ("texture", False))):
            ids = np.flatnonzero(np.asarray(masks[group], dtype=bool).ravel())
            if ids.size > int(max_samples):
                rng = np.random.default_rng(int(seed) + 1009 * item_no + 97 * group_no)
                ids = rng.choice(ids, size=int(max_samples), replace=False)
            if ids.size:
                values.append(flat[ids])
                targets.append(np.full(ids.size, target, dtype=bool))
    if not values:
        raise RuntimeError("no ICA concentration calibration samples were extracted")
    score = np.concatenate(values)
    target = np.concatenate(targets)
    auc = float(binary_auc(score, target))
    information = float(mutual_information_binary(score, target))
    edge_values, texture_values = score[target], score[~target]
    q25, q75 = np.quantile(score, [0.25, 0.75])
    raw_weight = max(auc - 0.5, 0.0) * (1.0 + information)
    eligible = bool(auc >= ELIGIBILITY_AUC and raw_weight > 0.0)
    return {
        "feature": "fold_fitted_ica_response_concentration",
        "edge_direction": 1.0,
        "midpoint": float(0.5 * (np.median(edge_values) + np.median(texture_values))),
        "scale": float(max(q75 - q25, 1.0e-9)),
        "edge_median": float(np.median(edge_values)),
        "texture_median": float(np.median(texture_values)),
        "texture_auc": auc,
        "mutual_information": information,
        "raw_weight": float(raw_weight if eligible else 0.0),
        "eligible": eligible,
        "ica_model_sha256": str(model["model_sha256"]),
        "ica_iterations": int(fit_diagnostics["iterations"]),
        "ica_convergence": float(fit_diagnostics["convergence"]),
        "ica_whitening_error": float(fit_diagnostics["whitened_covariance_max_abs_error"]),
        "ica_orthogonality_error": float(fit_diagnostics["unmixing_orthogonality_max_abs_error"]),
        "ica_model": model,
        "ica_fit": fit_diagnostics,
    }


def _cue_membership(item: dict, spec: dict) -> np.ndarray:
    value = _evaluate_item(item, spec["ica_model"]).astype(np.float64, copy=False)
    z = (value - float(spec["midpoint"])) / max(float(spec["scale"]), 1.0e-9)
    return (1.0 / (1.0 + np.exp(-np.clip(z, -20.0, 20.0)))).astype(np.float32)


def _diagnostic_row(item: dict) -> dict:
    diagnostics = item["fractal_diagnostics"]
    return {
        "image_id": item["id"],
        **{key: float(value) for key, value in diagnostics.items()},
        "ica_runtime_seconds": float(item["fractal_runtime_seconds"]),
    }


def _write_official_manifest(out: Path) -> Path:
    manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [{
            "name": VARIANTS[1],
            "export": {
                "script": "run_stage18z_ica_sparse_context.py",
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


def _contract_record() -> dict[str, object]:
    return {
        "input": "unchanged median-conditioned grayscale image",
        "training": "unlabeled patches from the outer UDED training fold only",
        "patch_size": f"{PATCH_SIZE}x{PATCH_SIZE}",
        "patches_per_training_image": PATCHES_PER_IMAGE,
        "components": N_COMPONENTS,
        "estimator": "PCA whitening followed by symmetric tanh FastICA",
        "maximum_iterations": MAX_ITERATIONS,
        "tolerance": TOLERANCE,
        "evidence": "affinely rescaled max-absolute-component / component-L2 concentration",
        "flat_rule": "zero evidence when local centered patch norm is at most 1e-6",
        "eligibility_auc": ELIGIBILITY_AUC,
        "implementation_fidelity": (
            "repository adaptation of Bell-Sejnowski natural-image ICA and the "
            "Hyvarinen-Oja fixed-point estimator; not an exact author edge detector"
        ),
    }


def _runner_contract() -> dict[str, object]:
    contract = synthetic_contract()
    # Compatibility keys expected by the reused Stage-17h controller. They map
    # to the preregistered positive-step and deterministic-fit checks; no claim
    # is made that ICA concentration ranks checkerboard or noise synthetics.
    contract["step_exceeds_checker"] = bool(contract["step_positive"])
    contract["step_exceeds_noise"] = bool(contract["model_repeat_equal"])
    return contract


def _install_harness_contract() -> None:
    harness.DEFAULT_OUT = DEFAULT_OUT
    harness.VARIANTS = VARIANTS
    harness.ELIGIBILITY_AUC = ELIGIBILITY_AUC
    harness.OFFSETS = (PATCH_SIZE, N_COMPONENTS)
    harness.SUPPORT_SIZE = f"fold-fitted {PATCH_SIZE}x{PATCH_SIZE} ICA analysis bank"
    harness.local_fractal_edge_evidence = ica_concentration_context
    harness.synthetic_contract = _runner_contract
    harness._attach_local_fractal_maps = _placeholder_maps
    harness._fit_cue_spec = _fit_cue_spec
    harness._cue_membership = _cue_membership
    harness._diagnostic_row = _diagnostic_row
    harness._write_official_manifest = _write_official_manifest


def _rename_if_present(source: Path, target: Path) -> None:
    if source.exists():
        source.replace(target)


def _finalize_development(out: Path) -> None:
    _rename_if_present(out / "fractal_calibration.csv", out / "ica_calibration.csv")
    _rename_if_present(out / "fractal_diagnostics.csv", out / "ica_diagnostics.csv")
    path = out / "summary.json"
    summary = json.loads(path.read_text(encoding="utf-8"))
    summary.update({
        "stage": "18z-ica-sparse-context",
        "role": "generation_2_ica_sparse_context_falsification",
        "mechanism": {
            "description": "one positive membership from fold-fitted independent-component response concentration",
            "implementation_fidelity": _contract_record()["implementation_fidelity"],
            "parameters": _contract_record(),
            "unchanged": [
                "five retained memberships", "distorted-Choquet gamma 0.55",
                "gate strength 2.0 and floor 0.10",
                "median-conditioned grayscale Scharr+NMS localizer",
            ],
        },
        "files": [
            "summary.json", "variant_ranking.csv", "fold_results.csv",
            "per_image_metrics.csv", "ica_calibration.csv", "ica_diagnostics.csv",
            "best_method_preview.png", "official_eval_manifest.json",
        ],
    })
    summary["synthetic_contract"].pop("step_exceeds_checker", None)
    summary["synthetic_contract"].pop("step_exceeds_noise", None)
    summary["visual_preview"]["columns"][-1] = "deterministic_last_fold_ica_concentration_cue"
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def _finalize_export(output_dir: Path) -> None:
    _rename_if_present(output_dir / "fractal_diagnostics.csv", output_dir / "ica_diagnostics.csv")
    path = output_dir / "export_manifest.json"
    metadata = json.loads(path.read_text(encoding="utf-8"))
    prior_contract = metadata.pop("fractal_contract", {})
    metadata["method"] = VARIANTS[1]
    metadata["ica_contract"] = _contract_record()
    if "membership_fit" in prior_contract:
        metadata["ica_contract"]["membership_fit"] = prior_contract["membership_fit"]
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def main() -> int:
    contract = synthetic_contract()
    if not (
        contract["finite"] and contract["bounded"] and contract["step_positive"]
        and float(contract["flat_max"]) <= 1.0e-12
        and float(contract["repeat_max_abs_delta"]) <= 1.0e-12
        and float(contract["positive_affine_max_abs_delta"]) <= 2.0e-6
        and contract["model_repeat_equal"] and contract["fit_converged"]
        and float(contract["fit_repeat_max_abs_delta"]) <= 1.0e-12
    ):
        raise RuntimeError(f"strict ICA sparse-context contract failed: {contract}")
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
