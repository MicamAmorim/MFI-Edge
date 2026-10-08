from __future__ import annotations

"""Stage 15d: exact author-code EDPF reproduction on BSDS500 validation."""

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

from evaluation.bsds_official.export_stage15d_edpf import (
    AUTHOR_COMMIT,
    AUTHOR_REPOSITORY,
    OPENCV_COMMIT,
    OPENCV_TAG_OBJECT,
    export_edpf_maps,
)
from evaluation.bsds_official.run_official_bsds import (
    DEFAULT_CONFIG,
    _ensure_benchmark_sources,
    _incumbent_predictions,
    _load_json,
)
from src.bsds import _extract_boundaries


EXPERIMENT_ID = "stage15d_edpf_exact_reproduction"
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
    fig, axes = plt.subplots(3, 4, figsize=(12, 9), squeeze=False)
    titles = ("Input", "Mean annotator boundary", "MFI incumbent", "Exact EDPF")
    for row, image_path in enumerate(selected):
        boundaries = _extract_boundaries(loadmat(gt_dir / f"{image_path.stem}.mat"))
        agreement = np.mean(np.stack(boundaries, axis=0), axis=0)
        panels = (
            imread(image_path),
            agreement,
            np.asarray(Image.open(incumbent_dir / f"{image_path.stem}.png")) / 255.0,
            np.asarray(Image.open(candidate_dir / f"{image_path.stem}.png")) / 255.0,
        )
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
        "Stage 15d fixed BSDS500-val positions 1, 50, 100; qualitative only",
        fontsize=12,
    )
    fig.tight_layout()
    preview = OUT / "best_method_preview.png"
    fig.savefig(preview, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return {
        "path": str(preview.relative_to(ROOT)).replace("\\", "/"),
        "selection": "sorted BSDS500-validation positions 1, 50, and 100",
        "image_ids": [path.stem for path in selected],
        "panel_order": [
            "input",
            "mean annotator boundary (display only)",
            "retained MFI incumbent",
            "exact author-code EDPF baseline",
        ],
        "optimization_use": "none; documentary qualitative artifact",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = _load_json(DEFAULT_CONFIG)
    bsds_root, _ = _ensure_benchmark_sources(cfg, "val")
    image_dir = bsds_root / "BSDS500" / "data" / "images" / "val"
    gt_dir = bsds_root / "BSDS500" / "data" / "groundTruth" / "val"
    image_paths = sorted(image_dir.glob("*.jpg"))
    if len(image_paths) != 100:
        raise RuntimeError(f"expected 100 BSDS500-val images, found {len(image_paths)}")

    export = export_edpf_maps(image_dir, PREDICTIONS, split="val")
    incumbent_dir, incumbent_provenance = _incumbent_predictions(
        cfg, image_dir=image_dir, gt_dir=gt_dir, split="val"
    )
    preview = _write_preview(image_dir, gt_dir, incumbent_dir, PREDICTIONS)
    manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [
            {
                "name": "stage15d_exact_author_edpf",
                "prediction_dir": str(PREDICTIONS.relative_to(ROOT)).replace("\\", "/"),
                "exporter": "evaluation/bsds_official/export_stage15d_edpf.py",
                "author_commit": AUTHOR_COMMIT,
            }
        ],
    }
    manifest_path = OUT / "official_eval_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    summary = {
        "stage": "15d-edpf-exact-reproduction",
        "role": "matched_protocol_reproduction",
        "architecture_changed": False,
        "question": (
            "What performance does the exact strictly untrained author EDPF "
            "implementation obtain under the common BSDS500-validation path?"
        ),
        "implementation": {
            "fidelity": "exact unmodified author C++ detector; batch-I/O harness only",
            "training_class": "strictly untrained; fixed author implementation",
            "repository": AUTHOR_REPOSITORY,
            "commit": AUTHOR_COMMIT,
            "license": "MIT",
            "selected_variant": "grayscale EDPF(Mat)",
            "fixed_code_path": (
                "Prewitt ED with embedded thresholds 11/3 followed by author "
                "chain-level Helmholtz validation"
            ),
            "parameter_policy": "no parameter exposure, fitting, search, or tuning",
            "opencv_dependency": {
                "version": "3.4.20",
                "tag_object": OPENCV_TAG_OBJECT,
                "commit": OPENCV_COMMIT,
            },
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
            "binary_curve_caveat": (
                "native EDPF output has one nontrivial operating point; report "
                "ODS/OIS/AP but do not interpret AP as a dense confidence ranking"
            ),
            "stage15a_caveat": (
                "the unmodified Windows matcher remains stochastic and reference-"
                "uncertified; the fixed-seed diagnostic matcher is forbidden"
            ),
            "manifest": str(manifest_path.relative_to(ROOT)).replace("\\", "/"),
        },
        "stage14t_distinction": (
            "EDPF validates author ED chains; Stage 14t instead attenuated connected "
            "upper-level components and did not test this implementation"
        ),
        "decision_semantics": (
            "reproduction only; retain as a baseline if execution and scoring "
            "complete, without modifying MFI or tuning EDPF"
        ),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE15D_EDPF_EXACT_REPRODUCTION_COMPLETE")
    print(OUT / "summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
