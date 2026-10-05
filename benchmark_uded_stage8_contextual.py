from __future__ import annotations

from pathlib import Path
import argparse
import gc
import json
import math
import os
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import ndimage as ndi

from benchmark_uded import DEFAULT_UDED, MODEL_DIR, load_uded, prepare
from benchmark_uded_quick import resize_items
from benchmark_uded_fusion import compute_conf
from benchmark_uded_stage7 import fixed_eval, selection_metric, bootstrap_delta, overlay_edges, tolerance_error_map
from src.contextual_controller import (
    local_heterogeneity,
    contextual_score,
    single_controller_specs,
    route_confidences,
    router_specs,
)
from src.evaluation import counts_to_prf
from src.fuzzy_measures import measure_registry


ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "uded" / "stage8_contextual"

ROUTER_POOL = (
    "local_additive_evidence",
    "hetero_power_direct",
    "adaptive_power_geomean",
    "context_additive_estimated",
    "sugeno_learned_sum1.00",
    "power_q0.2",
)


def atomic_csv(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)


def atomic_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, default=float), encoding="utf-8")
    os.replace(tmp, path)


def load_csv(path: Path):
    if path.exists() and path.stat().st_size:
        return pd.read_csv(path)
    return pd.DataFrame()


def pjson(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"))


def aggregate_counts(counts):
    if not counts:
        return {"precision": 0.0, "recall": 0.0, "F1": 0.0}
    c = np.asarray(counts, dtype=np.int64).sum(axis=0)
    p, r, f = counts_to_prf(*c)
    return {"precision": float(p), "recall": float(r), "F1": float(f)}


def cv_threshold_score(scores, items, n_thresholds=21, n_folds=3):
    """Inner cross-validation over the natural selection split.

    Each fold's threshold is fitted on the other folds and frozen on that fold.
    Candidate ranking therefore uses out-of-fold F1 instead of the optimistic
    same-images threshold optimum.
    """
    n = len(items)
    folds = np.arange(n) % int(n_folds)
    all_counts = []
    thresholds = []
    fold_f1 = []
    for k in range(int(n_folds)):
        tr = np.where(folds != k)[0]
        va = np.where(folds == k)[0]
        tr_scores = [scores[i] for i in tr]
        tr_items = [items[i] for i in tr]
        va_scores = [scores[i] for i in va]
        va_items = [items[i] for i in va]
        fit = selection_metric(tr_scores, tr_items, n_thresholds)
        met, counts, _ = fixed_eval(va_scores, va_items, float(fit["threshold"]))
        thresholds.append(float(fit["threshold"]))
        fold_f1.append(float(met["F1"]))
        all_counts.extend(counts)
    agg = aggregate_counts(all_counts)
    return {
        "cv_precision": agg["precision"],
        "cv_recall": agg["recall"],
        "cv_F1": agg["F1"],
        "cv_mean_fold_F1": float(np.mean(fold_f1)),
        "cv_std_fold_F1": float(np.std(fold_f1)),
        "cv_threshold_mean": float(np.mean(thresholds)),
        "cv_threshold_std": float(np.std(thresholds)),
    }


def make_heterogeneity(items):
    out = []
    for d in items:
        out.append(local_heterogeneity(d["img"], sigma=1.0, window=5).astype(np.float32))
    return out


def single_complete(df, measure, expected):
    if df.empty:
        return False
    x = df[df.measure.astype(str) == str(measure)]
    return x[["strategy", "params"]].drop_duplicates().shape[0] >= int(expected)


def pair_key(a, b):
    return "::".join(sorted((str(a), str(b))))


def pair_complete(df, a, b, expected):
    if df.empty:
        return False
    key = pair_key(a, b)
    x = df[df.pair_key.astype(str) == key]
    return x[["params"]].drop_duplicates().shape[0] >= int(expected)


def evaluate_single_measure(spec, items, select_items, context_model, h_sel,
                            n_thresholds=21):
    confs = [np.asarray(x, dtype=np.float32) for x in compute_conf(spec, items, context_model)]
    conf_sel = confs[0::2]
    rows = []
    t0 = time.perf_counter()
    for strategy, params in single_controller_specs():
        scores = [
            contextual_score(d["scharr"], c, h, strategy, params)
            for d, c, h in zip(select_items, conf_sel, h_sel)
        ]
        cv = cv_threshold_score(scores, select_items, n_thresholds, 3)
        opt = selection_metric(scores, select_items, n_thresholds)
        rows.append({
            "candidate_type": "single",
            "measure": str(spec["name"]),
            "measure_kind": str(spec.get("kind", "")),
            "strategy": strategy,
            "params": pjson(params),
            **cv,
            "selection_ODS": float(opt["ODS"]),
            "selection_OIS": float(opt["OIS"]),
            "selection_AP": float(opt["AP"]),
            "selection_R50": float(opt["R50"]),
            "selection_threshold": float(opt["threshold"]),
        })
        del scores
    runtime = time.perf_counter() - t0
    del confs, conf_sel
    gc.collect()
    return rows, runtime


def router_pairs(names):
    names = [n for n in ROUTER_POOL if n in names]
    return [(names[i], names[j]) for i in range(len(names)) for j in range(i + 1, len(names))]


def evaluate_router_pair(a, b, specs_by_name, items, select_items, context_model, h_sel,
                         n_thresholds=21):
    ca = [np.asarray(x, dtype=np.float32) for x in compute_conf(specs_by_name[a], items, context_model)][0::2]
    cb = [np.asarray(x, dtype=np.float32) for x in compute_conf(specs_by_name[b], items, context_model)][0::2]
    rows = []
    t0 = time.perf_counter()
    for prm in router_specs():
        route_params = {k: v for k, v in prm.items() if k not in ("controller", "controller_params")}
        routed = [
            route_confidences(x, y, h, **route_params)
            for x, y, h in zip(ca, cb, h_sel)
        ]
        scores = [
            contextual_score(d["scharr"], c, h, prm["controller"], prm["controller_params"])
            for d, c, h in zip(select_items, routed, h_sel)
        ]
        cv = cv_threshold_score(scores, select_items, n_thresholds, 3)
        opt = selection_metric(scores, select_items, n_thresholds)
        rows.append({
            "candidate_type": "router",
            "measure": f"route({a}->{b})",
            "measure_kind": "local_measure_router",
            "measure_a": a,
            "measure_b": b,
            "pair_key": pair_key(a, b),
            "strategy": "heterogeneity_router",
            "params": pjson(prm),
            **cv,
            "selection_ODS": float(opt["ODS"]),
            "selection_OIS": float(opt["OIS"]),
            "selection_AP": float(opt["AP"]),
            "selection_R50": float(opt["R50"]),
            "selection_threshold": float(opt["threshold"]),
        })
        del routed, scores
    runtime = time.perf_counter() - t0
    del ca, cb
    gc.collect()
    return rows, runtime


def build_candidate_scores(row, specs_by_name, items, select_items, test_items,
                           context_model, h_sel, h_test):
    prm = json.loads(str(row.params))
    ctype = str(row.candidate_type)
    if ctype == "single":
        confs = [np.asarray(x, dtype=np.float32) for x in compute_conf(specs_by_name[str(row.measure)], items, context_model)]
        csel, ctest = confs[0::2], confs[1::2]
        ssel = [contextual_score(d["scharr"], c, h, str(row.strategy), prm)
                for d, c, h in zip(select_items, csel, h_sel)]
        stest = [contextual_score(d["scharr"], c, h, str(row.strategy), prm)
                 for d, c, h in zip(test_items, ctest, h_test)]
        return ssel, stest, csel, ctest

    a, b = str(row.measure_a), str(row.measure_b)
    ca = [np.asarray(x, dtype=np.float32) for x in compute_conf(specs_by_name[a], items, context_model)]
    cb = [np.asarray(x, dtype=np.float32) for x in compute_conf(specs_by_name[b], items, context_model)]
    route_params = {k: v for k, v in prm.items() if k not in ("controller", "controller_params")}
    csel = [route_confidences(x, y, h, **route_params) for x, y, h in zip(ca[0::2], cb[0::2], h_sel)]
    ctest = [route_confidences(x, y, h, **route_params) for x, y, h in zip(ca[1::2], cb[1::2], h_test)]
    ssel = [contextual_score(d["scharr"], c, h, prm["controller"], prm["controller_params"])
            for d, c, h in zip(select_items, csel, h_sel)]
    stest = [contextual_score(d["scharr"], c, h, prm["controller"], prm["controller_params"])
             for d, c, h in zip(test_items, ctest, h_test)]
    return ssel, stest, csel, ctest


def save_context_sheet(test_items, base_scores, base_thr, best_scores, best_thr,
                       best_conf, h_test, outpath, title, n=6):
    n = min(int(n), len(test_items))
    fig, axes = plt.subplots(n, 7, figsize=(20, 3 * n))
    if n == 1:
        axes = np.asarray([axes])
    for row, d, bs, fs, c, h in zip(axes, test_items[:n], base_scores[:n], best_scores[:n], best_conf[:n], h_test[:n]):
        bp = np.asarray(bs) >= float(base_thr)
        fp = np.asarray(fs) >= float(best_thr)
        tol = max(1, int(round(0.0075 * math.hypot(*d["gt"].shape))))
        row[0].imshow(d["img"]); row[0].set_title(f'{d["id"]}\nOriginal')
        row[1].imshow(d["gt"], cmap="gray"); row[1].set_title("Ground truth")
        row[2].imshow(overlay_edges(d["img"], bp)); row[2].set_title("Scharr+NMS")
        row[3].imshow(h, cmap="magma", vmin=0, vmax=1); row[3].set_title("Heterogeneity")
        row[4].imshow(c, cmap="inferno", vmin=0, vmax=1); row[4].set_title("MFI/controller conf")
        row[5].imshow(overlay_edges(d["img"], fp)); row[5].set_title("Stage 8")
        row[6].imshow(tolerance_error_map(d["gt"], fp, tol)); row[6].set_title("TP/FP/FN")
        for ax in row:
            ax.axis("off")
    fig.suptitle(title, fontsize=14)
    fig.tight_layout()
    fig.savefig(outpath, dpi=140, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uded-root", default=str(DEFAULT_UDED))
    ap.add_argument("--model-dir", default=str(MODEL_DIR))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--max-side", type=int, default=256)
    ap.add_argument("--thresholds", type=int, default=21)
    ap.add_argument("--bootstrap", type=int, default=5000)
    ap.add_argument("--top-heldout", type=int, default=10)
    ap.add_argument("--preview", type=int, default=6)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t_all = time.perf_counter()

    model_dir = Path(args.model_dir)
    learned = json.loads((model_dir / "learned_measures.json").read_text(encoding="utf-8"))
    context_model = json.loads((model_dir / "context_router.json").read_text(encoding="utf-8"))

    raw = resize_items(load_uded(Path(args.uded_root)), args.max_side)
    t0 = time.perf_counter()
    items, feature_names = prepare(raw)
    h_all = make_heterogeneity(items)
    prepare_s = time.perf_counter() - t0
    select_items, test_items = items[0::2], items[1::2]
    h_sel, h_test = h_all[0::2], h_all[1::2]

    specs = [s for s in measure_registry(len(feature_names), learned=learned) if s.get("routing") != "oracle"]
    specs_by_name = {str(s["name"]): s for s in specs}

    base_sel_scores = [d["scharr"] for d in select_items]
    base_test_scores = [d["scharr"] for d in test_items]
    base_cv = cv_threshold_score(base_sel_scores, select_items, args.thresholds, 3)
    base_sel = selection_metric(base_sel_scores, select_items, args.thresholds)
    base_fixed, base_counts, base_per = fixed_eval(base_test_scores, test_items, float(base_sel["threshold"]))
    atomic_json({"selection_cv": base_cv, "selection": base_sel, "heldout_fixed": base_fixed}, out / "baseline.json")

    pd.DataFrame([
        {"id": d["id"], "split": "selection" if i % 2 == 0 else "heldout"}
        for i, d in enumerate(items)
    ]).to_csv(out / "split.csv", index=False)

    single_path = out / "selection_single.csv"
    router_path = out / "selection_router.csv"
    runtime_path = out / "runtime.csv"
    single = load_csv(single_path)
    router = load_csv(router_path)
    runtime = load_csv(runtime_path)

    single_specs = single_controller_specs()
    router_grid = router_specs()

    for i, spec in enumerate(specs, 1):
        name = str(spec["name"])
        if single_complete(single, name, len(single_specs)):
            print(f"SINGLE SKIP [{i}/{len(specs)}] {name}", flush=True)
            continue
        print(f"SINGLE RUN [{i}/{len(specs)}] {name}", flush=True)
        rows, elapsed = evaluate_single_measure(spec, items, select_items, context_model, h_sel, args.thresholds)
        single = pd.concat([single, pd.DataFrame(rows)], ignore_index=True)
        single = single.drop_duplicates(["measure", "strategy", "params"], keep="last")
        atomic_csv(single, single_path)
        runtime = pd.concat([runtime, pd.DataFrame([{"unit": name, "type": "single", "elapsed_s": elapsed}])], ignore_index=True)
        runtime = runtime.drop_duplicates(["unit", "type"], keep="last")
        atomic_csv(runtime, runtime_path)
        atomic_json({"phase": "single", "index": i, "total": len(specs), "current": name}, out / "progress.json")
        gc.collect()

    pairs = router_pairs(set(specs_by_name))
    for i, (a, b) in enumerate(pairs, 1):
        if pair_complete(router, a, b, len(router_grid)):
            print(f"ROUTER SKIP [{i}/{len(pairs)}] {a} <> {b}", flush=True)
            continue
        print(f"ROUTER RUN [{i}/{len(pairs)}] {a} <> {b}", flush=True)
        rows, elapsed = evaluate_router_pair(a, b, specs_by_name, items, select_items, context_model, h_sel, args.thresholds)
        router = pd.concat([router, pd.DataFrame(rows)], ignore_index=True)
        router = router.drop_duplicates(["pair_key", "params"], keep="last")
        atomic_csv(router, router_path)
        runtime = pd.concat([runtime, pd.DataFrame([{"unit": pair_key(a, b), "type": "router", "elapsed_s": elapsed}])], ignore_index=True)
        runtime = runtime.drop_duplicates(["unit", "type"], keep="last")
        atomic_csv(runtime, runtime_path)
        atomic_json({"phase": "router", "index": i, "total": len(pairs), "current": pair_key(a, b)}, out / "progress.json")
        gc.collect()

    all_sel = pd.concat([single, router], ignore_index=True, sort=False)
    all_sel = all_sel.sort_values(["cv_F1", "selection_ODS", "selection_AP"], ascending=False).reset_index(drop=True)
    atomic_csv(all_sel, out / "selection_all_ranked.csv")

    # Only now expose held-out to the selection-ranked finalists.
    topk = min(int(args.top_heldout), len(all_sel))
    held_rows = []
    boot_rows = []
    best_cache = None
    for rank, (_, r) in enumerate(all_sel.head(topk).iterrows(), 1):
        print(f"HELDOUT FINALIST [{rank}/{topk}] {r.measure} {r.strategy}", flush=True)
        ssel, stest, csel, ctest = build_candidate_scores(r, specs_by_name, items, select_items, test_items, context_model, h_sel, h_test)
        fit = selection_metric(ssel, select_items, args.thresholds)
        met, counts, per = fixed_eval(stest, test_items, float(fit["threshold"]))
        boot = bootstrap_delta(base_counts, counts, int(args.bootstrap), seed=20261005 + rank)
        row = {
            "selection_rank": rank,
            "candidate_type": r.candidate_type,
            "measure": r.measure,
            "measure_kind": r.measure_kind,
            "strategy": r.strategy,
            "params": r.params,
            "cv_F1": float(r.cv_F1),
            "selection_ODS": float(fit["ODS"]),
            "selection_threshold": float(fit["threshold"]),
            "heldout_precision": float(met["precision"]),
            "heldout_recall": float(met["recall"]),
            "heldout_F1": float(met["F1"]),
            "delta_F1_vs_scharr": float(met["F1"] - base_fixed["F1"]),
            **boot,
        }
        if "measure_a" in r and pd.notna(r.get("measure_a", np.nan)):
            row["measure_a"] = r.get("measure_a")
            row["measure_b"] = r.get("measure_b")
        held_rows.append(row)
        boot_rows.append(row)
        if rank == 1:
            best_cache = (r.copy(), fit, met, stest, ctest, per)
        del ssel, csel
        gc.collect()

    held = pd.DataFrame(held_rows)
    atomic_csv(held, out / "heldout_finalists.csv")
    atomic_csv(pd.DataFrame(boot_rows), out / "paired_bootstrap_finalists.csv")

    # Family summaries are based only on selection CV, preserving held-out discipline.
    fam = (all_sel.groupby(["candidate_type", "measure_kind"], dropna=False)
           .agg(n=("cv_F1", "size"), mean_cv_F1=("cv_F1", "mean"), median_cv_F1=("cv_F1", "median"),
                best_cv_F1=("cv_F1", "max"), best_selection_ODS=("selection_ODS", "max"))
           .reset_index().sort_values(["best_cv_F1", "mean_cv_F1"], ascending=False))
    atomic_csv(fam, out / "selection_family_summary.csv")

    primary = held.iloc[0] if len(held) else None
    if best_cache is not None:
        br, fit, met, best_test_scores, best_test_conf, per = best_cache
        save_context_sheet(
            test_items, base_test_scores, float(base_sel["threshold"]),
            best_test_scores, float(fit["threshold"]), best_test_conf, h_test,
            out / "best_contact_sheet.png",
            f"UDED Stage 8 — selection winner {br.measure} / {br.strategy} | held-out F1={met['F1']:.4f} vs Scharr={base_fixed['F1']:.4f}",
            args.preview,
        )
        base_df = pd.DataFrame(base_per).add_prefix("baseline_")
        best_df = pd.DataFrame(per).add_prefix("stage8_")
        cmp = pd.concat([base_df, best_df], axis=1)
        cmp["delta_F1"] = cmp.stage8_F1 - cmp.baseline_F1
        atomic_csv(cmp, out / "per_image_primary_vs_baseline.csv")

    summary = {
        "status": "complete",
        "protocol": "15-image natural selection split with 3-fold inner threshold CV; held-out evaluated only for top selection-ranked finalists",
        "n_images": len(items),
        "n_selection": len(select_items),
        "n_heldout": len(test_items),
        "n_measures": len(specs),
        "n_single_configs": int(len(single)),
        "n_router_configs": int(len(router)),
        "n_total_selection_configs": int(len(all_sel)),
        "router_pool": [n for n in ROUTER_POOL if n in specs_by_name],
        "baseline": {"cv": base_cv, "selection": base_sel, "heldout_fixed": base_fixed},
        "primary_selection_winner": primary.to_dict() if primary is not None else None,
        "heldout_note": "Only the selection-ranked finalists were evaluated on held-out; held-out ordering is diagnostic and must not redefine the winner.",
        "prepare_s": prepare_s,
        "runtime_total_s": float(time.perf_counter() - t_all),
    }
    atomic_json(summary, out / "summary.json")
    atomic_json({"phase": "complete", "n_selection_configs": len(all_sel), "n_finalists": len(held)}, out / "progress.json")

    text = [
        "# UDED Stage 8 — contextual MFI controller",
        "",
        "Stage 8 tests MFI as a **contextual controller** rather than only a direct score fusion.",
        "Every non-oracle fuzzy measure remains in the single-measure competition. A separate local",
        "mixture-of-measures router tests whether image heterogeneity should switch between measures.",
        "",
        "## Anti-overfitting protocol",
        "",
        "The 15-image natural selection split is internally divided into 3 folds. For every candidate,",
        "the threshold used on each validation fold is learned on the other two folds. Candidates are",
        "ranked by out-of-fold F1. The 15-image held-out split is evaluated only for the top finalists.",
        "Held-out ranking is diagnostic and cannot redefine the selection winner.",
        "",
        f"Total selection configurations: **{len(all_sel)}**",
        f"Scharr inner-CV F1: **{base_cv['cv_F1']:.6f}**",
        f"Scharr frozen held-out F1: **{base_fixed['F1']:.6f}**",
    ]
    if primary is not None:
        text += [
            "",
            "## Primary result",
            f"Selection winner: **{primary['measure']} + {primary['strategy']}**",
            f"- inner-CV F1: **{float(primary['cv_F1']):.6f}**",
            f"- frozen held-out F1: **{float(primary['heldout_F1']):.6f}**",
            f"- delta vs Scharr: **{float(primary['delta_F1_vs_scharr']):+.6f}**",
            f"- bootstrap 95% CI: **[{float(primary['delta_F1_ci95_low']):.6f}, {float(primary['delta_F1_ci95_high']):.6f}]**",
            f"- P(delta>0): **{float(primary['p_delta_gt_0']):.4f}**",
        ]
    text += [
        "",
        "Evaluation still uses the project's tolerant-dilation proxy, not the official Berkeley bipartite matcher.",
    ]
    (out / "README.md").write_text("\n".join(text) + "\n", encoding="utf-8")

    print("STAGE8_DONE", flush=True)
    print(json.dumps(summary, separators=(",", ":"), default=float), flush=True)
    if len(held):
        print("STAGE8_FINALISTS", flush=True)
        print(held[["selection_rank", "measure", "strategy", "cv_F1", "heldout_F1", "delta_F1_vs_scharr", "delta_F1_ci95_low", "delta_F1_ci95_high", "p_delta_gt_0"]].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
