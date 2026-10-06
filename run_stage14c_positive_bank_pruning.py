from __future__ import annotations

"""Stage 14c: leakage-free pruning of the positive edge-signature bank.

Only UDED selection images are prepared. Each repeated-CV training fold learns
the full positive bank; the compact variant retains only universally stable
features already established by Stage 12d/14b. Both variants use the same
positive distorted-Choquet aggregation, localizer, gate, and train-fold-fitted
threshold, isolating feature-bank complexity as the sole planned change.
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
from run_stage12d_bipolar_cv import _choquet_maps, _make_repeated_folds
from src.bipolar_fuzzy import context_gate

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "local_dev" / "stage14c_positive_bank_pruning"
GAMMA = 0.55
STRENGTH = 2.0
FLOOR = 0.10
COMPACT_FEATURES = (
    "gabor4_s5",
    "hessian_s7",
    "gabor4_s13",
    "hessian_s13",
    "gabor4_scale_persistence",
)


def _filter_bank(bank, allowed):
    selected = [item for item in bank if item["feature"] in allowed]
    missing = sorted(set(allowed) - {item["feature"] for item in selected})
    if missing:
        raise RuntimeError(f"Compact features absent from a training fold: {missing}")
    return selected


def _contexts(items, names, bank):
    memberships, weights = [], None
    for item in items:
        from run_stage12d_bipolar_cv import _bank_memberships

        pos, pos_weights, _neg, _neg_weights = _bank_memberships(
            [item], names, bank, []
        )
        memberships.extend(pos)
        weights = pos_weights
    return _choquet_maps(memberships, weights, [GAMMA])[GAMMA]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uded-root", default=str(DEFAULT_UDED))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--max-side", type=int, default=256)
    parser.add_argument("--thresholds", type=int, default=41)
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--max-positive", type=int, default=10)
    parser.add_argument("--max-negative", type=int, default=8)
    parser.add_argument("--max-abs-corr", type=float, default=.88)
    parser.add_argument("--seed", type=int, default=20261006)
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    raw = resize_items(load_uded(ensure_uded(Path(args.uded_root))), args.max_side)
    selection, names = prepare(raw[0::2])
    if len(selection) != 15:
        raise RuntimeError(f"Expected 15 selection images, got {len(selection)}")

    splits = _make_repeated_folds(len(selection), args.folds, args.repeats, args.seed)
    variants = ("positive_full", "positive_compact")
    counts = defaultdict(list)
    f1s = defaultdict(list)
    thresholds = defaultdict(list)
    occurrences = Counter()
    fold_rows = []

    for split_no, (repeat, fold, tr_idx, va_idx) in enumerate(splits, 1):
        train = [selection[i] for i in tr_idx]
        valid = [selection[i] for i in va_idx]
        positive, _negative = learn_banks(
            train, names, args.seed + 10000 * repeat + fold,
            args.max_positive, args.max_negative, args.max_abs_corr,
        )
        occurrences.update(item["feature"] for item in positive)
        compact = _filter_bank(positive, COMPACT_FEATURES)
        bank_variants = {"positive_full": positive, "positive_compact": compact}
        print(
            f"STAGE14C_SPLIT {split_no:02d}/{len(splits)} "
            f"repeat={repeat+1} fold={fold+1} train={len(train)} valid={len(valid)}",
            flush=True,
        )

        for variant, bank in bank_variants.items():
            train_context = _contexts(train, names, bank)
            valid_context = _contexts(valid, names, bank)
            train_scores = [
                context_gate(item["scharr"], c, STRENGTH, FLOOR)
                for item, c in zip(train, train_context)
            ]
            valid_scores = [
                context_gate(item["scharr"], c, STRENGTH, FLOOR)
                for item, c in zip(valid, valid_context)
            ]
            fit = selection_metric(train_scores, train, args.thresholds)
            metric, event_counts, _ = fixed_eval(valid_scores, valid, float(fit["threshold"]))
            counts[variant].extend(event_counts)
            f1s[variant].append(float(metric["F1"]))
            thresholds[variant].append(float(fit["threshold"]))
            fold_rows.append({
                "repeat": repeat + 1,
                "fold": fold + 1,
                "variant": variant,
                "F1": float(metric["F1"]),
                "precision": float(metric["precision"]),
                "recall": float(metric["recall"]),
                "train_threshold": float(fit["threshold"]),
                "positive_bank_size": len(bank),
            })

    rows = []
    full_folds = np.asarray(f1s["positive_full"], dtype=float)
    for variant in variants:
        metric = aggregate_counts(counts[variant])
        values = np.asarray(f1s[variant], dtype=float)
        rows.append({
            "variant": variant,
            "cv_precision": float(metric["precision"]),
            "cv_recall": float(metric["recall"]),
            "cv_F1": float(metric["F1"]),
            "mean_fold_F1": float(np.mean(values)),
            "std_fold_F1": float(np.std(values)),
            "min_fold_F1": float(np.min(values)),
            "threshold_mean": float(np.mean(thresholds[variant])),
            "threshold_std": float(np.std(thresholds[variant])),
            "mean_fold_delta_vs_full": float(np.mean(values - full_folds)),
            "fold_wins_vs_full": int(np.sum(values > full_folds)),
        })

    ranking = pd.DataFrame(rows).sort_values("cv_F1", ascending=False)
    ranking.to_csv(out / "variant_ranking.csv", index=False)
    pd.DataFrame(fold_rows).to_csv(out / "fold_results.csv", index=False)
    pd.DataFrame([
        {"feature": feature, "split_occurrences": count,
         "fraction": count / len(splits)}
        for feature, count in occurrences.most_common()
    ]).to_csv(out / "bank_stability.csv", index=False)
    compact_values = np.asarray(f1s["positive_compact"], dtype=float)
    summary = {
        "stage": "14c-positive-bank-pruning",
        "dataset_role": "UDED selection only; development",
        "heldout_used": False,
        "external_feedback_used": False,
        "n_selection_images": len(selection),
        "repeats": args.repeats,
        "folds": args.folds,
        "n_validation_events": len(splits),
        "aggregation": {"family": "positive distorted Choquet", "gamma": GAMMA},
        "fixed_localizer_and_gate": {"localizer": "Scharr+NMS", "strength": STRENGTH, "floor": FLOOR},
        "compact_features": list(COMPACT_FEATURES),
        "compact_minus_full": {
            "mean_fold_delta_F1": float(np.mean(compact_values - full_folds)),
            "fold_wins": int(np.sum(compact_values > full_folds)),
            "fold_losses": int(np.sum(compact_values < full_folds)),
        },
        "interpretation_rule": "Prune the full bank only if the compact fixed feature subset is noninferior in aggregate CV F1 and has nonnegative mean fold delta; repeated-CV events are descriptive, not independent samples.",
        "forbidden_inference": "Do not use BSDS500 test, BIPEDv2 test, or UDED held-out to select or reinterpret these variants.",
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE14C_POSITIVE_BANK_PRUNING_DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
