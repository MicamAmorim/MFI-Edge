from __future__ import annotations

"""Stage 19D: bounded aggregation-family identification on development data."""

from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from scipy.stats import rankdata

import run_stage19b_descriptor_relevance_atlas as atlas
import run_stage19c_pairwise_complementarity as pairwise
from benchmark_uded import DEFAULT_UDED
from src.bipolar_fuzzy import distorted_choquet
from src.fuzzy_measures import interaction_matrix, shapley_values, tail_masks_from_order
from src.measure_learning import balanced_sample, learn_2additive


EXPERIMENT_ID = "stage19d_aggregation_identification"
OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
SHORTLIST_PATH = ROOT / "results/local_dev/stage19c_pairwise_complementarity/stage19d_shortlist.json"
EXPECTED_SHORTLIST = (
    "structure_tensor_coherence", "gabor4_s13", "semiglobal_changepoint",
    "hessian_s13", "brightness_entropy", "gabor4_s5",
)
INCUMBENT = tuple(atlas.DESCRIPTORS[:5])
FAMILIES = (
    "distorted_choquet_control",
    "nonnegative_additive_logistic",
    "monotone_2additive_choquet",
)
SEED = 20261020
FOLDS = 5
RIDGE = 1.0e-3
CAPACITY_RIDGE = 1.0e-4
CAPACITY_SAMPLES = 30000
GAMMA = 0.55


def _fold(dataset: str, image_id: str) -> int:
    token = hashlib.sha256(f"{SEED}:stage19d:{dataset}:{image_id}".encode()).digest()
    return int.from_bytes(token[:8], "little") % FOLDS


def _weights(y: np.ndarray) -> np.ndarray:
    y = np.asarray(y, float)
    p = float(np.mean(y))
    return np.where(y >= 0.5, 0.5 / max(p, 1e-9), 0.5 / max(1.0 - p, 1e-9))


def _fit_memberships(x: np.ndarray, y: np.ndarray) -> dict[str, np.ndarray]:
    yb = np.asarray(y) >= 0.5
    midpoint, scale, direction, reliability = [], [], [], []
    for column in np.asarray(x, float).T:
        pos, neg = column[yb], column[~yb]
        pm, nm = float(np.median(pos)), float(np.median(neg))
        both = np.concatenate([pos, neg])
        q25, q75 = np.quantile(both, [0.25, 0.75])
        s = max(float(q75 - q25), 0.05)
        d = 1.0 if pm >= nm else -1.0
        midpoint.append(0.5 * (pm + nm)); scale.append(s); direction.append(d)
        pooled = 0.5 * (float(np.std(pos)) + float(np.std(neg))) + 0.05
        reliability.append(max(d * (float(np.mean(pos)) - float(np.mean(neg))) / pooled, 1e-6))
    rel = np.asarray(reliability, float); rel /= rel.sum()
    return {"midpoint": np.asarray(midpoint), "scale": np.asarray(scale), "direction": np.asarray(direction), "reliability": rel}


def _apply_memberships(x: np.ndarray, spec: dict[str, np.ndarray]) -> np.ndarray:
    z = spec["direction"] * (np.asarray(x, float) - spec["midpoint"]) / spec["scale"]
    return expit(np.clip(z, -20.0, 20.0))


def _fit_positive_logistic(x: np.ndarray, y: np.ndarray, ridge: float = RIDGE) -> np.ndarray:
    x = np.asarray(x, float); y = np.asarray(y, float); w = _weights(y)
    def objective(beta: np.ndarray) -> tuple[float, np.ndarray]:
        z = beta[0] + x @ beta[1:]
        loss = np.sum(w * (np.logaddexp(0.0, z) - y * z)) / np.sum(w)
        loss += 0.5 * ridge * float(beta[1:] @ beta[1:])
        residual = w * (expit(z) - y) / np.sum(w)
        gradient = np.r_[np.sum(residual), x.T @ residual + ridge * beta[1:]]
        return float(loss), gradient
    result = minimize(objective, np.zeros(x.shape[1] + 1), jac=True, method="L-BFGS-B",
                      bounds=[(None, None), *[(0.0, None)] * x.shape[1]], options={"maxiter": 250})
    if not result.success or not np.all(np.isfinite(result.x)):
        raise RuntimeError(f"nonnegative logistic fit failed: {result.message}")
    return np.asarray(result.x)


def _fit_scalar_calibration(score: np.ndarray, y: np.ndarray) -> np.ndarray:
    return _fit_positive_logistic(np.asarray(score, float)[:, None], y, ridge=RIDGE)


def _choquet_from_table(x: np.ndarray, table: np.ndarray) -> np.ndarray:
    x = np.clip(np.asarray(x, float), 0.0, 1.0)
    order = np.argsort(x, axis=1, kind="stable")
    xs = np.take_along_axis(x, order, axis=1)
    previous = np.column_stack([np.zeros(len(x)), xs[:, :-1]])
    masks = tail_masks_from_order(order)
    return np.sum((xs - previous) * np.asarray(table, float)[masks], axis=1)


def _fit_family(name: str, frame: pd.DataFrame, shortlist: tuple[str, ...], seed: int) -> dict[str, object]:
    columns = INCUMBENT if name == FAMILIES[0] else shortlist
    raw = frame.loc[:, list(columns)].to_numpy(float)
    y = frame["tolerant_union"].to_numpy(float)
    membership = _fit_memberships(raw, y)
    x = _apply_memberships(raw, membership)
    model: dict[str, object] = {"name": name, "columns": columns, "membership": membership}
    if name == FAMILIES[0]:
        score = distorted_choquet(x, membership["reliability"], GAMMA).reshape(-1)
        model["weights"] = membership["reliability"]
        model["calibration"] = _fit_scalar_calibration(score, y)
    elif name == FAMILIES[1]:
        model["beta"] = _fit_positive_logistic(x, y)
    else:
        bx, by = balanced_sample(x, y, max_samples=CAPACITY_SAMPLES, seed=seed)
        capacity = learn_2additive(bx, by, ridge=CAPACITY_RIDGE)
        if not bool(capacity["fit_success"]):
            raise RuntimeError("2-additive constrained fit did not converge")
        table = np.asarray(capacity["capacity_table"], float)
        score = _choquet_from_table(x, table)
        model["capacity"] = capacity
        model["calibration"] = _fit_scalar_calibration(score, y)
    return model


def _predict(model: dict[str, object], frame: pd.DataFrame) -> np.ndarray:
    raw = frame.loc[:, list(model["columns"])].to_numpy(float)
    x = _apply_memberships(raw, model["membership"])
    name = str(model["name"])
    if name == FAMILIES[0]:
        score = distorted_choquet(x, np.asarray(model["weights"]), GAMMA).reshape(-1)
        beta = np.asarray(model["calibration"]); return expit(beta[0] + beta[1] * score)
    if name == FAMILIES[1]:
        beta = np.asarray(model["beta"]); return expit(beta[0] + x @ beta[1:])
    table = np.asarray(model["capacity"]["capacity_table"], float)
    score = _choquet_from_table(x, table)
    beta = np.asarray(model["calibration"]); return expit(beta[0] + beta[1] * score)


def _auc(y: np.ndarray, p: np.ndarray) -> float:
    yb = np.asarray(y) >= 0.5; n1, n0 = int(yb.sum()), int((~yb).sum())
    if not n1 or not n0: return float("nan")
    ranks = rankdata(p, method="average")
    return float((ranks[yb].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def _ap(y: np.ndarray, p: np.ndarray) -> float:
    yb = np.asarray(y) >= 0.5
    if not np.any(yb): return float("nan")
    order = np.argsort(-np.asarray(p), kind="stable"); labels = yb[order]
    precision = np.cumsum(labels) / np.arange(1, len(labels) + 1)
    return float(np.sum(precision * labels) / np.sum(labels))


def _metrics(frame: pd.DataFrame, prediction: np.ndarray) -> dict[str, float]:
    y = frame["tolerant_union"].to_numpy(float); p = np.clip(prediction, 1e-8, 1 - 1e-8)
    loss = -(y * np.log(p) + (1 - y) * np.log(1 - p)); w = _weights(y)
    ece = 0.0
    for lo in np.linspace(0.0, 0.9, 10):
        mask = (p >= lo) & (p < lo + 0.1 if lo < 0.9 else p <= 1.0)
        if np.any(mask): ece += float(np.mean(mask) * abs(np.mean(p[mask]) - np.mean(y[mask])))
    return {"balanced_logloss": float(np.sum(w * loss) / np.sum(w)), "logloss": float(np.mean(loss)),
            "brier": float(np.mean((p - y) ** 2)), "roc_auc": _auc(y, p), "average_precision": _ap(y, p),
            "ece10": ece}


def _record_parameters(model: dict[str, object], dataset: str, fold: str,
                       params: list[dict[str, object]], shapley: list[dict[str, object]],
                       interactions: list[dict[str, object]]) -> None:
    name = str(model["name"]); columns = tuple(model["columns"])
    if name == FAMILIES[0]:
        for feature, value in zip(columns, np.asarray(model["weights"])):
            params.append({"dataset": dataset, "fold": fold, "family": name, "parameter": feature, "value": float(value)})
    elif name == FAMILIES[1]:
        beta = np.asarray(model["beta"])
        params.append({"dataset": dataset, "fold": fold, "family": name, "parameter": "intercept", "value": float(beta[0])})
        for feature, value in zip(columns, beta[1:]):
            params.append({"dataset": dataset, "fold": fold, "family": name, "parameter": feature, "value": float(value)})
    else:
        cap = model["capacity"]; sv = np.asarray(cap["shapley"]); im = np.asarray(cap["interaction"])
        for feature, value in zip(columns, sv):
            shapley.append({"dataset": dataset, "fold": fold, "descriptor": feature, "shapley": float(value)})
        for i, a in enumerate(columns):
            for j, b in enumerate(columns[i + 1:], i + 1):
                interactions.append({"dataset": dataset, "fold": fold, "descriptor_a": a, "descriptor_b": b, "interaction": float(im[i, j])})


def _evaluate(samples: pd.DataFrame, shortlist: tuple[str, ...]) -> tuple[pd.DataFrame, ...]:
    folds, transfers, params, shapley, interactions = [], [], [], [], []
    domains = sorted(samples["dataset"].unique())
    for dataset in domains:
        domain = pairwise._model_frame(samples[samples["dataset"] == dataset]).reset_index(drop=True)
        domain["fold"] = domain["image_id"].map(lambda image_id: _fold(dataset, str(image_id)))
        for fold in range(FOLDS):
            train, test = domain[domain["fold"] != fold], domain[domain["fold"] == fold]
            for family in FAMILIES:
                model = _fit_family(family, train, shortlist, SEED + 1000 * domains.index(dataset) + fold)
                row = {"dataset": dataset, "fold": fold, "family": family, **_metrics(test, _predict(model, test))}
                folds.append(row); _record_parameters(model, dataset, str(fold), params, shapley, interactions)
    for source in domains:
        train = pairwise._model_frame(samples[samples["dataset"] == source]).reset_index(drop=True)
        for target in domains:
            if target == source: continue
            test = pairwise._model_frame(samples[samples["dataset"] == target]).reset_index(drop=True)
            for family in FAMILIES:
                model = _fit_family(family, train, shortlist, SEED + 10000 + domains.index(source))
                transfers.append({"source_dataset": source, "target_dataset": target, "family": family,
                                  **_metrics(test, _predict(model, test))})
                _record_parameters(model, source, f"transfer_to:{target}", params, shapley, interactions)
    return tuple(pd.DataFrame(rows) for rows in (folds, transfers, params, shapley, interactions))


def _summarize(folds: pd.DataFrame, transfers: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    summary = folds.groupby(["dataset", "family"], as_index=False).agg(
        mean_balanced_logloss=("balanced_logloss", "mean"), sd_balanced_logloss=("balanced_logloss", "std"),
        mean_logloss=("logloss", "mean"), mean_brier=("brier", "mean"), mean_roc_auc=("roc_auc", "mean"),
        mean_average_precision=("average_precision", "mean"), mean_ece10=("ece10", "mean"))
    records = []
    for family in FAMILIES:
        own = summary[summary["family"] == family]
        worst_loss = float(own["mean_balanced_logloss"].max()); worst_auc = float(own["mean_roc_auc"].min())
        collapse = False
        for row in transfers[transfers["family"] == family].itertuples():
            target_loss = float(own[own["dataset"] == row.target_dataset]["mean_balanced_logloss"].iloc[0])
            collapse |= float(row.balanced_logloss) > target_loss + 0.02
        records.append({"family": family, "weaker_domain_balanced_logloss": worst_loss,
                        "weaker_domain_auc": worst_auc, "transfer_collapse": bool(collapse)})
    ordered = sorted(records, key=lambda row: (row["transfer_collapse"], row["weaker_domain_balanced_logloss"], -row["weaker_domain_auc"], row["family"]))
    identification = {"selection_scope": "Stage-19E synthesis input only; no detector promotion",
                      "ordering_rule": "non-collapsed first, then lower weaker-domain mean class-balanced log loss, then higher weaker-domain AUC",
                      "transfer_collapse_rule": "source-to-target class-balanced log loss exceeds target within-domain family mean by more than 0.02",
                      "ordered_families": ordered, "recommended_family_for_stage19e": ordered[0]["family"]}
    return summary, identification


def _preview(summary: pd.DataFrame, transfers: pd.DataFrame, interactions: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 4, figsize=(20, 5))
    datasets = sorted(summary["dataset"].unique()); x = np.arange(len(FAMILIES)); width = 0.35
    for k, dataset in enumerate(datasets):
        table = summary[summary["dataset"] == dataset].set_index("family").loc[list(FAMILIES)]
        axes[0].bar(x + (k - 0.5) * width, table["mean_balanced_logloss"], width, label=dataset)
        axes[1].bar(x + (k - 0.5) * width, table["mean_roc_auc"], width, label=dataset)
    axes[0].set_title("Within-domain balanced log loss"); axes[1].set_title("Within-domain ROC-AUC")
    for axis in axes[:2]: axis.set_xticks(x, ["control", "additive", "2-additive"], rotation=20)
    pivot = transfers.pivot(index="family", columns="target_dataset", values="balanced_logloss").loc[list(FAMILIES)]
    im = axes[2].imshow(pivot.to_numpy(), cmap="viridis"); axes[2].set_title("Cross-domain balanced log loss")
    axes[2].set_xticks(range(len(pivot.columns)), pivot.columns, rotation=25); axes[2].set_yticks(range(3), ["control", "additive", "2-additive"])
    mean_i = interactions[interactions["fold"].isin([str(x) for x in range(FOLDS)])].groupby(["descriptor_a", "descriptor_b"])["interaction"].mean().sort_values()
    axes[3].barh([f"{a}\n{b}" for a, b in mean_i.index], mean_i.to_numpy()); axes[3].set_title("Mean 2-additive interactions")
    axes[0].legend(fontsize=7); fig.colorbar(im, ax=axes[2], shrink=0.7)
    fig.suptitle("Stage 19D aggregation identification; development analysis only")
    fig.subplots_adjust(left=0.06, right=0.99, bottom=0.25, top=0.84, wspace=0.45)
    fig.savefig(OUT / "best_method_preview.png", dpi=150); plt.close(fig)


def _manifest() -> None:
    content = {"schema_version": 1, "split": "train", "include_incumbent": True, "methods": [],
               "analysis_only_note": "Stage 19D compares aggregation families on sampled descriptor evidence and creates no detector map; score only the unchanged incumbent on BSDS500 train."}
    (OUT / "official_eval_manifest.json").write_text(json.dumps(content, indent=2), encoding="utf-8")


def _smoke() -> int:
    rng = np.random.default_rng(SEED); n = 1200
    frame = pd.DataFrame({name: rng.random(n) for name in set(INCUMBENT) | set(EXPECTED_SHORTLIST)})
    frame["tolerant_union"] = (0.7 * frame["gabor4_s13"] + 0.3 * frame["structure_tensor_coherence"] > 0.5).astype(float)
    frame["image_id"] = np.repeat([f"i{k}" for k in range(12)], n // 12)
    for family in FAMILIES:
        model = _fit_family(family, frame, EXPECTED_SHORTLIST, SEED)
        prediction = _predict(model, frame)
        if not np.all(np.isfinite(prediction)) or np.min(prediction) < 0 or np.max(prediction) > 1: raise RuntimeError("smoke prediction contract failed")
    print("STAGE19D_AGGREGATION_IDENTIFICATION_SMOKE_OK"); return 0


def main() -> int:
    global OUT
    parser = argparse.ArgumentParser(); parser.add_argument("--uded-root", default=str(DEFAULT_UDED)); parser.add_argument("--out", default=str(OUT)); parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args(); OUT = Path(args.out); OUT.mkdir(parents=True, exist_ok=True)
    if args.smoke: return _smoke()
    frozen = json.loads(SHORTLIST_PATH.read_text(encoding="utf-8")); shortlist = tuple(frozen["shortlist"])
    if shortlist != EXPECTED_SHORTLIST: raise RuntimeError(f"Stage 19C shortlist changed: {shortlist!r}")
    samples = pairwise._load_samples(Path(args.uded_root))
    folds, transfers, params, shapley, interactions = _evaluate(samples, shortlist)
    family_summary, identification = _summarize(folds, transfers)
    folds.to_csv(OUT / "aggregation_fold_metrics.csv", index=False); family_summary.to_csv(OUT / "family_summary.csv", index=False)
    transfers.to_csv(OUT / "cross_domain_transfer.csv", index=False); params.to_csv(OUT / "parameter_stability.csv", index=False)
    shapley.to_csv(OUT / "choquet_shapley.csv", index=False); interactions.to_csv(OUT / "choquet_interactions.csv", index=False)
    (OUT / "stage19e_identification.json").write_text(json.dumps(identification, indent=2), encoding="utf-8")
    _preview(family_summary, transfers, interactions); _manifest()
    summary = {"stage": "19d-aggregation-identification", "role": "bounded_gt_guided_analysis_experiment_3_of_3", "architecture_changed": False,
               "promotion_allowed": False, "protected_split_used": False, "shortlist": list(shortlist), "families": list(FAMILIES),
               "dataset_contract": {"BSDS500_train_images": 200, "BSDS500_validation_read": False, "BSDS500_test_blob_read": False,
                                    "UDED_selection_overlap_clean_images": 14, "grouping_unit": "image"},
               "fit_contract": {"folds": FOLDS, "ridge": RIDGE, "capacity_ridge": CAPACITY_RIDGE, "capacity_samples": CAPACITY_SAMPLES,
                                "gamma": GAMMA, "membership_and_parameters_fit_inside_training_images": True},
               "identification": identification,
               "visual_preview": {"path": (OUT / "best_method_preview.png").relative_to(ROOT).as_posix(),
                                  "panel_order": ["within-domain balanced log loss", "within-domain ROC-AUC", "cross-domain balanced log loss", "mean 2-additive interactions"],
                                  "optimization_use": "Stage-19E synthesis input only; no qualitative selection"},
               "official_attachment": "Incumbent-only BSDS500-train attachment; Stage 19D creates no candidate detector map and reads no BSDS validation.",
               "next_required_action": "Stage 19E synthesis must freeze the complete ordered Stage-20 queue before Stage 20A runs."}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE19D_AGGREGATION_IDENTIFICATION_COMPLETE", flush=True); return 0


if __name__ == "__main__":
    raise SystemExit(main())
