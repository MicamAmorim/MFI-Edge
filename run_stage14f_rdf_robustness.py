from __future__ import annotations

"""Stage 14f: paired synthetic robustness falsification for one RDF operator.

The five-feature positive bank is frozen from Stage 12d / Stage 14c. The only
model change is standard distorted-Choquet versus d-CC (FBPC, absolute RDF).
Thresholds are fitted on a fixed clean calibration subset and frozen across all
paired corruption conditions in the synthetic validation development split.
"""

from pathlib import Path
import argparse
import json

import numpy as np
import pandas as pd

from benchmark_uded_stage7 import fixed_eval, selection_metric
from run_stage12b_fuzzy_signature import membership_stack, distorted_choquet, prepare
from src.advanced_fuzzy_v2 import d_choquet_family
from src.bipolar_fuzzy import context_gate
from src.ch_mfi import distorted_probability_capacity
from synthetic_v2 import BASE as SYNTHETIC_BASE, build_split, make_sample

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "local_dev" / "stage14f_rdf_robustness"
DEFAULT_BANK = ROOT / "results" / "local_dev" / "stage12d_bipolar_cv" / "frozen_candidates.json"
FEATURES = (
    "gabor4_s5",
    "hessian_s7",
    "gabor4_s13",
    "hessian_s13",
    "gabor4_scale_persistence",
)
GAMMA = 0.55
GATE_STRENGTH = 2.0
GATE_FLOOR = 0.10
SEVERITIES = (0.35, 0.65, 1.0)
CORRUPTIONS = ("gaussian", "blur", "texture", "compound")
VARIANTS = ("standard_choquet", "dcc_fbpc_abs")


def _frozen_compact_bank(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    bank = payload["positive_bank"]
    selected = [row for row in bank if row["feature"] in FEATURES]
    if {row["feature"] for row in selected} != set(FEATURES):
        raise RuntimeError("Stage-12d frozen bank is missing a required compact feature")
    selected.sort(key=lambda row: FEATURES.index(row["feature"]))
    total = sum(float(row["weight"]) for row in selected)
    for row in selected:
        row["weight"] = float(row["weight"]) / total
    return selected


def _condition(base: dict, family: str | None = None, severity: float = 0.0) -> dict:
    cfg = {
        "n": 96,
        "seed": int(base["seed"]),
        "primitive": str(base["primitive"]),
        "angle": float(base["angle"]),
        "contrast": float(base["contrast"]),
        "noise": "none",
        "noise_level": 0.0,
        "blur": 0.0,
        "motion": 0,
        "illumination": 0.0,
        "texture": 0.0,
        "gap_length": 0,
    }
    if family == "gaussian":
        cfg.update(noise="gaussian", noise_level=0.004 + 0.016 * severity)
    elif family == "blur":
        cfg["blur"] = 0.5 + 1.5 * severity
    elif family == "texture":
        cfg["texture"] = 0.025 + 0.075 * severity
    elif family == "compound":
        cfg.update(
            noise="gaussian",
            noise_level=0.005 + 0.01 * severity,
            blur=0.5 + 0.8 * severity,
            texture=0.02 + 0.04 * severity,
            illumination=0.08 * severity,
        )
    elif family not in (None, "clean"):
        raise ValueError(f"unsupported predeclared corruption: {family}")
    return cfg


def _capacity(bank: list[dict]) -> dict:
    weights = np.asarray([row["weight"] for row in bank], dtype=float)
    return distorted_probability_capacity(weights, gamma=GAMMA)


def _maps(item: dict, names: list[str], bank: list[dict], capacity: dict) -> tuple[np.ndarray, np.ndarray]:
    prepared, _ = prepare([item])
    row = prepared[0]
    memberships, weights = membership_stack(row, names, bank, "edge")
    control = distorted_choquet(memberships, weights, GAMMA)
    candidate = d_choquet_family(
        memberships,
        capacity,
        mode="dcc",
        F="FBPC",
        rdf="abs",
    )
    return (
        context_gate(row["scharr"], control, GATE_STRENGTH, GATE_FLOOR),
        context_gate(row["scharr"], candidate, GATE_STRENGTH, GATE_FLOOR),
    )


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
    capacity = _capacity(bank)

    # Fixed row-order split: first half calibrates clean-only thresholds; the
    # second half supplies paired clean/corrupt development evaluation.
    calibration_rows = manifest.iloc[::2]
    evaluation_rows = manifest.iloc[1::2]
    calibration = {name: [] for name in VARIANTS}
    evaluated: dict[str, dict] = {}

    def make_item(row: pd.Series, family: str | None, severity: float = 0.0) -> dict:
        base = row.to_dict()
        cfg = _condition(base, family, severity)
        image, gt = make_sample(cfg)
        label = "clean" if family is None else f"{family}_s{severity:.2f}"
        return {
            "id": f"{base['id']}__{label}",
            "img": np.round(np.clip(image, 0.0, 1.0) * 255).astype(np.uint8),
            "gt": np.asarray(gt, dtype=bool),
            "condition": label,
            "severity": 0.0 if family is None else float(severity),
        }

    # Prepare each calibration image once; clean maps fit each model's threshold.
    names: list[str] | None = None
    for _, row in calibration_rows.iterrows():
        item = make_item(row, None)
        prepared, current_names = prepare([item])
        names = current_names
        memberships, weights = membership_stack(prepared[0], names, bank, "edge")
        control_map = distorted_choquet(memberships, weights, GAMMA)
        candidate_map = d_choquet_family(memberships, capacity, mode="dcc", F="FBPC", rdf="abs")
        for variant, context in ((VARIANTS[0], control_map), (VARIANTS[1], candidate_map)):
            score = context_gate(prepared[0]["scharr"], context, GATE_STRENGTH, GATE_FLOOR)
            calibration[variant].append((score, item))
    assert names is not None
    thresholds = {
        variant: float(selection_metric(
            [pair[0] for pair in calibration[variant]],
            [pair[1] for pair in calibration[variant]],
            args.thresholds,
        )["threshold"])
        for variant in VARIANTS
    }

    eval_items: dict[str, list[dict]] = {"clean": []}
    eval_scores: dict[str, dict[str, list[np.ndarray]]] = {
        variant: {"clean": []} for variant in VARIANTS
    }
    conditions = [(None, 0.0)] + [
        (family, severity) for family in CORRUPTIONS for severity in SEVERITIES
    ]
    for family, severity in conditions:
        label = "clean" if family is None else f"{family}_s{severity:.2f}"
        eval_items[label] = []
        for variant in VARIANTS:
            eval_scores[variant][label] = []
        for _, row in evaluation_rows.iterrows():
            item = make_item(row, family, severity)
            control_score, candidate_score = _maps(item, names, bank, capacity)
            eval_items[label].append(item)
            eval_scores[VARIANTS[0]][label].append(control_score)
            eval_scores[VARIANTS[1]][label].append(candidate_score)

    metrics: dict[str, dict[str, dict]] = {variant: {} for variant in VARIANTS}
    metric_rows = []
    for variant in VARIANTS:
        for label, items in eval_items.items():
            score, _, per_image = fixed_eval(eval_scores[variant][label], items, thresholds[variant])
            metrics[variant][label] = score
            metric_rows.append({
                "variant": variant,
                "condition": label,
                "family": "clean" if label == "clean" else label.rsplit("_s", 1)[0],
                "severity": 0.0 if label == "clean" else float(label.rsplit("_s", 1)[1]),
                "threshold_fitted_on_clean_calibration": thresholds[variant],
                "pooled_F1": score["F1"],
                "macro_image_F1": score["mean_image_F1"],
                "per_image_metrics": per_image,
            })
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{k: v for k, v in row.items() if k != "per_image_metrics"} for row in metric_rows]).to_csv(
        out / "condition_metrics.csv", index=False
    )
    pd.DataFrame([
        {"variant": row["variant"], "condition": row["condition"], **per}
        for row in metric_rows for per in row["per_image_metrics"]
    ]).to_csv(out / "per_image_metrics.csv", index=False)

    clean_f1 = {v: float(metrics[v]["clean"]["mean_image_F1"]) for v in VARIANTS}
    degradation_rows = []
    family_deltas = {family: [] for family in CORRUPTIONS}
    for family in CORRUPTIONS:
        for severity in SEVERITIES:
            label = f"{family}_s{severity:.2f}"
            deltas = {
                variant: float(metrics[variant][label]["mean_image_F1"] - clean_f1[variant])
                for variant in VARIANTS
            }
            advantage = deltas[VARIANTS[1]] - deltas[VARIANTS[0]]
            family_deltas[family].append(advantage)
            degradation_rows.append({
                "family": family,
                "severity": severity,
                "standard_clean_F1": clean_f1[VARIANTS[0]],
                "dcc_clean_F1": clean_f1[VARIANTS[1]],
                "standard_corrupt_F1": float(metrics[VARIANTS[0]][label]["mean_image_F1"]),
                "dcc_corrupt_F1": float(metrics[VARIANTS[1]][label]["mean_image_F1"]),
                "standard_degradation_delta_F1": deltas[VARIANTS[0]],
                "dcc_degradation_delta_F1": deltas[VARIANTS[1]],
                "dcc_minus_standard_degradation_delta_F1": advantage,
            })
    degradation_path = out / "degradation_by_family_severity.csv"
    pd.DataFrame(degradation_rows).to_csv(degradation_path, index=False)
    mean_advantage = float(np.mean([row["dcc_minus_standard_degradation_delta_F1"] for row in degradation_rows]))
    clean_delta = clean_f1[VARIANTS[1]] - clean_f1[VARIANTS[0]]
    family_wins = sum(float(np.mean(values)) > 0.0 for values in family_deltas.values())
    summary = {
        "stage": "14f-rdf-robustness-falsification",
        "dataset_role": "synthetic_v2 validation only; development",
        "external_or_uded_data_used": False,
        "calibration": "first 20 manifest rows, clean-only threshold fit per variant; fixed thresholds on evaluation conditions",
        "evaluation": "last 20 manifest rows; paired clean reference and same-base generated corruptions",
        "fixed_architecture": {
            "features": list(FEATURES),
            "feature_parameters_source": "Stage 12d frozen positive bank; selected compact features and renormalized frozen weights",
            "localizer": "Scharr+NMS",
            "gate": {"strength": GATE_STRENGTH, "floor": GATE_FLOOR},
            "gamma": GAMMA,
        },
        "comparison": "positive distorted-Choquet control vs d-CC with FBPC and absolute RDF; only aggregation mechanism changes",
        "corruptions": {family: list(SEVERITIES) for family in CORRUPTIONS},
        "primary_metric": "mean image F1, averaged equally across 12 corruption family-severity cells",
        "primary_criterion": "d-CC minus standard clean-referenced degradation delta >= +0.01 mean F1; clean d-CC minus standard >= -0.01; positive mean degradation advantage in at least 3 of 4 families",
        "primary_result": {
            "mean_degradation_advantage_F1": mean_advantage,
            "clean_delta_F1_dcc_minus_standard": clean_delta,
            "families_with_positive_mean_advantage": int(family_wins),
            "criterion_met": bool(mean_advantage >= 0.01 and clean_delta >= -0.01 and family_wins >= 3),
        },
        "thresholds": thresholds,
        "metrics": metrics,
        "per_condition_metrics_file": "condition_metrics.csv",
        "per_image_metrics_file": "per_image_metrics.csv",
        "degradation_file": "degradation_by_family_severity.csv",
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE14F_RDF_ROBUSTNESS_COMPLETE")
    print(out / "summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
