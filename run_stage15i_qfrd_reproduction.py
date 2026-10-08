from __future__ import annotations

"""Stage 15i exact author-code QFrD reproduction on BSDS500 validation."""

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

from evaluation.bsds_official.export_stage15i_qfrd import AUTHOR_COMMIT, export_qfrd_maps
from evaluation.bsds_official.run_official_bsds import DEFAULT_CONFIG, _ensure_benchmark_sources, _incumbent_predictions, _load_json
from src.bsds import _extract_boundaries

EXPERIMENT_ID = "stage15i_qfrd_exact_reproduction"
OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
PREDICTIONS = OUT / "predictions"
POSITIONS = (0, 49, 99)


def _preview(image_dir: Path, gt_dir: Path, incumbent_dir: Path) -> dict[str, object]:
    selected = [sorted(image_dir.glob("*.jpg"))[index] for index in POSITIONS]
    fig, axes = plt.subplots(3, 4, figsize=(12, 9), squeeze=False)
    titles = ("Input", "Mean annotator boundary", "MFI incumbent", "Exact author QFrD")
    for row, image_path in enumerate(selected):
        agreement = np.mean(np.stack(_extract_boundaries(loadmat(gt_dir / f"{image_path.stem}.mat"))), axis=0)
        panels = (imread(image_path), agreement,
                  np.asarray(Image.open(incumbent_dir / f"{image_path.stem}.png")) / 255.0,
                  np.asarray(Image.open(PREDICTIONS / f"{image_path.stem}.png")) / 255.0)
        for column, (panel, title) in enumerate(zip(panels, titles)):
            axis = axes[row, column]
            axis.imshow(panel, cmap=None if column == 0 else "gray", vmin=None if column == 0 else 0, vmax=None if column == 0 else 1)
            axis.set_title(title if row == 0 else image_path.stem, fontsize=9)
            axis.axis("off")
    fig.suptitle("Stage 15i fixed BSDS500-val positions 1, 50, 100; qualitative only")
    fig.tight_layout()
    path = OUT / "best_method_preview.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "selection": "sorted BSDS500-validation positions 1, 50, and 100", "image_ids": [path.stem for path in selected], "panel_order": ["input", "mean annotator boundary (display only)", "retained MFI incumbent", "exact author-code QFrD soft NMS response"], "optimization_use": "none; documentary qualitative artifact"}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    cfg = _load_json(DEFAULT_CONFIG)
    bsds_root, _ = _ensure_benchmark_sources(cfg, "val")
    image_dir = bsds_root / "BSDS500" / "data" / "images" / "val"
    gt_dir = bsds_root / "BSDS500" / "data" / "groundTruth" / "val"
    images = sorted(image_dir.glob("*.jpg"))
    if len(images) != 100:
        raise RuntimeError(f"expected 100 BSDS500-val images, found {len(images)}")
    export = export_qfrd_maps(image_dir, PREDICTIONS, split="val")
    incumbent_dir, incumbent_provenance = _incumbent_predictions(cfg, image_dir=image_dir, gt_dir=gt_dir, split="val")
    preview = _preview(image_dir, gt_dir, incumbent_dir)
    manifest = {"schema_version": 1, "split": "val", "include_incumbent": True, "methods": [{"name": "stage15i_exact_author_qfrd", "prediction_dir": str(PREDICTIONS.relative_to(ROOT)).replace("\\", "/"), "exporter": "evaluation/bsds_official/export_stage15i_qfrd.py", "author_commit": AUTHOR_COMMIT}]}
    manifest_path = OUT / "official_eval_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    summary = {
        "stage": "15i-qfrd-exact-reproduction", "role": "matched_protocol_reproduction", "architecture_changed": False,
        "question": "What does the pinned fixed-default exact author QFrD code obtain under the common BSDS500-validation path?",
        "implementation": export,
        "dataset": {"name": "BSDS500", "split": "validation", "role": "development/matched-protocol reproduction", "n_images": len(images), "protected_split_used": False, "native_resolution": True, "ground_truth_use_by_detector": False},
        "reported_bsds500_test_document_only": {"ods": 0.6145, "ois": 0.6361, "ap": 0.5996},
        "incumbent_export": incumbent_provenance, "preview": preview,
        "official_evaluation": {"status": "pending controller attachment", "protocol": "all annotations, 99 thresholds, maxDist=0.0075, thinning, native resolution", "stage15a_caveat": "the unmodified Windows matcher remains stochastic and reference-uncertified; the fixed-seed diagnostic matcher is forbidden", "manifest": str(manifest_path.relative_to(ROOT)).replace("\\", "/")},
        "decision_semantics": "reproduction baseline only; retain results without QFrD/fractional tuning or MFI change before Stage 15o",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE15I_QFRD_EXACT_REPRODUCTION_COMPLETE")
    print(OUT / "summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
