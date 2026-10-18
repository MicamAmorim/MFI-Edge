from __future__ import annotations

"""Stage 18t fixed fold-fitted isotonic calibration of compact memberships."""

from pathlib import Path
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import run_stage16p_copula_context as harness
from run_stage12b_fuzzy_signature import membership_stack
from run_stage12c_leakfree_cv import learn_banks as base_learn_banks
from src.edge_signature import GROUPS
from src.edge_signature_relational import extract_relational_samples
from src.isotonic_membership import (
    apply_isotonic_calibrator,
    calibrator_from_record,
    calibrator_to_record,
    fit_isotonic_calibrator,
)
from src.bipolar_fuzzy import distorted_choquet


EXPERIMENT_ID = "stage18t_isotonic_membership_calibration"
VARIANTS = ("compact_mfi", "isotonic_calibrated_compact_mfi")
DEFAULT_OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
BASE_LEARN_BANKS = base_learn_banks
BASE_SCORE_PAIRS = harness._score_pairs


def _balanced_weights(labels: np.ndarray) -> np.ndarray:
    labels = np.asarray(labels, dtype=np.int8)
    weights = np.empty(labels.shape, dtype=np.float64)
    for value in (0, 1):
        count = int(np.sum(labels == value))
        if count == 0:
            raise RuntimeError("isotonic calibration requires both edge and texture samples")
        weights[labels == value] = 0.5 / count
    return weights


def _learn_banks(train_items, base_names, seed, max_positive, max_negative, max_abs_corr):
    positive, negative = BASE_LEARN_BANKS(
        train_items, base_names, seed, max_positive, max_negative, max_abs_corr
    )
    samples = extract_relational_samples(train_items, base_names, 2500, seed=seed)
    edge_code, texture_code = GROUPS.index("edge"), GROUPS.index("texture")
    keep = (samples.groups == edge_code) | (samples.groups == texture_code)
    labels = (samples.groups[keep] == edge_code).astype(np.float64)
    weights = _balanced_weights(labels)
    feature_index = {name: index for index, name in enumerate(samples.feature_names)}
    for row in positive:
        raw = samples.X[keep, feature_index[str(row["feature"])]].astype(np.float64)
        z = float(row["edge_direction"]) * (raw - float(row["midpoint"])) / max(
            float(row["scale"]), 1.0e-12
        )
        membership = 1.0 / (1.0 + np.exp(-np.clip(z, -20.0, 20.0)))
        calibrator = fit_isotonic_calibrator(membership, labels, weights)
        row["isotonic_calibrator"] = calibrator_to_record(calibrator)
    return positive, negative


def _context_pairs(items: list[dict], names: list[str], compact: list[dict]):
    controls, candidates, mean_calibrated = [], [], []
    spec = harness._raw_compact(compact)
    for item in items:
        memberships, weights = membership_stack(item, names, spec, "edge")
        calibrated_channels = []
        for channel, row in enumerate(spec):
            calibrator = calibrator_from_record(row["isotonic_calibrator"])
            calibrated_channels.append(
                apply_isotonic_calibrator(memberships[..., channel], calibrator)
            )
        calibrated = np.stack(calibrated_channels, axis=-1)
        controls.append(distorted_choquet(memberships, weights, harness.GAMMA))
        candidates.append(distorted_choquet(calibrated, weights, harness.GAMMA))
        mean_calibrated.append(np.mean(calibrated, axis=-1).astype(np.float32))
    return controls, candidates, mean_calibrated


def _score_pairs(items: list[dict], names: list[str], compact: list[dict]):
    controls, candidates, diagnostics = BASE_SCORE_PAIRS(items, names, compact)
    for control, candidate in zip(controls, candidates):
        if not np.array_equal(np.asarray(control) > 0.0, np.asarray(candidate) > 0.0):
            raise RuntimeError("isotonic calibration changed positive score support")
    return controls, candidates, diagnostics


def _contract_checks() -> dict:
    scores = np.asarray([0.0, 0.0, 0.2, 0.4, 0.4, 0.8, 1.0], dtype=np.float64)
    labels = np.asarray([0, 1, 0, 1, 0, 1, 1], dtype=np.float64)
    first = fit_isotonic_calibrator(scores, labels, _balanced_weights(labels))
    second = fit_isotonic_calibrator(scores, labels, _balanced_weights(labels))
    probe = np.linspace(-0.1, 1.1, 257)
    mapped = apply_isotonic_calibrator(probe, first)
    flat_labels = np.asarray([0, 0, 1, 1], dtype=np.float64)
    flat = fit_isotonic_calibrator(
        np.ones(4, dtype=np.float64), flat_labels, _balanced_weights(flat_labels)
    )
    checks = {
        "finite_and_bounded": bool(
            np.all(np.isfinite(mapped)) and np.all((mapped >= 0.0) & (mapped <= 1.0))
        ),
        "monotone_non_decreasing": bool(np.all(np.diff(mapped) >= 0.0)),
        "duplicate_scores_aggregated": bool(first.upper_bounds.size < scores.size),
        "balanced_constant_score_maps_to_half": bool(flat.values.size == 1 and flat.values[0] == 0.5),
        "repeat_bitwise_equal": bool(
            np.array_equal(first.upper_bounds, second.upper_bounds)
            and np.array_equal(first.values, second.values)
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(f"isotonic calibration contract failed: {checks}")
    return checks


def _write_official_manifest(out: Path, seed: int) -> Path:
    manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [{
            "name": VARIANTS[1],
            "export": {
                "script": "run_stage18t_isotonic_membership_calibration.py",
                "args": [
                    "--export-bsds", "--image-dir", "{image_dir}",
                    "--output-dir", "{output_dir}", "--split", "{split}",
                    "--seed", str(seed),
                ],
                "timeout_minutes": 240,
            },
        }],
    }
    path = out / "official_eval_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def _rewrite_outputs(export_mode: bool) -> None:
    if export_mode:
        output_arg = sys.argv[sys.argv.index("--output-dir") + 1]
        out = Path(output_arg)
        old = out / "rank_diagnostics.csv"
        if old.exists():
            old.replace(out / "isotonic_diagnostics.csv")
            diagnostics_path = out / "isotonic_diagnostics.csv"
            diagnostics_path.write_text(
                diagnostics_path.read_text(encoding="utf-8").replace(
                    "mean_rank_membership", "mean_isotonic_membership"
                ),
                encoding="utf-8",
            )
        manifest_path = out / "export_manifest.json"
        metadata = json.loads(manifest_path.read_text(encoding="utf-8"))
        metadata.pop("copula_contract", None)
        metadata["method"] = VARIANTS[1]
        metadata["isotonic_membership_contract"] = {
            "fit_scope": "UDED selection only; full fit for BSDS export",
            "fit_target": "class-balanced edge versus texture samples",
            "mapping": "per-feature weighted PAV piecewise-constant monotone calibration",
            "extrapolation": "nearest terminal block",
            "unchanged": "features, singleton weights, Choquet gamma, gate and Scharr+NMS",
            "checks": _contract_checks(),
        }
        manifest_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return

    out = (
        Path(sys.argv[sys.argv.index("--out") + 1])
        if "--out" in sys.argv
        else DEFAULT_OUT
    )
    old = out / "rank_diagnostics.csv"
    if old.exists():
        old.replace(out / "isotonic_diagnostics.csv")
        diagnostics_path = out / "isotonic_diagnostics.csv"
        diagnostics_path.write_text(
            diagnostics_path.read_text(encoding="utf-8").replace(
                "mean_rank_membership", "mean_isotonic_membership"
            ),
            encoding="utf-8",
        )
    summary_path = out / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["stage"] = "18t-isotonic-membership-calibration"
    summary["role"] = "generation_2_isotonic_membership_calibration_falsification"
    summary["mechanism"] = {
        "description": (
            "outer-training-fold-only class-balanced weighted isotonic calibration "
            "of each retained sigmoid membership before unchanged Choquet aggregation"
        ),
        "implementation_fidelity": (
            "deterministic weighted pool-adjacent-violators score calibration adapted "
            "to fuzzy memberships; not a multivariate classifier or probability claim"
        ),
        "parameters": {
            "calibration_model": "weighted squared-loss isotonic regression",
            "class_prior": "edge and texture each total weight 0.5",
            "mapping": "piecewise constant with nearest terminal-block extrapolation",
            "fit_scope": "inside every outer UDED training fold",
        },
        "contract_checks": _contract_checks(),
        "unchanged": [
            "five retained raw features and fold-fitted singleton weights",
            "distorted-Choquet gamma 0.55",
            "gate strength 2.0 and floor 0.10",
            "median-conditioned grayscale Scharr+NMS localizer and threshold fitting",
        ],
    }
    summary["promotion_rule"] = (
        "Conjunctive: UDED aggregate F1 delta at least +0.002, precision delta at "
        "least -0.002, recall delta at least -0.003, nonnegative mean paired fold-F1, "
        "and at least 9/15 fold wins. The official attachment must complete; BSDS500-"
        "validation ODS delta must be at least +0.002 and OIS/AP deltas must both be "
        "nonnegative. Isotonic contracts, exact positive-score support equality, and "
        "the deterministic preview must pass."
    )
    summary["visual_preview"]["columns"][-1] = "mean_isotonic_calibrated_membership"
    summary["files"] = [
        "summary.json", "variant_ranking.csv", "fold_results.csv",
        "per_image_metrics.csv", "isotonic_diagnostics.csv",
        "best_method_preview.png", "official_eval_manifest.json",
    ]
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def main() -> int:
    export_mode = "--export-bsds" in sys.argv
    if "--seed" not in sys.argv:
        sys.argv.extend(["--seed", "20261009"])
    harness.EXPERIMENT_ID = EXPERIMENT_ID
    harness.DEFAULT_OUT = DEFAULT_OUT
    harness.VARIANTS = VARIANTS
    harness.learn_banks = _learn_banks
    harness._context_pairs = _context_pairs
    harness._score_pairs = _score_pairs
    harness._rank_contract_checks = _contract_checks
    harness._write_official_manifest = _write_official_manifest
    code = int(harness.main())
    if code == 0:
        _rewrite_outputs(export_mode)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
