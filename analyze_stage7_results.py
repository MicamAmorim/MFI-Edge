from __future__ import annotations

from pathlib import Path
import argparse
import json
import math

import numpy as np
import pandas as pd
from PIL import Image


def strategy_family(name: str) -> str:
    s = str(name)
    for p in ("soft_", "residual_", "adaptive_exp_", "proposal_", "rank_", "geodesic_"):
        if s.startswith(p):
            return p.rstrip("_")
    return s.split("_")[0]


def group_summary(df: pd.DataFrame, key: str) -> pd.DataFrame:
    rows = []
    for name, g in df.groupby(key, dropna=False):
        rows.append({
            key: name,
            "n_configs": int(len(g)),
            "mean_selection_ODS": float(g.selection_ODS.mean()),
            "median_selection_ODS": float(g.selection_ODS.median()),
            "best_selection_ODS": float(g.selection_ODS.max()),
            "mean_selection_delta_vs_scharr": float(g.selection_delta.mean()),
            "mean_heldout_F1": float(g.heldout_F1.mean()),
            "median_heldout_F1": float(g.heldout_F1.median()),
            "best_heldout_F1_posthoc": float(g.heldout_F1.max()),
            "mean_heldout_delta_vs_scharr": float(g.heldout_delta.mean()),
            "median_heldout_delta_vs_scharr": float(g.heldout_delta.median()),
            "fraction_heldout_above_scharr": float((g.heldout_delta > 0).mean()),
            "mean_transfer_gap": float(g.transfer_gap.mean()),
            "median_transfer_gap": float(g.transfer_gap.median()),
        })
    return pd.DataFrame(rows).sort_values(
        ["best_selection_ODS", "mean_heldout_delta_vs_scharr"], ascending=False
    ).reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage7", default="/app/persist/stage7")
    ap.add_argument("--print-top", type=int, default=10)
    args = ap.parse_args()

    root = Path(args.stage7)
    sel = pd.read_csv(root / "selection_all.csv")
    held = pd.read_csv(root / "heldout_fixed_all.csv")
    baseline = json.loads((root / "baseline.json").read_text())
    boot = pd.read_csv(root / "paired_bootstrap_top10.csv") if (root / "paired_bootstrap_top10.csv").exists() else pd.DataFrame()

    keys = ["measure", "strategy", "params"]
    use_sel = sel.rename(columns={
        "ODS": "selection_ODS", "OIS": "selection_OIS", "AP": "selection_AP",
        "R50": "selection_R50", "threshold": "selection_threshold",
    })
    use_held = held.rename(columns={
        "F1": "heldout_F1", "precision": "heldout_precision", "recall": "heldout_recall",
        "mean_image_F1": "heldout_mean_image_F1",
    })
    keep_h = keys + [c for c in ["heldout_F1", "heldout_precision", "heldout_recall", "heldout_mean_image_F1", "gt_conf_mean"] if c in use_held]
    df = use_sel.merge(use_held[keep_h], on=keys, how="inner", suffixes=("_sel", "_held"))
    df["strategy_family"] = df.strategy.map(strategy_family)

    bsel = float(baseline["selection"]["ODS"])
    bhold = float(baseline["heldout_fixed"]["F1"])
    df["selection_delta"] = df.selection_ODS - bsel
    df["heldout_delta"] = df.heldout_F1 - bhold
    df["transfer_gap"] = df.heldout_delta - df.selection_delta

    rank_sel = df.sort_values(["selection_ODS", "selection_AP", "selection_OIS"], ascending=False).reset_index(drop=True)
    rank_hold = df.sort_values(["heldout_F1", "selection_ODS"], ascending=False).reset_index(drop=True)
    topn = max(1, int(args.print_top))

    by_kind = group_summary(df, "measure_kind")
    by_strategy = group_summary(df, "strategy_family")
    by_measure = group_summary(df, "measure")

    by_kind.to_csv(root / "analysis_by_measure_kind.csv", index=False)
    by_strategy.to_csv(root / "analysis_by_strategy_family.csv", index=False)
    by_measure.to_csv(root / "analysis_by_measure.csv", index=False)
    rank_sel.head(100).to_csv(root / "top100_by_selection.csv", index=False)
    rank_hold.head(100).to_csv(root / "top100_by_heldout_posthoc.csv", index=False)

    # Reduced qualitative sheet for repository browsing.
    src = root / "best_contact_sheet.png"
    small = root / "best_contact_sheet_small.jpg"
    if src.exists():
        im = Image.open(src).convert("RGB")
        if im.width > 1600:
            h = max(1, round(im.height * 1600 / im.width))
            im = im.resize((1600, h), Image.Resampling.LANCZOS)
        im.save(small, "JPEG", quality=85, optimize=True)

    win = rank_sel.iloc[0]
    post = rank_hold.iloc[0]

    best_kind = by_kind.sort_values("mean_heldout_delta_vs_scharr", ascending=False).iloc[0]
    best_strategy = by_strategy.sort_values("mean_heldout_delta_vs_scharr", ascending=False).iloc[0]
    least_overfit_kind = by_kind.sort_values("mean_transfer_gap", ascending=False).iloc[0]
    most_overfit_kind = by_kind.sort_values("mean_transfer_gap", ascending=True).iloc[0]

    boot_match = None
    if len(boot):
        a = set(tuple(x) for x in rank_sel.head(10)[keys].astype(str).to_numpy())
        b = set(tuple(x) for x in boot[keys].astype(str).to_numpy())
        boot_match = (a == b)

    summary = {
        "n_configs": int(len(df)),
        "n_measures": int(df.measure.nunique()),
        "n_measure_kinds": int(df.measure_kind.nunique()),
        "n_strategy_families": int(df.strategy_family.nunique()),
        "baseline_selection_ODS": bsel,
        "baseline_heldout_F1": bhold,
        "selection_winner": {
            "measure": str(win.measure), "measure_kind": str(win.measure_kind),
            "strategy": str(win.strategy), "params": str(win.params),
            "selection_ODS": float(win.selection_ODS), "heldout_F1": float(win.heldout_F1),
            "selection_delta": float(win.selection_delta), "heldout_delta": float(win.heldout_delta),
            "transfer_gap": float(win.transfer_gap),
        },
        "posthoc_heldout_best_not_for_model_selection": {
            "measure": str(post.measure), "measure_kind": str(post.measure_kind),
            "strategy": str(post.strategy), "params": str(post.params),
            "selection_ODS": float(post.selection_ODS), "heldout_F1": float(post.heldout_F1),
            "heldout_delta": float(post.heldout_delta),
        },
        "best_measure_kind_by_mean_heldout_delta": best_kind.to_dict(),
        "best_strategy_family_by_mean_heldout_delta": best_strategy.to_dict(),
        "least_overfit_measure_kind_by_transfer_gap": least_overfit_kind.to_dict(),
        "most_overfit_measure_kind_by_transfer_gap": most_overfit_kind.to_dict(),
        "fraction_all_configs_above_scharr_on_heldout": float((df.heldout_delta > 0).mean()),
        "median_all_heldout_delta": float(df.heldout_delta.median()),
        "mean_all_heldout_delta": float(df.heldout_delta.mean()),
        "bootstrap_top10_matches_selection_top10": boot_match,
        "small_contact_sheet_bytes": int(small.stat().st_size) if small.exists() else None,
    }
    (root / "stage7_family_analysis.json").write_text(json.dumps(summary, indent=2, default=float), encoding="utf-8")

    lines = [
        "# UDED Stage 7 — family/generalization analysis",
        "",
        f"- Configurations: **{len(df)}**",
        f"- Measures: **{df.measure.nunique()}**",
        f"- Scharr selection ODS: **{bsel:.6f}**",
        f"- Scharr held-out F1: **{bhold:.6f}**",
        "",
        "## Selection winner (valid model-selection result)",
        f"**{win.measure} + {win.strategy}** — selection ODS {win.selection_ODS:.6f}; held-out F1 {win.heldout_F1:.6f}; delta held-out {win.heldout_delta:+.6f}.",
        "",
        "## Best held-out row (post-hoc diagnostic only)",
        f"**{post.measure} + {post.strategy}** — held-out F1 {post.heldout_F1:.6f}; delta {post.heldout_delta:+.6f}. This row MUST NOT be reported as a selected winner.",
        "",
        "## Interpretation",
        f"Best measure-kind by mean held-out delta: **{best_kind['measure_kind']}** ({best_kind['mean_heldout_delta_vs_scharr']:+.6f}).",
        f"Best strategy family by mean held-out delta: **{best_strategy['strategy_family']}** ({best_strategy['mean_heldout_delta_vs_scharr']:+.6f}).",
        f"Fraction of all configurations above Scharr on held-out: **{float((df.heldout_delta > 0).mean()):.3f}**.",
        "",
        "The Stage-7 selection/held-out discrepancy is quantified by `transfer_gap = heldout_delta - selection_delta`; more negative values indicate stronger selection-to-heldout degradation.",
        "",
        "See `analysis_by_measure_kind.csv`, `analysis_by_strategy_family.csv`, `analysis_by_measure.csv`, `top100_by_selection.csv`, and `top100_by_heldout_posthoc.csv`.",
    ]
    (root / "STAGE7_ANALYSIS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Concise, log-friendly output.
    print("STAGE7_ANALYSIS_BEGIN")
    print(json.dumps(summary, separators=(",", ":"), default=float))
    print("TOP_SELECTION")
    for _, r in rank_sel.head(topn).iterrows():
        print(f"{r.measure}|{r.measure_kind}|{r.strategy}|sel={r.selection_ODS:.6f}|hold={r.heldout_F1:.6f}|dhold={r.heldout_delta:+.6f}|gap={r.transfer_gap:+.6f}")
    print("TOP_HELDOUT_POSTHOC")
    for _, r in rank_hold.head(topn).iterrows():
        print(f"{r.measure}|{r.measure_kind}|{r.strategy}|sel={r.selection_ODS:.6f}|hold={r.heldout_F1:.6f}|dhold={r.heldout_delta:+.6f}")
    print("BY_KIND")
    for _, r in by_kind.iterrows():
        print(f"{r.measure_kind}|n={int(r.n_configs)}|mean_dhold={r.mean_heldout_delta_vs_scharr:+.6f}|frac_pos={r.fraction_heldout_above_scharr:.3f}|gap={r.mean_transfer_gap:+.6f}")
    print("BY_STRATEGY")
    for _, r in by_strategy.iterrows():
        print(f"{r.strategy_family}|n={int(r.n_configs)}|mean_dhold={r.mean_heldout_delta_vs_scharr:+.6f}|frac_pos={r.fraction_heldout_above_scharr:.3f}|gap={r.mean_transfer_gap:+.6f}")
    psc = root / "parallel_scaling.csv"
    if psc.exists():
        print("PARALLEL_SCALING")
        print(psc.read_text(encoding="utf-8").strip())
    print("STAGE7_ANALYSIS_END")


if __name__ == "__main__":
    main()
