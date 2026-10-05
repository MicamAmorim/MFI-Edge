from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
import argparse
import gc
import json
import os
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Avoid BLAS/OpenMP oversubscription when the outer experiment uses threads.
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

from benchmark_uded import DEFAULT_UDED, load_uded, prepare
from benchmark_uded_quick import resize_items
from benchmark_uded_stage7 import bootstrap_delta, fixed_eval, selection_metric, tolerance_error_map
from benchmark_uded_stage8_contextual import cv_threshold_score
from prepare_uded_runtime import prepare_uded
from src.ch_mfi import CHMFIConfig, CHMFIResult, run_ch_mfi
from src.context_maps import analyze_context
from src.research_grid import build_grid

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "local_dev" / "ch_mfi"


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


def ensure_uded(root: Path):
    if (root / "test_pair.lst").exists():
        return root
    print(f"UDED not found at {root}; downloading official repository...", flush=True)
    prepare_uded(root)
    if not (root / "test_pair.lst").exists():
        raise FileNotFoundError(f"UDED preparation failed: {root / 'test_pair.lst'}")
    return root


def enrich_context(items):
    for i, d in enumerate(items, start=1):
        print(f"CTX {i:02d}/{len(items)} {d['id']}", flush=True)
        d["ch_context"] = analyze_context(d["pre_img"])
    return items


def run_scores(cfg: CHMFIConfig, items):
    scores = []
    runtimes = []
    summaries = []
    for d in items:
        t0 = time.perf_counter()
        r: CHMFIResult = run_ch_mfi(
            d["pre_img"],
            cfg,
            precomputed=d["features"],
            context=d["ch_context"],
        )
        dt = time.perf_counter() - t0
        scores.append(np.asarray(r.score, np.float32))
        runtimes.append(dt)
        summaries.append({
            "id": d["id"],
            "runtime_s": dt,
            "mean_mfi": float(np.mean(r.mfi)),
            "mean_uncertainty": float(np.mean(r.uncertainty)),
            "mean_localizer": float(np.mean(r.localizer)),
        })
        del r
    return scores, runtimes, summaries


def evaluate_selection(cfg: CHMFIConfig, select_items, n_thresholds: int):
    t0 = time.perf_counter()
    scores, runtimes, summaries = run_scores(cfg, select_items)
    cv = cv_threshold_score(scores, select_items, n_thresholds=n_thresholds, n_folds=3)
    opt = selection_metric(scores, select_items, n_thresholds)
    total = time.perf_counter() - t0
    row = {
        "name": cfg.name,
        "hierarchy": cfg.hierarchy,
        "operator_mode": cfg.operator_mode,
        "measure_kind": str(cfg.within_measure.get("kind", "")),
        "dissimilarity": cfg.dissimilarity or "",
        "granularity": cfg.granularity,
        "localizer_mode": cfg.localizer_mode,
        "controller": cfg.controller,
        "alpha": cfg.alpha,
        "beta_uncertainty": cfg.beta_uncertainty,
        "cv_F1": float(cv["cv_F1"]),
        "cv_mean_fold_F1": float(cv["cv_mean_fold_F1"]),
        "cv_std_fold_F1": float(cv["cv_std_fold_F1"]),
        "selection_ODS": float(opt["ODS"]),
        "selection_OIS": float(opt["OIS"]),
        "selection_AP": float(opt["AP"]),
        "selection_R50": float(opt["R50"]),
        "selection_threshold": float(opt["threshold"]),
        "mean_image_runtime_s": float(np.mean(runtimes)),
        "selection_runtime_s": float(total),
        "config_json": json.dumps(asdict(cfg), sort_keys=True, default=float),
    }
    return row, summaries


def config_by_name(configs, name):
    for c in configs:
        if c.name == name:
            return c
    raise KeyError(name)


def baseline_selection(select_items, n_thresholds):
    scores = [np.asarray(d["scharr"], np.float32) for d in select_items]
    cv = cv_threshold_score(scores, select_items, n_thresholds=n_thresholds, n_folds=3)
    opt = selection_metric(scores, select_items, n_thresholds)
    return scores, cv, opt


def evaluate_heldout(cfg, test_items, threshold, baseline_scores, bootstrap):
    scores, runtimes, summaries = run_scores(cfg, test_items)
    met, counts, per = fixed_eval(scores, test_items, float(threshold))
    bmet, bcounts, bper = fixed_eval(baseline_scores, test_items, None)
    # If baseline threshold is supplied in caller, this placeholder is replaced.
    return scores, met, counts, per, runtimes, summaries


def save_contact_sheet(items, cfg, threshold, outpath: Path, n=6):
    n = min(int(n), len(items))
    fig, axes = plt.subplots(n, 7, figsize=(21, 3.2 * n))
    if n == 1:
        axes = np.asarray([axes])
    for row, d in zip(axes, items[:n]):
        r = run_ch_mfi(d["pre_img"], cfg, precomputed=d["features"], context=d["ch_context"])
        pred = np.asarray(r.score) >= float(threshold)
        err = tolerance_error_map(pred, d["gt"], max(1, int(round(0.0075 * np.hypot(*d["gt"].shape)))))
        views = [
            (d["img"], d["id"], None),
            (d["gt"], "GT", "gray"),
            (r.mfi, "MFI attention", "inferno"),
            (r.uncertainty, "Uncertainty", "magma"),
            (r.localizer, "Dynamic localizer", "gray"),
            (pred, "Final edge", "gray"),
            (err, "TP / FP / FN", None),
        ]
        for ax, (im, title, cmap) in zip(row, views):
            ax.imshow(im, cmap=cmap)
            ax.set_title(title)
            ax.axis("off")
        del r
    fig.suptitle(cfg.name)
    fig.tight_layout()
    fig.savefig(outpath, dpi=150, bbox_inches="tight")
    plt.close(fig)


def profile_parallel(configs, select_items, thresholds, worker_values, outpath):
    subset = configs[: min(8, len(configs))]
    rows = []
    for workers in worker_values:
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=int(workers)) as ex:
            futs = [ex.submit(evaluate_selection, c, select_items, thresholds) for c in subset]
            for f in as_completed(futs):
                f.result()
        elapsed = time.perf_counter() - t0
        rows.append({"workers": workers, "elapsed_s": elapsed, "configs": len(subset)})
        print(f"PROFILE workers={workers}: {elapsed:.2f}s", flush=True)
    base = rows[0]["elapsed_s"] if rows else 1.0
    for r in rows:
        r["speedup_vs_1"] = base / max(r["elapsed_s"], 1e-9)
    pd.DataFrame(rows).to_csv(outpath, index=False)


def main():
    ap = argparse.ArgumentParser(description="Local CPU benchmark for Contextual-Hierarchical MFI-Edge")
    ap.add_argument("--uded-root", default=str(DEFAULT_UDED))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--preset", choices=("smoke", "standard", "wide"), default="standard")
    ap.add_argument("--max-side", type=int, default=256)
    ap.add_argument("--thresholds", type=int, default=31)
    ap.add_argument("--workers", type=int, default=0, help="0=auto; threads share precomputed features")
    ap.add_argument("--top-heldout", type=int, default=12)
    ap.add_argument("--bootstrap", type=int, default=5000)
    ap.add_argument("--preview", type=int, default=6)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--profile-workers", action="store_true")
    args = ap.parse_args()

    workers = int(args.workers) if args.workers > 0 else min(8, max(1, (os.cpu_count() or 4) - 2))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    uded = ensure_uded(Path(args.uded_root))

    raw = load_uded(uded, limit=args.limit)
    raw = resize_items(raw, int(args.max_side))
    items, feature_names = prepare(raw)
    items = enrich_context(items)
    select_items = items[0::2]
    test_items = items[1::2]
    n_features = len(feature_names)
    configs = build_grid(args.preset, n_features)

    print(f"PRESET={args.preset} configs={len(configs)} workers={workers} features={n_features}", flush=True)
    atomic_json({
        "preset": args.preset,
        "configs": len(configs),
        "workers": workers,
        "cpu_count": os.cpu_count(),
        "max_side": args.max_side,
        "thresholds": args.thresholds,
        "feature_names": feature_names,
        "selection_images": [d["id"] for d in select_items],
        "heldout_images": [d["id"] for d in test_items],
    }, out / "run_manifest.json")

    baseline_sel_scores, baseline_cv, baseline_opt = baseline_selection(select_items, args.thresholds)
    baseline_test_scores = [np.asarray(d["scharr"], np.float32) for d in test_items]
    baseline_test_met, baseline_test_counts, baseline_test_per = fixed_eval(
        baseline_test_scores, test_items, float(baseline_opt["threshold"])
    )
    atomic_json({
        "selection_cv": baseline_cv,
        "selection": {k: v for k, v in baseline_opt.items() if k != "curve"},
        "heldout_fixed": baseline_test_met,
    }, out / "baseline_scharr.json")

    if args.profile_workers:
        profile_parallel(configs, select_items, args.thresholds, (1, 2, 4, workers), out / "parallel_scaling.csv")

    rows = []
    per_rows = []
    checkpoint = out / "selection_ranking.csv"
    done = set()
    if checkpoint.exists() and checkpoint.stat().st_size:
        old = pd.read_csv(checkpoint)
        rows = old.to_dict("records")
        done = set(old.name.astype(str))
        print(f"RESUME: {len(done)} configurations already complete", flush=True)

    pending = [c for c in configs if c.name not in done]
    t_sweep = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(evaluate_selection, c, select_items, args.thresholds): c for c in pending}
        for j, fut in enumerate(as_completed(futures), start=1):
            cfg = futures[fut]
            try:
                row, summaries = fut.result()
                rows.append(row)
                for r in summaries:
                    per_rows.append({"name": cfg.name, **r})
                rank = pd.DataFrame(rows).sort_values(["cv_F1", "selection_ODS", "selection_AP"], ascending=False)
                atomic_csv(rank, checkpoint)
                if per_rows:
                    atomic_csv(pd.DataFrame(per_rows), out / "selection_per_image.csv")
                print(f"DONE {j}/{len(pending)} {cfg.name} cvF1={row['cv_F1']:.5f} ODS={row['selection_ODS']:.5f}", flush=True)
            except Exception as exc:
                print(f"FAILED {cfg.name}: {type(exc).__name__}: {exc}", flush=True)
                rows.append({"name": cfg.name, "failed": True, "error": f"{type(exc).__name__}: {exc}"})
                atomic_csv(pd.DataFrame(rows), checkpoint)

    sweep_s = time.perf_counter() - t_sweep
    ranking = pd.DataFrame(rows)
    ranking = ranking[ranking.get("failed", False) != True] if "failed" in ranking.columns else ranking
    ranking = ranking.sort_values(["cv_F1", "selection_ODS", "selection_AP"], ascending=False).reset_index(drop=True)
    atomic_csv(ranking, checkpoint)

    held_rows = []
    top = ranking.head(int(args.top_heldout))
    for rank_idx, row in top.iterrows():
        cfg = config_by_name(configs, str(row["name"]))
        print(f"HELDOUT [{rank_idx+1}/{len(top)}] {cfg.name}", flush=True)
        scores, runtimes, summaries = run_scores(cfg, test_items)
        met, counts, per = fixed_eval(scores, test_items, float(row["selection_threshold"]))
        boot = bootstrap_delta(counts, baseline_test_counts, n_boot=int(args.bootstrap), seed=1000 + rank_idx)
        held_rows.append({
            "selection_rank": rank_idx + 1,
            "name": cfg.name,
            "cv_F1": float(row["cv_F1"]),
            "selection_ODS": float(row["selection_ODS"]),
            "heldout_precision": float(met["precision"]),
            "heldout_recall": float(met["recall"]),
            "heldout_F1": float(met["F1"]),
            "delta_F1_vs_scharr": float(met["F1"] - baseline_test_met["F1"]),
            "bootstrap_ci_low": float(boot["ci_low"]),
            "bootstrap_ci_high": float(boot["ci_high"]),
            "bootstrap_p_positive": float(boot["p_positive"]),
            "mean_runtime_s": float(np.mean(runtimes)),
            "selection_threshold": float(row["selection_threshold"]),
        })
        if rank_idx == 0:
            save_contact_sheet(test_items, cfg, float(row["selection_threshold"]), out / "best_contact_sheet.png", n=args.preview)
        del scores
        gc.collect()

    held = pd.DataFrame(held_rows)
    atomic_csv(held, out / "heldout_top.csv")
    summary = {
        "preset": args.preset,
        "n_configs": int(len(configs)),
        "workers": workers,
        "sweep_s": sweep_s,
        "baseline_heldout_F1": float(baseline_test_met["F1"]),
        "selection_winner": ranking.iloc[0].to_dict() if len(ranking) else None,
        "heldout_of_selection_winner": held.iloc[0].to_dict() if len(held) else None,
        "note": "Held-out rows are only for candidates selected by inner-CV/selection ranking; do not re-rank the full search using held-out data.",
    }
    atomic_json(summary, out / "summary.json")
    print("LOCAL_CH_MFI_DONE", json.dumps(summary, default=float), flush=True)


if __name__ == "__main__":
    main()
