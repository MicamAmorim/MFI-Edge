from __future__ import annotations

"""Stage 14h: paired synthetic falsification of gravitational conditioning.

Compare the retained five-feature positive distorted-Choquet controller with
the same controller after replacing its median prefilter by the repository's
fixed grayscale gravitational smoother. Calibration and evaluation follow the
same clean-only paired synthetic validation protocol as Stage 14f.
"""

from pathlib import Path
import argparse
import json

import numpy as np
import pandas as pd

from benchmark_uded_stage7 import fixed_eval, selection_metric
from run_stage12b_fuzzy_signature import membership_stack, distorted_choquet
from run_stage14f_rdf_robustness import (
    _condition, _frozen_compact_bank,
    FEATURES, GAMMA, GATE_STRENGTH, GATE_FLOOR, CORRUPTIONS, SEVERITIES,
)
from src.classical_detectors import detector_score
from src.conditioning import apply_conditioning
from src.pipeline import precompute_multiscale_features
from src.postprocess import gradient_orientation, non_maximum_suppression
from benchmark_uded import SCALES
from src.bipolar_fuzzy import context_gate
from synthetic_v2 import BASE as SYNTHETIC_BASE, build_split, make_sample

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "local_dev" / "stage14h_gravity_smoothing"
DEFAULT_BANK = ROOT / "results" / "local_dev" / "stage12d_bipolar_cv" / "frozen_candidates.json"
VARIANTS = ("median_control", "gravitational")
GRAVITY = {"G": 0.05, "omega_c": 20.0, "iterations": 30,
           "interaction_radius_frac": 0.02, "step": 0.20}


def _prepare(item: dict, method: str) -> tuple[dict, list[str]]:
    pre_img = apply_conditioning(item["img"], method, **(GRAVITY if method == "gravity" else {"size": 3}))
    feats, names = precompute_multiscale_features(pre_img, SCALES, feature_mode="oriented_ms")
    ori = gradient_orientation(pre_img, 1.0)
    scharr = non_maximum_suppression(detector_score(pre_img, "scharr", 1.0), ori)
    return {**item, "pre_img": pre_img, "features": feats, "orientation": ori, "scharr": scharr}, names


def _score(item: dict, names: list[str], bank: list[dict], method: str) -> np.ndarray:
    row, current_names = _prepare(item, method)
    if current_names != names:
        raise RuntimeError("Feature order changed between synthetic samples")
    memberships, weights = membership_stack(row, names, bank, "edge")
    context = distorted_choquet(memberships, weights, GAMMA)
    return context_gate(row["scharr"], context, GATE_STRENGTH, GATE_FLOOR)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic-root", default=str(SYNTHETIC_BASE))
    parser.add_argument("--frozen-bank", default=str(DEFAULT_BANK))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--thresholds", type=int, default=41)
    args = parser.parse_args()

    root = Path(args.synthetic_root)
    manifest_path = root / "validation" / "manifest.csv"
    if not manifest_path.exists():
        if root.resolve() != SYNTHETIC_BASE.resolve():
            raise FileNotFoundError(f"No synthetic validation manifest at {manifest_path}")
        build_split("validation", 40, 41000)
    manifest = pd.read_csv(manifest_path).reset_index(drop=True)
    if len(manifest) != 40:
        raise RuntimeError(f"Expected the fixed 40-item synthetic validation split, found {len(manifest)}")
    bank = _frozen_compact_bank(Path(args.frozen_bank))
    _capacity(bank)  # Validate the frozen bank's normalized weights.
    calibration_rows, evaluation_rows = manifest.iloc[::2], manifest.iloc[1::2]

    def make_item(row: pd.Series, family: str | None, severity: float = 0.0) -> dict:
        base = row.to_dict()
        image, gt = make_sample(_condition(base, family, severity))
        label = "clean" if family is None else f"{family}_s{severity:.2f}"
        return {"id": f"{base['id']}__{label}",
                "img": np.round(np.clip(image, 0.0, 1.0) * 255).astype(np.uint8),
                "gt": np.asarray(gt, dtype=bool), "condition": label,
                "severity": 0.0 if family is None else float(severity)}

    names = None
    calibration = {variant: [] for variant in VARIANTS}
    for _, row in calibration_rows.iterrows():
        item = make_item(row, None)
        for variant, method in zip(VARIANTS, ("median", "gravity")):
            score = _score(item, names, bank, method) if names is not None else None
            if names is None:
                prepared, names = _prepare(item, method)
                memberships, weights = membership_stack(prepared, names, bank, "edge")
                context = distorted_choquet(memberships, weights, GAMMA)
                score = context_gate(prepared["scharr"], context, GATE_STRENGTH, GATE_FLOOR)
            calibration[variant].append((score, item))
    thresholds = {v: float(selection_metric([x[0] for x in calibration[v]],
                                             [x[1] for x in calibration[v]],
                                             args.thresholds)["threshold"]) for v in VARIANTS}

    conditions = [(None, 0.0)] + [(f, s) for f in CORRUPTIONS for s in SEVERITIES]
    eval_items, eval_scores = {}, {v: {} for v in VARIANTS}
    for family, severity in conditions:
        label = "clean" if family is None else f"{family}_s{severity:.2f}"
        eval_items[label] = []
        for v in VARIANTS:
            eval_scores[v][label] = []
        for _, row in evaluation_rows.iterrows():
            item = make_item(row, family, severity)
            eval_items[label].append(item)
            for variant, method in zip(VARIANTS, ("median", "gravity")):
                eval_scores[variant][label].append(_score(item, names, bank, method))

    results, image_rows, condition_rows = {v: {} for v in VARIANTS}, [], []
    for variant in VARIANTS:
        for label, items in eval_items.items():
            met, _, per_image = fixed_eval(eval_scores[variant][label], items, thresholds[variant])
            results[variant][label] = met
            condition_rows.append({"variant": variant, "condition": label,
                                   "mean_image_F1": met["mean_image_F1"], "pooled_F1": met["F1"]})
            image_rows.extend({"variant": variant, "condition": label, **x} for x in per_image)

    clean = {v: float(results[v]["clean"]["mean_image_F1"]) for v in VARIANTS}
    family_adv = {f: [] for f in CORRUPTIONS}
    degradation = []
    for family in CORRUPTIONS:
        for severity in SEVERITIES:
            label = f"{family}_s{severity:.2f}"
            scores = {v: float(results[v][label]["mean_image_F1"]) for v in VARIANTS}
            advantage = scores["gravitational"] - scores["median_control"]
            family_adv[family].append(advantage)
            degradation.append({"family": family, "severity": severity,
                                "median_F1": scores["median_control"], "gravity_F1": scores["gravitational"],
                                "gravity_minus_median_F1": advantage,
                                "median_degradation": scores["median_control"] - clean["median_control"],
                                "gravity_degradation": scores["gravitational"] - clean["gravitational"]})
    mean_adv = float(np.mean([x["gravity_minus_median_F1"] for x in degradation]))
    clean_delta = clean["gravitational"] - clean["median_control"]
    positive_families = sum(float(np.mean(x)) > 0 for x in family_adv.values())
    criterion = mean_adv >= .005 and clean_delta >= -.01 and positive_families >= 3
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(condition_rows).to_csv(out / "condition_metrics.csv", index=False)
    pd.DataFrame(image_rows).to_csv(out / "per_image_metrics.csv", index=False)
    pd.DataFrame(degradation).to_csv(out / "degradation_by_family_severity.csv", index=False)
    summary = {"stage": "14h-gravitational-smoothing-falsification",
               "dataset_role": "synthetic_v2 validation only; development", "external_or_uded_data_used": False,
               "calibration": "20 even-index clean images; thresholds frozen for all conditions",
               "evaluation": "20 odd-index paired clean/corrupt images; Gaussian noise, blur, texture, compound at 3 fixed severities",
               "fixed_architecture": {"features": list(FEATURES), "localizer": "Scharr+NMS",
                                      "gate": {"strength": GATE_STRENGTH, "floor": GATE_FLOOR}, "gamma": GAMMA},
               "comparison": "median 3x3 conditioning versus gravitational smoothing replacing median before both descriptor and Scharr branches",
               "gravity_parameters": GRAVITY,
               "primary_metric": "mean per-image absolute F1 advantage averaged equally across 12 corruption cells",
               "promotion_rule": "mean corrupted F1 advantage >= +0.005; clean delta >= -0.01; positive mean advantage in at least 3 of 4 families",
               "primary_result": {"mean_corrupted_F1_advantage": mean_adv, "clean_F1_delta": clean_delta,
                                  "families_with_positive_advantage": positive_families, "criterion_met": criterion},
               "thresholds": thresholds, "metrics": results,
               "files": ["condition_metrics.csv", "per_image_metrics.csv", "degradation_by_family_severity.csv"]}
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE14H_GRAVITY_SMOOTHING_COMPLETE")
    print(out / "summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
