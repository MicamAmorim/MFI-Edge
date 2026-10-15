from __future__ import annotations

"""Stage 16v: exact author Structured Edge forest replacement falsification."""

from collections import defaultdict
from pathlib import Path
import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
from PIL import Image

from automation.visual_report import write_panel_grid
from benchmark_uded import DEFAULT_UDED, load_uded
from benchmark_uded_quick import resize_items
from benchmark_uded_stage7 import fixed_eval, selection_metric
from benchmark_uded_stage8_contextual import aggregate_counts
from run_stage12b_fuzzy_signature import membership_stack, prepare
from run_stage12c_leakfree_cv import ensure_uded, learn_banks
from run_stage12d_bipolar_cv import _make_repeated_folds
from run_stage14c_positive_bank_pruning import FLOOR, GAMMA, STRENGTH
from run_stage16f_rolling_guidance_localizer import _ordered_compact
from src.bipolar_fuzzy import context_gate, distorted_choquet


EXPERIMENT_ID = "stage16v_structured_forest"
DEFAULT_OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
VARIANTS = ("compact_mfi", "dollar_zitnick_structured_forest")
PREVIEW_POSITIONS = (0, 7, 14)
EDGES_COMMIT = "94260b5d0fc068202598312e01a37604972dcc9e"
TOOLBOX_COMMIT = "e87332637bbe8e8b92dd487c87567d9628404523"
EDGES_DIR = ROOT / "evaluation" / "bsds_official" / "vendor" / "pdollar_edges"
TOOLBOX_DIR = ROOT / "evaluation" / "bsds_official" / "vendor" / "pdollar_toolbox_e87332637bbe"
MODEL_PATH = EDGES_DIR / "models" / "forest" / "modelBsds.mat"
MATLAB_HELPER = ROOT / "evaluation" / "bsds_official" / "export_stage16v_structured_forest.m"
DEFAULT_MATLAB = Path(r"C:\Program Files\MATLAB\R2023a\bin\matlab.exe")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_head(path: Path) -> str:
    trust = ["-c", f"safe.directory={path.resolve().as_posix()}"]
    completed = subprocess.run(
        ["git", *trust, "-C", str(path), "rev-parse", "HEAD"],
        cwd=str(ROOT), check=True, capture_output=True, text=True,
    )
    return completed.stdout.strip()


def _git_clean(path: Path) -> bool:
    trust = ["-c", f"safe.directory={path.resolve().as_posix()}"]
    completed = subprocess.run(
        ["git", *trust, "-C", str(path), "status", "--porcelain", "--untracked-files=no"],
        cwd=str(ROOT), check=True, capture_output=True, text=True,
    )
    return not completed.stdout.strip()


def _verify_dependencies() -> dict:
    if (
        not EDGES_DIR.is_dir()
        or _git_head(EDGES_DIR) != EDGES_COMMIT
        or not _git_clean(EDGES_DIR)
    ):
        raise RuntimeError(f"pinned pdollar/edges checkout missing or wrong at {EDGES_DIR}")
    if (
        not TOOLBOX_DIR.is_dir()
        or _git_head(TOOLBOX_DIR) != TOOLBOX_COMMIT
        or not _git_clean(TOOLBOX_DIR)
    ):
        raise RuntimeError(f"pinned pdollar/toolbox checkout missing or wrong at {TOOLBOX_DIR}")
    if not MODEL_PATH.is_file():
        raise RuntimeError(
            "pinned modelBsds.mat is absent; materialize models/forest from the pinned "
            "pdollar/edges sparse checkout without changing its commit"
        )
    matlab = Path(os.environ.get("MATLAB_EXE", str(DEFAULT_MATLAB))).resolve()
    if not matlab.is_file():
        raise RuntimeError(f"MATLAB executable not found at {matlab}")
    return {
        "edges_commit": EDGES_COMMIT,
        "toolbox_commit": TOOLBOX_COMMIT,
        "model_sha256": _sha256(MODEL_PATH),
        "model_bytes": MODEL_PATH.stat().st_size,
        "matlab": str(matlab),
    }


def _matlab_quote(path: Path) -> str:
    return str(path.resolve()).replace("'", "''").replace("\\", "/")


def _run_author_detector(input_dir: Path, output_dir: Path) -> dict:
    provenance = _verify_dependencies()
    output_dir.mkdir(parents=True, exist_ok=True)
    prefdir = ROOT / "automation" / "runtime" / "stage16v_matlab_pref"
    prefdir.mkdir(parents=True, exist_ok=True)
    matlab = provenance["matlab"]
    command = (
        f"addpath('{_matlab_quote(MATLAB_HELPER.parent)}');"
        "export_stage16v_structured_forest("
        f"'{_matlab_quote(TOOLBOX_DIR)}','{_matlab_quote(EDGES_DIR)}',"
        f"'{_matlab_quote(MODEL_PATH)}','{_matlab_quote(input_dir)}',"
        f"'{_matlab_quote(output_dir)}');"
    )
    env = dict(os.environ)
    env["MATLAB_PREFDIR"] = str(prefdir.resolve())
    subprocess.run(
        [matlab, "-batch", command], cwd=str(ROOT), env=env, check=True,
    )
    return provenance


def _read_scores(output_dir: Path, ids: list[str]) -> list[np.ndarray]:
    maps = []
    for image_id in ids:
        path = output_dir / f"{image_id}.png"
        if not path.is_file():
            raise RuntimeError(f"missing Structured Edge map: {path}")
        with Image.open(path) as image:
            score = np.asarray(image.convert("L"), dtype=np.float32) / 255.0
        if not np.all(np.isfinite(score)) or np.min(score) < 0.0 or np.max(score) > 1.0:
            raise RuntimeError(f"invalid Structured Edge map: {path}")
        maps.append(score)
    return maps


def _contexts(items: list[dict], names: list[str], compact: list[dict]) -> list[np.ndarray]:
    contexts = []
    for item in items:
        memberships, weights = membership_stack(item, names, compact, "edge")
        contexts.append(distorted_choquet(memberships, weights, GAMMA))
    return contexts


def _incumbent_scores(items: list[dict], names: list[str], compact: list[dict]) -> list[np.ndarray]:
    return [
        context_gate(item["scharr"], context, STRENGTH, FLOOR).astype(np.float32)
        for item, context in zip(items, _contexts(items, names, compact))
    ]


def _write_official_manifest(out: Path) -> Path:
    manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [{
            "name": VARIANTS[1],
            "export": {
                "script": "automation/stage16v_structured_forest_venv_launcher.py",
                "args": [
                    "--export-bsds", "--image-dir", "{image_dir}",
                    "--output-dir", "{output_dir}", "--split", "{split}",
                ],
                "timeout_minutes": 240,
            },
        }],
    }
    path = out / "official_eval_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def export_bsds(args: argparse.Namespace) -> int:
    image_dir = Path(args.image_dir)
    output_dir = Path(args.output_dir)
    image_paths = sorted(image_dir.glob("*.jpg"))
    if not image_paths:
        raise RuntimeError(f"no BSDS JPG images found in {image_dir}")
    provenance = _run_author_detector(image_dir, output_dir)
    ids = [path.stem for path in image_paths]
    _read_scores(output_dir, ids)
    export_manifest = {
        "method": VARIANTS[1],
        "dataset": "BSDS500",
        "split": args.split,
        "bsds_ground_truth_read": False,
        "native_resolution": True,
        "training": "fixed author model trained on BSDS500 train only",
        "validation_used_for_fitting": False,
        "output": "author NMS score serialized directly to 8-bit PNG",
        "provenance": provenance,
        "n_maps": len(ids),
    }
    (output_dir / "export_manifest.json").write_text(
        json.dumps(export_manifest, indent=2), encoding="utf-8"
    )
    return 0


def run_experiment(args: argparse.Namespace) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    raw = resize_items(load_uded(ensure_uded(Path(args.uded_root))), args.max_side)
    selection, names = prepare(raw[0::2])
    if len(selection) != 15:
        raise RuntimeError(f"expected 15 UDED selection images, found {len(selection)}")

    input_dir = out / "structured_forest_uded" / "inputs"
    map_dir = out / "structured_forest_uded" / "maps"
    input_dir.mkdir(parents=True, exist_ok=True)
    for item in selection:
        image = np.asarray(item["img"])
        if np.issubdtype(image.dtype, np.floating) and float(np.max(image)) <= 1.0:
            image = np.rint(np.clip(image, 0.0, 1.0) * 255.0)
        Image.fromarray(np.asarray(np.clip(image, 0, 255), dtype=np.uint8)).convert("RGB").save(
            input_dir / f"{item['id']}.png"
        )
    provenance = _run_author_detector(input_dir, map_dir)
    forest_scores = _read_scores(map_dir, [str(item["id"]) for item in selection])

    splits = _make_repeated_folds(len(selection), args.folds, args.repeats, args.seed)
    counts: dict[str, list] = defaultdict(list)
    fold_f1: dict[str, list[float]] = defaultdict(list)
    thresholds: dict[str, list[float]] = defaultdict(list)
    fold_rows, image_rows = [], []
    first_repeat_predictions: dict[str, dict[int, np.ndarray]] = {
        name: {} for name in VARIANTS
    }

    for split_no, (repeat, fold, tr_idx, va_idx) in enumerate(splits, start=1):
        train = [selection[index] for index in tr_idx]
        valid = [selection[index] for index in va_idx]
        positive, _negative = learn_banks(
            train, names, args.seed + 10000 * repeat + fold,
            args.max_positive, args.max_negative, args.max_abs_corr,
        )
        compact = _ordered_compact(positive)
        incumbent_train = _incumbent_scores(train, names, compact)
        incumbent_valid = _incumbent_scores(valid, names, compact)
        score_pairs = (
            (incumbent_train, incumbent_valid),
            ([forest_scores[index] for index in tr_idx], [forest_scores[index] for index in va_idx]),
        )
        print(
            f"STAGE16V_SPLIT {split_no:02d}/{len(splits)} "
            f"repeat={repeat + 1} fold={fold + 1}", flush=True,
        )
        for variant, (train_maps, valid_maps) in zip(VARIANTS, score_pairs):
            threshold = float(selection_metric(train_maps, train, args.thresholds)["threshold"])
            metric, event_counts, per_image = fixed_eval(valid_maps, valid, threshold)
            counts[variant].extend(event_counts)
            fold_f1[variant].append(float(metric["F1"]))
            thresholds[variant].append(threshold)
            fold_rows.append({
                "repeat": repeat + 1, "fold": fold + 1, "variant": variant,
                "train_threshold": threshold, **metric,
            })
            image_rows.extend({
                "repeat": repeat + 1, "fold": fold + 1, "variant": variant, **row,
            } for row in per_image)
            if repeat == 0:
                for global_index, score in zip(va_idx, valid_maps):
                    first_repeat_predictions[variant][int(global_index)] = score >= threshold

    aggregate = {name: aggregate_counts(counts[name]) for name in VARIANTS}
    incumbent_folds = np.asarray(fold_f1[VARIANTS[0]], dtype=np.float64)
    candidate_folds = np.asarray(fold_f1[VARIANTS[1]], dtype=np.float64)
    deltas = {
        "aggregate_F1": float(aggregate[VARIANTS[1]]["F1"] - aggregate[VARIANTS[0]]["F1"]),
        "aggregate_precision": float(aggregate[VARIANTS[1]]["precision"] - aggregate[VARIANTS[0]]["precision"]),
        "aggregate_recall": float(aggregate[VARIANTS[1]]["recall"] - aggregate[VARIANTS[0]]["recall"]),
        "mean_fold_F1": float(np.mean(candidate_folds - incumbent_folds)),
        "fold_wins": int(np.sum(candidate_folds > incumbent_folds)),
    }
    uded_gate = bool(
        deltas["aggregate_F1"] >= 0.005
        and deltas["aggregate_precision"] >= -0.003
        and deltas["aggregate_recall"] >= -0.003
        and deltas["mean_fold_F1"] >= 0.002
        and deltas["fold_wins"] >= 10
    )

    ranking = []
    for variant in VARIANTS:
        values = np.asarray(fold_f1[variant], dtype=np.float64)
        ranking.append({
            "variant": variant,
            "cv_precision": aggregate[variant]["precision"],
            "cv_recall": aggregate[variant]["recall"],
            "cv_F1": aggregate[variant]["F1"],
            "mean_fold_F1": float(np.mean(values)),
            "std_fold_F1": float(np.std(values)),
            "threshold_mean": float(np.mean(thresholds[variant])),
            "threshold_std": float(np.std(thresholds[variant])),
        })
    pd.DataFrame(ranking).sort_values("cv_F1", ascending=False).to_csv(
        out / "variant_ranking.csv", index=False
    )
    pd.DataFrame(fold_rows).to_csv(out / "fold_results.csv", index=False)
    pd.DataFrame(image_rows).to_csv(out / "per_image_metrics.csv", index=False)

    runtime_source = map_dir / "per_image_runtime.csv"
    runtime_rows = list(csv.DictReader(runtime_source.open(encoding="utf-8")))
    pd.DataFrame(runtime_rows).to_csv(out / "per_image_runtime.csv", index=False)
    map_hashes = {f"{item['id']}.png": _sha256(map_dir / f"{item['id']}.png") for item in selection}
    (out / "map_hashes.json").write_text(json.dumps(map_hashes, indent=2), encoding="utf-8")

    if any(len(first_repeat_predictions[name]) != len(selection) for name in VARIANTS):
        raise RuntimeError("first-repeat out-of-fold preview predictions are incomplete")
    rows = []
    for position in PREVIEW_POSITIONS:
        item = selection[position]
        rows.append([
            item["img"], item["gt"],
            first_repeat_predictions[VARIANTS[0]][position],
            first_repeat_predictions[VARIANTS[1]][position],
            forest_scores[position],
        ])
    preview_path = write_panel_grid(out / "best_method_preview.png", rows)
    manifest_path = _write_official_manifest(out)
    summary = {
        "stage": "16v-structured-forest",
        "role": "generation_2_exact_structured_patch_forest_replacement_falsification",
        "architecture_changed": False,
        "protected_split_used": False,
        "datasets": {
            "UDED_selection": {
                "n_images": len(selection),
                "role": "development repeated threshold-CV; fixed forest has no UDED fitting",
                "repeats": args.repeats, "folds": args.folds,
            },
            "BSDS500_train": {
                "role": "author-model training provenance only",
                "candidate_retrained_by_repository": False,
            },
            "BSDS500_validation": {
                "role": "development official attachment; excluded from author-model fitting",
                "status": "pending controller attachment",
            },
        },
        "mechanism": {
            "description": "author Structured Edge forest predicts a structured 16x16 edge mask from each 32x32 patch",
            "implementation_fidelity": "exact pinned author inference with shipped modelBsds and author edgesEval NMS setting",
            "training_class": "non-neural supervised structured random forest",
            "distinction_from_stage14n": "full structured labels, author channels, self-similarity, eight deep trees, mask sharpening and patch aggregation; not the shallow dense pixel forest",
            "provenance": provenance,
            "candidate_parameters": "immutable author model; nms=1 as in edgesEval; nThreads=1 runtime-only determinism",
        },
        "promotion_rule": (
            "Conjunctive: UDED aggregate F1 delta at least +0.005, precision and recall "
            "deltas each at least -0.003, mean paired fold-F1 delta at least +0.002, "
            "and at least 10/15 fold wins. The official attachment must complete and "
            "BSDS500-validation ODS/OIS/AP must each improve by at least +0.02 versus "
            "compact MFI. Exact provenance, synthetic bitwise repeatability, bounded "
            "maps, hashes, runtimes, and deterministic preview must all pass."
        ),
        "uded_gate": {"met": uded_gate, "deltas": deltas},
        "metrics": aggregate,
        "promotion_pending_official_bsds_val": True,
        "official_evaluation": {
            "manifest": str(manifest_path.relative_to(ROOT)).replace("\\", "/"),
            "required_before_promotion": True,
            "stage15a_caveat": "unmodified Windows matcher remains stochastic and reference-uncertified",
        },
        "visual_preview": {
            "file": preview_path.name,
            "selection": "fixed UDED-selection positions 1, 8, and 15",
            "columns": [
                "input", "ground_truth", "compact_MFI_out_of_fold_prediction",
                "structured_forest_out_of_fold_prediction", "structured_forest_soft_score",
            ],
            "use": "documentary only; not an optimization signal",
        },
        "files": [
            "summary.json", "variant_ranking.csv", "fold_results.csv",
            "per_image_metrics.csv", "per_image_runtime.csv", "map_hashes.json",
            "best_method_preview.png", "official_eval_manifest.json",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE16V_STRUCTURED_FOREST_COMPLETE", flush=True)
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
    parser.add_argument("--seed", type=int, default=20261009)
    parser.add_argument("--export-bsds", action="store_true")
    parser.add_argument("--image-dir")
    parser.add_argument("--output-dir")
    parser.add_argument("--split", default="val")
    args = parser.parse_args()
    if args.export_bsds:
        if not args.image_dir or not args.output_dir:
            parser.error("--export-bsds requires --image-dir and --output-dir")
        return export_bsds(args)
    return run_experiment(args)


if __name__ == "__main__":
    raise SystemExit(main())
