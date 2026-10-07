from __future__ import annotations

"""Stage 14u: fixed Yager-rule evidential ignorance fusion.

This single-point falsification separates the retained five-feature context
into a four-cue Choquet source and the scale-persistence source, combines them
with Scharr+NMS strength as binary edge/non-edge evidence, sends conjunctive
conflict to explicit ignorance, and uses the pignistic edge probability in the
unchanged context gate.
"""

from collections import defaultdict
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from PIL import Image
from skimage.io import imread

from automation.visual_report import write_panel_grid
from benchmark_uded import DEFAULT_UDED, load_uded
from benchmark_uded_quick import resize_items
from benchmark_uded_stage7 import fixed_eval, selection_metric
from benchmark_uded_stage8_contextual import aggregate_counts
from run_stage12b_fuzzy_signature import membership_stack, prepare
from run_stage12c_leakfree_cv import ensure_uded, learn_banks
from run_stage12d_bipolar_cv import _make_repeated_folds
from run_stage14c_positive_bank_pruning import (
    COMPACT_FEATURES,
    FLOOR,
    GAMMA,
    STRENGTH,
    _filter_bank,
)
from src.bipolar_fuzzy import context_gate, distorted_choquet


DEFAULT_OUT = ROOT / "results" / "local_dev" / "stage14u_yager_evidential_ignorance"
VARIANTS = ("compact_scharr_incumbent", "fixed_yager_evidential_ignorance")
PERSISTENCE_FEATURE = "gabor4_scale_persistence"


def _ordered_compact(bank: list[dict]) -> list[dict]:
    selected = _filter_bank(bank, COMPACT_FEATURES)
    by_feature = {str(row["feature"]): row for row in selected}
    missing = [name for name in COMPACT_FEATURES if name not in by_feature]
    if missing:
        raise RuntimeError(f"compact bank missing features: {missing}")
    return [by_feature[name] for name in COMPACT_FEATURES]


def _least_committed_binary_mass(q: np.ndarray):
    """Maximum-ignorance binary mass assignment preserving BetP(edge)=q."""
    x = np.clip(np.asarray(q, dtype=np.float64), 0.0, 1.0)
    edge = np.maximum(2.0 * x - 1.0, 0.0)
    nonedge = np.maximum(1.0 - 2.0 * x, 0.0)
    ignorance = 1.0 - edge - nonedge
    return edge, nonedge, ignorance


def _yager_fuse_three(cues: tuple[np.ndarray, np.ndarray, np.ndarray]):
    """Fuse three binary masses conjunctively and assign conflict to Theta."""
    masses = [_least_committed_binary_mass(cue) for cue in cues]
    theta_product = np.ones_like(masses[0][0], dtype=np.float64)
    edge_or_theta = np.ones_like(theta_product)
    nonedge_or_theta = np.ones_like(theta_product)
    for edge, nonedge, ignorance in masses:
        theta_product *= ignorance
        edge_or_theta *= edge + ignorance
        nonedge_or_theta *= nonedge + ignorance
    edge = edge_or_theta - theta_product
    nonedge = nonedge_or_theta - theta_product
    conflict = np.clip(1.0 - edge - nonedge - theta_product, 0.0, 1.0)
    ignorance = np.clip(theta_product + conflict, 0.0, 1.0)
    pignistic_edge = np.clip(edge + 0.5 * ignorance, 0.0, 1.0)
    total = edge + nonedge + ignorance
    if not np.allclose(total, 1.0, atol=2e-6):
        raise RuntimeError("Yager masses do not sum to one")
    return tuple(x.astype(np.float32) for x in (
        edge, nonedge, ignorance, conflict, pignistic_edge,
    ))


def _source_maps(item: dict, names: list[str], compact: list[dict]):
    stack, weights = membership_stack(item, names, compact, "edge")
    persistence_index = COMPACT_FEATURES.index(PERSISTENCE_FEATURE)
    context_indices = [i for i in range(len(COMPACT_FEATURES)) if i != persistence_index]
    context_stack = stack[..., context_indices]
    context_weights = np.asarray(weights[context_indices], dtype=np.float64)
    context_weights /= max(float(np.sum(context_weights)), np.finfo(float).tiny)
    four_cue_context = distorted_choquet(context_stack, context_weights, GAMMA)
    persistence = stack[..., persistence_index]
    localizer = np.clip(np.asarray(item["scharr"], dtype=np.float32), 0.0, 1.0)
    return localizer, four_cue_context, persistence


def _score_maps(items: list[dict], names: list[str], compact: list[dict]):
    incumbents, candidates = [], []
    pignistic_maps, ignorance_maps, conflict_maps, diagnostics = [], [], [], []
    for item in items:
        stack, weights = membership_stack(item, names, compact, "edge")
        full_context = distorted_choquet(stack, weights, GAMMA)
        incumbent = context_gate(item["scharr"], full_context, STRENGTH, FLOOR).astype(np.float32)
        localizer, four_context, persistence = _source_maps(item, names, compact)
        edge, nonedge, ignorance, conflict, pignistic = _yager_fuse_three(
            (localizer, four_context, persistence)
        )
        candidate = context_gate(localizer, pignistic, STRENGTH, FLOOR).astype(np.float32)
        positive = localizer > 0
        region = positive if np.any(positive) else np.ones_like(positive, dtype=bool)
        diagnostics.append({
            "mean_pignistic_edge_at_nms": float(np.mean(pignistic[region])),
            "mean_ignorance_at_nms": float(np.mean(ignorance[region])),
            "mean_conflict_at_nms": float(np.mean(conflict[region])),
            "mean_edge_belief_at_nms": float(np.mean(edge[region])),
            "mean_nonedge_belief_at_nms": float(np.mean(nonedge[region])),
            "candidate_to_incumbent_mass_ratio": float(
                np.sum(candidate) / max(float(np.sum(incumbent)), np.finfo(float).tiny)
            ),
        })
        incumbents.append(incumbent)
        candidates.append(candidate)
        pignistic_maps.append(pignistic)
        ignorance_maps.append(ignorance)
        conflict_maps.append(conflict)
    return incumbents, candidates, pignistic_maps, ignorance_maps, conflict_maps, diagnostics


def _save_soft_png(score: np.ndarray, path: Path) -> None:
    x = np.asarray(score, dtype=np.float32)
    if not np.all(np.isfinite(x)):
        raise RuntimeError(f"non-finite candidate score for {path.stem}")
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.rint(np.clip(x, 0.0, 1.0) * 255.0).astype(np.uint8), mode="L").save(path)


def _fit_full_context(args: argparse.Namespace):
    raw = resize_items(load_uded(ensure_uded(Path(args.uded_root))), args.max_side_development)
    selection, names = prepare(raw[0::2])
    positive, _ = learn_banks(
        selection, names, args.seed, args.max_positive, args.max_negative, args.max_abs_corr
    )
    return names, _ordered_compact(positive)


def _write_official_manifest(out: Path) -> Path:
    manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [{
            "name": VARIANTS[1],
            "export": {
                "script": "run_stage14u_yager_evidential_ignorance.py",
                "args": [
                    "--export-bsds", "--image-dir", "{image_dir}",
                    "--output-dir", "{output_dir}", "--split", "{split}",
                ],
            },
        }],
    }
    path = out / "official_eval_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def export_bsds(args: argparse.Namespace) -> int:
    names, compact = _fit_full_context(args)
    image_paths = sorted(Path(args.image_dir).glob("*.jpg"))
    if not image_paths:
        raise RuntimeError(f"no BSDS JPG images found in {args.image_dir}")
    output_dir = Path(args.output_dir)
    for index, path in enumerate(image_paths, start=1):
        print(f"STAGE14U_BSDS_EXPORT {index:03d}/{len(image_paths):03d} {path.stem}", flush=True)
        prepared, candidate_names = prepare([{"id": path.stem, "img": imread(path)}])
        if list(candidate_names) != list(names):
            raise RuntimeError(f"feature-name mismatch while exporting {path.stem}")
        maps = _score_maps(prepared, names, compact)
        _save_soft_png(maps[1][0], output_dir / f"{path.stem}.png")
    metadata = {
        "method": VARIANTS[1],
        "dataset": "BSDS500",
        "split": args.split,
        "bsds_ground_truth_read": False,
        "native_resolution": True,
        "output": "8-bit soft PNG, no export-time per-image normalization",
        "development_source": "UDED selection only",
        "evidential_fusion": {
            "frame": ["edge", "nonedge"],
            "sources": ["Scharr+NMS", "four-cue Choquet context", "scale persistence"],
            "mass_mapping": "maximum-ignorance binary assignment preserving BetP=q",
            "combination": "three-way conjunctive fusion with conflict assigned to Theta (Yager rule)",
            "decision": "BetP(edge)",
            "gate_strength": STRENGTH,
            "gate_floor": FLOOR,
        },
        "n_maps": len(image_paths),
    }
    (output_dir / "export_manifest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return 0


def run_experiment(args: argparse.Namespace) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    raw = resize_items(load_uded(ensure_uded(Path(args.uded_root))), args.max_side)
    selection, names = prepare(raw[0::2])
    if len(selection) != 15:
        raise RuntimeError(f"Expected 15 UDED selection images, found {len(selection)}")

    splits = _make_repeated_folds(len(selection), args.folds, args.repeats, args.seed)
    counts, folds, thresholds = defaultdict(list), defaultdict(list), defaultdict(list)
    fold_rows, image_rows, diagnostic_rows = [], [], []
    preview = None

    for split_index, (repeat, fold, tr_idx, va_idx) in enumerate(splits, start=1):
        train, valid = [selection[i] for i in tr_idx], [selection[i] for i in va_idx]
        positive, _ = learn_banks(
            train, names, args.seed + 10000 * repeat + fold,
            args.max_positive, args.max_negative, args.max_abs_corr,
        )
        compact = _ordered_compact(positive)
        train_maps = _score_maps(train, names, compact)
        valid_maps = _score_maps(valid, names, compact)
        print(
            f"STAGE14U_SPLIT {split_index:02d}/{len(splits)} "
            f"repeat={repeat + 1} fold={fold + 1}", flush=True,
        )
        split_predictions = {}
        for index, variant in enumerate(VARIANTS):
            train_scores, valid_scores = train_maps[index], valid_maps[index]
            threshold = float(selection_metric(train_scores, train, args.thresholds)["threshold"])
            metric, event_counts, per_image = fixed_eval(valid_scores, valid, threshold)
            split_predictions[variant] = [np.asarray(x) >= threshold for x in valid_scores]
            counts[variant].extend(event_counts)
            folds[variant].append(metric)
            thresholds[variant].append(threshold)
            fold_rows.append({
                "repeat": repeat + 1, "fold": fold + 1, "variant": variant,
                "train_threshold": threshold, **metric,
            })
            image_rows.extend(
                {"repeat": repeat + 1, "fold": fold + 1, "variant": variant, **row}
                for row in per_image
            )
        for item, diagnostic in zip(valid, valid_maps[5]):
            diagnostic_rows.append({
                "repeat": repeat + 1, "fold": fold + 1,
                "id": str(item["id"]), **diagnostic,
            })
        if preview is None:
            preview = {
                "item": valid[0],
                "incumbent": split_predictions[VARIANTS[0]][0],
                "candidate": split_predictions[VARIANTS[1]][0],
                "ignorance": valid_maps[3][0],
                "conflict": valid_maps[4][0],
            }

    aggregate = {name: aggregate_counts(counts[name]) for name in VARIANTS}
    inc_name, cand_name = VARIANTS
    fold_delta = np.asarray([b["F1"] - a["F1"] for a, b in zip(folds[inc_name], folds[cand_name])])
    f1_delta = float(aggregate[cand_name]["F1"] - aggregate[inc_name]["F1"])
    precision_delta = float(aggregate[cand_name]["precision"] - aggregate[inc_name]["precision"])
    uded_gate = bool(
        f1_delta >= 0
        and precision_delta >= 0
        and float(np.mean(fold_delta)) >= 0
        and int(np.sum(fold_delta > 0)) >= 9
    )

    ranking = []
    for name in VARIANTS:
        values = np.asarray([row["F1"] for row in folds[name]])
        ranking.append({
            "variant": name,
            "cv_precision": float(aggregate[name]["precision"]),
            "cv_recall": float(aggregate[name]["recall"]),
            "cv_F1": float(aggregate[name]["F1"]),
            "mean_fold_F1": float(np.mean(values)),
            "std_fold_F1": float(np.std(values)),
            "threshold_mean": float(np.mean(thresholds[name])),
            "threshold_std": float(np.std(thresholds[name])),
        })
    pd.DataFrame(ranking).sort_values("cv_F1", ascending=False).to_csv(out / "variant_ranking.csv", index=False)
    pd.DataFrame(fold_rows).to_csv(out / "fold_results.csv", index=False)
    pd.DataFrame(image_rows).to_csv(out / "per_image_metrics.csv", index=False)
    pd.DataFrame(diagnostic_rows).to_csv(out / "evidential_diagnostics.csv", index=False)

    if preview is None:
        raise RuntimeError("No deterministic preview sample was captured")
    preview_path = write_panel_grid(out / "best_method_preview.png", [[
        preview["item"]["pre_img"], preview["item"]["gt"],
        preview["incumbent"], preview["candidate"],
        preview["ignorance"], preview["conflict"],
    ]])
    manifest_path = _write_official_manifest(out)
    summary = {
        "stage": "14u-fixed-yager-evidential-ignorance",
        "dataset_role": "UDED selection repeated CV plus BSDS500 validation; development",
        "heldout_used": False,
        "external_test_feedback_used": False,
        "n_selection_images": len(selection),
        "repeats": args.repeats,
        "folds": args.folds,
        "mechanism": {
            "description": "fixed three-source Yager-rule evidence fusion feeding the unchanged Scharr context gate",
            "sources": ["Scharr+NMS strength", "four-cue distorted-Choquet context", "scale-persistence membership"],
            "source_overlap": "none: scale persistence is removed from the four-cue Choquet source",
            "mass_mapping": "m(E)=max(2q-1,0), m(N)=max(1-2q,0), m(Theta)=1-|2q-1|",
            "combination": "unnormalized three-way conjunctive mass; all conflict assigned to Theta",
            "decision": "BetP(E)=m(E)+0.5*m(Theta)",
            "gate_strength": STRENGTH,
            "gate_floor": FLOOR,
            "fit_policy": "compact memberships and thresholds fit inside each outer fold; evidential construction fixed globally",
        },
        "promotion_rule": "All criteria are conjunctive: UDED aggregate F1 delta >= 0, precision delta >= 0, mean fold-F1 delta >= 0, at least 9/15 F1 wins, completed official BSDS500-val evaluation, ODS delta >= +0.002, and nonnegative OIS and AP deltas.",
        "uded_gate": {
            "aggregate_F1_delta": f1_delta,
            "aggregate_precision_delta": precision_delta,
            "mean_fold_F1_delta": float(np.mean(fold_delta)),
            "fold_F1_wins": int(np.sum(fold_delta > 0)),
            "met": uded_gate,
        },
        "promotion_pending_official_bsds_val": True,
        "metrics": aggregate,
        "visual_preview": {
            "file": preview_path.name,
            "selection": "first validation image of the first deterministic repeated-CV split",
            "columns": [
                "conditioned_input", "ground_truth", "compact_scharr_incumbent",
                "yager_evidential_candidate", "fused_ignorance", "fused_conflict",
            ],
            "use": "documentary only; not an optimization signal",
        },
        "official_evaluation": {
            "manifest": manifest_path.name,
            "split": "BSDS500 validation",
            "protocol": "official MATLAB multi-annotator boundary evaluation",
            "required_before_promotion": True,
        },
        "files": [
            "variant_ranking.csv", "fold_results.csv", "per_image_metrics.csv",
            "evidential_diagnostics.csv", "best_method_preview.png",
            "official_eval_manifest.json",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE14U_YAGER_EVIDENTIAL_IGNORANCE_COMPLETE", flush=True)
    return 0


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
    parser.add_argument("--max-abs-corr", type=float, default=0.88)
    parser.add_argument("--seed", type=int, default=20261007)
    parser.add_argument("--export-bsds", action="store_true")
    parser.add_argument("--image-dir")
    parser.add_argument("--output-dir")
    parser.add_argument("--split", default="val")
    parser.add_argument("--max-side-development", type=int, default=256)
    args = parser.parse_args()
    if args.export_bsds:
        if not args.image_dir or not args.output_dir:
            parser.error("--export-bsds requires --image-dir and --output-dir")
        return export_bsds(args)
    return run_experiment(args)


if __name__ == "__main__":
    raise SystemExit(main())
