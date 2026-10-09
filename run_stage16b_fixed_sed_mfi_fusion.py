from __future__ import annotations

"""Stage 16b: fixed equal-weight fusion of compact MFI and exact SED.

The experiment contains no learned fusion weight or router. UDED thresholds
and compact memberships are fit inside the existing repeated outer folds.
BSDS500 validation uses the unchanged official attachment.
"""

from collections import defaultdict
from pathlib import Path
import argparse
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
from evaluation.bsds_official.export_stage15b_sed import (
    AUTHOR_COMMIT,
    AUTHOR_REPOSITORY,
    DEFAULT_MATLAB,
    MATLAB_WRAPPER_DIR,
    ensure_author_source,
    export_sed_maps,
)
from evaluation.bsds_official.run_official_bsds import (
    DEFAULT_CONFIG,
    _incumbent_predictions,
    _load_json,
)
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


EXPERIMENT_ID = "stage16b_fixed_sed_mfi_fusion"
DEFAULT_OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
FUSION_WEIGHT = 0.5
VARIANTS = ("compact_mfi", "exact_sed", "fixed_equal_mean")
FROZEN_BSDS_SED = (
    ROOT / "results" / "local_dev" / "stage15b_sed_exact_reproduction" / "predictions"
)
PREVIEW_POSITIONS = (0, 7, 14)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _matlab_quote(value: Path | str) -> str:
    return str(value).replace("'", "''").replace("\\", "/")


def _to_rgb_uint8(image: np.ndarray) -> np.ndarray:
    x = np.asarray(image)
    if x.ndim == 2:
        x = np.repeat(x[..., None], 3, axis=2)
    if x.ndim != 3 or x.shape[2] < 3:
        raise ValueError(f"SED input must be grayscale or RGB, got {x.shape}")
    y = np.asarray(x[..., :3], dtype=np.float64)
    if np.nanmax(y) <= 1.0:
        y *= 255.0
    if not np.all(np.isfinite(y)):
        raise RuntimeError("non-finite SED input")
    return np.rint(np.clip(y, 0.0, 255.0)).astype(np.uint8)


def _save_inputs(items: list[dict], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for item in items:
        Image.fromarray(_to_rgb_uint8(item["img"]), mode="RGB").save(
            directory / f"{item['id']}.png"
        )


def _run_uded_sed(input_dir: Path, output_dir: Path, timeout_minutes: float) -> dict:
    author_source = ensure_author_source()
    output_dir.mkdir(parents=True, exist_ok=True)
    runtime_csv = output_dir / "per_image_runtime.csv"
    matlab = Path(os.environ.get("MATLAB_EXE", str(DEFAULT_MATLAB))).resolve()
    if not matlab.exists():
        raise FileNotFoundError(f"MATLAB executable not found: {matlab}")
    prefdir = output_dir / "matlab_preferences"
    prefdir.mkdir(parents=True, exist_ok=True)
    expression = (
        f"addpath('{_matlab_quote(MATLAB_WRAPPER_DIR)}');"
        "stage16b_export_sed_png("
        f"'{_matlab_quote(author_source)}',"
        f"'{_matlab_quote(input_dir)}',"
        f"'{_matlab_quote(output_dir)}',"
        f"'{_matlab_quote(runtime_csv)}');"
    )
    environment = os.environ.copy()
    environment["MATLAB_PREFDIR"] = str(prefdir)
    completed = subprocess.run(
        [str(matlab), "-batch", expression],
        cwd=ROOT,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=float(timeout_minutes) * 60.0,
        check=False,
    )
    if completed.returncode:
        tail = "\n".join((completed.stdout or "").splitlines()[-80:])
        raise RuntimeError(f"SED MATLAB export failed ({completed.returncode})\n{tail}")

    hashes: dict[str, str] = {}
    for input_path in sorted(input_dir.glob("*.png")):
        output_path = output_dir / input_path.name
        if not output_path.exists():
            raise RuntimeError(f"missing SED output {output_path}")
        with Image.open(input_path) as source, Image.open(output_path) as score:
            if score.mode != "L" or score.size != source.size:
                raise RuntimeError(f"invalid SED map contract for {output_path}")
        hashes[input_path.stem] = _sha256(output_path)
    (output_dir / "map_hashes.json").write_text(
        json.dumps(hashes, indent=2), encoding="utf-8"
    )
    return {
        "author_repository": AUTHOR_REPOSITORY,
        "author_commit": AUTHOR_COMMIT,
        "implementation_fidelity": "unchanged exact author detector; PNG batch-I/O adapter only",
        "n_maps": len(hashes),
        "map_hashes": "uded_sed_maps/map_hashes.json",
        "runtime_csv": "uded_sed_maps/per_image_runtime.csv",
        "stdout_tail": "\n".join((completed.stdout or "").splitlines()[-20:]),
    }


def _load_soft_maps(directory: Path, items: list[dict]) -> dict[str, np.ndarray]:
    maps: dict[str, np.ndarray] = {}
    for item in items:
        path = directory / f"{item['id']}.png"
        if not path.exists():
            raise RuntimeError(f"missing map {path}")
        score = np.asarray(Image.open(path).convert("L"), dtype=np.float32) / 255.0
        if score.shape != np.asarray(item["gt"]).shape:
            raise RuntimeError(f"map shape mismatch for {item['id']}")
        maps[str(item["id"])] = score
    return maps


def _ordered_compact(bank: list[dict]) -> list[dict]:
    selected = _filter_bank(bank, COMPACT_FEATURES)
    by_feature = {str(row["feature"]): row for row in selected}
    return [by_feature[name] for name in COMPACT_FEATURES]


def _incumbent_scores(items: list[dict], names: list[str], compact: list[dict]) -> list[np.ndarray]:
    scores = []
    for item in items:
        memberships, weights = membership_stack(item, names, compact, "edge")
        context = distorted_choquet(memberships, weights, GAMMA)
        raw = context_gate(item["scharr"], context, STRENGTH, FLOOR)
        scores.append(np.rint(np.clip(raw, 0.0, 1.0) * 255.0).astype(np.float32) / 255.0)
    return scores


def _variant_scores(
    items: list[dict],
    names: list[str],
    compact: list[dict],
    sed_maps: dict[str, np.ndarray],
) -> dict[str, list[np.ndarray]]:
    incumbent = _incumbent_scores(items, names, compact)
    sed = [sed_maps[str(item["id"])] for item in items]
    mean = [
        ((1.0 - FUSION_WEIGHT) * a + FUSION_WEIGHT * b).astype(np.float32)
        for a, b in zip(incumbent, sed)
    ]
    return {"compact_mfi": incumbent, "exact_sed": sed, "fixed_equal_mean": mean}


def _write_manifest(out: Path) -> Path:
    manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [
            {
                "name": "stage16b_fixed_equal_mean",
                "export": {
                    "script": "run_stage16b_fixed_sed_mfi_fusion.py",
                    "args": [
                        "--export-bsds",
                        "--image-dir", "{image_dir}",
                        "--gt-dir", "{gt_dir}",
                        "--output-dir", "{output_dir}",
                        "--split", "{split}",
                    ],
                    "timeout_minutes": 240,
                },
            },
            {
                "name": "stage16b_exact_sed_constituent",
                "prediction_dir": str(FROZEN_BSDS_SED.relative_to(ROOT)).replace("\\", "/"),
            },
        ],
    }
    path = out / "official_eval_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def _ensure_frozen_bsds_sed(image_dir: Path, split: str) -> Path:
    expected = {path.stem for path in image_dir.glob("*.jpg")}
    hash_path = FROZEN_BSDS_SED / "map_hashes.json"

    def verified() -> bool:
        present = {path.stem for path in FROZEN_BSDS_SED.glob("*.png")}
        if expected != present or not hash_path.exists():
            return False
        registered = json.loads(hash_path.read_text(encoding="utf-8"))
        return set(registered) == expected and all(
            _sha256(FROZEN_BSDS_SED / f"{image_id}.png") == registered[image_id]
            for image_id in sorted(expected)
        )

    if not verified():
        export_sed_maps(image_dir, FROZEN_BSDS_SED, split=split)
    if not verified():
        raise RuntimeError("frozen Stage-15b SED map set failed completeness/hash verification")
    return FROZEN_BSDS_SED


def export_bsds(args: argparse.Namespace) -> int:
    image_dir = Path(args.image_dir).resolve()
    gt_dir = Path(args.gt_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    cfg = _load_json(DEFAULT_CONFIG)
    incumbent_dir, incumbent_meta = _incumbent_predictions(
        cfg, image_dir=image_dir, gt_dir=gt_dir, split=args.split
    )
    sed_dir = _ensure_frozen_bsds_sed(image_dir, args.split)
    hashes: dict[str, str] = {}
    for image_path in sorted(image_dir.glob("*.jpg")):
        incumbent = np.asarray(
            Image.open(incumbent_dir / f"{image_path.stem}.png").convert("L"), dtype=np.float32
        ) / 255.0
        sed = np.asarray(
            Image.open(sed_dir / f"{image_path.stem}.png").convert("L"), dtype=np.float32
        ) / 255.0
        if incumbent.shape != sed.shape:
            raise RuntimeError(f"constituent shape mismatch for {image_path.stem}")
        fused = np.rint(
            np.clip((1.0 - FUSION_WEIGHT) * incumbent + FUSION_WEIGHT * sed, 0.0, 1.0)
            * 255.0
        ).astype(np.uint8)
        output = output_dir / f"{image_path.stem}.png"
        Image.fromarray(fused, mode="L").save(output)
        hashes[image_path.stem] = _sha256(output)
    metadata = {
        "method": "fixed equal arithmetic mean of compact MFI and exact author SED",
        "split": args.split,
        "bsds_ground_truth_read": False,
        "native_resolution": True,
        "fusion_weight_sed": FUSION_WEIGHT,
        "incumbent": incumbent_meta,
        "sed_source": str(sed_dir.relative_to(ROOT)).replace("\\", "/"),
        "sed_author_commit": AUTHOR_COMMIT,
        "n_maps": len(hashes),
        "map_hashes": hashes,
        "output": "8-bit soft PNG without candidate-specific normalization",
    }
    (output_dir / "export_manifest.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return 0


def run_experiment(args: argparse.Namespace) -> int:
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    raw = resize_items(load_uded(ensure_uded(Path(args.uded_root))), args.max_side)
    raw_selection = raw[0::2]
    selection, names = prepare(raw_selection)
    if len(selection) != 15:
        raise RuntimeError(f"expected 15 UDED selection images, found {len(selection)}")

    sed_input_dir = out / "uded_sed_inputs"
    sed_output_dir = out / "uded_sed_maps"
    _save_inputs(raw_selection, sed_input_dir)
    sed_export = _run_uded_sed(sed_input_dir, sed_output_dir, args.sed_timeout_minutes)
    sed_maps = _load_soft_maps(sed_output_dir, selection)

    splits = _make_repeated_folds(len(selection), args.folds, args.repeats, args.seed)
    counts: dict[str, list] = defaultdict(list)
    fold_f1: dict[str, list[float]] = defaultdict(list)
    thresholds: dict[str, list[float]] = defaultdict(list)
    fold_rows: list[dict] = []
    image_rows: list[dict] = []
    first_repeat_predictions: dict[str, dict[int, np.ndarray]] = {
        name: {} for name in VARIANTS
    }

    for split_no, (repeat, fold, tr_idx, va_idx) in enumerate(splits, start=1):
        train = [selection[index] for index in tr_idx]
        valid = [selection[index] for index in va_idx]
        positive, _negative = learn_banks(
            train,
            names,
            args.seed + 10000 * repeat + fold,
            args.max_positive,
            args.max_negative,
            args.max_abs_corr,
        )
        compact = _ordered_compact(positive)
        train_scores = _variant_scores(train, names, compact, sed_maps)
        valid_scores = _variant_scores(valid, names, compact, sed_maps)
        print(
            f"STAGE16B_SPLIT {split_no:02d}/{len(splits)} "
            f"repeat={repeat + 1} fold={fold + 1}",
            flush=True,
        )
        for variant in VARIANTS:
            threshold = float(
                selection_metric(train_scores[variant], train, args.thresholds)["threshold"]
            )
            metric, event_counts, per_image = fixed_eval(
                valid_scores[variant], valid, threshold
            )
            counts[variant].extend(event_counts)
            fold_f1[variant].append(float(metric["F1"]))
            thresholds[variant].append(threshold)
            fold_rows.append(
                {
                    "repeat": repeat + 1,
                    "fold": fold + 1,
                    "variant": variant,
                    "train_threshold": threshold,
                    **metric,
                }
            )
            image_rows.extend(
                {
                    "repeat": repeat + 1,
                    "fold": fold + 1,
                    "variant": variant,
                    **row,
                }
                for row in per_image
            )
            if repeat == 0:
                for global_index, score in zip(va_idx, valid_scores[variant]):
                    first_repeat_predictions[variant][int(global_index)] = score >= threshold

    aggregate = {name: aggregate_counts(counts[name]) for name in VARIANTS}
    candidate = VARIANTS[-1]
    deltas = {}
    for baseline in VARIANTS[:-1]:
        candidate_folds = np.asarray(fold_f1[candidate], dtype=np.float64)
        baseline_folds = np.asarray(fold_f1[baseline], dtype=np.float64)
        deltas[baseline] = {
            "aggregate_F1": float(aggregate[candidate]["F1"] - aggregate[baseline]["F1"]),
            "aggregate_precision": float(
                aggregate[candidate]["precision"] - aggregate[baseline]["precision"]
            ),
            "mean_fold_F1": float(np.mean(candidate_folds - baseline_folds)),
            "fold_wins": int(np.sum(candidate_folds > baseline_folds)),
        }
    uded_gate = bool(
        all(deltas[name]["aggregate_F1"] >= 0.002 for name in VARIANTS[:-1])
        and aggregate[candidate]["precision"]
        >= max(aggregate[name]["precision"] for name in VARIANTS[:-1]) - 0.002
        and all(deltas[name]["mean_fold_F1"] >= 0.0 for name in VARIANTS[:-1])
        and all(deltas[name]["fold_wins"] >= 9 for name in VARIANTS[:-1])
    )

    ranking = []
    for variant in VARIANTS:
        values = np.asarray(fold_f1[variant], dtype=np.float64)
        ranking.append(
            {
                "variant": variant,
                "cv_precision": aggregate[variant]["precision"],
                "cv_recall": aggregate[variant]["recall"],
                "cv_F1": aggregate[variant]["F1"],
                "mean_fold_F1": float(np.mean(values)),
                "std_fold_F1": float(np.std(values)),
                "threshold_mean": float(np.mean(thresholds[variant])),
                "threshold_std": float(np.std(thresholds[variant])),
            }
        )
    pd.DataFrame(ranking).sort_values("cv_F1", ascending=False).to_csv(
        out / "variant_ranking.csv", index=False
    )
    pd.DataFrame(fold_rows).to_csv(out / "fold_results.csv", index=False)
    pd.DataFrame(image_rows).to_csv(out / "per_image_metrics.csv", index=False)

    if any(
        len(first_repeat_predictions[name]) != len(selection) for name in VARIANTS
    ):
        raise RuntimeError("first-repeat out-of-fold preview predictions are incomplete")
    rows = []
    for position in PREVIEW_POSITIONS:
        item = selection[position]
        rows.append(
            [
                item["img"],
                item["gt"],
                first_repeat_predictions["compact_mfi"][position],
                first_repeat_predictions["exact_sed"][position],
                first_repeat_predictions["fixed_equal_mean"][position],
            ]
        )
    preview_path = write_panel_grid(out / "best_method_preview.png", rows)
    manifest_path = _write_manifest(out)
    summary = {
        "stage": "16b-fixed-sed-mfi-fusion",
        "role": "generation_2_bounded_falsification",
        "architecture_changed": False,
        "protected_split_used": False,
        "datasets": {
            "UDED_selection": {
                "n_images": len(selection),
                "role": "development repeated leakage-free CV",
                "repeats": args.repeats,
                "folds": args.folds,
            },
            "BSDS500_validation": {
                "role": "development official attachment",
                "status": "pending controller attachment",
            },
        },
        "mechanism": {
            "description": "equal arithmetic mean of serialized compact-MFI and exact-author-SED soft maps",
            "formula": "0.5 * compact_MFI + 0.5 * exact_SED",
            "weight_selection": "fixed before result inspection; no search, fitting, or router",
            "constituent_localization": "each constituent retains its own fixed localization/NMS path",
            "sed": sed_export,
        },
        "promotion_rule": (
            "Conjunctive: on UDED the fusion must exceed each constituent by at least "
            "+0.002 aggregate F1, have precision no more than 0.002 below the higher "
            "constituent precision, have nonnegative mean paired fold-F1 delta and at "
            "least 9/15 fold wins against each constituent. The official attachment "
            "must complete, and on BSDS500 validation fusion ODS must exceed the better "
            "constituent by at least +0.002 while OIS and AP are each no lower than the "
            "better constituent. All conditions are required."
        ),
        "uded_gate": {"met": uded_gate, "deltas": deltas},
        "metrics": aggregate,
        "promotion_pending_official_bsds_val": True,
        "official_evaluation": {
            "manifest": str(manifest_path.relative_to(ROOT)).replace("\\", "/"),
            "required_before_promotion": True,
            "stage15a_caveat": (
                "the unmodified Windows matcher remains stochastic and reference-uncertified; "
                "the fixed-seed diagnostic matcher is forbidden"
            ),
        },
        "visual_preview": {
            "file": preview_path.name,
            "selection": "fixed UDED-selection positions 1, 8, and 15",
            "columns": [
                "input",
                "ground_truth",
                "compact_MFI_out_of_fold_prediction",
                "exact_SED_out_of_fold_prediction",
                "fixed_equal_mean_out_of_fold_prediction",
            ],
            "use": "documentary only; not an optimization signal",
        },
        "files": [
            "summary.json",
            "variant_ranking.csv",
            "fold_results.csv",
            "per_image_metrics.csv",
            "best_method_preview.png",
            "official_eval_manifest.json",
            "uded_sed_maps/map_hashes.json",
            "uded_sed_maps/per_image_runtime.csv",
        ],
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print("STAGE16B_FIXED_SED_MFI_FUSION_COMPLETE", flush=True)
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
    parser.add_argument("--sed-timeout-minutes", type=float, default=120)
    parser.add_argument("--export-bsds", action="store_true")
    parser.add_argument("--image-dir")
    parser.add_argument("--gt-dir")
    parser.add_argument("--output-dir")
    parser.add_argument("--split", default="val")
    args = parser.parse_args()
    if args.export_bsds:
        if not args.image_dir or not args.gt_dir or not args.output_dir:
            parser.error("--export-bsds requires --image-dir, --gt-dir, and --output-dir")
        return export_bsds(args)
    return run_experiment(args)


if __name__ == "__main__":
    raise SystemExit(main())
