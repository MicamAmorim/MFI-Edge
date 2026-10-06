from __future__ import annotations

"""Stage 12d — repeated leakage-free CV for formal bipolar signature evidence.

This stage deliberately stops using the repeatedly inspected UDED held-out split.
All architecture ranking is performed only on the 15 UDED selection images with
repeated outer CV.  Evidence banks and thresholds are rebuilt inside every
training fold.

The main new family is a separable bi-capacity

    v(A,B) = mu_plus(A) - lambda*mu_minus(B)

implemented as independent distorted-capacity Choquet integrals over positive
boundary memberships and texture/anti-boundary memberships.  A Stage-12b ratio
combiner is kept only as an empirical control.

Outputs include frozen selection-only candidate specifications that can be
carried unchanged to an external BSDS/BIPED validation stage.
"""

from pathlib import Path
import argparse
import json
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

from benchmark_uded import DEFAULT_UDED, load_uded
from benchmark_uded_quick import resize_items
from benchmark_uded_stage7 import fixed_eval, selection_metric
from benchmark_uded_stage8_contextual import aggregate_counts
from prepare_uded_runtime import prepare_uded
from run_stage12b_fuzzy_signature import prepare, membership_stack, save_preview
from run_stage12c_leakfree_cv import ensure_uded, learn_banks
from src.bipolar_fuzzy import (
    distorted_choquet,
    normalized_separable_bicapacity,
    ratio_control,
    context_gate,
)

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "local_dev" / "stage12d_bipolar_cv"


def candidate_grid():
    rows = []

    # Positive controls: enough to preserve the strongest Stage-12c region.
    for gp in (.55, .75, 1.0):
        for a in (1.0, 2.0):
            for floor in (.10, .25):
                rows.append({
                    "name": f"positive__gp{gp:g}__a{a:g}__floor{floor:g}",
                    "family": "positive_control",
                    "gamma_plus": gp,
                    "gamma_minus": None,
                    "lambda": 0.0,
                    "strength": a,
                    "floor": floor,
                })

    # Formal separable bi-capacity family with independent interaction shapes.
    for gp in (.55, .75, 1.0):
        for gm in (.55, 1.0, 1.75):
            for lam in (.35, .70, 1.0):
                for a in (1.0, 2.0):
                    for floor in (.10, .25):
                        rows.append({
                            "name": (
                                f"bicap__gp{gp:g}__gm{gm:g}__l{lam:g}"
                                f"__a{a:g}__floor{floor:g}"
                            ),
                            "family": "separable_bicapacity",
                            "gamma_plus": gp,
                            "gamma_minus": gm,
                            "lambda": lam,
                            "strength": a,
                            "floor": floor,
                        })

    # Empirical ratio controls from the promising Stage-12b/12c dual line.
    for gp in (.55, 1.0):
        for gm in (.55, 1.0):
            for lam in (.70, 1.0):
                for a in (1.0, 2.0):
                    rows.append({
                        "name": (
                            f"ratioctl__gp{gp:g}__gm{gm:g}__l{lam:g}"
                            f"__a{a:g}__floor0.1"
                        ),
                        "family": "ratio_control",
                        "gamma_plus": gp,
                        "gamma_minus": gm,
                        "lambda": lam,
                        "strength": a,
                        "floor": .10,
                    })
    return rows


def _bank_memberships(items, base_names, positive, negative):
    pm, nm, pw, nw = [], [], None, None
    for d in items:
        a, aw = membership_stack(d, base_names, positive, "edge")
        b, bw = membership_stack(d, base_names, negative, "texture")
        pm.append(a); nm.append(b); pw = aw; nw = bw
    return pm, pw, nm, nw


def _choquet_maps(memberships, weights, gammas):
    return {
        float(g): [distorted_choquet(x, weights, float(g)) for x in memberships]
        for g in gammas
    }


def _context_maps(pos_maps, neg_maps, cfg):
    gp = float(cfg["gamma_plus"])
    family = str(cfg["family"])
    if family == "positive_control":
        return pos_maps[gp]
    gm = float(cfg["gamma_minus"])
    lam = float(cfg["lambda"])
    if family == "separable_bicapacity":
        return [
            normalized_separable_bicapacity(p, n, lam)
            for p, n in zip(pos_maps[gp], neg_maps[gm])
        ]
    if family == "ratio_control":
        return [ratio_control(p, n, lam) for p, n in zip(pos_maps[gp], neg_maps[gm])]
    raise ValueError(f"unknown family: {family}")


def _scores(items, context, cfg):
    return [
        context_gate(d["scharr"], c, float(cfg["strength"]), float(cfg["floor"]))
        for d, c in zip(items, context)
    ]


def _make_repeated_folds(n, folds, repeats, seed):
    out = []
    for r in range(int(repeats)):
        rng = np.random.default_rng(int(seed) + 1009 * r)
        perm = rng.permutation(n)
        lab = np.empty(n, dtype=int)
        lab[perm] = np.arange(n) % int(folds)
        for k in range(int(folds)):
            tr = np.flatnonzero(lab != k)
            va = np.flatnonzero(lab == k)
            out.append((r, k, tr, va))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uded-root", default=str(DEFAULT_UDED))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--max-side", type=int, default=256)
    ap.add_argument("--thresholds", type=int, default=41)
    ap.add_argument("--folds", type=int, default=3)
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--max-positive", type=int, default=10)
    ap.add_argument("--max-negative", type=int, default=8)
    ap.add_argument("--max-abs-corr", type=float, default=.88)
    ap.add_argument("--seed", type=int, default=20261006)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    raw = resize_items(load_uded(ensure_uded(Path(args.uded_root))), args.max_side)
    items, base_names = prepare(raw)
    selection = items[0::2]
    # IMPORTANT: items[1::2] is intentionally unused in Stage 12d.

    configs = candidate_grid()
    by_name = {x["name"]: x for x in configs}
    gp_set = sorted({float(x["gamma_plus"]) for x in configs})
    gm_set = sorted({float(x["gamma_minus"]) for x in configs if x["gamma_minus"] is not None})

    counts_by_cfg = defaultdict(list)
    fold_f1 = defaultdict(list)
    fold_threshold = defaultdict(list)
    baseline_counts = []
    baseline_f1 = []
    fold_rows = []
    pos_occ, neg_occ = Counter(), Counter()

    split_plan = _make_repeated_folds(
        len(selection), args.folds, args.repeats, args.seed
    )

    for split_index, (repeat, fold, tr_idx, va_idx) in enumerate(split_plan, start=1):
        train = [selection[i] for i in tr_idx]
        valid = [selection[i] for i in va_idx]
        print(
            f"STAGE12D_SPLIT {split_index:02d}/{len(split_plan)} "
            f"repeat={repeat+1} fold={fold+1} train={len(train)} valid={len(valid)}",
            flush=True,
        )

        positive, negative = learn_banks(
            train, base_names,
            int(args.seed) + 10000 * repeat + fold,
            args.max_positive, args.max_negative, args.max_abs_corr,
        )
        pos_occ.update(x["feature"] for x in positive)
        neg_occ.update(x["feature"] for x in negative)

        tr_pm, tr_pw, tr_nm, tr_nw = _bank_memberships(train, base_names, positive, negative)
        va_pm, va_pw, va_nm, va_nw = _bank_memberships(valid, base_names, positive, negative)
        tr_pos = _choquet_maps(tr_pm, tr_pw, gp_set)
        va_pos = _choquet_maps(va_pm, va_pw, gp_set)
        tr_neg = _choquet_maps(tr_nm, tr_nw, gm_set)
        va_neg = _choquet_maps(va_nm, va_nw, gm_set)

        bfit = selection_metric([d["scharr"] for d in train], train, args.thresholds)
        bmet, bcounts, _ = fixed_eval(
            [d["scharr"] for d in valid], valid, float(bfit["threshold"])
        )
        baseline_counts.extend(bcounts)
        baseline_f1.append(float(bmet["F1"]))

        for cfg in configs:
            tr_ctx = _context_maps(tr_pos, tr_neg, cfg)
            va_ctx = _context_maps(va_pos, va_neg, cfg)
            tr_scores = _scores(train, tr_ctx, cfg)
            va_scores = _scores(valid, va_ctx, cfg)
            fit = selection_metric(tr_scores, train, args.thresholds)
            met, counts, _ = fixed_eval(va_scores, valid, float(fit["threshold"]))
            counts_by_cfg[cfg["name"]].extend(counts)
            fold_f1[cfg["name"]].append(float(met["F1"]))
            fold_threshold[cfg["name"]].append(float(fit["threshold"]))
            fold_rows.append({
                "repeat": repeat + 1,
                "fold": fold + 1,
                "name": cfg["name"],
                "family": cfg["family"],
                "F1": float(met["F1"]),
                "precision": float(met["precision"]),
                "recall": float(met["recall"]),
                "train_threshold": float(fit["threshold"]),
                "positive_bank_size": len(positive),
                "negative_bank_size": len(negative),
            })

    base = aggregate_counts(baseline_counts)
    rows = []
    for cfg in configs:
        name = cfg["name"]
        met = aggregate_counts(counts_by_cfg[name])
        fs = np.asarray(fold_f1[name], dtype=float)
        ts = np.asarray(fold_threshold[name], dtype=float)
        rows.append({
            **cfg,
            "cv_precision": float(met["precision"]),
            "cv_recall": float(met["recall"]),
            "cv_F1": float(met["F1"]),
            "mean_fold_F1": float(np.mean(fs)),
            "std_fold_F1": float(np.std(fs)),
            "min_fold_F1": float(np.min(fs)),
            "threshold_mean": float(np.mean(ts)),
            "threshold_std": float(np.std(ts)),
            "delta_cv_F1_vs_scharr": float(met["F1"] - base["F1"]),
        })

    ranking = pd.DataFrame(rows).sort_values(
        ["cv_F1", "mean_fold_F1", "std_fold_F1"],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    ranking.to_csv(out / "repeated_cv_ranking.csv", index=False)
    pd.DataFrame(fold_rows).to_csv(out / "fold_results.csv", index=False)

    stability_rows = []
    total_splits = len(split_plan)
    for bank, counter in (("positive", pos_occ), ("texture_negative", neg_occ)):
        for feature, count in counter.most_common():
            stability_rows.append({
                "bank": bank,
                "feature": feature,
                "split_occurrences": int(count),
                "fraction": float(count / total_splits),
            })
    pd.DataFrame(stability_rows).to_csv(out / "bank_stability.csv", index=False)

    fam = []
    for family, g in ranking.groupby("family"):
        fam.append({
            "family": family,
            "best_cv_F1": float(g["cv_F1"].max()),
            "top5_mean_cv_F1": float(g.head(5)["cv_F1"].mean()),
            "top10_mean_cv_F1": float(g.head(10)["cv_F1"].mean()),
            "n_top20_global": int((ranking.head(20)["family"] == family).sum()),
        })
    pd.DataFrame(fam).sort_values("best_cv_F1", ascending=False).to_csv(
        out / "family_summary.csv", index=False
    )

    # Freeze three predeclared selection-only representatives for external validation.
    representatives = {
        "overall": ranking.iloc[0].to_dict(),
        "bicapacity": ranking[ranking.family == "separable_bicapacity"].iloc[0].to_dict(),
        "ratio_control": ranking[ranking.family == "ratio_control"].iloc[0].to_dict(),
        "positive_control": ranking[ranking.family == "positive_control"].iloc[0].to_dict(),
    }

    positive, negative = learn_banks(
        selection, base_names, args.seed + 999999,
        args.max_positive, args.max_negative, args.max_abs_corr,
    )
    full_pm, full_pw, full_nm, full_nw = _bank_memberships(
        selection, base_names, positive, negative
    )
    full_pos = _choquet_maps(full_pm, full_pw, gp_set)
    full_neg = _choquet_maps(full_nm, full_nw, gm_set)

    frozen = {
        "stage": "12d-repeated-leakage-free-bipolar-cv",
        "development_dataset": "UDED selection only",
        "heldout_used": False,
        "repeats": int(args.repeats),
        "folds": int(args.folds),
        "feature_mode": "oriented_ms + relational signature",
        "positive_bank": positive,
        "texture_negative_bank": negative,
        "candidates": {},
    }

    for key, row in representatives.items():
        cfg = by_name[str(row["name"])]
        ctx = _context_maps(full_pos, full_neg, cfg)
        scores = _scores(selection, ctx, cfg)
        fit = selection_metric(scores, selection, args.thresholds)
        frozen["candidates"][key] = {
            "config": cfg,
            "repeated_cv_F1": float(row["cv_F1"]),
            "repeated_cv_delta_vs_scharr": float(row["delta_cv_F1_vs_scharr"]),
            "threshold_fitted_on_all_selection": float(fit["threshold"]),
        }

    (out / "frozen_candidates.json").write_text(
        json.dumps(frozen, indent=2, default=float), encoding="utf-8"
    )

    # Selection-only preview of the overall winner.  This is illustrative only.
    win_cfg = by_name[str(representatives["overall"]["name"])]
    win_ctx = _context_maps(full_pos, full_neg, win_cfg)
    win_scores = _scores(selection, win_ctx, win_cfg)
    win_fit = selection_metric(win_scores, selection, args.thresholds)
    gp = float(win_cfg["gamma_plus"])
    gm = float(win_cfg["gamma_minus"]) if win_cfg["gamma_minus"] is not None else gm_set[0]
    save_preview(
        selection,
        full_pos[gp],
        full_neg[gm],
        win_ctx,
        win_scores,
        float(win_fit["threshold"]),
        out / "selection_winner_preview.png",
        str(win_cfg["name"]),
    )

    summary = {
        "stage": "12d-repeated-leakage-free-bipolar-cv",
        "selection_images": len(selection),
        "heldout_used": False,
        "splits": len(split_plan),
        "repeats": int(args.repeats),
        "folds": int(args.folds),
        "baseline": {
            **{k: float(v) for k, v in base.items()},
            "mean_fold_F1": float(np.mean(baseline_f1)),
            "std_fold_F1": float(np.std(baseline_f1)),
        },
        "winner": representatives["overall"],
        "best_bicapacity": representatives["bicapacity"],
        "best_ratio_control": representatives["ratio_control"],
        "best_positive_control": representatives["positive_control"],
        "next_rule": (
            "Do not inspect UDED held-out again. Carry the frozen representatives "
            "to an external BSDS/BIPED validation stage."
        ),
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=float), encoding="utf-8"
    )

    print("STAGE12D_BIPOLAR_CV_DONE")
    print(json.dumps(summary, indent=2, default=float))


if __name__ == "__main__":
    main()
