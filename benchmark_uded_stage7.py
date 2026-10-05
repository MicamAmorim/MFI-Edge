from __future__ import annotations

from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import gc
import json
import math
import os
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import ndimage as ndi

from benchmark_uded import (
    DEFAULT_UDED,
    MODEL_DIR,
    _variable_tol_curve,
    load_uded,
    prepare,
)
from benchmark_uded_quick import resize_items
from benchmark_uded_fusion import compute_conf, gt_conf_stats
from src.advanced_fusion import advanced_fusion_specs, fuse_advanced
from src.evaluation import tolerant_counts, counts_to_prf
from src.fuzzy_measures import measure_registry


ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "uded" / "stage7"


def fixed_eval(scores, items, threshold, frac_diag=0.0075):
    """Evaluate one frozen threshold on a fixed image set."""
    mp = npred = mg = ngt = 0
    counts = []
    per_image = []
    for s, d in zip(scores, items):
        g = np.asarray(d["gt"], dtype=bool)
        tol = max(1, int(round(float(frac_diag) * math.hypot(*g.shape))))
        cnt = tuple(int(x) for x in tolerant_counts(np.asarray(s) >= float(threshold), g, tol))
        p, r, f = counts_to_prf(*cnt)
        counts.append(cnt)
        mp += cnt[0]
        npred += cnt[1]
        mg += cnt[2]
        ngt += cnt[3]
        per_image.append({
            "id": d["id"],
            "tol_px": tol,
            "precision": float(p),
            "recall": float(r),
            "F1": float(f),
            "matched_pred": cnt[0],
            "n_pred": cnt[1],
            "matched_gt": cnt[2],
            "n_gt": cnt[3],
        })
    p, r, f = counts_to_prf(mp, npred, mg, ngt)
    return {
        "precision": float(p),
        "recall": float(r),
        "F1": float(f),
        "mean_image_F1": float(np.mean([x["F1"] for x in per_image])) if per_image else 0.0,
    }, counts, per_image


def selection_metric(scores, items, n_thresholds=21):
    m = _variable_tol_curve(
        scores,
        [d["gt"] for d in items],
        beta=1.0,
        n_thresholds=int(n_thresholds),
        frac_diag=0.0075,
    )
    return {k: v for k, v in m.items() if k != "curve"}


def bootstrap_delta(base_counts, cand_counts, n_boot=5000, seed=20261004):
    rng = np.random.default_rng(seed)
    base_counts = np.asarray(base_counts, dtype=np.int64)
    cand_counts = np.asarray(cand_counts, dtype=np.int64)
    n = len(base_counts)
    deltas = np.empty(int(n_boot), dtype=float)
    for b in range(int(n_boot)):
        ids = rng.integers(0, n, size=n)
        bc = np.sum(base_counts[ids], axis=0)
        cc = np.sum(cand_counts[ids], axis=0)
        fb = counts_to_prf(*bc)[2]
        fc = counts_to_prf(*cc)[2]
        deltas[b] = float(fc - fb)
    lo, hi = np.quantile(deltas, [0.025, 0.975])
    return {
        "delta_F1_boot_mean": float(np.mean(deltas)),
        "delta_F1_ci95_low": float(lo),
        "delta_F1_ci95_high": float(hi),
        "p_delta_gt_0": float(np.mean(deltas > 0)),
        "n_boot": int(n_boot),
    }


def _key(measure, strategy, params_json):
    return (str(measure), str(strategy), str(params_json))


def evaluate_measure(spec, items, select_items, test_items, context_model, roi_q,
                     n_thresholds=21):
    """Evaluate all Stage-7 fusion strategies for one fuzzy-measure spec."""
    name = str(spec["name"])
    t_measure = time.perf_counter()
    confs = compute_conf(spec, items, context_model)
    conf_runtime = time.perf_counter() - t_measure

    conf_sel = confs[0::2]
    conf_test = confs[1::2]
    gtconf_sel = gt_conf_stats(conf_sel, select_items)
    gtconf_test = gt_conf_stats(conf_test, test_items)

    sel_rows = []
    fixed_rows = []
    count_cache = {}
    specs = advanced_fusion_specs(roi_q)

    for strategy, params in specs:
        params_json = json.dumps(params, sort_keys=True)
        t0 = time.perf_counter()
        sv = [
            fuse_advanced(d["scharr"], c, strategy, params)
            for d, c in zip(select_items, conf_sel)
        ]
        st = [
            fuse_advanced(d["scharr"], c, strategy, params)
            for d, c in zip(test_items, conf_test)
        ]
        ms = selection_metric(sv, select_items, n_thresholds)
        mf, counts, _ = fixed_eval(st, test_items, ms["threshold"])
        eval_runtime = time.perf_counter() - t0

        base = {
            "measure": name,
            "measure_kind": str(spec.get("kind", "")),
            "strategy": strategy,
            "params": params_json,
            "synthetic_roi_q": float(roi_q),
        }
        sel_rows.append({
            **base,
            "gt_conf_mean": float(gtconf_sel),
            "conf_runtime_s": float(conf_runtime),
            "fusion_eval_runtime_s": float(eval_runtime),
            **ms,
        })
        fixed_rows.append({
            **base,
            "selection_threshold": float(ms["threshold"]),
            "gt_conf_mean": float(gtconf_test),
            **mf,
        })
        count_cache[_key(name, strategy, params_json)] = counts
        del sv, st

    runtime = {
        "measure": name,
        "measure_kind": str(spec.get("kind", "")),
        "n_strategies": len(specs),
        "conf_runtime_s": float(conf_runtime),
        "all_fusions_runtime_s": float(time.perf_counter() - t_measure - conf_runtime),
        "total_measure_runtime_s": float(time.perf_counter() - t_measure),
        "mean_conf_runtime_per_image_s": float(conf_runtime / max(len(items), 1)),
    }
    del confs, conf_sel, conf_test
    gc.collect()
    return sel_rows, fixed_rows, count_cache, runtime


def _run_conf_only(spec, items, context_model):
    compute_conf(spec, items, context_model)
    return str(spec["name"])


def benchmark_parallel_scaling(specs_by_name, items, context_model, workers=(1, 2, 4),
                               n_images=8):
    preferred = [
        "context_additive_estimated",
        "power_q0.2",
        "sugeno_learned_sum1.40",
        "scale_2additive_learned",
    ]
    names = [n for n in preferred if n in specs_by_name]
    if len(names) < 4:
        names.extend([n for n in specs_by_name if n not in names][:4 - len(names)])
    selected_specs = [specs_by_name[n] for n in names[:4]]
    subset = items[: min(int(n_images), len(items))]
    rows = []
    baseline_elapsed = None

    for workers_n in workers:
        t0 = time.perf_counter()
        if int(workers_n) <= 1:
            for spec in selected_specs:
                _run_conf_only(spec, subset, context_model)
        else:
            with ThreadPoolExecutor(max_workers=int(workers_n)) as ex:
                futs = [
                    ex.submit(_run_conf_only, spec, subset, context_model)
                    for spec in selected_specs
                ]
                for fut in as_completed(futs):
                    fut.result()
        elapsed = time.perf_counter() - t0
        if baseline_elapsed is None:
            baseline_elapsed = elapsed
        pairs = len(selected_specs) * len(subset)
        rows.append({
            "workers": int(workers_n),
            "elapsed_s": float(elapsed),
            "speedup_vs_1": float(baseline_elapsed / elapsed) if elapsed > 0 else float("nan"),
            "measure_image_pairs": int(pairs),
            "pairs_per_s": float(pairs / elapsed) if elapsed > 0 else float("nan"),
            "measures": ",".join(names[:4]),
            "n_images": len(subset),
        })
    return pd.DataFrame(rows)


def overlay_edges(img, edge):
    x = np.asarray(img)
    if x.ndim == 2:
        x = np.stack([x, x, x], axis=2)
    else:
        x = x[..., :3]
    x = x.astype(float)
    if x.max() > 1.0:
        x = x / 255.0
    out = np.clip(x.copy(), 0.0, 1.0)
    e = np.asarray(edge, dtype=bool)
    out[e] = np.array([1.0, 0.0, 0.0])
    return out


def tolerance_error_map(gt, pred, tol):
    gt = np.asarray(gt, dtype=bool)
    pred = np.asarray(pred, dtype=bool)
    gt_d = ndi.binary_dilation(gt, iterations=int(tol))
    pred_d = ndi.binary_dilation(pred, iterations=int(tol))
    tp = pred & gt_d
    fp = pred & ~gt_d
    fn = gt & ~pred_d
    out = np.zeros((*gt.shape, 3), dtype=float)
    out[tp] = np.array([0.0, 1.0, 0.0])
    out[fp] = np.array([1.0, 0.0, 0.0])
    out[fn] = np.array([0.0, 0.4, 1.0])
    return out


def save_contact_sheet(test_items, baseline_scores, baseline_threshold, best_scores,
                       best_threshold, best_confs, outpath, title, n=6):
    n = min(int(n), len(test_items))
    fig, axes = plt.subplots(n, 6, figsize=(18, 3.0 * n))
    if n == 1:
        axes = np.asarray([axes])

    for row, d, bs, fs, conf in zip(
        axes,
        test_items[:n],
        baseline_scores[:n],
        best_scores[:n],
        best_confs[:n],
    ):
        base_pred = np.asarray(bs) >= float(baseline_threshold)
        best_pred = np.asarray(fs) >= float(best_threshold)
        tol = max(1, int(round(0.0075 * math.hypot(*d["gt"].shape))))

        row[0].imshow(d["img"])
        row[0].set_title(f'{d["id"]}\nOriginal')

        row[1].imshow(d["gt"], cmap="gray")
        row[1].set_title("Ground truth")

        row[2].imshow(overlay_edges(d["img"], base_pred))
        row[2].set_title("Scharr+NMS\nfrozen threshold")

        row[3].imshow(conf, cmap="inferno", vmin=0, vmax=1)
        row[3].set_title("MFI confidence")

        row[4].imshow(overlay_edges(d["img"], best_pred))
        row[4].set_title("Stage-7 best\nfrozen threshold")

        row[5].imshow(tolerance_error_map(d["gt"], best_pred, tol))
        row[5].set_title("Errors\nTP/FP/FN")

        for ax in row:
            ax.axis("off")

    fig.suptitle(title, fontsize=14)
    fig.tight_layout()
    fig.savefig(outpath, dpi=150, bbox_inches="tight")
    plt.close(fig)


def save_pr_curve(select_items, baseline_scores, best_scores, outpath, best_label):
    b = _variable_tol_curve(
        baseline_scores,
        [d["gt"] for d in select_items],
        n_thresholds=61,
        frac_diag=0.0075,
    )["curve"]
    m = _variable_tol_curve(
        best_scores,
        [d["gt"] for d in select_items],
        n_thresholds=61,
        frac_diag=0.0075,
    )["curve"]
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.plot(b[:, 2], b[:, 1], label="Scharr+NMS")
    ax.plot(m[:, 2], m[:, 1], label=best_label)
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.25)
    ax.legend()
    ax.set_title("UDED selection split — PR curve")
    fig.tight_layout()
    fig.savefig(outpath, dpi=160, bbox_inches="tight")
    plt.close(fig)


def save_parallel_plot(df, outpath):
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(df["workers"], df["speedup_vs_1"], marker="o")
    ax.set_xlabel("Worker threads")
    ax.set_ylabel("Speedup vs 1 worker")
    ax.set_title("MFI confidence computation parallel scaling")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(outpath, dpi=160, bbox_inches="tight")
    plt.close(fig)


def write_report(out, summary, best_row, best_fixed, baseline_fixed, boot_best,
                 n_measures, n_configs, runtime_summary):
    delta = float(best_fixed["F1"] - baseline_fixed["F1"])
    lo = boot_best.get("delta_F1_ci95_low", float("nan"))
    hi = boot_best.get("delta_F1_ci95_high", float("nan"))
    pgt = boot_best.get("p_delta_gt_0", float("nan"))
    text = f"""# UDED Stage 7 — advanced MFI fusion

This run evaluates every deployable fuzzy-measure variant present in the Stage-5
registry against the same advanced fusion grid while keeping the MFI aggregation
backbone fixed at **CF1F2(CL,CL)** and the five-scale schedule used by the current
prototype.

## Protocol

- UDED images: {summary['n_images']} total.
- Natural-image split: {summary['n_selection']} selection / {summary['n_heldout']} held-out.
- Threshold selection: selection split only; threshold is frozen before held-out evaluation.
- Number of fuzzy-measure variants: {n_measures}.
- Total measure × fusion configurations: {n_configs}.
- Tolerance: 0.75% of image diagonal, rounded to at least 1 px.
- Images resized to maximum side {summary['max_side']} px.
- Metric implementation is still the tolerant-dilation proxy, not the official Berkeley bipartite matcher.

## Primary result

Baseline Scharr+NMS held-out F1: **{baseline_fixed['F1']:.6f}**

Selection winner: **{best_row['measure']} + {best_row['strategy']}**

- selection ODS: **{best_row['ODS']:.6f}**
- frozen held-out precision: **{best_fixed['precision']:.6f}**
- frozen held-out recall: **{best_fixed['recall']:.6f}**
- frozen held-out F1: **{best_fixed['F1']:.6f}**
- delta F1 vs baseline: **{delta:+.6f}**
- paired-bootstrap 95% CI for delta F1: **[{lo:.6f}, {hi:.6f}]**
- P(delta F1 > 0): **{pgt:.4f}**

The winner is defined only by selection-split metrics. Held-out metrics are reported
after the choice and are not used to choose the winner.

## Visual checks

![Held-out qualitative comparison](best_contact_sheet.png)

![Selection PR curve](selection_pr_curve.png)

![Parallel scaling](parallel_scaling.png)

The contact sheet uses the first held-out images in dataset order rather than
cherry-picking examples.

## Runtime

- workers used in the main sweep: **{runtime_summary['workers']}**
- feature/preparation wall time: **{runtime_summary['prepare_wall_s']:.2f} s**
- advanced measure/fusion sweep wall time: **{runtime_summary['measure_sweep_wall_s']:.2f} s**
- whole Stage-7 benchmark wall time: **{runtime_summary['total_wall_s']:.2f} s**

See `runtime_by_measure.csv`, `prepare_per_image.csv`, and
`parallel_scaling.csv` for processing details.

## Scope note

This is exhaustive over the **current deployable fuzzy-measure registry × Stage-7
fusion grid**. It is not the full Cartesian product of every aggregation operator
(CF, CC, CF1F2 and all operator pairs), feature subset, scale schedule and fusion
parameter. That larger factorial should be chunked across independent workers/jobs
to keep real-image evaluation tractable.
"""
    (out / "README.md").write_text(text, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uded-root", default=str(DEFAULT_UDED))
    ap.add_argument("--model-dir", default=str(MODEL_DIR))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--max-side", type=int, default=256)
    ap.add_argument("--thresholds", type=int, default=21)
    ap.add_argument("--bootstrap", type=int, default=5000)
    ap.add_argument("--workers", type=int, default=max(1, min(4, os.cpu_count() or 1)))
    ap.add_argument("--preview", type=int, default=6)
    ap.add_argument("--parallel-benchmark-images", type=int, default=8)
    args = ap.parse_args()

    total_t0 = time.perf_counter()
    root = Path(args.uded_root)
    model_dir = Path(args.model_dir)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    learned = json.loads((model_dir / "learned_measures.json").read_text(encoding="utf-8"))
    context_model = json.loads((model_dir / "context_router.json").read_text(encoding="utf-8"))
    validation = pd.read_csv(model_dir / "validation_best_per_measure.csv")
    roi_by_measure = dict(zip(validation.measure.astype(str), validation.roi_q.astype(float)))

    raw = resize_items(load_uded(root), args.max_side)

    prep_t0 = time.perf_counter()
    items, feature_names = prepare(raw)
    prepare_wall = time.perf_counter() - prep_t0
    pd.DataFrame([
        {"id": d["id"], "prepare_s": float(d.get("prepare_s", float("nan")))}
        for d in items
    ]).to_csv(out / "prepare_per_image.csv", index=False)

    select_items = items[0::2]
    test_items = items[1::2]
    pd.DataFrame([
        {"id": d["id"], "split": "selection" if i % 2 == 0 else "heldout"}
        for i, d in enumerate(items)
    ]).to_csv(out / "uded_natural_split.csv", index=False)

    base_sel_scores = [d["scharr"] for d in select_items]
    base_test_scores = [d["scharr"] for d in test_items]
    base_sel = selection_metric(base_sel_scores, select_items, args.thresholds)
    base_fixed, base_counts, base_per = fixed_eval(
        base_test_scores, test_items, base_sel["threshold"]
    )

    specs = [
        s for s in measure_registry(len(feature_names), learned=learned)
        if s.get("routing") != "oracle"
    ]
    specs_by_name = {str(s["name"]): s for s in specs}

    sweep_t0 = time.perf_counter()
    all_sel_rows = []
    all_fixed_rows = []
    all_counts = {}
    runtime_rows = []

    def submit_one(spec):
        name = str(spec["name"])
        rq = float(roi_by_measure.get(name, 0.50))
        print(f"STAGE7 {name} ROI={rq:.2f}", flush=True)
        return evaluate_measure(
            spec, items, select_items, test_items, context_model, rq, args.thresholds
        )

    if int(args.workers) <= 1:
        results = [submit_one(spec) for spec in specs]
    else:
        results = []
        with ThreadPoolExecutor(max_workers=int(args.workers)) as ex:
            futs = {ex.submit(submit_one, spec): str(spec["name"]) for spec in specs}
            for fut in as_completed(futs):
                name = futs[fut]
                print(f"STAGE7 DONE {name}", flush=True)
                results.append(fut.result())

    for sel_rows, fixed_rows, count_cache, runtime in results:
        all_sel_rows.extend(sel_rows)
        all_fixed_rows.extend(fixed_rows)
        all_counts.update(count_cache)
        runtime_rows.append(runtime)

    measure_sweep_wall = time.perf_counter() - sweep_t0

    sel = pd.DataFrame(all_sel_rows).sort_values(
        ["ODS", "AP", "OIS"], ascending=False
    ).reset_index(drop=True)
    fixed = pd.DataFrame(all_fixed_rows)
    runtimes = pd.DataFrame(runtime_rows).sort_values("total_measure_runtime_s")

    sel.to_csv(out / "selection_all.csv", index=False)
    fixed.to_csv(out / "heldout_fixed_all.csv", index=False)
    runtimes.to_csv(out / "runtime_by_measure.csv", index=False)

    selected = sel.head(30).copy()
    joined = selected.merge(
        fixed,
        on=["measure", "measure_kind", "strategy", "params", "synthetic_roi_q"],
        suffixes=("_selection", "_heldout"),
    )
    joined["delta_F1_vs_baseline"] = joined["F1"] - float(base_fixed["F1"])
    joined.to_csv(out / "selected_top30_fixed_heldout.csv", index=False)

    boot_rows = []
    for _, r in sel.head(10).iterrows():
        key = _key(r["measure"], r["strategy"], r["params"])
        frow = fixed[
            (fixed.measure == r["measure"])
            & (fixed.strategy == r["strategy"])
            & (fixed.params == r["params"])
        ].iloc[0]
        b = bootstrap_delta(base_counts, all_counts[key], args.bootstrap)
        boot_rows.append({
            "measure": r["measure"],
            "strategy": r["strategy"],
            "params": r["params"],
            "selection_ODS": float(r["ODS"]),
            "fixed_heldout_F1": float(frow["F1"]),
            "baseline_fixed_heldout_F1": float(base_fixed["F1"]),
            "observed_delta_F1": float(frow["F1"] - base_fixed["F1"]),
            **b,
        })
    bootdf = pd.DataFrame(boot_rows)
    bootdf.to_csv(out / "paired_bootstrap_top10.csv", index=False)

    best = sel.iloc[0]
    best_fixed_row = fixed[
        (fixed.measure == best["measure"])
        & (fixed.strategy == best["strategy"])
        & (fixed.params == best["params"])
    ].iloc[0]
    best_boot = bootdf[
        (bootdf.measure == best["measure"])
        & (bootdf.strategy == best["strategy"])
        & (bootdf.params == best["params"])
    ].iloc[0].to_dict()

    best_spec = specs_by_name[str(best["measure"])]
    best_confs = compute_conf(best_spec, items, context_model)
    best_params = json.loads(str(best["params"]))
    best_sel_scores = [
        fuse_advanced(d["scharr"], c, str(best["strategy"]), best_params)
        for d, c in zip(select_items, best_confs[0::2])
    ]
    best_test_scores = [
        fuse_advanced(d["scharr"], c, str(best["strategy"]), best_params)
        for d, c in zip(test_items, best_confs[1::2])
    ]
    best_fixed_metrics, _, best_per = fixed_eval(
        best_test_scores, test_items, float(best["threshold"])
    )

    base_per_df = pd.DataFrame(base_per).add_prefix("baseline_")
    best_per_df = pd.DataFrame(best_per).add_prefix("best_")
    per_cmp = pd.concat([base_per_df, best_per_df], axis=1)
    per_cmp["delta_F1"] = per_cmp["best_F1"] - per_cmp["baseline_F1"]
    per_cmp.to_csv(out / "per_image_best_vs_baseline.csv", index=False)

    save_contact_sheet(
        test_items,
        base_test_scores,
        float(base_sel["threshold"]),
        best_test_scores,
        float(best["threshold"]),
        best_confs[1::2],
        out / "best_contact_sheet.png",
        (
            f'UDED held-out — {best["measure"]} + {best["strategy"]} | '
            f'F1={best_fixed_metrics["F1"]:.4f} vs Scharr={base_fixed["F1"]:.4f}'
        ),
        n=args.preview,
    )
    save_pr_curve(
        select_items,
        base_sel_scores,
        best_sel_scores,
        out / "selection_pr_curve.png",
        f'{best["measure"]}+{best["strategy"]}',
    )

    scaling = benchmark_parallel_scaling(
        specs_by_name,
        items,
        context_model,
        workers=(1, 2, 4),
        n_images=args.parallel_benchmark_images,
    )
    scaling.to_csv(out / "parallel_scaling.csv", index=False)
    save_parallel_plot(scaling, out / "parallel_scaling.png")

    total_wall = time.perf_counter() - total_t0
    runtime_summary = {
        "workers": int(args.workers),
        "prepare_wall_s": float(prepare_wall),
        "prepare_sum_per_image_s": float(np.nansum([
            d.get("prepare_s", np.nan) for d in items
        ])),
        "measure_sweep_wall_s": float(measure_sweep_wall),
        "total_wall_s": float(total_wall),
        "n_images": len(items),
        "n_measures": len(specs),
        "n_configurations": len(sel),
        "images_per_second_total": float(len(items) / total_wall) if total_wall > 0 else float("nan"),
    }
    (out / "runtime_summary.json").write_text(
        json.dumps(runtime_summary, indent=2), encoding="utf-8"
    )

    summary = {
        "dataset": "UDED",
        "n_images": len(items),
        "n_selection": len(select_items),
        "n_heldout": len(test_items),
        "max_side": int(args.max_side),
        "feature_names": list(feature_names),
        "aggregation_backbone": "CF1F2(CL,CL)",
        "scales": [25, 13, 7, 5, 3],
        "measure_variants": len(specs),
        "measure_fusion_configurations": len(sel),
        "workers": int(args.workers),
        "protocol": (
            "rank all configurations on alternating-index natural selection split; "
            "freeze each selected threshold; evaluate held-out at that frozen threshold"
        ),
        "baseline_selection": base_sel,
        "baseline_fixed_heldout": base_fixed,
        "best_selection": best.to_dict(),
        "best_selection_fixed_heldout": best_fixed_row.to_dict(),
        "best_bootstrap": best_boot,
        "caveat": (
            "tolerant dilation proxy, not official Berkeley bipartite matching; "
            f"images resized to <= {args.max_side}px; all deployable fuzzy measures are crossed "
            "with the Stage-7 fusion grid, but aggregation operator/family, feature-set and "
            "scale-schedule Cartesian products are not part of this run"
        ),
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=float), encoding="utf-8"
    )

    write_report(
        out,
        summary,
        best,
        best_fixed_row,
        base_fixed,
        best_boot,
        len(specs),
        len(sel),
        runtime_summary,
    )

    print("\nSTAGE7 SELECTION TOP 20", flush=True)
    print(
        sel.head(20)[
            ["measure", "strategy", "ODS", "OIS", "AP", "R50", "gt_conf_mean"]
        ].to_string(index=False),
        flush=True,
    )
    print("\nSTAGE7 TOP 20 -> FROZEN HELDOUT", flush=True)
    print(
        joined.head(20)[
            [
                "measure",
                "strategy",
                "ODS",
                "selection_threshold",
                "precision",
                "recall",
                "F1",
                "delta_F1_vs_baseline",
            ]
        ].to_string(index=False),
        flush=True,
    )
    print("\nSTAGE7 PARALLEL SCALING", flush=True)
    print(scaling.to_string(index=False), flush=True)
    print("UDED_STAGE7_DONE", flush=True)


if __name__ == "__main__":
    main()
