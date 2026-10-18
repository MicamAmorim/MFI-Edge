from __future__ import annotations

"""Stage 18p: fixed median-OWA aggregation of compact positive context."""

from pathlib import Path
import argparse
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import run_stage16r_sugeno_context as harness
from src.median_owa_context import median_owa_context


EXPERIMENT_ID = "stage18p_median_owa_context"
DEFAULT_OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
VARIANTS = ("compact_mfi", "median_owa_compact_mfi")


def _aggregation_contract_checks() -> dict:
    probe = np.asarray(
        [[0.05, 0.25, 0.40, 0.70, 0.95], [0.80, 0.10, 0.55, 0.35, 0.65]],
        dtype=np.float64,
    )
    raised = np.clip(probe + 0.03, 0.0, 1.0)
    first = median_owa_context(probe)
    second = median_owa_context(probe)
    raised_out = median_owa_context(raised)
    constants = np.asarray([0.0, 0.2, 0.5, 0.8, 1.0], dtype=np.float64)
    idempotent = np.asarray(
        [median_owa_context(np.full((1, 5), value))[0] for value in constants]
    )
    permuted = median_owa_context(probe[:, [3, 0, 4, 1, 2]])
    expected = np.sort(probe, axis=-1)[:, 2]
    localizer = np.asarray([[0.0, 0.2], [0.7, 0.0]], dtype=np.float32)
    gated_low = harness.context_gate(localizer, np.zeros_like(localizer), harness.STRENGTH, harness.FLOOR)
    gated_high = harness.context_gate(localizer, np.ones_like(localizer), harness.STRENGTH, harness.FLOOR)
    checks = {
        "finite_and_bounded": bool(np.all(np.isfinite(first)) and np.all((first >= 0.0) & (first <= 1.0))),
        "repeat_bitwise_equal": bool(np.array_equal(first, second)),
        "componentwise_monotone": bool(np.all(raised_out + 1.0e-7 >= first)),
        "idempotent": bool(np.allclose(idempotent, constants, atol=1.0e-7, rtol=0.0)),
        "permutation_invariant": bool(np.array_equal(first, permuted)),
        "central_order_statistic_exact": bool(np.allclose(first, expected, atol=1.0e-7, rtol=0.0)),
        "score_support_preserved": bool(
            np.array_equal(gated_low > 0.0, localizer > 0.0)
            and np.array_equal(gated_high > 0.0, localizer > 0.0)
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(f"median-OWA aggregation contract failure: {checks}")
    return checks


def _write_official_manifest(out: Path, seed: int) -> Path:
    manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [{
            "name": VARIANTS[1],
            "export": {
                "script": "run_stage18p_median_owa_context.py",
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


def _configure_harness() -> None:
    harness.EXPERIMENT_ID = EXPERIMENT_ID
    harness.DEFAULT_OUT = DEFAULT_OUT
    harness.VARIANTS = VARIANTS
    harness.distorted_capacity_sugeno = median_owa_context
    harness._aggregation_contract_checks = _aggregation_contract_checks
    harness._write_official_manifest = _write_official_manifest


def _rename_diagnostics(directory: Path) -> None:
    old = directory / "sugeno_diagnostics.csv"
    new = directory / "median_owa_diagnostics.csv"
    if old.exists():
        content = old.read_text(encoding="utf-8").replace(
            "mean_sugeno_context", "mean_median_owa_context"
        )
        new.write_text(content, encoding="utf-8")
        old.unlink()


def _finalize_development(out: Path) -> None:
    _rename_diagnostics(out)
    path = out / "summary.json"
    summary = json.loads(path.read_text(encoding="utf-8"))
    summary["stage"] = "18p-median-owa-context"
    summary["role"] = "generation_2_median_owa_context_falsification"
    summary["mechanism"] = {
        "description": "replace only distorted-Choquet arithmetic accumulation by the median OWA central order statistic over the same five memberships",
        "implementation_fidelity": "exact five-input median OWA from Yager's OWA family; repository application, not a published complete edge detector",
        "parameters": {"ordered_weight_vector": [0.0, 0.0, 1.0, 0.0, 0.0], "membership_count": 5},
        "contract_checks": _aggregation_contract_checks(),
        "unchanged": [
            "five retained features and fold-fitted membership calibration",
            "gate strength 2.0 and floor 0.10",
            "median-conditioned grayscale Scharr+NMS localizer",
            "outer-fold threshold fitting",
        ],
    }
    summary["promotion_rule"] = (
        "Conjunctive: UDED aggregate F1 delta at least +0.002, precision delta nonnegative, "
        "recall delta at least -0.003, mean paired fold-F1 nonnegative, and at least 9/15 fold wins. "
        "The official attachment must complete; BSDS500-validation ODS delta must be at least +0.002 "
        "and OIS/AP deltas must both be nonnegative. Median-OWA contract checks, exact score-support "
        "preservation, and the deterministic preview are required."
    )
    deltas = summary["uded_gate"]["deltas"]
    summary["uded_gate"]["met"] = bool(
        deltas["aggregate_F1"] >= 0.002
        and deltas["aggregate_precision"] >= 0.0
        and deltas["aggregate_recall"] >= -0.003
        and deltas["mean_fold_F1"] >= 0.0
        and deltas["fold_wins"] >= 9
    )
    summary["visual_preview"]["columns"][-2:] = [
        "median_OWA_candidate_out_of_fold_prediction",
        "median_OWA_context",
    ]
    summary["files"] = [
        "summary.json", "variant_ranking.csv", "fold_results.csv",
        "per_image_metrics.csv", "median_owa_diagnostics.csv",
        "best_method_preview.png", "official_eval_manifest.json",
    ]
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def _finalize_export(output_dir: Path) -> None:
    _rename_diagnostics(output_dir)
    path = output_dir / "export_manifest.json"
    metadata = json.loads(path.read_text(encoding="utf-8"))
    metadata.pop("sugeno_contract", None)
    metadata["method"] = VARIANTS[1]
    metadata["median_owa_contract"] = {
        "formula": "third order statistic of five calibrated memberships",
        "ordered_weight_vector": [0.0, 0.0, 1.0, 0.0, 0.0],
        "checks": _aggregation_contract_checks(),
        "localizer": "unchanged median-conditioned grayscale Scharr+NMS",
    }
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def main() -> int:
    _configure_harness()
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
        if result == 0:
            _finalize_export(Path(args.output_dir))
        return result
    result = harness.run_experiment(args)
    if result == 0:
        _finalize_development(Path(args.out))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
