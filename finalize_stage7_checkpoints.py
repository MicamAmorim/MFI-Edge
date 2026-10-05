from __future__ import annotations

from pathlib import Path
import argparse
import json
import math
import os
import time

import pandas as pd


def atomic_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, default=_json_default), encoding="utf-8")
    os.replace(tmp, path)


def atomic_csv(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)


def _json_default(x):
    try:
        if pd.isna(x):
            return None
    except Exception:
        pass
    try:
        return float(x)
    except Exception:
        return str(x)


def row_key(row):
    return (str(row["measure"]), str(row["strategy"]), str(row["params"]))


def find_match(df: pd.DataFrame, row):
    if df.empty:
        return pd.DataFrame()
    m = (
        (df["measure"].astype(str) == str(row["measure"]))
        & (df["strategy"].astype(str) == str(row["strategy"]))
        & (df["params"].astype(str) == str(row["params"]))
    )
    return df[m]


def safe_float(v):
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)

    required = [
        out / "selection_all.csv",
        out / "heldout_fixed_all.csv",
        out / "paired_bootstrap_top10.csv",
        out / "baseline.json",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing Stage-7 checkpoints: {missing}")

    sel = pd.read_csv(out / "selection_all.csv")
    fixed = pd.read_csv(out / "heldout_fixed_all.csv")
    boot = pd.read_csv(out / "paired_bootstrap_top10.csv")
    baseline = json.loads((out / "baseline.json").read_text(encoding="utf-8"))

    sort_cols = [c for c in ["ODS", "AP", "OIS"] if c in sel.columns]
    sel = sel.sort_values(sort_cols, ascending=[False] * len(sort_cols)).reset_index(drop=True)
    top10 = sel.head(10).copy()

    boot_keys = set(row_key(r) for _, r in boot.iterrows())
    top10_keys = [row_key(r) for _, r in top10.iterrows()]
    missing_boot_keys = [k for k in top10_keys if k not in boot_keys]
    extra_boot_keys = [k for k in boot_keys if k not in set(top10_keys)]

    boot_complete_rows = 0
    if len(boot):
        for _, r in boot.iterrows():
            vals_ok = all(
                pd.notna(r.get(c))
                for c in ["delta_F1_ci95_low", "delta_F1_ci95_high", "p_delta_gt_0", "n_boot"]
            )
            if vals_ok and float(r.get("n_boot", 0)) >= 5000:
                boot_complete_rows += 1

    ranking_rows = []
    for rank, (_, r) in enumerate(top10.iterrows(), 1):
        fr = find_match(fixed, r)
        br = find_match(boot, r)
        row = {
            "selection_rank": rank,
            "measure": str(r["measure"]),
            "strategy": str(r["strategy"]),
            "params": str(r["params"]),
            "selection_ODS": safe_float(r.get("ODS")),
            "selection_AP": safe_float(r.get("AP")),
            "selection_OIS": safe_float(r.get("OIS")),
            "selection_threshold": safe_float(r.get("threshold")),
        }
        if len(fr):
            f = fr.iloc[0]
            row.update({
                "heldout_precision": safe_float(f.get("precision")),
                "heldout_recall": safe_float(f.get("recall")),
                "heldout_F1": safe_float(f.get("F1")),
                "heldout_mean_image_F1": safe_float(f.get("mean_image_F1")),
            })
        if len(br):
            b = br.iloc[0]
            row.update({
                "observed_delta_F1_vs_scharr": safe_float(b.get("observed_delta_F1")),
                "delta_F1_boot_mean": safe_float(b.get("delta_F1_boot_mean")),
                "delta_F1_ci95_low": safe_float(b.get("delta_F1_ci95_low")),
                "delta_F1_ci95_high": safe_float(b.get("delta_F1_ci95_high")),
                "p_delta_gt_0": safe_float(b.get("p_delta_gt_0")),
                "n_boot": safe_float(b.get("n_boot")),
            })
        ranking_rows.append(row)

    ranking = pd.DataFrame(ranking_rows)
    atomic_csv(ranking, out / "final_selection_top10.csv")

    best = top10.iloc[0]
    best_fixed_df = find_match(fixed, best)
    best_boot_df = find_match(boot, best)
    best_fixed = best_fixed_df.iloc[0].to_dict() if len(best_fixed_df) else {}
    best_boot = best_boot_df.iloc[0].to_dict() if len(best_boot_df) else {}

    fixed_sorted = fixed.sort_values(["F1", "precision", "recall"], ascending=False).reset_index(drop=True)
    exploratory_best = fixed_sorted.iloc[0].to_dict() if len(fixed_sorted) else {}

    runtime_summary = {}
    rp = out / "runtime_by_measure.csv"
    if rp.exists():
        rt = pd.read_csv(rp)
        runtime_summary["n_measures_profiled"] = int(len(rt))
        for c in ["conf_runtime_s", "all_fusions_runtime_s", "total_measure_runtime_s", "mean_conf_runtime_per_image_s"]:
            if c in rt.columns and len(rt):
                vals = pd.to_numeric(rt[c], errors="coerce").dropna()
                if len(vals):
                    runtime_summary[c] = {
                        "sum": float(vals.sum()),
                        "mean": float(vals.mean()),
                        "median": float(vals.median()),
                        "p95": float(vals.quantile(0.95)),
                        "max": float(vals.max()),
                    }

    parallel = None
    pp = out / "parallel_scaling.csv"
    if pp.exists():
        try:
            parallel = pd.read_csv(pp).to_dict("records")
        except Exception:
            parallel = None

    alignment_ok = (len(missing_boot_keys) == 0 and len(top10_keys) == 10)
    full_bootstrap_ok = alignment_ok and boot_complete_rows >= 10
    status = "complete" if full_bootstrap_ok else "complete_sweep_bootstrap_alignment_issue"

    baseline_fixed = baseline.get("heldout_fixed", {})
    observed_best_delta = None
    if best_fixed and baseline_fixed:
        try:
            observed_best_delta = float(best_fixed["F1"]) - float(baseline_fixed["F1"])
        except Exception:
            pass

    summary = {
        "status": status,
        "finalized_from_checkpoints": True,
        "finalized_unix": time.time(),
        "n_configs": int(len(sel)),
        "n_measures": int(sel["measure"].astype(str).nunique()) if "measure" in sel.columns else None,
        "bootstrap_rows": int(len(boot)),
        "bootstrap_rows_complete_5000": int(boot_complete_rows),
        "bootstrap_matches_selection_top10": bool(alignment_ok),
        "missing_bootstrap_top10_keys": [list(x) for x in missing_boot_keys],
        "extra_bootstrap_keys": [list(x) for x in extra_boot_keys],
        "baseline": baseline,
        "selection_winner": {
            "measure": str(best["measure"]),
            "strategy": str(best["strategy"]),
            "params": str(best["params"]),
            "selection_ODS": safe_float(best.get("ODS")),
            "selection_AP": safe_float(best.get("AP")),
            "selection_OIS": safe_float(best.get("OIS")),
            "selection_threshold": safe_float(best.get("threshold")),
            "heldout": {k: safe_float(best_fixed.get(k)) for k in ["precision", "recall", "F1", "mean_image_F1"]},
            "observed_delta_F1_vs_scharr": observed_best_delta,
            "bootstrap": {k: _json_default(v) for k, v in best_boot.items()},
        },
        "exploratory_best_on_heldout_do_not_use_for_selection": {
            "measure": str(exploratory_best.get("measure", "")),
            "strategy": str(exploratory_best.get("strategy", "")),
            "params": str(exploratory_best.get("params", "")),
            "F1": safe_float(exploratory_best.get("F1")),
            "precision": safe_float(exploratory_best.get("precision")),
            "recall": safe_float(exploratory_best.get("recall")),
        },
        "runtime_summary": runtime_summary,
        "parallel_scaling": parallel,
        "artifacts": {
            "best_contact_sheet": (out / "best_contact_sheet.png").exists(),
            "selection_pr_curve": (out / "selection_pr_curve.png").exists(),
            "per_image_best_vs_baseline": (out / "per_image_best_vs_baseline.csv").exists(),
        },
    }
    atomic_json(summary, out / "summary_final.json")

    report = f"""# UDED Stage 7 — final checkpoint summary

Stage 7 was finalized from the persisted checkpoints after the full model sweep and the
5,000-resample paired bootstrap. No synthetic/real-image sweep was repeated in this finalization step.

## Coverage

- configurations evaluated: **{len(sel)}**
- fuzzy measures represented: **{summary['n_measures']}**
- paired-bootstrap rows: **{len(boot)}**
- bootstrap rows with >=5000 resamples and complete CI/p statistic: **{boot_complete_rows}**
- bootstrap keys aligned with the actual top-10 selection ranking: **{alignment_ok}**

## Baseline

- Scharr+NMS held-out F1: **{safe_float(baseline_fixed.get('F1'))}**

## Selection winner (chosen without looking at held-out)

- measure: **{best['measure']}**
- strategy: **{best['strategy']}**
- params: `{best['params']}`
- selection ODS: **{safe_float(best.get('ODS'))}**
- selection AP: **{safe_float(best.get('AP'))}**
- selection OIS: **{safe_float(best.get('OIS'))}**
- held-out F1: **{safe_float(best_fixed.get('F1'))}**
- observed delta F1 vs Scharr: **{observed_best_delta}**
- bootstrap CI95: **[{safe_float(best_boot.get('delta_F1_ci95_low'))}, {safe_float(best_boot.get('delta_F1_ci95_high'))}]**
- P(delta F1 > 0): **{safe_float(best_boot.get('p_delta_gt_0'))}**

## Important protocol note

The `exploratory_best_on_heldout_do_not_use_for_selection` entry in `summary_final.json` is diagnostic only.
It must not be reported as the selected winner because that would use the held-out split for model selection.

## Runtime

See `runtime_by_measure.csv` and the aggregated runtime statistics in `summary_final.json`.
If `parallel_scaling.csv` is absent, the 1/2/4-worker scaling microbenchmark still needs to be run separately;
this does not affect the scientific sweep or bootstrap results.

## Visual outputs

- `best_contact_sheet.png`
- `selection_pr_curve.png`
- `per_image_best_vs_baseline.csv`
- `final_selection_top10.csv`

The contact sheet uses held-out images in dataset order rather than cherry-picked examples.
Evaluation is still the project's tolerant-dilation proxy, not the official Berkeley boundary matcher.
"""
    (out / "README_FINAL.md").write_text(report, encoding="utf-8")

    progress_path = out / "progress.json"
    progress = {}
    if progress_path.exists():
        try:
            progress = json.loads(progress_path.read_text(encoding="utf-8"))
        except Exception:
            progress = {}
    progress.update({
        "status": status,
        "postprocess_complete": True,
        "bootstrap_matches_selection_top10": bool(alignment_ok),
        "bootstrap_rows_complete_5000": int(boot_complete_rows),
        "updated_unix": time.time(),
    })
    atomic_json(progress, progress_path)

    print("UDED_STAGE7_CHECKPOINT_FINALIZATION_DONE", flush=True)
    print(json.dumps(summary, indent=2, default=_json_default), flush=True)


if __name__ == "__main__":
    main()
