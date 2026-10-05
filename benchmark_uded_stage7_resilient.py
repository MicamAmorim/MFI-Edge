from __future__ import annotations

from pathlib import Path
import argparse
import gc
import json
import math
import os
import time

import numpy as np
import pandas as pd

from benchmark_uded import DEFAULT_UDED, MODEL_DIR, load_uded, prepare
from benchmark_uded_quick import resize_items
from benchmark_uded_fusion import compute_conf
from benchmark_uded_stage7 import (
    fixed_eval,
    selection_metric,
    bootstrap_delta,
    evaluate_measure,
    save_contact_sheet,
    save_pr_curve,
    save_parallel_plot,
    benchmark_parallel_scaling,
)
from src.advanced_fusion import advanced_fusion_specs, fuse_advanced
from src.fuzzy_measures import measure_registry


ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "uded" / "stage7_resilient"


def atomic_csv(df: pd.DataFrame, path: Path, sort_cols=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    x = df.copy()
    if sort_cols and len(x):
        cols = [c for c in sort_cols if c in x.columns]
        if cols:
            x = x.sort_values(cols).reset_index(drop=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    x.to_csv(tmp, index=False)
    os.replace(tmp, path)


def atomic_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, default=float), encoding="utf-8")
    os.replace(tmp, path)


def read_csv(path: Path):
    return pd.read_csv(path) if path.exists() and path.stat().st_size > 0 else pd.DataFrame()


def merge_rows(old: pd.DataFrame, rows, keys):
    new = pd.DataFrame(rows)
    if old.empty:
        out = new
    elif new.empty:
        out = old
    else:
        out = pd.concat([old, new], ignore_index=True)
    if len(out):
        use = [k for k in keys if k in out.columns]
        if use:
            out = out.drop_duplicates(use, keep="last")
    return out.reset_index(drop=True)


def complete_measure(name, roi_q, sel_df, fixed_df):
    expected = len(advanced_fusion_specs(float(roi_q)))
    if sel_df.empty or fixed_df.empty:
        return False
    a = sel_df[sel_df.measure.astype(str) == str(name)]
    b = fixed_df[fixed_df.measure.astype(str) == str(name)]
    ka = a[["strategy", "params"]].drop_duplicates().shape[0] if len(a) else 0
    kb = b[["strategy", "params"]].drop_duplicates().shape[0] if len(b) else 0
    return ka >= expected and kb >= expected


def progress_snapshot(out, specs, roi_by_measure, sel_df, fixed_df, current=None, status="running"):
    done = []
    for s in specs:
        n = str(s["name"])
        q = float(roi_by_measure.get(n, 0.50))
        if complete_measure(n, q, sel_df, fixed_df):
            done.append(n)
    atomic_json({
        "status": status,
        "current_measure": current,
        "completed_measures": done,
        "n_completed": len(done),
        "n_total": len(specs),
        "fraction": float(len(done) / max(len(specs), 1)),
        "updated_unix": time.time(),
    }, out / "progress.json")


def best_fixed_row(fixed, best):
    m = (
        (fixed.measure.astype(str) == str(best["measure"]))
        & (fixed.strategy.astype(str) == str(best["strategy"]))
        & (fixed.params.astype(str) == str(best["params"]))
    )
    return fixed[m].iloc[0]


def write_report(out, base_sel, base_fixed, best, best_fixed, boot, n_measures, n_configs,
                 prepare_s, sweep_s, total_s, workers, max_side):
    delta = float(best_fixed["F1"] - base_fixed["F1"])
    text = f"""# UDED Stage 7 — resumable advanced fusion

This is the checkpointed/resumable UDED Stage-7 run. Each fuzzy measure is evaluated
sequentially and committed to persistent CSV checkpoints before the next measure starts.
This avoids losing completed work if the container exits or hits a memory limit.

## Protocol

- fuzzy measures: **{n_measures}**
- measure × fusion configurations: **{n_configs}**
- natural-image split: alternating selection / held-out
- threshold chosen on selection only and frozen for held-out
- maximum image side: **{max_side}px**
- main sweep workers: **{workers}** (deliberately conservative for 1 GB RAM)
- bootstrap: applied only to the top selection finalists after the full sweep

## Baseline

Scharr+NMS selection ODS: **{float(base_sel['ODS']):.6f}**  
Frozen held-out F1: **{float(base_fixed['F1']):.6f}**

## Selection winner

**{best['measure']} + {best['strategy']}**  
params: `{best['params']}`

- selection ODS: **{float(best['ODS']):.6f}**
- held-out precision: **{float(best_fixed['precision']):.6f}**
- held-out recall: **{float(best_fixed['recall']):.6f}**
- held-out F1: **{float(best_fixed['F1']):.6f}**
- delta F1 vs Scharr: **{delta:+.6f}**
- bootstrap 95% CI: **[{float(boot.get('delta_F1_ci95_low', float('nan'))):.6f}, {float(boot.get('delta_F1_ci95_high', float('nan'))):.6f}]**
- P(delta F1 > 0): **{float(boot.get('p_delta_gt_0', float('nan'))):.4f}**

## Runtime

- prepare: **{prepare_s:.2f}s**
- resumable sweep: **{sweep_s:.2f}s**
- total: **{total_s:.2f}s**

## Artefacts

- `selection_all.csv`
- `heldout_fixed_all.csv`
- `runtime_by_measure.csv`
- `paired_bootstrap_top10.csv`
- `per_image_best_vs_baseline.csv`
- `best_contact_sheet.png`
- `selection_pr_curve.png`
- `parallel_scaling.csv`
- `parallel_scaling.png`
- `progress.json`

The visual sheet uses the first held-out images in dataset order, not cherry-picked examples.
The evaluation remains the project's tolerant-dilation proxy, not the official Berkeley matcher.
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
    ap.add_argument("--workers", type=int, default=1,
                    help="Main sweep is sequential by default to stay under 1 GB RAM.")
    ap.add_argument("--preview", type=int, default=6)
    ap.add_argument("--parallel-benchmark-images", type=int, default=2)
    args = ap.parse_args()

    t_all = time.perf_counter()
    root = Path(args.uded_root)
    model_dir = Path(args.model_dir)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    learned = json.loads((model_dir / "learned_measures.json").read_text(encoding="utf-8"))
    context_model = json.loads((model_dir / "context_router.json").read_text(encoding="utf-8"))
    validation = pd.read_csv(model_dir / "validation_best_per_measure.csv")
    roi_by_measure = dict(zip(validation.measure.astype(str), validation.roi_q.astype(float)))

    raw = resize_items(load_uded(root), args.max_side)
    t0 = time.perf_counter()
    items, feature_names = prepare(raw)
    prepare_s = time.perf_counter() - t0
    atomic_csv(pd.DataFrame([
        {"id": d["id"], "prepare_s": float(d.get("prepare_s", float("nan")))} for d in items
    ]), out / "prepare_per_image.csv")

    select_items = items[0::2]
    test_items = items[1::2]
    atomic_csv(pd.DataFrame([
        {"id": d["id"], "split": "selection" if i % 2 == 0 else "heldout"}
        for i, d in enumerate(items)
    ]), out / "uded_natural_split.csv")

    base_sel_scores = [d["scharr"] for d in select_items]
    base_test_scores = [d["scharr"] for d in test_items]
    base_sel = selection_metric(base_sel_scores, select_items, args.thresholds)
    base_fixed, base_counts, base_per = fixed_eval(base_test_scores, test_items, base_sel["threshold"])
    atomic_json({"selection": base_sel, "heldout_fixed": base_fixed}, out / "baseline.json")

    specs = [s for s in measure_registry(len(feature_names), learned=learned)
             if s.get("routing") != "oracle"]
    specs_by_name = {str(s["name"]): s for s in specs}

    sel_path = out / "selection_all.csv"
    fixed_path = out / "heldout_fixed_all.csv"
    runtime_path = out / "runtime_by_measure.csv"
    sel_df = read_csv(sel_path)
    fixed_df = read_csv(fixed_path)
    runtime_df = read_csv(runtime_path)

    progress_snapshot(out, specs, roi_by_measure, sel_df, fixed_df)
    t_sweep = time.perf_counter()

    # Deliberately sequential. Each completed measure is checkpointed atomically.
    for idx, spec in enumerate(specs, 1):
        name = str(spec["name"])
        rq = float(roi_by_measure.get(name, 0.50))
        if complete_measure(name, rq, sel_df, fixed_df):
            print(f"RESUME SKIP [{idx}/{len(specs)}] {name}", flush=True)
            continue

        print(f"RESUME RUN [{idx}/{len(specs)}] {name} ROI={rq:.2f}", flush=True)
        progress_snapshot(out, specs, roi_by_measure, sel_df, fixed_df, current=name)
        try:
            sel_rows, fixed_rows, _count_cache, runtime = evaluate_measure(
                spec, items, select_items, test_items, context_model, rq, args.thresholds
            )
            sel_df = merge_rows(sel_df, sel_rows, ["measure", "strategy", "params"])
            fixed_df = merge_rows(fixed_df, fixed_rows, ["measure", "strategy", "params"])
            runtime_df = merge_rows(runtime_df, [runtime], ["measure"])
            atomic_csv(sel_df, sel_path, ["measure", "strategy", "params"])
            atomic_csv(fixed_df, fixed_path, ["measure", "strategy", "params"])
            atomic_csv(runtime_df, runtime_path, ["measure"])
            print(f"CHECKPOINT DONE {name}: {len(sel_rows)} configs", flush=True)
            del _count_cache, sel_rows, fixed_rows
            gc.collect()
        except Exception as exc:
            atomic_json({"measure": name, "error": repr(exc), "time": time.time()}, out / "last_error.json")
            progress_snapshot(out, specs, roi_by_measure, sel_df, fixed_df, current=name, status="error")
            raise

    sweep_s = time.perf_counter() - t_sweep
    progress_snapshot(out, specs, roi_by_measure, sel_df, fixed_df, status="sweep_complete")

    sel = read_csv(sel_path).sort_values(["ODS", "AP", "OIS"], ascending=False).reset_index(drop=True)
    fixed = read_csv(fixed_path)
    n_configs = len(sel)

    # Bootstrap only the top ten selection finalists; checkpoint each one.
    boot_path = out / "paired_bootstrap_top10.csv"
    bootdf = read_csv(boot_path)
    for rank, (_, r) in enumerate(sel.head(10).iterrows(), 1):
        mname, strategy, pjson = str(r.measure), str(r.strategy), str(r.params)
        if not bootdf.empty:
            exists = ((bootdf.measure.astype(str) == mname)
                      & (bootdf.strategy.astype(str) == strategy)
                      & (bootdf.params.astype(str) == pjson)).any()
            if exists:
                print(f"BOOT SKIP {rank}/10 {mname} {strategy}", flush=True)
                continue
        print(f"BOOT RUN {rank}/10 {mname} {strategy}", flush=True)
        spec = specs_by_name[mname]
        confs = compute_conf(spec, items, context_model)
        params = json.loads(pjson)
        test_scores = [
            fuse_advanced(d["scharr"], c, strategy, params)
            for d, c in zip(test_items, confs[1::2])
        ]
        frow = best_fixed_row(fixed, r)
        _, cand_counts, _ = fixed_eval(test_scores, test_items, float(r.threshold))
        b = bootstrap_delta(base_counts, cand_counts, args.bootstrap)
        row = {
            "measure": mname,
            "strategy": strategy,
            "params": pjson,
            "selection_ODS": float(r.ODS),
            "fixed_heldout_F1": float(frow.F1),
            "baseline_fixed_heldout_F1": float(base_fixed["F1"]),
            "observed_delta_F1": float(frow.F1 - base_fixed["F1"]),
            **b,
        }
        bootdf = merge_rows(bootdf, [row], ["measure", "strategy", "params"])
        atomic_csv(bootdf, boot_path, ["selection_ODS"])
        del confs, test_scores, cand_counts
        gc.collect()

    best = sel.iloc[0]
    best_fixed = best_fixed_row(fixed, best)
    bmatch = bootdf[(bootdf.measure.astype(str) == str(best.measure))
                    & (bootdf.strategy.astype(str) == str(best.strategy))
                    & (bootdf.params.astype(str) == str(best.params))]
    best_boot = bmatch.iloc[0].to_dict() if len(bmatch) else {}

    # Recompute only the winner for visual artefacts and per-image comparison.
    best_spec = specs_by_name[str(best.measure)]
    best_confs = compute_conf(best_spec, items, context_model)
    best_params = json.loads(str(best.params))
    best_sel_scores = [
        fuse_advanced(d["scharr"], c, str(best.strategy), best_params)
        for d, c in zip(select_items, best_confs[0::2])
    ]
    best_test_scores = [
        fuse_advanced(d["scharr"], c, str(best.strategy), best_params)
        for d, c in zip(test_items, best_confs[1::2])
    ]
    best_metrics, _, best_per = fixed_eval(best_test_scores, test_items, float(best.threshold))

    base_df = pd.DataFrame(base_per).add_prefix("baseline_")
    best_df = pd.DataFrame(best_per).add_prefix("best_")
    cmp = pd.concat([base_df, best_df], axis=1)
    cmp["delta_F1"] = cmp["best_F1"] - cmp["baseline_F1"]
    atomic_csv(cmp, out / "per_image_best_vs_baseline.csv")

    save_contact_sheet(
        test_items, base_test_scores, float(base_sel["threshold"]),
        best_test_scores, float(best.threshold), best_confs[1::2],
        out / "best_contact_sheet.png",
        f"UDED held-out — {best.measure} + {best.strategy} | F1={best_metrics['F1']:.4f} vs Scharr={base_fixed['F1']:.4f}",
        n=args.preview,
    )
    save_pr_curve(
        select_items, base_sel_scores, best_sel_scores,
        out / "selection_pr_curve.png",
        f"{best.measure}+{best.strategy}",
    )

    # Runtime scaling is intentionally last. Core scientific results are already checkpointed.
    try:
        scale = benchmark_parallel_scaling(
            specs_by_name, items, context_model, workers=(1, 2, 4),
            n_images=max(1, int(args.parallel_benchmark_images))
        )
        atomic_csv(scale, out / "parallel_scaling.csv", ["workers"])
        save_parallel_plot(scale, out / "parallel_scaling.png")
    except Exception as exc:
        atomic_json({"error": repr(exc)}, out / "parallel_scaling_error.json")

    total_s = time.perf_counter() - t_all
    summary = {
        "status": "complete",
        "n_images": len(items),
        "n_selection": len(select_items),
        "n_heldout": len(test_items),
        "n_measures": len(specs),
        "n_configs": n_configs,
        "baseline": {"selection": base_sel, "heldout_fixed": base_fixed},
        "winner": {
            "measure": str(best.measure),
            "strategy": str(best.strategy),
            "params": str(best.params),
            "selection_ODS": float(best.ODS),
            "selection_threshold": float(best.threshold),
            "heldout": {k: float(best_fixed[k]) for k in ["precision", "recall", "F1", "mean_image_F1"] if k in best_fixed},
            "bootstrap": best_boot,
        },
        "runtime": {"prepare_s": prepare_s, "sweep_s": sweep_s, "total_s": total_s},
    }
    atomic_json(summary, out / "summary.json")
    write_report(out, base_sel, base_fixed, best, best_fixed, best_boot, len(specs), n_configs,
                 prepare_s, sweep_s, total_s, args.workers, args.max_side)
    progress_snapshot(out, specs, roi_by_measure, sel, fixed, status="complete")
    print("UDED_STAGE7_RESILIENT_DONE", flush=True)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
