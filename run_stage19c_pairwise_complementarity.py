from __future__ import annotations

"""Stage 19C: pairwise redundancy/complementarity on development-only data."""

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
from benchmark_uded import DEFAULT_UDED, load_uded
from run_stage12b_fuzzy_signature import ensure_uded


EXPERIMENT_ID = "stage19c_pairwise_complementarity"
OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
DESCRIPTORS = atlas.DESCRIPTORS
INCUMBENT = DESCRIPTORS[:5]
SEED = 20261019
MODEL_SAMPLES_PER_IMAGE = 512
FOLDS = 5
RIDGE = 1.0e-3


def _fold(image_id: str) -> int:
    token = hashlib.sha256(f"{SEED}:stage19c:{image_id}".encode()).digest()
    return int.from_bytes(token[:8], "little") % FOLDS


def _load_samples(uded_root: Path) -> pd.DataFrame:
    atlas._verify_bsds_source()
    rows: list[pd.DataFrame] = []
    train_paths = atlas._tree_paths("BSDS500/data/images/train")
    bsds_ids = [Path(path).stem for path in train_paths if path.lower().endswith(".jpg")]
    if len(bsds_ids) != 200:
        raise RuntimeError(f"expected 200 pinned BSDS train images, found {len(bsds_ids)}")
    for position, image_id in enumerate(bsds_ids):
        print(f"STAGE19C_BSDS_TRAIN {position + 1:03d}/200 {image_id}", flush=True)
        image, boundaries = atlas._load_bsds_train(image_id)
        frame, *_ = atlas._process_record("BSDS500_train", image_id, image, boundaries)
        rows.append(frame)
    clean, manifest = atlas._overlap_clean_uded(uded_root)
    previous = json.loads((ROOT / "results/local_dev/stage19b_descriptor_relevance_atlas/overlap_clean_dataset_manifest.json").read_text(encoding="utf-8"))
    if manifest != previous:
        raise RuntimeError("Stage 19C overlap-clean manifest differs from frozen Stage 19B manifest")
    for position, item in enumerate(clean):
        image_id = str(item["id"])
        print(f"STAGE19C_UDED_CLEAN {position + 1:02d}/{len(clean):02d} {image_id}", flush=True)
        frame, *_ = atlas._process_record(
            "UDED_selection_overlap_clean", image_id, np.asarray(item["img"]), [np.asarray(item["gt"], dtype=bool)]
        )
        rows.append(frame)
    return pd.concat(rows, ignore_index=True)


def _balanced_weights(y: np.ndarray) -> np.ndarray:
    y = np.asarray(y, dtype=float)
    p = float(np.mean(y))
    return np.where(y >= 0.5, 0.5 / max(p, 1e-9), 0.5 / max(1.0 - p, 1e-9))


def _fit_logistic(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    design = np.column_stack([np.ones(len(x)), x])
    weights = _balanced_weights(y)
    def objective(beta: np.ndarray) -> tuple[float, np.ndarray]:
        z = design @ beta
        loss = np.sum(weights * (np.logaddexp(0.0, z) - y * z)) / np.sum(weights)
        loss += 0.5 * RIDGE * float(beta[1:] @ beta[1:])
        grad = design.T @ (weights * (expit(z) - y)) / np.sum(weights)
        grad[1:] += RIDGE * beta[1:]
        return float(loss), grad
    result = minimize(objective, np.zeros(design.shape[1]), jac=True, method="L-BFGS-B", options={"maxiter": 100})
    if not result.success or not np.all(np.isfinite(result.x)):
        raise RuntimeError(f"Stage 19C logistic fit failed: {result.message}")
    return np.asarray(result.x)


def _model_frame(table: pd.DataFrame) -> pd.DataFrame:
    pieces = []
    for _image_id, image in table.groupby("image_id", sort=True):
        pieces.append(image.iloc[: min(MODEL_SAMPLES_PER_IMAGE, len(image))])
    return pd.concat(pieces, ignore_index=True)


def _cv_predict(table: pd.DataFrame, columns: tuple[str, ...], interaction: tuple[str, str] | None = None) -> tuple[np.ndarray, pd.DataFrame]:
    frame = _model_frame(table).copy()
    frame["fold"] = frame["image_id"].map(_fold)
    predictions = np.zeros(len(frame), dtype=float)
    coefficient_rows = []
    for fold in range(FOLDS):
        train = frame["fold"].to_numpy() != fold
        test = ~train
        train_x = frame.loc[train, list(columns)].to_numpy(dtype=float)
        test_x = frame.loc[test, list(columns)].to_numpy(dtype=float)
        mean = np.mean(train_x, axis=0); scale = np.std(train_x, axis=0)
        scale[scale < 1e-9] = 1.0
        train_x = (train_x - mean) / scale; test_x = (test_x - mean) / scale
        labels = list(columns)
        if interaction is not None:
            ia, ib = columns.index(interaction[0]), columns.index(interaction[1])
            train_x = np.column_stack([train_x, train_x[:, ia] * train_x[:, ib]])
            test_x = np.column_stack([test_x, test_x[:, ia] * test_x[:, ib]])
            labels.append(f"{interaction[0]}*{interaction[1]}")
        beta = _fit_logistic(train_x, frame.loc[train, "tolerant_union"].to_numpy(dtype=float))
        predictions[test] = expit(beta[0] + test_x @ beta[1:])
        coefficient_rows.extend({"fold": fold, "term": term, "coefficient": float(value)} for term, value in zip(labels, beta[1:]))
    frame["prediction"] = predictions
    return predictions, pd.DataFrame(coefficient_rows)


def _per_image_loss(frame: pd.DataFrame, prediction: np.ndarray) -> pd.Series:
    y = frame["tolerant_union"].to_numpy(dtype=float)
    p = np.clip(prediction, 1e-8, 1.0 - 1e-8)
    loss = -(y * np.log(p) + (1.0 - y) * np.log(1.0 - p))
    return pd.Series(loss, index=frame.index).groupby(frame["image_id"]).mean()


def _correlations(samples: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    rows = []; matrices = {}
    for dataset, table in samples.groupby("dataset", sort=True):
        per_image = []
        for image_id, image in table.groupby("image_id", sort=True):
            ranks = np.column_stack([rankdata(image[name].to_numpy(), method="average") for name in DESCRIPTORS])
            corr = np.corrcoef(ranks, rowvar=False)
            per_image.append(corr)
            for i, a in enumerate(DESCRIPTORS):
                for j, b in enumerate(DESCRIPTORS[i + 1 :], i + 1):
                    rows.append({"dataset": dataset, "image_id": image_id, "descriptor_a": a, "descriptor_b": b, "spearman": float(corr[i, j])})
        matrices[dataset] = np.nanmedian(np.stack(per_image), axis=0)
    return pd.DataFrame(rows), matrices


def _relevance() -> pd.DataFrame:
    metrics = pd.read_csv(ROOT / "results/local_dev/stage19b_descriptor_relevance_atlas/descriptor_image_metrics.csv")
    table = metrics[metrics["target_view"] == "tolerant_union"]
    rows = []
    for descriptor in DESCRIPTORS:
        domains = {}
        for dataset, group in table[table["descriptor"] == descriptor].groupby("dataset"):
            domains[dataset] = {"auc": float(group["roc_auc"].mean()), "effect": float(group["rank_biserial_effect"].mean())}
        bs = domains["BSDS500_train"]; ud = domains["UDED_selection_overlap_clean"]
        same = np.sign(bs["effect"]) == np.sign(ud["effect"]) and bs["effect"] != 0 and ud["effect"] != 0
        eligible = bool(same and bs["auc"] >= 0.5 and ud["auc"] >= 0.5)
        score = min(abs(bs["effect"]), abs(ud["effect"])) - 0.5 * abs(abs(bs["effect"]) - abs(ud["effect"])) if same else -max(abs(bs["effect"]), abs(ud["effect"]))
        rows.append({"descriptor": descriptor, "bsds_auc": bs["auc"], "uded_auc": ud["auc"], "bsds_effect": bs["effect"], "uded_effect": ud["effect"], "same_effect_direction": bool(same), "shared_relevant": eligible, "shared_stability_score": float(score)})
    return pd.DataFrame(rows)


def _analyses(samples: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    conditional_rows = []; pair_rows = []; coefficient_rows = []
    single_losses: dict[tuple[str, str], pd.Series] = {}
    for dataset, raw in samples.groupby("dataset", sort=True):
        model = _model_frame(raw)
        for descriptor in DESCRIPTORS:
            prediction, coefficients = _cv_predict(raw, (descriptor,))
            single_losses[(dataset, descriptor)] = _per_image_loss(model, prediction)
            coefficients["dataset"] = dataset; coefficients["model"] = f"single:{descriptor}"
            coefficient_rows.append(coefficients)
        for descriptor in DESCRIPTORS:
            baseline = tuple(name for name in INCUMBENT if name != descriptor) if descriptor in INCUMBENT else INCUMBENT
            base_prediction, _ = _cv_predict(raw, baseline)
            full_prediction, _ = _cv_predict(raw, (*baseline, descriptor))
            base_loss = _per_image_loss(model, base_prediction); full_loss = _per_image_loss(model, full_prediction)
            delta = base_loss - full_loss
            conditional_rows.append({"dataset": dataset, "descriptor": descriptor, "reference": "+".join(baseline), "mean_logloss_gain": float(delta.mean()), "median_logloss_gain": float(delta.median()), "image_wins": int(np.sum(delta > 0)), "image_count": int(len(delta))})
        for i, a in enumerate(DESCRIPTORS):
            for b in DESCRIPTORS[i + 1 :]:
                additive, add_coef = _cv_predict(raw, (a, b))
                interactive, int_coef = _cv_predict(raw, (a, b), (a, b))
                add_loss = _per_image_loss(model, additive); int_loss = _per_image_loss(model, interactive)
                best_single = pd.concat([single_losses[(dataset, a)], single_losses[(dataset, b)]], axis=1).min(axis=1)
                interaction_gain = add_loss - int_loss
                pair_gain = best_single - add_loss
                interaction_term = int_coef[int_coef["term"] == f"{a}*{b}"]["coefficient"]
                pair_rows.append({"dataset": dataset, "descriptor_a": a, "descriptor_b": b, "pair_additive_gain_vs_best_single": float(pair_gain.mean()), "interaction_logloss_gain": float(interaction_gain.mean()), "interaction_image_wins": int(np.sum(interaction_gain > 0)), "image_count": int(len(interaction_gain)), "mean_interaction_coefficient": float(interaction_term.mean()), "interaction_sign": int(np.sign(interaction_term.mean()))})
                add_coef["dataset"] = dataset; add_coef["model"] = f"additive:{a}+{b}"
                int_coef["dataset"] = dataset; int_coef["model"] = f"interaction:{a}+{b}"
                coefficient_rows.extend([add_coef, int_coef])
    return pd.DataFrame(conditional_rows), pd.DataFrame(pair_rows), pd.concat(coefficient_rows, ignore_index=True)


def _shortlist(relevance: pd.DataFrame, correlations: pd.DataFrame, pairwise: pd.DataFrame) -> dict[str, object]:
    med = correlations.groupby(["dataset", "descriptor_a", "descriptor_b"])["spearman"].median().reset_index()
    pair_lookup = {(row.dataset, row.descriptor_a, row.descriptor_b): row for row in pairwise.itertuples()}
    corr_lookup = {(row.dataset, row.descriptor_a, row.descriptor_b): row.spearman for row in med.itertuples()}
    ordered = relevance[relevance["shared_relevant"]].sort_values(["shared_stability_score", "descriptor"], ascending=[False, True])["descriptor"].tolist()
    retained = []; decisions = []
    for descriptor in ordered:
        blocked = None
        for other in retained:
            a, b = sorted((descriptor, other), key=DESCRIPTORS.index)
            redundant = all(abs(corr_lookup[(dataset, a, b)]) >= 0.90 for dataset in ("BSDS500_train", "UDED_selection_overlap_clean"))
            complementary = all(pair_lookup[(dataset, a, b)].pair_additive_gain_vs_best_single > 0.0 for dataset in ("BSDS500_train", "UDED_selection_overlap_clean"))
            if redundant and not complementary:
                blocked = other; break
        decisions.append({"descriptor": descriptor, "retained_after_redundancy": blocked is None, "redundant_with": blocked})
        if blocked is None:
            retained.append(descriptor)
    shortlist = retained[:6]
    return {"descriptor_pool": list(DESCRIPTORS), "shared_relevant_order": ordered, "redundancy_decisions": decisions, "shortlist": shortlist, "shortlist_limit": 6, "rule": "same-direction and AUC>=0.5 in both domains; bilateral |median Spearman|>=0.90 pruned unless pair additive log-loss gain is positive in both domains; rank by frozen shared-stability score"}


def _pair_stability(pairwise: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (a, b), table in pairwise.groupby(["descriptor_a", "descriptor_b"], sort=True):
        by_domain = {row.dataset: row for row in table.itertuples()}
        bs = by_domain["BSDS500_train"]; ud = by_domain["UDED_selection_overlap_clean"]
        sign_agreement = bool(bs.interaction_sign == ud.interaction_sign and bs.interaction_sign != 0)
        gains = (float(bs.interaction_logloss_gain), float(ud.interaction_logloss_gain))
        score = min(gains) - abs(gains[0] - gains[1])
        if not sign_agreement:
            score -= max(abs(float(bs.mean_interaction_coefficient)), abs(float(ud.mean_interaction_coefficient)))
        rows.append({"descriptor_a": a, "descriptor_b": b, "bsds_interaction_gain": gains[0], "uded_interaction_gain": gains[1], "bsds_interaction_sign": int(bs.interaction_sign), "uded_interaction_sign": int(ud.interaction_sign), "interaction_sign_agreement": sign_agreement, "shared_interaction_stability_score": float(score)})
    return pd.DataFrame(rows)


def _write_preview(matrices: dict[str, np.ndarray], relevance: pd.DataFrame, shortlist: list[str]) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    for axis, dataset in zip(axes[:2], ("BSDS500_train", "UDED_selection_overlap_clean")):
        im = axis.imshow(matrices[dataset], vmin=-1, vmax=1, cmap="coolwarm")
        axis.set_title(f"Median image Spearman\n{dataset}")
        axis.set_xticks(range(len(DESCRIPTORS)), range(1, len(DESCRIPTORS) + 1)); axis.set_yticks(range(len(DESCRIPTORS)), range(1, len(DESCRIPTORS) + 1))
    ordered = relevance.sort_values("shared_stability_score")
    colors = ["tab:green" if value in shortlist else "tab:gray" for value in ordered["descriptor"]]
    axes[2].barh(ordered["descriptor"], ordered["shared_stability_score"], color=colors)
    axes[2].set_title("Shared stability (green=shortlist)")
    fig.colorbar(im, ax=axes[:2], shrink=0.8); fig.suptitle("Stage 19C pairwise development analysis; no detector selection")
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.22, top=0.85, wspace=0.45)
    fig.savefig(OUT / "best_method_preview.png", dpi=150); plt.close(fig)


def _manifest() -> None:
    content = {"schema_version": 1, "split": "train", "include_incumbent": True, "methods": [], "analysis_only_note": "Stage 19C is pairwise analysis with no candidate detector map; score only the unchanged incumbent on allowed BSDS500 train."}
    (OUT / "official_eval_manifest.json").write_text(json.dumps(content, indent=2), encoding="utf-8")


def _smoke() -> int:
    rng = np.random.default_rng(SEED)
    frame = pd.DataFrame({"image_id": np.repeat([f"i{x}" for x in range(10)], 40), "tolerant_union": rng.integers(0, 2, 400), "a": rng.random(400), "b": rng.random(400)})
    prediction, coefficients = _cv_predict(frame, ("a", "b"), ("a", "b"))
    if not np.all(np.isfinite(prediction)) or len(coefficients) != FOLDS * 3:
        raise RuntimeError("Stage 19C smoke failed")
    print("STAGE19C_PAIRWISE_COMPLEMENTARITY_SMOKE_OK"); return 0


def main() -> int:
    global OUT
    parser = argparse.ArgumentParser(); parser.add_argument("--uded-root", default=str(DEFAULT_UDED)); parser.add_argument("--out", default=str(OUT)); parser.add_argument("--smoke", action="store_true"); args = parser.parse_args()
    if args.smoke: return _smoke()
    OUT = Path(args.out); OUT.mkdir(parents=True, exist_ok=True)
    samples = _load_samples(Path(args.uded_root))
    correlations, matrices = _correlations(samples)
    relevance = _relevance()
    conditional, pairwise, coefficients = _analyses(samples)
    interaction_stability = _pair_stability(pairwise)
    shortlist = _shortlist(relevance, correlations, pairwise)
    correlations.to_csv(OUT / "pairwise_rank_correlations.csv", index=False)
    relevance.to_csv(OUT / "descriptor_shared_stability.csv", index=False)
    conditional.to_csv(OUT / "conditional_incremental_information.csv", index=False)
    pairwise.to_csv(OUT / "pairwise_interactions.csv", index=False)
    interaction_stability.to_csv(OUT / "pairwise_shared_stability.csv", index=False)
    coefficients.to_csv(OUT / "pairwise_model_coefficients.csv", index=False)
    (OUT / "stage19d_shortlist.json").write_text(json.dumps(shortlist, indent=2), encoding="utf-8")
    _write_preview(matrices, relevance, shortlist["shortlist"]); _manifest()
    summary = {"stage": "19c-pairwise-complementarity", "role": "bounded_gt_guided_analysis_experiment_2_of_3", "architecture_changed": False, "promotion_allowed": False, "protected_split_used": False, "dataset_contract": {"BSDS500_train_images": 200, "BSDS500_validation_read": False, "BSDS500_test_blob_read": False, "UDED_selection_overlap_clean_images": 14, "grouping_unit": "image"}, "model_contract": {"target": "fixed tolerant-union boundary view", "folds": FOLDS, "fold_assignment": "deterministic image hash", "model_samples_per_image": MODEL_SAMPLES_PER_IMAGE, "pair_model": "class-balanced L2 logistic with standardized two main effects; signed bilinear product added only for interaction contrast", "ridge": RIDGE, "higher_order_search": False}, "shortlist": shortlist, "visual_preview": {"path": (OUT / "best_method_preview.png").relative_to(ROOT).as_posix(), "panel_order": ["BSDS median pairwise Spearman", "UDED median pairwise Spearman", "shared-stability shortlist"], "optimization_use": "Stage-19D shortlist visualization only; no qualitative selection"}, "official_attachment": "Incumbent-only BSDS500-train attachment; Stage 19C creates no candidate detector and reads no BSDS validation.", "decision_rule": "Freeze the machine-derived shortlist for Stage 19D; do not promote or alter MFI.", "files": ["summary.json", "pairwise_rank_correlations.csv", "descriptor_shared_stability.csv", "conditional_incremental_information.csv", "pairwise_interactions.csv", "pairwise_shared_stability.csv", "pairwise_model_coefficients.csv", "stage19d_shortlist.json", "best_method_preview.png", "official_eval_manifest.json"]}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE19C_PAIRWISE_COMPLEMENTARITY_COMPLETE"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
