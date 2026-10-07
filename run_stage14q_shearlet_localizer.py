from __future__ import annotations

"""Stage 14q: fixed anisotropic singularity localizer.

This is a bounded, non-learned discrete operationalization of the shearlet
edge-analysis hypothesis.  A small bank of odd, anisotropic Gaussian-derivative
atoms replaces Scharr; the retained compact Choquet context and all fitting
semantics remain unchanged.
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
from scipy.ndimage import convolve
from skimage.io import imread

from automation.visual_report import write_panel_grid
from benchmark_uded import DEFAULT_UDED, load_uded
from benchmark_uded_quick import resize_items
from benchmark_uded_stage7 import fixed_eval, selection_metric
from benchmark_uded_stage8_contextual import aggregate_counts
from run_stage12b_fuzzy_signature import membership_stack, prepare
from run_stage12c_leakfree_cv import ensure_uded, learn_banks
from run_stage12d_bipolar_cv import _make_repeated_folds
from run_stage14c_positive_bank_pruning import COMPACT_FEATURES, FLOOR, GAMMA, STRENGTH, _filter_bank
from src.bipolar_fuzzy import context_gate, distorted_choquet
from src.postprocess import non_maximum_suppression


DEFAULT_OUT = ROOT / "results" / "local_dev" / "stage14q_shearlet_localizer"
VARIANTS = ("compact_incumbent", "fixed_anisotropic_singularity_localizer")
NORMAL_SIGMAS = (1.0, 2.0)
NORMAL_ANGLES_DEG = (0.0, 45.0, 90.0, 135.0)
TANGENT_FACTOR = 2.0


def _ordered_compact(bank: list[dict]) -> list[dict]:
    selected = _filter_bank(bank, COMPACT_FEATURES)
    by_feature = {str(row["feature"]): row for row in selected}
    missing = [name for name in COMPACT_FEATURES if name not in by_feature]
    if missing:
        raise RuntimeError(f"compact bank missing features: {missing}")
    return [by_feature[name] for name in COMPACT_FEATURES]


def _contexts(items: list[dict], names: list[str], compact: list[dict]):
    contexts = []
    for item in items:
        stack, weights = membership_stack(item, names, compact, "edge")
        contexts.append(distorted_choquet(stack, weights, GAMMA))
    return contexts


def _odd_anisotropic_atom(sigma_n: float, theta: float) -> np.ndarray:
    """Odd normal derivative with fixed 2:1 tangent elongation."""
    sigma_t = TANGENT_FACTOR * sigma_n
    radius = int(np.ceil(3.0 * sigma_t))
    yy, xx = np.mgrid[-radius:radius + 1, -radius:radius + 1]
    ct, st = np.cos(theta), np.sin(theta)
    normal = xx * ct + yy * st
    tangent = -xx * st + yy * ct
    atom = -normal * np.exp(-0.5 * ((normal / sigma_n) ** 2 + (tangent / sigma_t) ** 2))
    atom -= np.mean(atom)
    norm = float(np.sum(np.abs(atom)))
    if norm <= 0:
        raise RuntimeError("degenerate anisotropic atom")
    return (2.0 * atom / norm).astype(np.float32)


ATOM_BANK = tuple(
    (sigma, np.deg2rad(angle), _odd_anisotropic_atom(sigma, np.deg2rad(angle)))
    for sigma in NORMAL_SIGMAS for angle in NORMAL_ANGLES_DEG
)


def _singularity_localizer(image: np.ndarray):
    gray = np.asarray(image, dtype=np.float32)
    if gray.ndim == 3:
        gray = np.mean(gray[..., :3], axis=-1, dtype=np.float32)
    gray = np.clip(gray, 0.0, 1.0)
    responses = np.stack([np.abs(convolve(gray, atom, mode="reflect")) for _, _, atom in ATOM_BANK])
    winner = np.argmax(responses, axis=0)
    modulus = np.take_along_axis(responses, winner[None, ...], axis=0)[0]
    orientations = np.asarray([theta for _, theta, _ in ATOM_BANK], dtype=np.float32)
    theta = orientations[winner]
    localized = non_maximum_suppression(np.clip(modulus, 0.0, 1.0), theta)
    return localized.astype(np.float32), modulus.astype(np.float32), winner


def _score_maps(items: list[dict], contexts: list[np.ndarray]):
    incumbent, candidate, raw_modulus, winners = [], [], [], []
    for item, context in zip(items, contexts):
        incumbent.append(context_gate(item["scharr"], context, STRENGTH, FLOOR))
        localized, modulus, winner = _singularity_localizer(item["pre_img"])
        candidate.append(context_gate(localized, context, STRENGTH, FLOOR).astype(np.float32))
        raw_modulus.append(modulus)
        winners.append(winner)
    return incumbent, candidate, raw_modulus, winners


def _save_soft_png(score: np.ndarray, path: Path) -> None:
    x = np.asarray(score, dtype=np.float32)
    if not np.all(np.isfinite(x)):
        raise RuntimeError(f"non-finite candidate score for {path.stem}")
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.rint(np.clip(x, 0.0, 1.0) * 255.0).astype(np.uint8), mode="L").save(path)


def _fit_full_context(args: argparse.Namespace):
    raw = resize_items(load_uded(ensure_uded(Path(args.uded_root))), args.max_side_development)
    selection, names = prepare(raw[0::2])
    positive, _ = learn_banks(selection, names, args.seed, args.max_positive, args.max_negative, args.max_abs_corr)
    return names, _ordered_compact(positive)


def _write_official_manifest(out: Path) -> Path:
    manifest = {
        "schema_version": 1, "split": "val", "include_incumbent": True,
        "methods": [{"name": VARIANTS[1], "export": {
            "script": "run_stage14q_shearlet_localizer.py",
            "args": ["--export-bsds", "--image-dir", "{image_dir}", "--output-dir", "{output_dir}", "--split", "{split}"],
        }}],
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
        print(f"STAGE14Q_BSDS_EXPORT {index:03d}/{len(image_paths):03d} {path.stem}", flush=True)
        prepared, candidate_names = prepare([{"id": path.stem, "img": imread(path)}])
        if list(candidate_names) != list(names):
            raise RuntimeError(f"feature-name mismatch while exporting {path.stem}")
        context = _contexts(prepared, names, compact)
        _, candidate, _, _ = _score_maps(prepared, context)
        _save_soft_png(candidate[0], output_dir / f"{path.stem}.png")
    metadata = {
        "method": VARIANTS[1], "dataset": "BSDS500", "split": args.split,
        "bsds_ground_truth_read": False, "native_resolution": True,
        "output": "8-bit soft PNG, no per-image normalization",
        "development_source": "UDED selection only",
        "bank": {"normal_sigmas": NORMAL_SIGMAS, "normal_angles_deg": NORMAL_ANGLES_DEG, "tangent_factor": TANGENT_FACTOR},
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
        positive, _ = learn_banks(train, names, args.seed + 10000 * repeat + fold, args.max_positive, args.max_negative, args.max_abs_corr)
        compact = _ordered_compact(positive)
        train_maps = _score_maps(train, _contexts(train, names, compact))
        valid_maps = _score_maps(valid, _contexts(valid, names, compact))
        print(f"STAGE14Q_SPLIT {split_index:02d}/{len(splits)} repeat={repeat + 1} fold={fold + 1}", flush=True)
        split_predictions = {}
        for index, variant in enumerate(VARIANTS):
            train_scores, valid_scores = train_maps[index], valid_maps[index]
            threshold = float(selection_metric(train_scores, train, args.thresholds)["threshold"])
            metric, event_counts, per_image = fixed_eval(valid_scores, valid, threshold)
            split_predictions[variant] = [np.asarray(x) >= threshold for x in valid_scores]
            counts[variant].extend(event_counts); folds[variant].append(metric); thresholds[variant].append(threshold)
            fold_rows.append({"repeat": repeat + 1, "fold": fold + 1, "variant": variant, "train_threshold": threshold, **metric})
            image_rows.extend({"repeat": repeat + 1, "fold": fold + 1, "variant": variant, **row} for row in per_image)
        valid_modulus, valid_winners = valid_maps[2], valid_maps[3]
        diagnostic_rows.append({
            "repeat": repeat + 1, "fold": fold + 1,
            "valid_mean_raw_modulus": float(np.mean([np.mean(x) for x in valid_modulus])),
            **{f"winner_fraction_atom_{i}": float(np.mean([np.mean(w == i) for w in valid_winners])) for i in range(len(ATOM_BANK))},
        })
        if preview is None:
            preview = {"item": valid[0], "incumbent": split_predictions[VARIANTS[0]][0], "candidate": split_predictions[VARIANTS[1]][0], "modulus": valid_modulus[0]}

    aggregate = {name: aggregate_counts(counts[name]) for name in VARIANTS}
    inc_name, cand_name = VARIANTS
    fold_delta = np.asarray([b["F1"] - a["F1"] for a, b in zip(folds[inc_name], folds[cand_name])])
    f1_delta = float(aggregate[cand_name]["F1"] - aggregate[inc_name]["F1"])
    precision_delta = float(aggregate[cand_name]["precision"] - aggregate[inc_name]["precision"])
    uded_gate = bool(f1_delta >= 0 and precision_delta >= 0 and np.mean(fold_delta) >= 0 and np.sum(fold_delta > 0) >= 9)
    ranking = []
    for name in VARIANTS:
        values = np.asarray([row["F1"] for row in folds[name]])
        ranking.append({"variant": name, "cv_precision": float(aggregate[name]["precision"]), "cv_recall": float(aggregate[name]["recall"]), "cv_F1": float(aggregate[name]["F1"]), "mean_fold_F1": float(np.mean(values)), "std_fold_F1": float(np.std(values)), "threshold_mean": float(np.mean(thresholds[name])), "threshold_std": float(np.std(thresholds[name]))})
    pd.DataFrame(ranking).sort_values("cv_F1", ascending=False).to_csv(out / "variant_ranking.csv", index=False)
    pd.DataFrame(fold_rows).to_csv(out / "fold_results.csv", index=False)
    pd.DataFrame(image_rows).to_csv(out / "per_image_metrics.csv", index=False)
    pd.DataFrame(diagnostic_rows).to_csv(out / "atom_diagnostics.csv", index=False)
    if preview is None:
        raise RuntimeError("No deterministic preview sample was captured")
    preview_path = write_panel_grid(out / "best_method_preview.png", [[preview["item"]["pre_img"], preview["item"]["gt"], preview["incumbent"], preview["candidate"], preview["modulus"], preview["incumbent"]]])
    manifest_path = _write_official_manifest(out)
    summary = {
        "stage": "14q-fixed-anisotropic-singularity-localizer",
        "dataset_role": "UDED selection repeated CV plus BSDS500 validation; development",
        "heldout_used": False, "external_test_feedback_used": False,
        "n_selection_images": len(selection), "repeats": args.repeats, "folds": args.folds,
        "mechanism": {"description": "max modulus over a fixed elongated odd anisotropic atom bank, atom-normal NMS, then unchanged compact Choquet context gate", "bank": {"normal_sigmas": NORMAL_SIGMAS, "normal_angles_deg": NORMAL_ANGLES_DEG, "tangent_factor": TANGENT_FACTOR}, "fit_policy": "compact memberships and thresholds fit inside each outer fold; atom bank fixed globally"},
        "promotion_rule": "All criteria are conjunctive: UDED aggregate F1 and precision deltas >= 0, mean fold-F1 delta >= 0, at least 9/15 fold wins, completed official BSDS500-val evaluation, ODS delta >= +0.002, and nonnegative OIS and AP deltas.",
        "uded_gate": {"aggregate_F1_delta": f1_delta, "aggregate_precision_delta": precision_delta, "mean_fold_F1_delta": float(np.mean(fold_delta)), "fold_F1_wins": int(np.sum(fold_delta > 0)), "met": uded_gate},
        "promotion_pending_official_bsds_val": True, "metrics": aggregate,
        "visual_preview": {"file": preview_path.name, "selection": "first validation image of the first deterministic repeated-CV split", "columns": ["conditioned_input", "ground_truth", "compact_incumbent", "anisotropic_candidate", "raw_max_modulus", "current_retained_incumbent"], "use": "documentary only; not an optimization signal"},
        "official_evaluation": {"manifest": manifest_path.name, "split": "BSDS500 validation", "protocol": "official MATLAB multi-annotator boundary evaluation", "required_before_promotion": True},
        "files": ["variant_ranking.csv", "fold_results.csv", "per_image_metrics.csv", "atom_diagnostics.csv", "best_method_preview.png", "official_eval_manifest.json"],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE14Q_SHEARLET_LOCALIZER_COMPLETE", flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uded-root", default=str(DEFAULT_UDED)); parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--max-side", type=int, default=256); parser.add_argument("--thresholds", type=int, default=41)
    parser.add_argument("--folds", type=int, default=3); parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--max-positive", type=int, default=10); parser.add_argument("--max-negative", type=int, default=8)
    parser.add_argument("--max-abs-corr", type=float, default=0.88); parser.add_argument("--seed", type=int, default=20261007)
    parser.add_argument("--export-bsds", action="store_true"); parser.add_argument("--image-dir"); parser.add_argument("--output-dir")
    parser.add_argument("--split", default="val"); parser.add_argument("--max-side-development", type=int, default=256)
    args = parser.parse_args()
    if args.export_bsds:
        if not args.image_dir or not args.output_dir:
            parser.error("--export-bsds requires --image-dir and --output-dir")
        return export_bsds(args)
    return run_experiment(args)


if __name__ == "__main__":
    raise SystemExit(main())
