from __future__ import annotations

"""Stage 21F: decompose frozen incumbent/Stage-20C context and localization."""

from argparse import Namespace
from pathlib import Path
import csv
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from PIL import Image
from scipy.io import loadmat
from scipy.ndimage import distance_transform_edt
from skimage.io import imread

from automation.stage21d_ranking_localization_diagnosis import auc_binary, average_precision, extract_boundaries, official_module
from automation.visual_report import write_panel_grid
from benchmark_uded import DEFAULT_UDED, load_uded
from benchmark_uded_quick import resize_items
from run_stage12b_fuzzy_signature import prepare
from run_stage12c_leakfree_cv import ensure_uded, learn_banks
from run_stage14c_positive_bank_pruning import COMPACT_FEATURES, FLOOR, STRENGTH, _contexts, _filter_bank
from run_stage20_frozen_queue_candidate import SEED, _attach_descriptors, _candidate_context, _fit_full
from src.bipolar_fuzzy import context_gate
from src.classical_detectors import detector_score

OUT = ROOT / "results/local_dev/stage21f_context_localizer_nms_decomposition"
INCUMBENT_CACHE = ROOT / "automation/runtime/official_eval_cache/incumbent/val/e4fa09acaf61ec23"
CANDIDATE_CACHE = ROOT / "automation/runtime/official_eval_cache/experiments/stage20c_dominant_pair_2additive_choquet/stage20c_dominant_pair_2additive_choquet/val"
DESCRIPTORS = ("gabor4_s13", "semiglobal_changepoint")
PREVIEW_POSITIONS = (0, 49, 99)
TOLERANCE = 0.0075
FINAL_THRESHOLDS = {"incumbent": 0.18, "stage20c": 0.25555555555555554}


def save_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"refusing to write empty table: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def density_matched_support(score: np.ndarray, count: int) -> np.ndarray:
    flat = np.asarray(score, dtype=np.float64).ravel()
    count = max(0, min(int(count), flat.size))
    mask = np.zeros(flat.size, dtype=bool)
    if count:
        mask[np.argsort(-flat, kind="stable")[:count]] = True
    return mask.reshape(score.shape)


def spatial_row(image_id: str, method: str, stage: str, score: np.ndarray,
                union: np.ndarray, reference_count: int) -> dict:
    prediction = density_matched_support(score, reference_count)
    to_gt = distance_transform_edt(~union)
    to_prediction = distance_transform_edt(~prediction)
    tolerance = TOLERANCE * float(np.hypot(*score.shape))
    gt_values = to_prediction[union]
    pred_values = to_gt[prediction]
    return {
        "image_id": image_id, "method": method, "stage": stage,
        "density_reference_pixels": reference_count,
        "gt_to_support_mean_px": float(gt_values.mean()) if gt_values.size else float("nan"),
        "support_to_gt_mean_px": float(pred_values.mean()) if pred_values.size else float("nan"),
        "gt_supported_at_0p0075": float(np.mean(gt_values <= tolerance)) if gt_values.size else float("nan"),
        "support_supported_at_0p0075": float(np.mean(pred_values <= tolerance)) if pred_values.size else float("nan"),
        "contract": "top-k support matched to frozen final ODS density; descriptive union distance, not Berkeley matching",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    prior = json.loads((ROOT / "results/local_dev/stage21e_spatial_tolerance_response_curve/summary.json").read_text(encoding="utf-8"))
    if prior.get("status") != "completed":
        raise RuntimeError("Stage 21E must be complete before Stage 21F")

    args = Namespace(uded_root=str(ROOT / "external/UDED"), max_side_development=256, seed=SEED,
                     max_positive=10, max_negative=8, max_abs_corr=0.88)
    _training, names, _candidate_compact, model = _fit_full(args, DESCRIPTORS)
    incumbent_raw = resize_items(load_uded(ensure_uded(Path(DEFAULT_UDED))), 256)
    incumbent_selection, incumbent_names = prepare(incumbent_raw[0::2])
    incumbent_positive, _ = learn_banks(
        incumbent_selection, incumbent_names, 20261006,
        max_positive=10, max_negative=8, max_abs_corr=0.88,
    )
    incumbent_compact = _filter_bank(incumbent_positive, COMPACT_FEATURES)
    if list(incumbent_names) != list(names):
        raise RuntimeError("incumbent/candidate feature-name drift")

    mod = official_module()
    cfg = json.loads((ROOT / "evaluation/bsds_official/config.json").read_text(encoding="utf-8"))
    bsds_root, _ = mod._ensure_benchmark_sources(cfg, "val")
    image_dir = bsds_root / "BSDS500/data/images/val"
    gt_dir = bsds_root / "BSDS500/data/groundTruth/val"
    image_paths = sorted(image_dir.glob("*.jpg"))
    if len(image_paths) != 100:
        raise RuntimeError("expected exactly 100 BSDS validation images")

    rank_rows, spatial_rows, preview_rows = [], [], []
    aggregate: dict[tuple[str, str], dict[str, list[np.ndarray]]] = {}
    byte_checks = {"incumbent": 0, "stage20c": 0}
    for number, path in enumerate(image_paths, start=1):
        image_id = path.stem
        print(f"STAGE21F_DECOMPOSE {number:03d}/100 {image_id}", flush=True)
        image = imread(path)
        prepared, candidate_names = prepare([{"id": image_id, "img": image}])
        if list(candidate_names) != list(names):
            raise RuntimeError(f"feature-name drift for {image_id}")
        _attach_descriptors(prepared, DESCRIPTORS, "STAGE21F_DESCRIPTOR")
        item = prepared[0]
        incumbent_context = _contexts([item], names, incumbent_compact)[0]
        candidate_context = _candidate_context(item, model)
        local_pre_nms = detector_score(item["pre_img"], "scharr", 1.0).astype(np.float32)
        stages = {
            ("incumbent", "context"): incumbent_context,
            ("stage20c", "context"): candidate_context,
            ("shared", "scharr_pre_nms"): local_pre_nms,
            ("incumbent", "context_local_pre_nms"): context_gate(local_pre_nms, incumbent_context, STRENGTH, FLOOR),
            ("stage20c", "context_local_pre_nms"): context_gate(local_pre_nms, candidate_context, STRENGTH, FLOOR),
            ("incumbent", "final_post_nms"): context_gate(item["scharr"], incumbent_context, STRENGTH, FLOOR),
            ("stage20c", "final_post_nms"): context_gate(item["scharr"], candidate_context, STRENGTH, FLOOR),
        }
        frozen = {
            "incumbent": np.asarray(Image.open(INCUMBENT_CACHE / f"{image_id}.png"), dtype=np.uint8),
            "stage20c": np.asarray(Image.open(CANDIDATE_CACHE / f"{image_id}.png"), dtype=np.uint8),
        }
        for method in ("incumbent", "stage20c"):
            serialized = np.rint(np.clip(stages[(method, "final_post_nms")], 0.0, 1.0) * 255.0).astype(np.uint8)
            if not np.array_equal(serialized, frozen[method]):
                raise RuntimeError(f"frozen final-map byte mismatch for {method}/{image_id}")
            byte_checks[method] += 1
            stages[(method, "final_post_nms")] = frozen[method].astype(np.float32) / 255.0

        boundaries = extract_boundaries(loadmat(gt_dir / f"{image_id}.mat"))
        if not boundaries:
            raise RuntimeError(f"could not parse annotations for {image_id}")
        union = np.any(np.stack(boundaries), axis=0)
        labels = distance_transform_edt(~union) <= TOLERANCE * float(np.hypot(*union.shape))
        reference_counts = {method: int(np.count_nonzero(stages[(method, "final_post_nms")] >= FINAL_THRESHOLDS[method]))
                            for method in ("incumbent", "stage20c")}
        for (method, stage), score in stages.items():
            key = (method, stage)
            aggregate.setdefault(key, {"labels": [], "scores": []})
            aggregate[key]["labels"].append(labels.ravel())
            aggregate[key]["scores"].append(np.asarray(score).ravel())
            rank_rows.append({"image_id": image_id, "method": method, "stage": stage,
                              "tolerant_union_auc": auc_binary(labels, score),
                              "tolerant_union_ap": average_precision(labels, score),
                              "contract": "within 0.0075 diagonal of annotation union; diagnostic, not Berkeley matching"})
            density_method = "incumbent" if method == "shared" else method
            spatial_rows.append(spatial_row(image_id, method, stage, score, union, reference_counts[density_method]))
        if number - 1 in PREVIEW_POSITIONS:
            preview_rows.append([image, union, incumbent_context, candidate_context, local_pre_nms,
                                 stages[("incumbent", "context_local_pre_nms")],
                                 stages[("stage20c", "context_local_pre_nms")],
                                 stages[("incumbent", "final_post_nms")], stages[("stage20c", "final_post_nms")]])

    aggregate_rows = []
    for (method, stage), values in aggregate.items():
        labels = np.concatenate(values["labels"])
        scores = np.concatenate(values["scores"])
        aggregate_rows.append({"method": method, "stage": stage,
                               "tolerant_union_auc": auc_binary(labels, scores),
                               "tolerant_union_ap": average_precision(labels, scores),
                               "n_pixels": int(labels.size),
                               "contract": "pooled tolerant-union discrimination; diagnostic, not official ODS/OIS/AP"})
    write_csv(OUT / "stage_rank_discrimination.csv", aggregate_rows)
    write_csv(OUT / "per_image_stage_rank_discrimination.csv", rank_rows)
    write_csv(OUT / "per_image_density_matched_localization.csv", spatial_rows)
    write_panel_grid(OUT / "best_method_preview.png", preview_rows, panel_height=150, panel_width=150)

    manifest = {"schema_version": 1, "split": "val", "include_incumbent": True, "methods": [{
        "name": "stage20c_dominant_pair_2additive_choquet",
        "export": {"script": "automation/stage21b_frozen_export.py", "args": ["--method", "stage20c_dominant_pair_2additive_choquet", "--image-dir", "{image_dir}", "--output-dir", "{output_dir}", "--split", "{split}"]},
    }]}
    save_json(OUT / "official_eval_manifest.json", manifest)
    summary = {
        "stage": "stage21f_context_localizer_nms_decomposition", "status": "completed",
        "architecture_changed": False, "new_detector_or_parameter_fit": False,
        "frozen_model_reconstructed_from_registered_14_image_UDED_fit": True,
        "protected_split_used": False, "final_map_byte_checks": byte_checks,
        "stages": ["context", "scharr_pre_nms", "context_local_pre_nms", "final_post_nms"],
        "diagnostic_contract": "Tolerant-union AUC/AP and density-matched union distances are descriptive; only the unchanged final maps have official Berkeley meaning.",
        "berkeley_reference_reproduction_verified": False,
        "preview": {"file": "best_method_preview.png", "positions": [1, 50, 100], "columns": ["input", "annotation_union", "incumbent_context", "stage20c_context", "scharr_pre_nms", "incumbent_context_local_pre_nms", "stage20c_context_local_pre_nms", "incumbent_final_post_nms", "stage20c_final_post_nms"], "documentary_only": True},
        "next_stage_if_complete": "stage21g_human_consensus_ranking_analysis",
    }
    save_json(OUT / "summary.json", summary)
    (OUT / "summary.md").write_text("# Stage 21F context/localizer/NMS decomposition\n\nFrozen context, shared pre-NMS Scharr evidence, pre-NMS context-local coupling, and byte-verified final outputs. Intermediate metrics are descriptive and not official Berkeley scores.\n", encoding="utf-8")
    print("STAGE21F_CONTEXT_LOCALIZER_NMS_DECOMPOSITION_OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
