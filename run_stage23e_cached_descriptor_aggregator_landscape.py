from __future__ import annotations

"""Stage 23E: bounded cached evidence x aggregation factorial landscape."""

from collections import defaultdict
from pathlib import Path
import argparse, hashlib, json, math, sys, time

import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from scipy.optimize import minimize
from scipy.special import expit
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from automation.visual_report import write_panel_grid
from benchmark_uded import DEFAULT_UDED
from benchmark_uded_stage7 import fixed_eval, selection_metric
from benchmark_uded_stage8_contextual import aggregate_counts
from run_stage12d_bipolar_cv import _make_repeated_folds
from run_stage23c_cached_uded_descriptor_baselines import _identity, _implementation_hash, _load_overlap_clean_selection
from src.bipolar_fuzzy import distorted_choquet
from src.fuzzy_measures import tail_masks_from_order, validate_capacity_table
from src.measure_learning import balanced_sample, feature_reliability_weights, learn_2additive
from src.stage23_cache import load_cached, validate_manifest_record
from src.stage23_descriptors import DESCRIPTOR_IDS

EXPERIMENT_ID = "stage23e_cached_descriptor_aggregator_landscape"
OUT = ROOT / "results/local_dev" / EXPERIMENT_ID
CACHE_ROOT = ROOT / "cache/local_dev/stage23"
INPUT_SETS = ROOT / "results/local_dev/stage23d_cached_complementarity_map/stage23e_input_sets.json"
BASELINES = ROOT / "results/local_dev/stage23c_cached_uded_descriptor_baselines/individual_descriptor_baselines.csv"
SEED, GAMMA, RIDGE, CAPACITY_RIDGE, CAPACITY_SAMPLES = 20261029, 0.55, 1e-3, 1e-4, 30000
PREVIEW_POSITIONS = (0, 6, 13)
FAMILIES = ("equal_arithmetic_mean", "nonnegative_logistic_additive", "maximum_disjunction",
            "minimum_conjunction", "median_owa", "sugeno_capacity",
            "distorted_choquet_gamma055", "monotone_2additive_choquet")


def _load_maps(items):
    code_hash, rows = _implementation_hash(), []
    maps = {name: [] for name in DESCRIPTOR_IDS}
    for position, item in enumerate(items, 1):
        for name in DESCRIPTOR_IDS:
            identity = _identity(item, name, code_hash); value = load_cached(identity, CACHE_ROOT)
            if value is None: raise RuntimeError(f"forbidden Stage-23E cache miss: {name}/{item['id']}")
            record = validate_manifest_record(identity, CACHE_ROOT); value = np.asarray(value, np.float32)
            if value.shape != item["gt"].shape or not np.all(np.isfinite(value)): raise RuntimeError(f"invalid cache map: {name}/{item['id']}")
            maps[name].append(value); rows.append({"image_id": item["id"], "image_position": position, "descriptor_id": name,
                "cache_key": identity.cache_key(), "artifact_sha256": record["artifact_sha256"], "cache_hit": True})
    return maps, rows


def _sets():
    frozen, rows = json.loads(INPUT_SETS.read_text(encoding="utf-8")), []
    for i, row in enumerate(frozen["pairs"], 1): rows.append({"set_id": f"pair_{i:02d}", "kind": "pair", "descriptors": tuple(row["descriptors"]), "stage23d_score": float(row["score"])})
    for i, row in enumerate(frozen["triples"], 1): rows.append({"set_id": f"triple_{i:02d}", "kind": "triple", "descriptors": tuple(row["descriptors"]), "stage23d_score": float(row["score"])})
    rows.append({"set_id": "incumbent_anchor", "kind": "anchor", "descriptors": tuple(frozen["incumbent_anchor"]), "stage23d_score": float("nan")})
    for i, name in enumerate(frozen["single_controls"], 1): rows.append({"set_id": f"single_{i:02d}", "kind": "single", "descriptors": (name,), "stage23d_score": float("nan")})
    if len(rows) != 15 or len(frozen["pairs"]) != 8 or len(frozen["triples"]) != 4: raise RuntimeError("Stage-23D input-set drift")
    return rows


def _target(gt):
    tol = max(1, int(round(0.0075 * math.hypot(*gt.shape))))
    return ndi.distance_transform_edt(~np.asarray(gt, bool)) <= tol


def _fit_membership(raw, y):
    yb, midpoint, scale = np.asarray(y, bool), [], []
    for col in np.asarray(raw, float).T:
        midpoint.append(0.5 * (float(np.median(col[yb])) + float(np.median(col[~yb]))))
        q25, q75 = np.quantile(col, [0.25, 0.75]); scale.append(max(float(q75 - q25), 0.05))
    return {"midpoint": np.asarray(midpoint), "scale": np.asarray(scale)}


def _membership(raw, spec): return expit(np.clip((np.asarray(raw, float) - spec["midpoint"]) / spec["scale"], -20, 20))


def _class_weights(y):
    y = np.asarray(y, float); p = float(np.mean(y))
    return np.where(y >= .5, .5 / max(p, 1e-9), .5 / max(1 - p, 1e-9))


def _fit_logistic(x, y):
    x, y, w = np.asarray(x, float), np.asarray(y, float), _class_weights(y)
    def objective(beta):
        z = beta[0] + x @ beta[1:]; den = np.sum(w)
        loss = np.sum(w * (np.logaddexp(0, z) - y * z)) / den + .5 * RIDGE * float(beta[1:] @ beta[1:])
        r = w * (expit(z) - y) / den
        return float(loss), np.r_[np.sum(r), x.T @ r + RIDGE * beta[1:]]
    fit = minimize(objective, np.zeros(x.shape[1] + 1), jac=True, method="L-BFGS-B", bounds=[(None, None), *[(0, None)] * x.shape[1]], options={"maxiter": 250})
    return np.asarray(fit.x), bool(fit.success and np.all(np.isfinite(fit.x)))


def _choquet(x, table):
    shape, flat = x.shape[:-1], np.asarray(x, float).reshape(-1, x.shape[-1]); order = np.argsort(flat, axis=1, kind="stable")
    xs = np.take_along_axis(flat, order, axis=1); prev = np.column_stack([np.zeros(len(flat)), xs[:, :-1]])
    return np.sum((xs - prev) * np.asarray(table)[tail_masks_from_order(order)], axis=1).reshape(shape)


def _sugeno(x, table):
    shape, flat = x.shape[:-1], np.asarray(x, float).reshape(-1, x.shape[-1]); order = np.argsort(flat, axis=1, kind="stable")
    xs = np.take_along_axis(flat, order, axis=1)
    return np.max(np.minimum(xs, np.asarray(table)[tail_masks_from_order(order)]), axis=1).reshape(shape)


def _median(x):
    x = np.sort(np.asarray(x, float), axis=-1); n = x.shape[-1]
    return x[..., n // 2] if n % 2 else .5 * (x[..., n // 2 - 1] + x[..., n // 2])


def _fit_model(train_idx, spec, maps, items, seed):
    names = spec["descriptors"]
    raw_images = [np.stack([maps[n][int(i)] for n in names], axis=-1) for i in train_idx]
    targets = [_target(items[int(i)]["gt"]) for i in train_idx]
    raw = np.concatenate([x.reshape(-1, len(names)) for x in raw_images]); y = np.concatenate([x.ravel() for x in targets]).astype(float)
    membership = _fit_membership(raw, y); mx = _membership(raw, membership)
    sx, sy = balanced_sample(mx, y, max_samples=CAPACITY_SAMPLES, seed=seed)
    beta, logistic_ok = _fit_logistic(sx, sy); reliability = feature_reliability_weights(sx, sy)
    capacity = ({"fit_success": True, "capacity_table": [0., 1.], "shapley": [1.], "interaction": [[0.]]}
                if len(names) == 1 else learn_2additive(sx, sy, ridge=CAPACITY_RIDGE))
    table = np.asarray(capacity["capacity_table"], float)
    return {"membership": membership, "beta": beta, "logistic_ok": logistic_ok, "reliability": reliability,
            "capacity": capacity, "capacity_ok": bool(capacity["fit_success"] and validate_capacity_table(table, tol=5e-6))}


def _aggregate(family, x, model):
    if family == "equal_arithmetic_mean": out = np.mean(x, axis=-1)
    elif family == "nonnegative_logistic_additive": out = expit(model["beta"][0] + x @ model["beta"][1:])
    elif family == "maximum_disjunction": out = np.max(x, axis=-1)
    elif family == "minimum_conjunction": out = np.min(x, axis=-1)
    elif family == "median_owa": out = _median(x)
    elif family == "sugeno_capacity": out = _sugeno(x, model["capacity"]["capacity_table"])
    elif family == "distorted_choquet_gamma055": out = distorted_choquet(x, model["reliability"], GAMMA)
    elif family == "monotone_2additive_choquet": out = _choquet(x, model["capacity"]["capacity_table"])
    else: raise KeyError(family)
    out = np.clip(np.asarray(out, np.float32), 0, 1)
    if not np.all(np.isfinite(out)): raise RuntimeError(f"non-finite output: {family}")
    return out


def _alias(family, n):
    if n == 1 and family not in ("equal_arithmetic_mean", "nonnegative_logistic_additive"): return "equal_arithmetic_mean"
    if n == 2 and family == "median_owa": return "equal_arithmetic_mean"
    return None


def _rank_metrics(scores, items, indices, seed):
    ps, ys = [], []
    for score, i in zip(scores, indices):
        y, p = _target(items[int(i)]["gt"]).ravel(), np.asarray(score).ravel()
        if len(y) > 2048:
            token = hashlib.sha256(f"{seed}:{items[int(i)]['id']}".encode()).digest(); rng = np.random.default_rng(int.from_bytes(token[:8], "little"))
            take = np.sort(rng.choice(len(y), 2048, replace=False)); y, p = y[take], p[take]
        ys.append(y); ps.append(p)
    y, p = np.concatenate(ys).astype(bool), np.concatenate(ps).astype(float); n1, n0 = int(y.sum()), int((~y).sum())
    auc = .5 if not n1 or not n0 else float((rankdata(p, method="average")[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
    order = np.argsort(-p, kind="stable"); lab = y[order]; ap = float(np.sum((np.cumsum(lab) / np.arange(1, len(lab) + 1)) * lab) / max(np.sum(lab), 1))
    w = _class_weights(y.astype(float)); brier = float(np.sum(w * (p - y) ** 2) / np.sum(w)); ece = 0.
    for lo in np.linspace(0, .9, 10):
        m = (p >= lo) & (p < lo + .1 if lo < .9 else p <= 1)
        if np.any(m): ece += float(np.mean(m) * abs(np.mean(p[m]) - np.mean(y[m])))
    return {"tolerant_auc": auc, "tolerant_ap": ap, "balanced_brier": brier, "ece10": ece}


def _model_hash(spec, model):
    payload = {"descriptors": list(spec["descriptors"]), "membership": {k: np.asarray(v).tolist() for k, v in model["membership"].items()},
               "beta": model["beta"].tolist(), "reliability": model["reliability"].tolist(), "capacity_table": model["capacity"]["capacity_table"]}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _evaluate(items, maps, sets):
    counts, fold_f1 = defaultdict(list), defaultdict(list); fold_rows, image_rows, param_rows, runtime_rows = [], [], [], []
    first_scores, first_predictions = {}, {}
    for split_no, (repeat, fold, train_idx, valid_idx) in enumerate(_make_repeated_folds(len(items), 3, 5, SEED), 1):
        for set_no, spec in enumerate(sets, 1):
            started = time.perf_counter(); model = _fit_model(train_idx, spec, maps, items, SEED + 10000 * repeat + 100 * fold + set_no); model_hash = _model_hash(spec, model)
            if not model["logistic_ok"] or not model["capacity_ok"]: raise RuntimeError(f"required fit failed: {repeat}/{fold}/{spec['set_id']}")
            train_m = [_membership(np.stack([maps[n][int(i)] for n in spec["descriptors"]], axis=-1), model["membership"]) for i in train_idx]
            valid_m = [_membership(np.stack([maps[n][int(i)] for n in spec["descriptors"]], axis=-1), model["membership"]) for i in valid_idx]
            train_cache, valid_cache = {}, {}
            for family in FAMILIES:
                source, canonical = _alias(family, len(spec["descriptors"])), _alias(family, len(spec["descriptors"])) or family
                if canonical not in train_cache:
                    train_cache[canonical] = [_aggregate(canonical, x, model) for x in train_m]; valid_cache[canonical] = [_aggregate(canonical, x, model) for x in valid_m]
                train_scores, valid_scores = train_cache[canonical], valid_cache[canonical]
                threshold = float(selection_metric(train_scores, [items[int(i)] for i in train_idx], 41)["threshold"])
                metric, event_counts, per_image = fixed_eval(valid_scores, [items[int(i)] for i in valid_idx], threshold)
                rank = _rank_metrics(valid_scores, items, valid_idx, SEED + 1000 * repeat + 10 * fold)
                flat_scores = np.concatenate([score.ravel() for score in valid_scores])
                key = (spec["set_id"], family); counts[key].extend(event_counts); fold_f1[key].append(float(metric["F1"]))
                fold_rows.append({"repeat": repeat + 1, "fold": fold + 1, "set_id": spec["set_id"], "set_kind": spec["kind"], "descriptors": "|".join(spec["descriptors"]),
                    "aggregator": family, "alias_of": source or "", "model_sha256": model_hash, "fit_success": True, "train_threshold": threshold,
                    "support_density": float(np.mean([np.mean(s >= threshold) for s in valid_scores])),
                    "score_q05": float(np.quantile(flat_scores, .05)), "score_median": float(np.median(flat_scores)),
                    "score_q95": float(np.quantile(flat_scores, .95)), **metric, **rank})
                image_rows.extend({"repeat": repeat + 1, "fold": fold + 1, "set_id": spec["set_id"], "aggregator": family, "alias_of": source or "", **row} for row in per_image)
                if repeat == 0:
                    for i, score in zip(valid_idx, valid_scores): first_scores[(spec["set_id"], family, int(i))] = score; first_predictions[(spec["set_id"], family, int(i))] = score >= threshold
            param_rows.append({"repeat": repeat + 1, "fold": fold + 1, "set_id": spec["set_id"], "descriptors": "|".join(spec["descriptors"]), "model_sha256": model_hash,
                "logistic_fit_success": model["logistic_ok"], "capacity_fit_success": model["capacity_ok"], "membership_midpoint": json.dumps(model["membership"]["midpoint"].tolist()),
                "membership_scale": json.dumps(model["membership"]["scale"].tolist()), "logistic_beta": json.dumps(model["beta"].tolist()),
                "distorted_weights": json.dumps(model["reliability"].tolist()), "capacity_table": json.dumps(model["capacity"]["capacity_table"])})
            runtime_rows.append({"repeat": repeat + 1, "fold": fold + 1, "set_id": spec["set_id"], "seconds": time.perf_counter() - started})
        print(f"STAGE23E_SPLIT {split_no:02d}/15", flush=True)
    fold_frame, baseline, cells = pd.DataFrame(fold_rows), pd.read_csv(BASELINES).set_index("descriptor_id"), []
    for spec in sets:
        best_individual = max(float(baseline.loc[n, "F1"]) for n in spec["descriptors"])
        for family in FAMILIES:
            key = (spec["set_id"], family); agg = aggregate_counts(counts[key]); q = fold_frame[(fold_frame.set_id == spec["set_id"]) & (fold_frame.aggregator == family)]
            cells.append({"set_id": spec["set_id"], "set_kind": spec["kind"], "descriptors": "|".join(spec["descriptors"]), "set_size": len(spec["descriptors"]),
                "stage23d_score": spec["stage23d_score"], "aggregator": family, "alias_of": _alias(family, len(spec["descriptors"])) or "", **agg,
                "mean_fold_F1": float(q.F1.mean()), "std_fold_F1": float(q.F1.std(ddof=0)), "mean_tolerant_auc": float(q.tolerant_auc.mean()),
                "mean_tolerant_ap": float(q.tolerant_ap.mean()), "mean_balanced_brier": float(q.balanced_brier.mean()), "mean_ece10": float(q.ece10.mean()),
                "mean_support_density": float(q.support_density.mean()), "threshold_mean": float(q.train_threshold.mean()), "threshold_std": float(q.train_threshold.std(ddof=0)),
                "mean_score_q05": float(q.score_q05.mean()), "mean_score_median": float(q.score_median.mean()), "mean_score_q95": float(q.score_q95.mean()),
                "best_individual_F1": best_individual, "fit_successes": int(q.fit_success.sum())})
    cells = pd.DataFrame(cells)
    for set_id in cells.set_id.unique():
        ref = cells[(cells.set_id == set_id) & (cells.aggregator == FAMILIES[0])].iloc[0]; mask = cells.set_id == set_id
        cells.loc[mask, "delta_F1_vs_equal"] = cells.loc[mask, "F1"] - ref.F1; cells.loc[mask, "delta_AP_vs_equal"] = cells.loc[mask, "mean_tolerant_ap"] - ref.mean_tolerant_ap
        cells.loc[mask, "delta_F1_vs_best_individual"] = cells.loc[mask, "F1"] - cells.loc[mask, "best_individual_F1"]
        ref_folds = fold_frame[(fold_frame.set_id == set_id) & (fold_frame.aggregator == FAMILIES[0])].sort_values(["repeat", "fold"]).F1.to_numpy()
        for family in FAMILIES:
            q = fold_frame[(fold_frame.set_id == set_id) & (fold_frame.aggregator == family)].sort_values(["repeat", "fold"]).F1.to_numpy()
            cells.loc[(cells.set_id == set_id) & (cells.aggregator == family), "fold_wins_vs_equal"] = int(np.sum(q > ref_folds))
    return cells, fold_frame, pd.DataFrame(image_rows), pd.DataFrame(param_rows), pd.DataFrame(runtime_rows), first_scores, first_predictions


def _frontier(cells, sets):
    candidates = []
    for spec in sets:
        if spec["kind"] == "single": continue
        q = cells[(cells.set_id == spec["set_id"]) & (cells.alias_of == "") & (cells.aggregator != FAMILIES[0])].sort_values(["mean_fold_F1", "mean_tolerant_ap", "aggregator"], ascending=[False, False, True])
        row = q.iloc[0].to_dict(); row["frontier_score"] = .5 * row["delta_F1_vs_equal"] + .25 * row["delta_F1_vs_best_individual"] + .25 * row["delta_AP_vs_equal"]; candidates.append(row)
    candidates.sort(key=lambda r: (-r["frontier_score"], -r["mean_fold_F1"], -r["mean_tolerant_ap"], r["set_id"], r["aggregator"]))
    selected, uses = [], defaultdict(int)
    for row in candidates:
        if uses[row["aggregator"]] >= 2: continue
        selected.append({"set_id": row["set_id"], "descriptors": row["descriptors"].split("|"), "aggregator": row["aggregator"], "frontier_score": row["frontier_score"], "matched_control": FAMILIES[0]}); uses[row["aggregator"]] += 1
        if len(selected) == 3: break
    validation = [cell for row in selected for cell in (row, {"set_id": row["set_id"], "descriptors": row["descriptors"], "aggregator": FAMILIES[0], "matched_primary": row["aggregator"]})]
    return {"schema_version": 1, "source_experiment": EXPERIMENT_ID, "selection_rule": "docs/paper/STAGE23E_PREREGISTRATION.md", "primary_cells": selected, "validation_cells": validation, "maximum_cells": 6, "bsds_validation_read": False}


def _profiles(cells):
    return cells[cells.alias_of == ""].groupby(["set_kind", "set_size", "aggregator"], as_index=False).agg(cells=("set_id", "count"), mean_delta_F1_vs_equal=("delta_F1_vs_equal", "mean"), mean_delta_AP_vs_equal=("delta_AP_vs_equal", "mean"), mean_F1=("F1", "mean"), mean_AP=("mean_tolerant_ap", "mean"), mean_brier=("mean_balanced_brier", "mean"))


def main():
    global OUT, CACHE_ROOT
    parser = argparse.ArgumentParser(); parser.add_argument("--uded-root", default=str(DEFAULT_UDED)); parser.add_argument("--out", default=str(OUT)); parser.add_argument("--cache-root", default=str(CACHE_ROOT)); parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args(); OUT, CACHE_ROOT = Path(args.out), Path(args.cache_root)
    if args.smoke:
        rng = np.random.default_rng(SEED); x, y = rng.random((32, 24, 3)), rng.integers(0, 2, 32 * 24); membership = _fit_membership(x.reshape(-1, 3), y); m = _membership(x, membership)
        sx, sy = balanced_sample(m.reshape(-1, 3), y, 500, SEED); capacity = learn_2additive(sx, sy, ridge=CAPACITY_RIDGE)
        model = {"beta": _fit_logistic(sx, sy)[0], "reliability": feature_reliability_weights(sx, sy), "capacity": capacity}
        for family in FAMILIES:
            out = _aggregate(family, m, model); assert out.shape == x.shape[:2] and np.all(np.isfinite(out)) and 0 <= out.min() <= out.max() <= 1
        print("STAGE23E_AGGREGATOR_SMOKE_OK"); return 0
    OUT.mkdir(parents=True, exist_ok=True); items, manifest = _load_overlap_clean_selection(Path(args.uded_root))
    if any(r.get("excluded") and r.get("bytes_read") for r in manifest["records"]): raise RuntimeError("protected lineage bytes read")
    maps, cache_rows = _load_maps(items); sets = _sets(); cells, folds, per_image, parameters, runtime, first_scores, first_predictions = _evaluate(items, maps, sets)
    numeric = cells.select_dtypes(include=[np.number]).drop(columns=["stage23d_score"], errors="ignore")
    if len(cache_rows) != 182 or len(cells) != 120 or len(folds) != 1800 or not np.all(np.isfinite(numeric.to_numpy(dtype=float))): raise RuntimeError("Stage-23E cardinality/finite contract failed")
    frontier = _frontier(cells, sets); winner = frontier["primary_cells"][0]
    pd.DataFrame(cache_rows).to_csv(OUT / "descriptor_cache_provenance.csv", index=False); cells.to_csv(OUT / "landscape_cells.csv", index=False); folds.to_csv(OUT / "fold_metrics.csv", index=False)
    per_image.to_csv(OUT / "per_image_metrics.csv", index=False); parameters.to_csv(OUT / "fit_parameters.csv", index=False); _profiles(cells).to_csv(OUT / "evidence_aggregator_profiles.csv", index=False); runtime.to_csv(OUT / "runtime.csv", index=False)
    (OUT / "stage23f_frontier.json").write_text(json.dumps(frontier, indent=2), encoding="utf-8")
    rows = [[items[p]["img"], items[p]["gt"], first_scores[(winner["set_id"], winner["aggregator"], p)], first_predictions[(winner["set_id"], winner["aggregator"], p)], first_scores[(winner["set_id"], FAMILIES[0], p)], first_predictions[(winner["set_id"], FAMILIES[0], p)]] for p in PREVIEW_POSITIONS]
    preview = write_panel_grid(OUT / "best_method_preview.png", rows, panel_height=112, panel_width=112, gap=2)
    official = {"schema_version": 1, "split": "val", "include_incumbent": True, "methods": [], "analysis_only_note": "Stage 23E is a UDED cached-map screen; Stage 23F validates the frozen frontier. This attachment is incumbent-only."}
    (OUT / "official_eval_manifest.json").write_text(json.dumps(official, indent=2), encoding="utf-8")
    summary = {"status": "completed", "experiment_id": EXPERIMENT_ID, "role": "bounded_cached_descriptor_aggregator_landscape", "dataset": "UDED selection overlap-clean", "retained_images": len(items), "protected_lineage_bytes_read": False,
        "cache_hits": len(cache_rows), "cache_computations": 0, "input_sets": len(sets), "aggregators": list(FAMILIES), "nominal_cells": len(cells), "algebraic_alias_cells": int(np.sum(cells.alias_of != "")), "fold_rows": len(folds),
        "frontier": frontier, "incumbent_changed": False, "bsds_validation_candidate_read": False, "evaluation": "repository tolerant proxy at 0.0075 image diagonal; ranking/AP diagnostics are not Berkeley official metrics",
        "visual_preview": {"path": preview.relative_to(ROOT).as_posix(), "selection": "fixed overlap-clean UDED positions 1, 7, and 14", "selected_cell": winner, "panel_order": ["input", "ground_truth", "primary_score", "primary_prediction", "equal_mean_score", "equal_mean_prediction"], "optimization_use": "none"},
        "official_attachment": "incumbent-only BSDS500-validation attachment", "next_contract": "Stage 23F must preregister and validate only stage23f_frontier.json cells under matched development protocols."}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8"); print("STAGE23E_CACHED_DESCRIPTOR_AGGREGATOR_LANDSCAPE_COMPLETED"); print(OUT / "summary.json"); return 0


if __name__ == "__main__": raise SystemExit(main())
