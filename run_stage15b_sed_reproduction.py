from __future__ import annotations

"""Stage 15b: exact author-code SED reproduction on BSDS500 validation."""

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from scipy.io import loadmat
from skimage.io import imread

from evaluation.bsds_official.export_stage15b_sed import (
    AUTHOR_COMMIT,
    AUTHOR_REPOSITORY,
    export_sed_maps,
)
from evaluation.bsds_official.run_official_bsds import (
    DEFAULT_CONFIG,
    _ensure_benchmark_sources,
    _incumbent_predictions,
    _load_json,
)
from src.bsds import _extract_boundaries


EXPERIMENT_ID = "stage15b_sed_exact_reproduction"
OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
PREDICTIONS = OUT / "predictions"
FIXED_PREVIEW_POSITIONS = (0, 49, 99)


def _write_preview(
    image_dir: Path,
    gt_dir: Path,
    incumbent_dir: Path,
    candidate_dir: Path,
) -> dict:
    image_paths = sorted(image_dir.glob("*.jpg"))
    selected = [image_paths[index] for index in FIXED_PREVIEW_POSITIONS]
    image_ids = [path.stem for path in selected]
    fig, axes = plt.subplots(len(selected), 4, figsize=(12, 9), squeeze=False)
    titles = (
        "Input",
        "Mean annotator boundary",
        "MFI incumbent",
        "Exact author SED",
    )
    for row, image_path in enumerate(selected):
        image = imread(image_path)
        boundaries = _extract_boundaries(loadmat(gt_dir / f"{image_path.stem}.mat"))
        agreement = np.mean(np.stack(boundaries, axis=0), axis=0)
        incumbent = np.asarray(
            Image.open(incumbent_dir / f"{image_path.stem}.png"), dtype=float
        ) / 255.0
        candidate = np.asarray(
            Image.open(candidate_dir / f"{image_path.stem}.png"), dtype=float
        ) / 255.0
        panels = (image, agreement, incumbent, candidate)
        for column, (panel, title) in enumerate(zip(panels, titles)):
            axis = axes[row, column]
            axis.imshow(
                panel,
                cmap=None if column == 0 else "gray",
                vmin=None if column == 0 else 0,
                vmax=None if column == 0 else 1,
            )
            axis.set_title(title if row == 0 else image_path.stem, fontsize=9)
            axis.axis("off")
    fig.suptitle(
        "Stage 15b fixed BSDS500-val positions 1, 50, 100; qualitative only",
        fontsize=12,
    )
    fig.tight_layout()
    preview = OUT / "best_method_preview.png"
    fig.savefig(preview, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return {
        "path": str(preview.relative_to(ROOT)).replace("\\", "/"),
        "selection": (
            "sorted BSDS500-validation positions 1, 50, and 100, "
            "preregistered before map generation"
        ),
        "image_ids": image_ids,
        "panel_order": [
            "input",
            "mean annotator boundary (display only)",
            "retained MFI incumbent",
            "exact author-code SED candidate baseline",
        ],
        "optimization_use": "none; documentary qualitative artifact",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = _load_json(DEFAULT_CONFIG)
    bsds_root, _benchmark_dir = _ensure_benchmark_sources(cfg, "val")
    image_dir = bsds_root / "BSDS500" / "data" / "images" / "val"
    gt_dir = bsds_root / "BSDS500" / "data" / "groundTruth" / "val"
    image_paths = sorted(image_dir.glob("*.jpg"))
    if len(image_paths) != 100:
        raise RuntimeError(f"expected 100 BSDS500-val images, found {len(image_paths)}")

    export = export_sed_maps(image_dir, PREDICTIONS, split="val")
    incumbent_dir, incumbent_provenance = _incumbent_predictions(
        cfg,
        image_dir=image_dir,
        gt_dir=gt_dir,
        split="val",
    )
    preview = _write_preview(image_dir, gt_dir, incumbent_dir, PREDICTIONS)

    official_manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [
            {
                "name": "stage15b_exact_author_sed",
                "prediction_dir": str(PREDICTIONS.relative_to(ROOT)).replace("\\", "/"),
                "exporter": "evaluation/bsds_official/export_stage15b_sed.py",
                "author_commit": AUTHOR_COMMIT,
            }
        ],
    }
    (OUT / "official_eval_manifest.json").write_text(
        json.dumps(official_manifest, indent=2), encoding="utf-8"
    )

    summary = {
        "stage": "15b-sed-exact-reproduction",
        "role": "matched_protocol_reproduction",
        "architecture_changed": False,
        "question": (
            "What performance does the published, strictly untrained SED full model "
            "obtain when its exact author MATLAB detector is run at native resolution "
            "and scored on BSDS500 validation through the repository official path?"
        ),
        "implementation": {
            "fidelity": (
                "exact unmodified author MATLAB detector; repository adapter only "
                "provides batch I/O, validation, and fixed 8-bit serialization"
            ),
            "training_class": "strictly untrained; fixed author parameters",
            "repository": AUTHOR_REPOSITORY,
            "commit": AUTHOR_COMMIT,
            "source_license": (
                "no explicit license file found; fetched into ignored local vendor "
                "storage and not redistributed"
            ),
            "published_variant": "full colour SED model including author NMS",
            "parameter_policy": (
                "all detector values remain embedded author defaults; no parameter "
                "selection or post-result tuning is permitted"
            ),
            "author_code_note": (
                "the MATLAB implementation generated the manuscript F-measures; "
                "the separate C++ implementation was reported as timing-only"
            ),
        },
        "dataset": {
            "name": "BSDS500",
            "split": "validation",
            "role": "development/matched-protocol reproduction",
            "n_images": len(image_paths),
            "protected_split_used": False,
            "native_resolution": True,
            "ground_truth_use_by_detector": False,
        },
        "literature_report_separate_from_repository_evaluation": {
            "split": "BSDS500 test (200 images)",
            "colour_ODS": 0.71,
            "colour_OIS": 0.74,
            "colour_AP": 0.74,
            "source": "Akbarinia and Parraga, IJCV 2018, Table 1",
            "comparison_status": (
                "documentary only; not treated as our validation result or as "
                "reference reproduction"
            ),
        },
        "candidate_export": export,
        "per_image_outputs": str(PREDICTIONS.relative_to(ROOT)).replace("\\", "/"),
        "incumbent_export": incumbent_provenance,
        "preview": preview,
        "official_evaluation": {
            "status": "pending controller attachment",
            "protocol": (
                "all annotations, 99 thresholds, maxDist=0.0075, thinning, "
                "native resolution"
            ),
            "stage15a_caveat": (
                "the unmodified Windows matcher remains stochastic and reference-"
                "uncertified; the fixed-seed diagnostic matcher is forbidden"
            ),
            "manifest": str(
                (OUT / "official_eval_manifest.json").relative_to(ROOT)
            ).replace("\\", "/"),
        },
        "decision_semantics": (
            "reproduction only: retain SED as a verified baseline if execution and "
            "scoring complete; do not modify MFI architecture or tune SED from the result"
        ),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE15B_SED_EXACT_REPRODUCTION_COMPLETE")
    print(OUT / "summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
