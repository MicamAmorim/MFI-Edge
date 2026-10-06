from __future__ import annotations

"""Stage 14b — leakage-free polarity/mechanism ablation on UDED selection only.

Human-reviewed Stage-14 development experiment.

Question
--------
Does *spatially aligned* anti-texture evidence add useful information to the
existing positive fuzzy context, or is the ratio-control behaviour explainable
by its scalar nonlinear remapping alone?

Protocol
--------
- Development data only: UDED selection half (items 0::2).
- UDED held-out is never prepared/evaluated here.
- 5 repeats x 3 folds, matching Stage 12d's repeated leakage-free design.
- Positive/negative feature banks are learned inside each training fold.
- Thresholds are fitted only on the corresponding training fold.
- Scharr+NMS localizer is unchanged.
- The ratio-control parameters are the pre-existing Stage-12d development
  specification (gp=.55, gm=1, lambda=1, strength=2, floor=.1); no external
  BSDS/BIPED result is used to choose them.

Preregistered variants (one mechanism change: treatment of negative evidence)
-----------------------------------------------------------------------------
1. positive_only
   Positive distorted-Choquet context only.
2. ratio_spatial_negative
   Full spatially aligned positive-vs-negative ratio control.
3. ratio_image_mean_negative
   Replaces the negative map by its per-image mean. This preserves the global
   negative burden but destroys spatial anti-texture localization.
4. ratio_no_negative
   Sets the negative evidence to zero, retaining the ratio nonlinearity.

Primary falsification contrast:
    ratio_spatial_negative vs ratio_image_mean_negative

Secondary contrasts:
    ratio_spatial_negative vs positive_only
    ratio_spatial_negative vs ratio_no_negative

The experiment is descriptive/developmental. Repeated folds are not independent,
so fold win counts and mean deltas are reported without pretending they are a
formal independent-sample significance test.
"""

from collections import Counter, defaultdict
from pathlib import Path
import argparse
import json

import numpy as np
import pandas as pd

from benchmark_uded import DEFAULT_UDED, load_uded
from benchmark_uded_quick import resize_items
from benchmark_uded_stage7 import fixed_eval, selection_metric
from benchmark_uded_stage8_contextual import aggregate_counts
from run_stage12b_fuzzy_signature import prepare
from run_stage12c_leakfree_cv import ensure_uded, learn_banks
from run_stage12d_bipolar_cv import (
    _bank_memberships,
    _choquet_maps,
    _make_repeated_folds,
)
from src.bipolar_fuzzy import context_gate, ratio_control

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "local_dev" / "stage14b_polarity_ablation"

GP = 0.55
GM = 1.0
LAM = 1.0
STRENGTH = 2.0
FLOOR = 0.10
PRIOR = 0.05

VARIANTS = (
    "positive_only",
    "ratio_spatial_negative",
    "ratio_image_mean_negative",
    "ratio_no_negative",
)


def _context_for_variant(pos_maps, neg_maps, variant: str):
    out = []
    for p, n in zip(pos_maps, neg_maps):
        if variant == "positive_only":
            c = p
        elif variant == "ratio_spatial_negative":
            c = ratio_control(p, n, LAM, prior=PRIOR)
        elif variant == "ratio_image_mean_negative":
            nmean = np.full_like(n, float(np.mean(n)), dtype=np.float32)
            c = ratio_control(p, nmean, LAM, prior=PRIOR)
        elif variant == "ratio_no_negative":
            c = ratio_control(p, np.zeros_like(n), LAM, prior=PRIOR)
        else:
            raise ValueError(f"unknown variant: {variant}")
        out.append(np.asarray(c, np.float32))
    return out


def _scores(items, context):
    return [
        context_gate(d["scharr"], c, STRENGTH, FLOOR)
        for d, c in zip(items, context)
    ]


def _variant_eval(train, valid, tr_pos, tr_neg, va_pos, va_neg, variant, thresholds):
    tr_ctx = _context_for_variant(tr_pos, tr_neg, variant)
    va_ctx = _context_for_variant(va_pos, va_neg, variant)
    tr_scores = _scores(train, tr_ctx)
    va_scores = _scores(valid, va_ctx)
    fit = selection_metric(tr_scores, train, thresholds)
    met, counts, _ = fixed_eval(va_scores, valid, float(fit["threshold"]))
    return fit, met, counts


def main() -> int:
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

    # Load the dataset but prepare only the selection half.  The held-out half is
    # deliberately not passed through the Stage-14 feature pipeline.
    raw_all = resize_items(load_uded(ensure_uded(Path(args.uded_root))), args.max_side)
    raw_selection = raw_all[0::2]
    selection, base_names = prepare(raw_selection)

    if len(selection) != 15:
        raise RuntimeError(
            f"Expected 15 UDED selection images, got {len(selection)}. "
            "Refusing to run because the preregistered split changed."
        )

    split_plan = _make_repeated_folds(
        len(selection), args.folds, args.repeats, args.seed
    )

    counts_by_variant = defaultdict(list)
    fold_f1 = defaultdict(list)
    fold_threshold = defaultdict(list)
    baseline_counts = []
    baseline_fold_f1 = []
    fold_rows = []
    pos_occ, neg_occ = Counter(), Counter()

    for split_index, (repeat, fold, tr_idx, va_idx) in enumerate(split_plan, start=1):
        train = [selection[i] for i in tr_idx]
        valid = [selection[i] for i in va_idx]
        print(
            f"STAGE14B_SPLIT {split_index:02d}/{len(split_plan)} "
            f"repeat={repeat+1} fold={fold+1} train={len(train)} valid={len(valid)}",
            flush=True,
        )

        positive, negative = learn_banks(
            train,
            base_names,
            int(args.seed) + 10000 * repeat + fold,
            args.max_positive,
            args.max_negative,
            args.max_abs_corr,
        )
        pos_occ.update(x["feature"] for x in positive)
        neg_occ.update(x["feature"] for x in negative)

        tr_pm, tr_pw, tr_nm, tr_nw = _bank_memberships(
            train, base_names, positive, negative
        )
        va_pm, va_pw, va_nm, va_nw = _bank_memberships(
            valid, base_names, positive, negative
        )
        tr_pos = _choquet_maps(tr_pm, tr_pw, [GP])[GP]
        va_pos = _choquet_maps(va_pm, va_pw, [GP])[GP]
        tr_neg = _choquet_maps(tr_nm, tr_nw, [GM])[GM]
        va_neg = _choquet_maps(va_nm, va_nw, [GM])[GM]

        bfit = selection_metric([d["scharr"] for d in train], train, args.thresholds)
        bmet, bcounts, _ = fixed_eval(
            [d["scharr"] for d in valid], valid, float(bfit["threshold"])
        )
        baseline_counts.extend(bcounts)
        baseline_fold_f1.append(float(bmet["F1"]))

        for variant in VARIANTS:
            fit, met, counts = _variant_eval(
                train,
                valid,
                tr_pos,
                tr_neg,
                va_pos,
                va_neg,
                variant,
                args.thresholds,
            )
            counts_by_variant[variant].extend(counts)
            fold_f1[variant].append(float(met["F1"]))
            fold_threshold[variant].append(float(fit["threshold"]))
            fold_rows.append(
                {
                    "repeat": repeat + 1,
                    "fold": fold + 1,
                    "variant": variant,
                    "F1": float(met["F1"]),
                    "precision": float(met["precision"]),
                    "recall": float(met["recall"]),
                    "train_threshold": float(fit["threshold"]),
                    "positive_bank_size": len(positive),
                    "negative_bank_size": len(negative),
                }
            )

    baseline = aggregate_counts(baseline_counts)
    pos_folds = np.asarray(fold_f1["positive_only"], dtype=float)
    spatial_folds = np.asarray(fold_f1["ratio_spatial_negative"], dtype=float)
    meanneg_folds = np.asarray(fold_f1["ratio_image_mean_negative"], dtype=float)
    noneg_folds = np.asarray(fold_f1["ratio_no_negative"], dtype=float)

    rows = []
    for variant in VARIANTS:
        met = aggregate_counts(counts_by_variant[variant])
        fs = np.asarray(fold_f1[variant], dtype=float)
        ts = np.asarray(fold_threshold[variant], dtype=float)
        rows.append(
            {
                "variant": variant,
                "cv_precision": float(met["precision"]),
                "cv_recall": float(met["recall"]),
                "cv_F1": float(met["F1"]),
                "mean_fold_F1": float(np.mean(fs)),
                "std_fold_F1": float(np.std(fs)),
                "min_fold_F1": float(np.min(fs)),
                "threshold_mean": float(np.mean(ts)),
                "threshold_std": float(np.std(ts)),
                "delta_cv_F1_vs_scharr": float(met["F1"] - baseline["F1"]),
                "mean_fold_delta_vs_positive": float(np.mean(fs - pos_folds)),
                "fold_wins_vs_positive": int(np.sum(fs > pos_folds)),
            }
        )

    ranking = pd.DataFrame(rows).sort_values(
        ["cv_F1", "mean_fold_F1"], ascending=[False, False]
    ).reset_index(drop=True)
    ranking.to_csv(out / "variant_ranking.csv", index=False)
    pd.DataFrame(fold_rows).to_csv(out / "fold_results.csv", index=False)

    stability_rows = []
    total_splits = len(split_plan)
    for bank, counter in (("positive", pos_occ), ("texture_negative", neg_occ)):
        for feature, count in counter.most_common():
            stability_rows.append(
                {
                    "bank": bank,
                    "feature": feature,
                    "split_occurrences": int(count),
                    "fraction": float(count / total_splits),
                }
            )
    pd.DataFrame(stability_rows).to_csv(out / "bank_stability.csv", index=False)

    primary_delta = spatial_folds - meanneg_folds
    secondary_positive = spatial_folds - pos_folds
    secondary_noneg = spatial_folds - noneg_folds

    by_variant = {
        str(r["variant"]): {k: (float(v) if isinstance(v, (np.floating, float)) else int(v) if isinstance(v, (np.integer,)) else v)
                            for k, v in r.items()}
        for r in rows
    }

    support = bool(
        by_variant["ratio_spatial_negative"]["cv_F1"]
        > by_variant["ratio_image_mean_negative"]["cv_F1"]
        and float(np.mean(primary_delta)) > 0.0
    )

    summary = {
        "stage": "14b-polarity-mechanism-ablation",
        "dataset_role": "UDED selection only; development",
        "heldout_used": False,
        "external_feedback_used": False,
        "n_selection_images": len(selection),
        "repeats": int(args.repeats),
        "folds": int(args.folds),
        "n_validation_events": len(split_plan),
        "fixed_mechanism_parameters": {
            "gamma_plus": GP,
            "gamma_minus": GM,
            "lambda": LAM,
            "strength": STRENGTH,
            "floor": FLOOR,
            "ratio_prior": PRIOR,
        },
        "baseline_scharr": {
            "cv_precision": float(baseline["precision"]),
            "cv_recall": float(baseline["recall"]),
            "cv_F1": float(baseline["F1"]),
            "mean_fold_F1": float(np.mean(baseline_fold_f1)),
            "std_fold_F1": float(np.std(baseline_fold_f1)),
        },
        "variants": by_variant,
        "primary_contrast": {
            "name": "ratio_spatial_negative - ratio_image_mean_negative",
            "mean_fold_delta_F1": float(np.mean(primary_delta)),
            "std_fold_delta_F1": float(np.std(primary_delta)),
            "fold_wins": int(np.sum(primary_delta > 0)),
            "fold_ties": int(np.sum(primary_delta == 0)),
            "fold_losses": int(np.sum(primary_delta < 0)),
            "supports_spatial_negative_evidence": support,
        },
        "secondary_contrasts": {
            "spatial_ratio_minus_positive_only": {
                "mean_fold_delta_F1": float(np.mean(secondary_positive)),
                "fold_wins": int(np.sum(secondary_positive > 0)),
                "fold_losses": int(np.sum(secondary_positive < 0)),
            },
            "spatial_ratio_minus_ratio_no_negative": {
                "mean_fold_delta_F1": float(np.mean(secondary_noneg)),
                "fold_wins": int(np.sum(secondary_noneg > 0)),
                "fold_losses": int(np.sum(secondary_noneg < 0)),
            },
        },
        "interpretation_rule": (
            "Primary support requires spatial ratio-control to exceed the image-mean-negative "
            "control in aggregate CV F1 and have a positive mean fold delta. Fold counts are "
            "descriptive because repeated-CV validation events are not independent."
        ),
        "forbidden_inference": (
            "Do not use BSDS500 test, BIPEDv2 test, or UDED held-out to select or reinterpret "
            "these variants."
        ),
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=float), encoding="utf-8"
    )

    print("STAGE14B_POLARITY_ABLATION_DONE", flush=True)
    print(json.dumps(summary["primary_contrast"], indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
