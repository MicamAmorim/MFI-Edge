from __future__ import annotations

"""Stage 12c — leakage-free CV for signature evidence-bank selection.

Why this stage exists
---------------------
Stage 12b correctly kept the held-out split out of feature-bank construction, but
its reported `cv_F1` reused an evidence bank selected once on all 15 selection
images.  Thresholds were out-of-fold, feature selection was not.  This stage
rebuilds positive/texture banks inside every CV training fold before evaluating
that fold.

The old UDED held-out split is now treated as *development confirmation*, not a
publication test, because it has been inspected repeatedly during architecture
development.  A future external BSDS/BIPED test must remain untouched.
"""

from pathlib import Path
import argparse
import json
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

from benchmark_uded import DEFAULT_UDED, load_uded
from benchmark_uded_quick import resize_items
from benchmark_uded_stage7 import bootstrap_delta, fixed_eval, selection_metric
from benchmark_uded_stage8_contextual import aggregate_counts
from prepare_uded_runtime import prepare_uded
from src.edge_signature_relational import extract_relational_samples
from run_stage12b_fuzzy_signature import (
    prepare,
    _select_bank,
    membership_stack,
    distorted_choquet,
    combine_dual,
    gate,
    save_preview,
)

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "local_dev" / "stage12c_leakfree_cv"


def ensure_uded(root: Path):
    if not (root / "test_pair.lst").exists():
        prepare_uded(root)
    return root


def candidate_grid():
    rows = []
    gammas = (.55, .75, 1.0, 1.35, 1.75)
    for gamma in gammas:
        for a in (1.0, 2.0):
            for floor in (.10, .25, .50):
                rows.append({
                    "name": f"fuzzypos__g{gamma:g}__a{a:g}__floor{floor:g}",
                    "family": "positive", "gamma": gamma, "combine": "none",
                    "lambda": 0.0, "strength": a, "floor": floor,
                })
    for gamma in (.55, 1.0, 1.75):
        for kind in ("product", "contrast", "ratio"):
            for lam in (.35, .70, 1.0):
                for a in (1.0, 2.0):
                    for floor in (.10, .25):
                        rows.append({
                            "name": f"dual__g{gamma:g}__{kind}__l{lam:g}__a{a:g}__floor{floor:g}",
                            "family": "dual", "gamma": gamma, "combine": kind,
                            "lambda": lam, "strength": a, "floor": floor,
                        })
    return rows


def learn_banks(train_items, base_names, seed, max_positive, max_negative, max_abs_corr):
    samples = extract_relational_samples(train_items, base_names, 2500, seed=seed)
    positive = _select_bank(samples, +1.0, max_positive, max_abs_corr, .56)
    negative = _select_bank(
        samples, -1.0, max_negative, max_abs_corr, .54,
        exclude=[x["feature"] for x in positive],
    )
    return positive, negative


def bank_maps(items, base_names, positive, negative, gammas):
    pm, nm, pw, nw = [], [], None, None
    for d in items:
        a, aw = membership_stack(d, base_names, positive, "edge")
        b, bw = membership_stack(d, base_names, negative, "texture")
        pm.append(a); nm.append(b); pw = aw; nw = bw
    pos = {g: [distorted_choquet(x, pw, g) for x in pm] for g in gammas}
    if len(negative) >= 2:
        neg = {g: [distorted_choquet(x, nw, g) for x in nm] for g in gammas}
    else:
        neg = {g: [np.zeros_like(x) for x in pos[g]] for g in gammas}
    return pos, neg


def config_scores(items, pos, neg, cfg):
    scharr = [np.asarray(d["scharr"], np.float32) for d in items]
    g = float(cfg["gamma"])
    if cfg["family"] == "positive":
        ctx = pos[g]
    else:
        ctx = [combine_dual(p, n, str(cfg["combine"]), float(cfg["lambda"]))
               for p, n in zip(pos[g], neg[g])]
    scores = [gate(l, c, float(cfg["strength"]), float(cfg["floor"]))
              for l, c in zip(scharr, ctx)]
    return scores, ctx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uded-root", default=str(DEFAULT_UDED))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--max-side", type=int, default=256)
    ap.add_argument("--thresholds", type=int, default=41)
    ap.add_argument("--folds", type=int, default=3)
    ap.add_argument("--max-positive", type=int, default=10)
    ap.add_argument("--max-negative", type=int, default=8)
    ap.add_argument("--max-abs-corr", type=float, default=.88)
    ap.add_argument("--bootstrap", type=int, default=5000)
    ap.add_argument("--top-heldout", type=int, default=7)
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    raw = resize_items(load_uded(ensure_uded(Path(args.uded_root))), args.max_side)
    items, base_names = prepare(raw)
    selection_items, heldout_items = items[0::2], items[1::2]
    configs = candidate_grid()
    by_name = {x["name"]: x for x in configs}
    gammas = sorted({float(x["gamma"]) for x in configs})

    folds = np.arange(len(selection_items)) % int(args.folds)
    counts_by_cfg = defaultdict(list)
    f1_by_cfg = defaultdict(list)
    thresholds_by_cfg = defaultdict(list)
    baseline_counts = []
    baseline_fold_f1 = []
    fold_rows = []
    pos_occ, neg_occ = Counter(), Counter()

    for k in range(int(args.folds)):
        tr = np.where(folds != k)[0]
        va = np.where(folds == k)[0]
        train = [selection_items[i] for i in tr]
        valid = [selection_items[i] for i in va]
        print(f"STAGE12C_FOLD {k+1}/{args.folds} train={len(train)} valid={len(valid)}", flush=True)

        positive, negative = learn_banks(
            train, base_names, 20261200 + k,
            args.max_positive, args.max_negative, args.max_abs_corr,
        )
        pos_occ.update(x["feature"] for x in positive)
        neg_occ.update(x["feature"] for x in negative)

        tr_pos, tr_neg = bank_maps(train, base_names, positive, negative, gammas)
        va_pos, va_neg = bank_maps(valid, base_names, positive, negative, gammas)

        # Baseline threshold is fitted only on outer-fold training images.
        bfit = selection_metric([d["scharr"] for d in train], train, args.thresholds)
        bmet, bcounts, _ = fixed_eval([d["scharr"] for d in valid], valid, float(bfit["threshold"]))
        baseline_counts.extend(bcounts)
        baseline_fold_f1.append(float(bmet["F1"]))

        for cfg in configs:
            tr_scores, _ = config_scores(train, tr_pos, tr_neg, cfg)
            va_scores, _ = config_scores(valid, va_pos, va_neg, cfg)
            fit = selection_metric(tr_scores, train, args.thresholds)
            met, counts, _ = fixed_eval(va_scores, valid, float(fit["threshold"]))
            counts_by_cfg[cfg["name"]].extend(counts)
            f1_by_cfg[cfg["name"]].append(float(met["F1"]))
            thresholds_by_cfg[cfg["name"]].append(float(fit["threshold"]))
            fold_rows.append({
                "fold": k + 1, "name": cfg["name"], "family": cfg["family"],
                "F1": float(met["F1"]), "precision": float(met["precision"]),
                "recall": float(met["recall"]), "train_threshold": float(fit["threshold"]),
                "positive_bank_size": len(positive), "negative_bank_size": len(negative),
            })

    base_cv = aggregate_counts(baseline_counts)
    rank_rows = []
    for cfg in configs:
        met = aggregate_counts(counts_by_cfg[cfg["name"]])
        rank_rows.append({
            **cfg,
            "cv_precision": float(met["precision"]),
            "cv_recall": float(met["recall"]),
            "cv_F1": float(met["F1"]),
            "mean_fold_F1": float(np.mean(f1_by_cfg[cfg["name"]])),
            "std_fold_F1": float(np.std(f1_by_cfg[cfg["name"]])),
            "threshold_mean": float(np.mean(thresholds_by_cfg[cfg["name"]])),
            "threshold_std": float(np.std(thresholds_by_cfg[cfg["name"]])),
            "delta_cv_F1_vs_scharr": float(met["F1"] - base_cv["F1"]),
        })
    ranking = pd.DataFrame(rank_rows).sort_values(
        ["cv_F1", "mean_fold_F1"], ascending=False
    ).reset_index(drop=True)
    ranking.to_csv(out / "leakfree_selection_ranking.csv", index=False)
    pd.DataFrame(fold_rows).to_csv(out / "fold_results.csv", index=False)

    stab = []
    for family, counter in (("positive", pos_occ), ("texture_negative", neg_occ)):
        for feature, count in counter.most_common():
            stab.append({"bank": family, "feature": feature, "fold_occurrences": count,
                         "fraction": count / float(args.folds)})
    pd.DataFrame(stab).to_csv(out / "bank_stability.csv", index=False)

    # Refit banks on all selection images.  Held-out is development confirmation only.
    positive, negative = learn_banks(
        selection_items, base_names, 20261299,
        args.max_positive, args.max_negative, args.max_abs_corr,
    )
    (out / "evidence_banks_full_selection.json").write_text(json.dumps({
        "selection_only": True,
        "positive": positive,
        "texture_negative": negative,
        "note": "Refit after leakage-free ranking; UDED held-out is development confirmation, not final test.",
    }, indent=2), encoding="utf-8")

    sel_pos, sel_neg = bank_maps(selection_items, base_names, positive, negative, gammas)
    tst_pos, tst_neg = bank_maps(heldout_items, base_names, positive, negative, gammas)
    base_fit = selection_metric([d["scharr"] for d in selection_items], selection_items, args.thresholds)
    base_met, base_counts_h, _ = fixed_eval(
        [d["scharr"] for d in heldout_items], heldout_items, float(base_fit["threshold"])
    )

    held = []
    best_dual_saved = False
    for ri, row in ranking.head(int(args.top_heldout)).iterrows():
        cfg = by_name[str(row["name"])]
        sel_scores, sel_ctx = config_scores(selection_items, sel_pos, sel_neg, cfg)
        tst_scores, tst_ctx = config_scores(heldout_items, tst_pos, tst_neg, cfg)
        fit = selection_metric(sel_scores, selection_items, args.thresholds)
        met, counts, _ = fixed_eval(tst_scores, heldout_items, float(fit["threshold"]))
        boot = bootstrap_delta(base_counts_h, counts, n_boot=args.bootstrap, seed=12600 + int(ri))
        rec = {
            "selection_rank": int(ri) + 1, "name": cfg["name"], "family": cfg["family"],
            "leakfree_cv_F1": float(row["cv_F1"]),
            "heldout_precision": float(met["precision"]), "heldout_recall": float(met["recall"]),
            "heldout_F1": float(met["F1"]), "delta_F1_vs_scharr": float(met["F1"] - base_met["F1"]),
            "bootstrap_ci_low": float(boot["delta_F1_ci95_low"]),
            "bootstrap_ci_high": float(boot["delta_F1_ci95_high"]),
            "bootstrap_p_positive": float(boot["p_delta_gt_0"]),
            "selection_threshold": float(fit["threshold"]),
        }
        held.append(rec)

        g = float(cfg["gamma"])
        posmaps = tst_pos[g]
        negmaps = tst_neg[g]
        if ri == 0:
            save_preview(heldout_items, posmaps, negmaps, tst_ctx, tst_scores,
                         float(fit["threshold"]), out / "winner_preview.png", cfg["name"])
        if cfg["family"] == "dual" and not best_dual_saved:
            save_preview(heldout_items, posmaps, negmaps, tst_ctx, tst_scores,
                         float(fit["threshold"]), out / "best_dual_preview.png", cfg["name"])
            best_dual_saved = True

    pd.DataFrame(held).to_csv(out / "heldout_top7.csv", index=False)

    summary = {
        "stage": "12c-leakage-free-evidence-bank-cv",
        "selection_images": len(selection_items),
        "heldout_images": len(heldout_items),
        "folds": int(args.folds),
        "baseline_leakfree_cv": {
            **{k: float(v) for k, v in base_cv.items()},
            "mean_fold_F1": float(np.mean(baseline_fold_f1)),
            "std_fold_F1": float(np.std(baseline_fold_f1)),
        },
        "selection_winner": ranking.iloc[0].to_dict(),
        "heldout_selection_winner": held[0] if held else None,
        "methodology_note": (
            "Positive/negative feature banks and thresholds are rebuilt using only each CV training fold. "
            "The repeatedly inspected UDED held-out split is development confirmation only; external BSDS/BIPED remains required."
        ),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=float), encoding="utf-8")
    print("STAGE12C_LEAKFREE_DONE")
    print(json.dumps(summary, indent=2, default=float))


if __name__ == "__main__":
    main()
