from __future__ import annotations

"""Stage 15a: reproduce the evaluator fixture and audit the matched protocol."""

from pathlib import Path
import csv
import hashlib
import json
import os
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy.io import loadmat
from skimage.io import imread

from evaluation.bsds_official.export_stage15a_baselines import baseline_score
from evaluation.bsds_official.run_official_bsds import (
    DEFAULT_CONFIG,
    MATLAB_WRAPPER_DIR,
    _ensure_benchmark_sources,
    _evaluate_one,
    _git_head,
    _load_json,
    _matlab_executable,
)
from src.bsds import _extract_boundaries


OUT = ROOT / "results" / "local_dev" / "stage15a_protocol_audit"
REFERENCE_TOLERANCE = 1e-4
FIXED_PREVIEW_POSITIONS = (0, 49, 99)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reference_reproduction(cfg: dict, bsds_root: Path, benchmark_dir: Path) -> dict:
    bench_root = bsds_root / "bench"
    data_dir = bench_root / "data"
    reference_cfg = dict(cfg)
    reference_cfg.update({"nthresh": 5, "max_dist": 0.0075, "thinpb": True})
    result = _evaluate_one(
        _matlab_executable(cfg),
        benchmark_dir=benchmark_dir,
        image_dir=data_dir / "images",
        gt_dir=data_dir / "groundTruth",
        pred_dir=data_dir / "png",
        out_dir=OUT / "reference_eval",
        cfg=reference_cfg,
    )
    expected_values = np.loadtxt(data_dir / "test_2" / "eval_bdry.txt").reshape(-1)
    expected = {
        "ODS": float(expected_values[3]),
        "OIS": float(expected_values[6]),
        "AP": float(expected_values[7]),
    }
    observed = {key: float(result[key]) for key in expected}
    absolute_error = {key: abs(observed[key] - expected[key]) for key in expected}
    passed = all(value <= REFERENCE_TOLERANCE for value in absolute_error.values())
    return {
        "fixture": "pinned BSDS500 bench/data PNG boundary example",
        "n_images": 5,
        "nthresh": 5,
        "expected": expected,
        "observed": observed,
        "absolute_error": absolute_error,
        "tolerance": REFERENCE_TOLERANCE,
        "passed": passed,
        "meaning": (
            "Exact-path compatibility check against outputs shipped with the pinned "
            "benchmark; it is not a detector result or a BSDS500 split score."
        ),
        "matlab_processes": int(result.get("matlab_evaluate_processes", 1)),
    }


def _dataset_audit(image_dir: Path, gt_dir: Path) -> dict:
    image_paths = sorted(image_dir.glob("*.jpg"))
    gt_paths = sorted(gt_dir.glob("*.mat"))
    if len(image_paths) != 100 or len(gt_paths) != 100:
        raise RuntimeError(
            f"expected 100 BSDS validation pairs, got {len(image_paths)} images and "
            f"{len(gt_paths)} ground-truth files"
        )
    image_ids = [path.stem for path in image_paths]
    if image_ids != [path.stem for path in gt_paths]:
        raise RuntimeError("BSDS validation image/ground-truth IDs do not match")

    annotation_counts = []
    dimension_mismatches = []
    for image_path, gt_path in zip(image_paths, gt_paths):
        shape = imread(image_path).shape[:2]
        boundaries = _extract_boundaries(loadmat(gt_path))
        annotation_counts.append(len(boundaries))
        if not boundaries or any(np.asarray(item).shape != shape for item in boundaries):
            dimension_mismatches.append(image_path.stem)
    return {
        "n_images": len(image_paths),
        "native_resolution_preserved": True,
        "image_gt_ids_match": True,
        "annotation_count_min": int(min(annotation_counts)),
        "annotation_count_max": int(max(annotation_counts)),
        "annotation_count_mean": float(np.mean(annotation_counts)),
        "dimension_mismatches": dimension_mismatches,
        "all_annotations_available": bool(min(annotation_counts) > 1),
    }


def _find_incumbent_cache(image_ids: list[str]) -> Path | None:
    base = ROOT / "automation" / "runtime" / "official_eval_cache" / "incumbent" / "val"
    if not base.exists():
        return None
    for candidate in sorted((path for path in base.iterdir() if path.is_dir()), reverse=True):
        if all((candidate / f"{image_id}.png").exists() for image_id in image_ids):
            return candidate
    return None


def _write_preview(image_dir: Path, gt_dir: Path) -> dict:
    paths = sorted(image_dir.glob("*.jpg"))
    selected = [paths[index] for index in FIXED_PREVIEW_POSITIONS]
    ids = [path.stem for path in selected]
    incumbent_cache = _find_incumbent_cache(ids)

    fig, axes = plt.subplots(len(selected), 5, figsize=(15, 9), squeeze=False)
    for row, image_path in enumerate(selected):
        image = imread(image_path)
        boundaries = _extract_boundaries(loadmat(gt_dir / f"{image_path.stem}.mat"))
        agreement = np.mean(np.stack(boundaries, axis=0), axis=0)
        canny = baseline_score(image, "canny")
        scharr = baseline_score(image, "scharr")
        if incumbent_cache is None:
            incumbent = np.zeros_like(scharr)
        else:
            incumbent = np.asarray(
                Image.open(incumbent_cache / f"{image_path.stem}.png"), dtype=float
            ) / 255.0
        panels = (image, agreement, canny, scharr, incumbent)
        titles = (
            "Input",
            "Mean annotator boundary",
            "Fixed Canny",
            "Repository Scharr+NMS",
            "Retained incumbent",
        )
        for column, (panel, title) in enumerate(zip(panels, titles)):
            ax = axes[row, column]
            ax.imshow(panel, cmap=None if column == 0 else "gray", vmin=0 if column else None, vmax=1 if column else None)
            ax.set_title(title if row == 0 else image_path.stem, fontsize=9)
            ax.axis("off")
    fig.suptitle(
        "Stage 15a fixed validation positions 1, 50, 100; qualitative audit only",
        fontsize=12,
    )
    fig.tight_layout()
    preview = OUT / "best_method_preview.png"
    fig.savefig(preview, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return {
        "path": str(preview.relative_to(ROOT)).replace("\\", "/"),
        "selection": "sorted BSDS500-validation positions 1, 50, and 100, preregistered",
        "image_ids": ids,
        "panel_order": [
            "input",
            "mean annotator boundary (display only)",
            "fixed Canny",
            "repository Scharr+NMS",
            "retained incumbent",
        ],
        "incumbent_cache_available": incumbent_cache is not None,
        "optimization_use": "none; documentary qualitative artifact",
    }


def _write_protocol_matrix() -> None:
    rows = [
        {
            "protocol": "Stage15 official BSDS500 validation",
            "split_role": "development",
            "ground_truth": "all human boundary annotations",
            "matching": "Berkeley correspondPixels one-to-one",
            "thresholds": "99 fixed points in (0,1)",
            "max_dist": "0.0075 image diagonal",
            "thinning": "enabled after thresholding",
            "resolution": "native",
            "compatibility": "matched official Berkeley-family protocol",
        },
        {
            "protocol": "Pinned five-image fixture",
            "split_role": "evaluator unit/reference fixture",
            "ground_truth": "all fixture annotations",
            "matching": "same pinned correspondPixels",
            "thresholds": "5, as shipped example",
            "max_dist": "0.0075 image diagonal",
            "thinning": "enabled",
            "resolution": "native fixture",
            "compatibility": "implementation reproduction only; not a benchmark score",
        },
        {
            "protocol": "Stage13 BSDS proxy",
            "split_role": "historical document-only test diagnostic",
            "ground_truth": "consensus-collapsed",
            "matching": "local tolerant dilation",
            "thresholds": "project proxy grid",
            "max_dist": "different local tolerance",
            "thinning": "not official accumulation",
            "resolution": "max side 256",
            "compatibility": "incompatible with official ODS/OIS/AP",
        },
        {
            "protocol": "UDED selection repeated CV",
            "split_role": "development",
            "ground_truth": "dataset single edge target",
            "matching": "repository tolerant metric",
            "thresholds": "fold-fitted project grid",
            "max_dist": "repository UDED tolerance",
            "thinning": "detector-specific",
            "resolution": "max side 256",
            "compatibility": "distinct development axis; do not compare headline values",
        },
    ]
    path = OUT / "protocol_matrix.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    # Keep MATLAB preferences inside the experiment workspace. This avoids
    # dependence on an interactive user's profile without repurposing HOME.
    matlab_prefdir = OUT / "matlab_preferences"
    matlab_prefdir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MATLAB_PREFDIR", str(matlab_prefdir.resolve()))
    cfg = _load_json(DEFAULT_CONFIG)
    bsds_root, benchmark_dir = _ensure_benchmark_sources(cfg, "val")
    image_dir = bsds_root / "BSDS500" / "data" / "images" / "val"
    gt_dir = bsds_root / "BSDS500" / "data" / "groundTruth" / "val"

    reference = _reference_reproduction(cfg, bsds_root, benchmark_dir)
    dataset = _dataset_audit(image_dir, gt_dir)
    preview = _write_preview(image_dir, gt_dir)
    _write_protocol_matrix()

    source_eval = benchmark_dir / "evaluation_bdry_image.m"
    source_collect = benchmark_dir / "collect_eval_bdry.m"
    mex = benchmark_dir / f"correspondPixels.mexw64"
    manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [
            {
                "name": "stage15a_fixed_canny",
                "export": {
                    "script": "evaluation/bsds_official/export_stage15a_baselines.py",
                    "args": [
                        "--image-dir", "{image_dir}", "--output-dir", "{output_dir}",
                        "--split", "{split}", "--method", "canny",
                    ],
                },
            },
            {
                "name": "stage15a_repository_scharr_nms",
                "export": {
                    "script": "evaluation/bsds_official/export_stage15a_baselines.py",
                    "args": [
                        "--image-dir", "{image_dir}", "--output-dir", "{output_dir}",
                        "--split", "{split}", "--method", "scharr",
                    ],
                },
            },
        ],
    }
    (OUT / "official_eval_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )

    summary = {
        "stage": "15a-evaluator-and-protocol-audit",
        "role": "reproduction_protocol_audit",
        "architecture_changed": False,
        "protected_split_used": False,
        "reference_reproduction": reference,
        "dataset_audit": dataset,
        "evaluator": {
            "bsds500_commit": _git_head(bsds_root),
            "configured_bsds500_commit": cfg["sources"]["bsds500"]["commit"],
            "pdollar_edges_commit": _git_head(
                ROOT / cfg["sources"]["pdollar_edges"]["vendor_dir"]
            ),
            "configured_pdollar_edges_commit": cfg["sources"]["pdollar_edges"]["commit"],
            "nthresh": cfg["nthresh"],
            "max_dist": cfg["max_dist"],
            "thinpb": cfg["thinpb"],
            "soft_map_convention": "uint8 PNG divided by 255 by pinned evaluator",
            "source_hashes_sha256": {
                "evaluation_bdry_image.m": _sha256(source_eval),
                "collect_eval_bdry.m": _sha256(source_collect),
                "correspondPixels.mexw64": _sha256(mex),
                "evaluate_bsds_official.m": _sha256(
                    MATLAB_WRAPPER_DIR / "evaluate_bsds_official.m"
                ),
            },
            "matlab_compatibility": (
                "run-local syntax-only mirror plus isolated resumable native matching; "
                "pinned vendor sources remain unchanged"
            ),
        },
        "baselines": {
            "canny": "strictly untrained fixed binary operating-point audit",
            "scharr": "strictly untrained ungated incumbent localizer",
            "incumbent": "unchanged compact Choquet-gated Scharr+NMS controller",
        },
        "preview": preview,
        "official_bsds500_validation": "pending controller attachment",
        "decision_rule": (
            "Stage 15a establishes evaluator fidelity and measurement floors only; no "
            "method is promoted into MFI and no parameter is tuned from these results."
        ),
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print("STAGE15A_PROTOCOL_AUDIT_READY", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
