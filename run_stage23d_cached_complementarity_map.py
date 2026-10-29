from __future__ import annotations

"""Stage 23D: GT-conditioned complementarity over exact Stage-23C cache maps."""

from collections import defaultdict
from itertools import combinations
from pathlib import Path
import argparse
import json
import math
import sys

import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation.visual_report import write_panel_grid
from benchmark_uded import DEFAULT_UDED
from benchmark_uded_stage7 import selection_metric
from run_stage12d_bipolar_cv import _make_repeated_folds
from run_stage23c_cached_uded_descriptor_baselines import (
    _identity, _implementation_hash, _load_overlap_clean_selection,
)
from src.stage23_cache import load_cached, validate_manifest_record
from src.stage23_descriptors import DESCRIPTOR_IDS


EXPERIMENT_ID = "stage23d_cached_complementarity_map"
OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
CACHE_ROOT = ROOT / "cache" / "local_dev" / "stage23"
SEED = 20261029
PREVIEW_POSITIONS = (0, 6, 13)
FAMILIES = {
    "scharr_pre_nms_magnitude": "local_gradient",
    "lab_dizenzo_tensor_gradient": "vector_color",
    "gabor4_s5": "oriented_frequency", "gabor4_s13": "oriented_frequency",
    "hessian_s7": "curvature", "hessian_s13": "curvature",
    "gabor4_scale_persistence": "scale_persistence",
    "structure_tensor_coherence": "orientation_organization",
    "phase_congruency_max_moment": "phase_alignment",
    "halfdisc_distribution_contrast": "opposed_distribution",
    "pmi_dependency_deficit": "statistical_dependence",
    "semiglobal_changepoint": "semiglobal_changepoint",
    "fh_region_boundary": "region_adaptive",
}
ANCHOR = ["gabor4_s5", "hessian_s7", "gabor4_s13", "hessian_s13", "gabor4_scale_persistence"]


def _load_maps(items: list[dict]) -> tuple[dict[str, list[np.ndarray]], list[dict[str, object]]]:
    code_hash = _implementation_hash()
    maps = {name: [] for name in DESCRIPTOR_IDS}
    rows = []
    for position, item in enumerate(items, start=1):
        for descriptor_id in DESCRIPTOR_IDS:
            identity = _identity(item, descriptor_id, code_hash)
            value = load_cached(identity, CACHE_ROOT)
            if value is None:
                raise RuntimeError(f"forbidden Stage-23D cache miss: {descriptor_id}/{item['id']}")
            record = validate_manifest_record(identity, CACHE_ROOT)
            value = np.asarray(value, dtype=np.float32)
            if value.shape != item["gt"].shape or not np.all(np.isfinite(value)):
                raise RuntimeError(f"invalid exact cache map: {descriptor_id}/{item['id']}")
            maps[descriptor_id].append(value)
            rows.append({"image_id": item["id"], "image_position": position,
                         "descriptor_id": descriptor_id, "cache_key": identity.cache_key(),
                         "artifact_sha256": record["artifact_sha256"], "cache_hit": True})
    return maps, rows


def _corr(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    a, b = np.asarray(x, float).ravel(), np.asarray(y, float).ravel()
    pearson = 0.0 if min(np.std(a), np.std(b)) <= 1e-12 else float(np.corrcoef(a, b)[0, 1])
    ra, rb = rankdata(a, method="average"), rankdata(b, method="average")
    spearman = 0.0 if min(np.std(ra), np.std(rb)) <= 1e-12 else float(np.corrcoef(ra, rb)[0, 1])
    return pearson, spearman


def _safe_ratio(num: int | float, den: int | float) -> float:
    return float(num / den) if den else 0.0


def _pair_masks(pred_a: np.ndarray, pred_b: np.ndarray, gt: np.ndarray, tol: int) -> dict[str, float]:
    near_gt = ndi.distance_transform_edt(~gt) <= tol
    cover_a = gt & (ndi.distance_transform_edt(~pred_a) <= tol)
    cover_b = gt & (ndi.distance_transform_edt(~pred_b) <= tol)
    fp_a, fp_b = pred_a & ~near_gt, pred_b & ~near_gt
    domain = near_gt | pred_a | pred_b
    truth, a_dec, b_dec = near_gt[domain], pred_a[domain], pred_b[domain]
    a_correct, b_correct = a_dec == truth, b_dec == truth
    return {
        "shared_gt_coverage": _safe_ratio(np.count_nonzero(cover_a & cover_b), np.count_nonzero(gt)),
        "unique_gt_a": _safe_ratio(np.count_nonzero(cover_a & ~cover_b), np.count_nonzero(gt)),
        "unique_gt_b": _safe_ratio(np.count_nonzero(cover_b & ~cover_a), np.count_nonzero(gt)),
        "supported_prediction_overlap": _safe_ratio(np.count_nonzero(pred_a & pred_b & near_gt), np.count_nonzero((pred_a | pred_b) & near_gt)),
        "fp_overlap": _safe_ratio(np.count_nonzero(fp_a & fp_b), np.count_nonzero(fp_a | fp_b)),
        "unique_fp_a": _safe_ratio(np.count_nonzero(fp_a & ~fp_b), np.count_nonzero(pred_a)),
        "unique_fp_b": _safe_ratio(np.count_nonzero(fp_b & ~fp_a), np.count_nonzero(pred_b)),
        "p_a_correct_given_b_wrong": float(np.mean(a_correct[~b_correct])) if np.any(~b_correct) else 1.0,
        "p_b_correct_given_a_wrong": float(np.mean(b_correct[~a_correct])) if np.any(~a_correct) else 1.0,
        "gt_union_coverage": _safe_ratio(np.count_nonzero(cover_a | cover_b), np.count_nonzero(gt)),
    }


def _thresholds(items: list[dict], maps: dict[str, list[np.ndarray]], train_idx: np.ndarray) -> dict[str, float]:
    train_items = [items[int(i)] for i in train_idx]
    return {name: float(selection_metric([maps[name][int(i)] for i in train_idx], train_items, 41)["threshold"])
            for name in DESCRIPTOR_IDS}


def _pair_tables(items: list[dict], maps: dict[str, list[np.ndarray]]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    pairs = list(combinations(DESCRIPTOR_IDS, 2))
    corr_rows = []
    for image_index, item in enumerate(items):
        for a, b in pairs:
            p, s = _corr(maps[a][image_index], maps[b][image_index])
            corr_rows.append({"image_id": item["id"], "descriptor_a": a, "descriptor_b": b, "pearson": p, "spearman": s})
    corr = pd.DataFrame(corr_rows)
    occurrences: dict[tuple[int, int, int, str], np.ndarray] = {}
    balanced_rows, regime_rows = [], []
    for repeat, fold, train_idx, valid_idx in _make_repeated_folds(len(items), 3, 5, SEED):
        balanced = _thresholds(items, maps, train_idx)
        quantiles = {}
        for name in DESCRIPTOR_IDS:
            flat = np.concatenate([maps[name][int(i)].ravel() for i in train_idx])
            quantiles[name] = {"precision_q90": float(np.quantile(flat, 0.90)), "recall_q60": float(np.quantile(flat, 0.60))}
        for image_index in valid_idx:
            i = int(image_index); gt = np.asarray(items[i]["gt"], bool)
            tol = max(1, int(round(0.0075 * math.hypot(*gt.shape))))
            for name in DESCRIPTOR_IDS:
                occurrences[(repeat, fold, i, name)] = maps[name][i] >= balanced[name]
            for a, b in pairs:
                row = _pair_masks(occurrences[(repeat, fold, i, a)], occurrences[(repeat, fold, i, b)], gt, tol)
                balanced_rows.append({"repeat": repeat + 1, "fold": fold + 1, "image_id": items[i]["id"], "image_index": i,
                                      "descriptor_a": a, "descriptor_b": b, **row})
                regime_rows.append({"repeat": repeat + 1, "fold": fold + 1, "image_id": items[i]["id"],
                                    "descriptor_a": a, "descriptor_b": b, "regime": "balanced_f1", **row})
                for regime in ("precision_q90", "recall_q60"):
                    metric = _pair_masks(maps[a][i] >= quantiles[a][regime], maps[b][i] >= quantiles[b][regime], gt, tol)
                    regime_rows.append({"repeat": repeat + 1, "fold": fold + 1, "image_id": items[i]["id"],
                                        "descriptor_a": a, "descriptor_b": b, "regime": regime, **metric})
    per_image = pd.DataFrame(balanced_rows)
    metric_cols = ["shared_gt_coverage", "unique_gt_a", "unique_gt_b",
                   "supported_prediction_overlap", "fp_overlap", "unique_fp_a",
                   "unique_fp_b", "p_a_correct_given_b_wrong",
                   "p_b_correct_given_a_wrong", "gt_union_coverage"]
    summaries = []
    for a, b in pairs:
        q = per_image[(per_image.descriptor_a == a) & (per_image.descriptor_b == b)]
        c = corr[(corr.descriptor_a == a) & (corr.descriptor_b == b)]
        row = {"descriptor_a": a, "descriptor_b": b, "family_a": FAMILIES[a], "family_b": FAMILIES[b],
               "cross_family": FAMILIES[a] != FAMILIES[b], "mean_pearson": float(c.pearson.mean()),
               "median_pearson": float(c.pearson.median()), "mean_spearman": float(c.spearman.mean()),
               "median_spearman": float(c.spearman.median())}
        row.update({f"mean_{col}": float(q[col].mean()) for col in metric_cols})
        stability = float(np.mean((q.unique_gt_a > 0) & (q.unique_gt_b > 0)))
        row["bilateral_unique_stability"] = stability
        redundancy = min(abs(row["mean_spearman"]), 1.0)
        unique_gt = np.clip(row["mean_unique_gt_a"] + row["mean_unique_gt_b"], 0, 1)
        conditional = np.clip(0.5 * (row["mean_p_a_correct_given_b_wrong"] + row["mean_p_b_correct_given_a_wrong"]), 0, 1)
        unique_fp = np.clip(0.5 * (row["mean_unique_fp_a"] + row["mean_unique_fp_b"]), 0, 1)
        row["eligible"] = bool(row["cross_family"] and redundancy <= 0.95)
        row["complementarity_score"] = float(0.25 * (1 - redundancy) + 0.25 * unique_gt + 0.20 * conditional + 0.15 * stability + 0.15 * (1 - unique_fp))
        summaries.append(row)
    regime = pd.DataFrame(regime_rows).groupby(["descriptor_a", "descriptor_b", "regime"], as_index=False)[metric_cols].mean()
    per_image = per_image.merge(corr, on=["image_id", "descriptor_a", "descriptor_b"], how="left", validate="many_to_one")
    return pd.DataFrame(summaries), per_image, regime, occurrences


def _clusters(pairwise: pd.DataFrame, baseline: pd.DataFrame) -> dict[str, object]:
    graph = {name: set() for name in DESCRIPTOR_IDS}
    for row in pairwise.itertuples():
        if abs(row.mean_spearman) >= 0.90:
            graph[row.descriptor_a].add(row.descriptor_b); graph[row.descriptor_b].add(row.descriptor_a)
    unseen, clusters = set(DESCRIPTOR_IDS), []
    f1 = dict(zip(baseline.descriptor_id, baseline.F1))
    while unseen:
        stack, component = [min(unseen)], []
        while stack:
            node = stack.pop()
            if node not in unseen: continue
            unseen.remove(node); component.append(node); stack.extend(sorted(graph[node], reverse=True))
        component.sort(); rep = sorted(component, key=lambda x: (-float(f1[x]), x))[0]
        clusters.append({"members": component, "representative_by_stage23c_f1": rep})
    return {"threshold": 0.90, "clusters": clusters}


def _select_pairs(pairwise: pd.DataFrame) -> list[dict[str, object]]:
    eligible = pairwise[pairwise.eligible].sort_values(["complementarity_score", "descriptor_a", "descriptor_b"], ascending=[False, True, True])
    selected, descriptor_uses, family_uses = [], defaultdict(int), defaultdict(int)
    for row in eligible.to_dict("records"):
        a, b = row["descriptor_a"], row["descriptor_b"]
        family_pair = tuple(sorted((row["family_a"], row["family_b"])))
        if descriptor_uses[a] >= 3 or descriptor_uses[b] >= 3 or family_uses[family_pair] >= 2: continue
        selected.append({"descriptors": [a, b], "score": row["complementarity_score"]})
        descriptor_uses[a] += 1; descriptor_uses[b] += 1; family_uses[family_pair] += 1
        if len(selected) == 8: break
    return selected


def _triple_table(items: list[dict], pairwise: pd.DataFrame, selected_pairs: list[dict], occurrences: dict) -> tuple[pd.DataFrame, list[dict]]:
    eligible = pairwise[pairwise.eligible].sort_values(["complementarity_score", "descriptor_a", "descriptor_b"], ascending=[False, True, True]).head(24)
    pair_scores = {tuple(sorted((r.descriptor_a, r.descriptor_b))): float(r.complementarity_score) for r in eligible.itertuples()}
    pool = sorted({d for row in selected_pairs for d in row["descriptors"]})
    candidates = []
    for triple in combinations(pool, 3):
        keys = [tuple(sorted(p)) for p in combinations(triple, 2)]
        if len({FAMILIES[x] for x in triple}) == 3 and all(key in pair_scores for key in keys):
            candidates.append((float(np.mean([pair_scores[k] for k in keys])), triple))
    candidates = sorted(candidates, key=lambda x: (-x[0], x[1]))[:24]
    rows = []
    for mean_pair, triple in candidates:
        image_metrics = []
        for repeat, fold, image_index, name in sorted(occurrences):
            if name != triple[0]: continue
            preds = [occurrences[(repeat, fold, image_index, d)] for d in triple]
            gt = np.asarray(items[image_index]["gt"], bool); tol = max(1, int(round(0.0075 * math.hypot(*gt.shape))))
            covers = [gt & (ndi.distance_transform_edt(~p) <= tol) for p in preds]
            union = np.logical_or.reduce(covers)
            exclusive = [c & ~np.logical_or.reduce([covers[j] for j in range(3) if j != k]) for k, c in enumerate(covers)]
            majority = np.sum(np.stack(preds), axis=0) >= 2; near_gt = ndi.distance_transform_edt(~gt) <= tol
            image_metrics.append((_safe_ratio(np.count_nonzero(union), np.count_nonzero(gt)),
                                  sum(_safe_ratio(np.count_nonzero(x), np.count_nonzero(gt)) for x in exclusive),
                                  _safe_ratio(np.count_nonzero(majority & near_gt), np.count_nonzero(majority)),
                                  float(all(np.any(x) for x in exclusive))))
        union_cov, exclusive, majority_precision, stability = np.mean(np.asarray(image_metrics, float), axis=0)
        score = 0.35 * union_cov + 0.25 * min(exclusive, 1.0) + 0.20 * majority_precision + 0.10 * mean_pair + 0.10 * stability
        rows.append({"descriptor_a": triple[0], "descriptor_b": triple[1], "descriptor_c": triple[2],
                     "mean_pair_score": mean_pair, "union_gt_coverage": union_cov, "member_exclusive_gt_sum": exclusive,
                     "majority_prediction_precision": majority_precision, "exclusive_support_stability": stability, "triple_score": score})
    columns = ["descriptor_a", "descriptor_b", "descriptor_c", "mean_pair_score", "union_gt_coverage",
               "member_exclusive_gt_sum", "majority_prediction_precision", "exclusive_support_stability", "triple_score"]
    frame = pd.DataFrame(rows, columns=columns).sort_values(["triple_score", "descriptor_a", "descriptor_b", "descriptor_c"], ascending=[False, True, True, True])
    selected, uses = [], defaultdict(int)
    for row in frame.to_dict("records"):
        triple = [row["descriptor_a"], row["descriptor_b"], row["descriptor_c"]]
        if any(uses[x] >= 2 for x in triple): continue
        selected.append({"descriptors": triple, "score": row["triple_score"]})
        for x in triple: uses[x] += 1
        if len(selected) == 4: break
    return frame, selected


def _write_preview(items: list[dict], maps: dict[str, list[np.ndarray]]) -> dict[str, object]:
    rows = [[items[p]["img"], items[p]["gt"], *[maps[name][p] for name in DESCRIPTOR_IDS]] for p in PREVIEW_POSITIONS]
    path = write_panel_grid(OUT / "best_method_preview.png", rows, panel_height=112, panel_width=112, gap=2)
    return {"path": path.relative_to(ROOT).as_posix(), "selection": "sorted overlap-clean UDED positions 1, 7, and 14",
            "panel_order": ["input", "ground_truth", *DESCRIPTOR_IDS], "optimization_use": "none"}


def main() -> int:
    global OUT, CACHE_ROOT
    parser = argparse.ArgumentParser(); parser.add_argument("--uded-root", default=str(DEFAULT_UDED)); parser.add_argument("--out", default=str(OUT)); parser.add_argument("--cache-root", default=str(CACHE_ROOT)); parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args(); OUT, CACHE_ROOT = Path(args.out), Path(args.cache_root)
    if args.smoke:
        assert len(DESCRIPTOR_IDS) == 13 and len(FAMILIES) == 13 and len(list(combinations(DESCRIPTOR_IDS, 2))) == 78
        print("STAGE23D_CONTRACT_SMOKE_OK"); return 0
    OUT.mkdir(parents=True, exist_ok=True)
    items, dataset_manifest = _load_overlap_clean_selection(Path(args.uded_root))
    if any(r.get("excluded") and r.get("bytes_read") for r in dataset_manifest["records"]): raise RuntimeError("protected lineage bytes read")
    maps, cache_rows = _load_maps(items)
    pairwise, per_image, regimes, occurrences = _pair_tables(items, maps)
    baseline = pd.read_csv(ROOT / "results/local_dev/stage23c_cached_uded_descriptor_baselines/individual_descriptor_baselines.csv")
    clusters = _clusters(pairwise, baseline); selected_pairs = _select_pairs(pairwise)
    triples, selected_triples = _triple_table(items, pairwise, selected_pairs, occurrences)
    if len(cache_rows) != 182 or len(pairwise) != 78:
        raise RuntimeError("Stage-23D cache/pair cardinality contract failed")
    for name, frame in (("pairwise", pairwise), ("per_image", per_image), ("regimes", regimes), ("triples", triples)):
        numeric = frame.select_dtypes(include=[np.number])
        if not np.all(np.isfinite(numeric.to_numpy(dtype=float))):
            raise RuntimeError(f"non-finite {name} metric")
    if len(selected_pairs) > 8 or len(selected_triples) > 4:
        raise RuntimeError("Stage-23D forwarding budget exceeded")
    eligible_means = defaultdict(list)
    for row in pairwise[pairwise.eligible].itertuples():
        eligible_means[row.descriptor_a].append(row.complementarity_score); eligible_means[row.descriptor_b].append(row.complementarity_score)
    strongest = sorted(baseline.to_dict("records"), key=lambda r: (-r["F1"], r["descriptor_id"]))[0]["descriptor_id"]
    comp_order = sorted(DESCRIPTOR_IDS, key=lambda d: (-float(np.mean(eligible_means[d])) if eligible_means[d] else float("inf"), d))
    complementary = next((d for d in comp_order if d != strongest), strongest)
    input_sets = {"schema_version": 1, "source_experiment": EXPERIMENT_ID, "pairs": selected_pairs,
                  "triples": selected_triples, "incumbent_anchor": ANCHOR, "single_controls": [strongest, complementary],
                  "maximum_pairs": 8, "maximum_triples": 4, "aggregator_stage": "stage23e",
                  "selection_rule": "docs/paper/STAGE23D_PREREGISTRATION.md"}
    pd.DataFrame(cache_rows).to_csv(OUT / "descriptor_cache_provenance.csv", index=False)
    pairwise.to_csv(OUT / "pairwise_complementarity.csv", index=False); per_image.to_csv(OUT / "pairwise_per_image.csv", index=False)
    regimes.to_csv(OUT / "operating_regime_complementarity.csv", index=False); triples.to_csv(OUT / "triple_complementarity.csv", index=False)
    (OUT / "redundancy_clusters.json").write_text(json.dumps(clusters, indent=2), encoding="utf-8")
    (OUT / "stage23e_input_sets.json").write_text(json.dumps(input_sets, indent=2), encoding="utf-8")
    preview = _write_preview(items, maps)
    official = {"schema_version": 1, "split": "val", "include_incumbent": True, "methods": [],
                "analysis_only_note": "Stage 23D is UDED cached-map analysis and defines no BSDS candidate; official attachment is incumbent-only."}
    (OUT / "official_eval_manifest.json").write_text(json.dumps(official, indent=2), encoding="utf-8")
    summary = {"status": "completed", "experiment_id": EXPERIMENT_ID, "role": "cached_gt_conditioned_complementarity_map",
               "dataset": "UDED selection overlap-clean", "retained_images": len(items), "protected_lineage_bytes_read": False,
               "descriptor_count": len(DESCRIPTOR_IDS), "pair_count": len(pairwise), "cache_hits": len(cache_rows), "cache_computations": 0,
               "selected_pair_count": len(selected_pairs), "selected_triple_count": len(selected_triples),
               "single_controls": [strongest, complementary], "incumbent_changed": False,
               "evaluation": "repository tolerant proxy at 0.0075 image diagonal; not Berkeley official evaluation",
               "visual_preview": preview, "official_attachment": "incumbent-only BSDS500-validation attachment",
               "next_contract": "Stage 23E may consume only stage23e_input_sets.json and exact cached maps under the frozen eight-family aggregator screen."}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE23D_CACHED_COMPLEMENTARITY_MAP_COMPLETED"); print(OUT / "summary.json"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
