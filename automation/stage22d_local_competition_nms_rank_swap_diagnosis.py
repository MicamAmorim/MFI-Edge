from __future__ import annotations

"""Stage 22D: frozen-pipeline local competition and NMS rank-swap diagnosis."""

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
from scipy.ndimage import distance_transform_edt, maximum_filter, uniform_filter
from scipy.stats import rankdata
from skimage.io import imread

from automation.stage21d_ranking_localization_diagnosis import extract_boundaries, official_module
from automation.visual_report import write_panel_grid
from benchmark_uded import DEFAULT_UDED, load_uded
from benchmark_uded_quick import resize_items
from run_stage12b_fuzzy_signature import prepare
from run_stage12c_leakfree_cv import ensure_uded, learn_banks
from run_stage14c_positive_bank_pruning import COMPACT_FEATURES, FLOOR, STRENGTH, _contexts, _filter_bank
from run_stage20_frozen_queue_candidate import SEED, _attach_descriptors, _candidate_context, _fit_full
from src.bipolar_fuzzy import context_gate
from src.classical_detectors import detector_score

OUT = ROOT / "results/local_dev/stage22d_local_competition_nms_rank_swap_diagnosis"
INCUMBENT_CACHE = ROOT / "automation/runtime/official_eval_cache/incumbent/val/e4fa09acaf61ec23"
CANDIDATE_CACHE = ROOT / "automation/runtime/official_eval_cache/experiments/stage20c_dominant_pair_2additive_choquet/stage20c_dominant_pair_2additive_choquet/val"
DESCRIPTORS = ("gabor4_s13", "semiglobal_changepoint")
PREVIEW_POSITIONS = (0, 49, 99)
TOLERANCE = 0.0075
ODS_THRESHOLDS = {"incumbent": 0.18, "stage20c": 0.255}
DOMINANCE = {
    "demotion_scale": 0.10, "local_error_scale": 0.25,
    "multiplicity_scale": 0.05, "dominance_score": 0.60,
    "component_floor": 0.50, "minimum_components": 2,
}


def save_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise RuntimeError(f"refusing to write empty table: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def percentile_rank(values: np.ndarray) -> np.ndarray:
    ranks = rankdata(np.asarray(values).ravel(), method="average")
    return ((ranks - 0.5) / ranks.size).reshape(values.shape).astype(np.float32)


def consensus_maps(boundaries: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    stack = np.stack(boundaries).astype(bool)
    union = np.any(stack, axis=0)
    consensus = np.sum(stack, axis=0) >= int(np.ceil(stack.shape[0] / 2))
    return union, consensus


def selected_at_density(score: np.ndarray, count: int) -> np.ndarray:
    flat = np.asarray(score).ravel()
    count = min(max(int(count), 0), flat.size)
    selected = np.zeros(flat.size, dtype=bool)
    if count:
        selected[np.argsort(-flat, kind="stable")[:count]] = True
    return selected.reshape(score.shape)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    prior = json.loads((ROOT / "results/local_dev/stage22c_inter_image_score_calibration_diagnosis/summary.json").read_text(encoding="utf-8"))
    if prior.get("status") != "completed":
        raise RuntimeError("Stage 22C must be complete before Stage 22D")

    args = Namespace(uded_root=str(ROOT / "external/UDED"), max_side_development=256, seed=SEED,
                     max_positive=10, max_negative=8, max_abs_corr=0.88)
    _training, names, _candidate_compact, model = _fit_full(args, DESCRIPTORS)
    incumbent_raw = resize_items(load_uded(ensure_uded(Path(DEFAULT_UDED))), 256)
    incumbent_selection, incumbent_names = prepare(incumbent_raw[0::2])
    incumbent_positive, _ = learn_banks(incumbent_selection, incumbent_names, 20261006,
                                         max_positive=10, max_negative=8, max_abs_corr=0.88)
    incumbent_compact = _filter_bank(incumbent_positive, COMPACT_FEATURES)
    if list(incumbent_names) != list(names):
        raise RuntimeError("incumbent/candidate feature-name drift")

    mod = official_module()
    cfg = json.loads((ROOT / "evaluation/bsds_official/config.json").read_text(encoding="utf-8"))
    bsds_root, _ = mod._ensure_benchmark_sources(cfg, "val")
    image_dir = bsds_root / "BSDS500/data/images/val"
    gt_dir = bsds_root / "BSDS500/data/groundTruth/val"
    paths = sorted(image_dir.glob("*.jpg"))
    if len(paths) != 100:
        raise RuntimeError("expected exactly 100 BSDS validation images")

    transition_rows, swap_rows, suppression_rows, early_rows, previews = [], [], [], [], []
    byte_checks = {"incumbent": 0, "stage20c": 0}
    pooled_early = {"false": 0, "competition": 0, "scale": 0, "unresolved": 0}
    early_inputs = []
    multiplicity_totals = {method: {"selected": 0, "supported_gt": 0, "duplicates": 0} for method in ODS_THRESHOLDS}
    demotion_totals = {method: {"eligible": 0, "demoted": 0} for method in ODS_THRESHOLDS}

    for number, path in enumerate(paths, start=1):
        image_id = path.stem
        print(f"STAGE22D_LOCAL_COMPETITION {number:03d}/100 {image_id}", flush=True)
        image = imread(path)
        prepared, candidate_names = prepare([{"id": image_id, "img": image}])
        if list(candidate_names) != list(names):
            raise RuntimeError(f"feature-name drift for {image_id}")
        _attach_descriptors(prepared, DESCRIPTORS, "STAGE22D_DESCRIPTOR")
        item = prepared[0]
        contexts = {
            "incumbent": _contexts([item], names, incumbent_compact)[0],
            "stage20c": _candidate_context(item, model),
        }
        scharr_pre = detector_score(item["pre_img"], "scharr", 1.0).astype(np.float32)
        pre = {method: context_gate(scharr_pre, context, STRENGTH, FLOOR) for method, context in contexts.items()}
        final_float = {method: context_gate(item["scharr"], context, STRENGTH, FLOOR) for method, context in contexts.items()}
        frozen = {
            "incumbent": np.asarray(Image.open(INCUMBENT_CACHE / f"{image_id}.png"), dtype=np.uint8),
            "stage20c": np.asarray(Image.open(CANDIDATE_CACHE / f"{image_id}.png"), dtype=np.uint8),
        }
        final = {}
        for method in ODS_THRESHOLDS:
            serialized = np.rint(np.clip(final_float[method], 0, 1) * 255).astype(np.uint8)
            if not np.array_equal(serialized, frozen[method]):
                raise RuntimeError(f"frozen final-map byte mismatch for {method}/{image_id}")
            byte_checks[method] += 1
            final[method] = frozen[method].astype(np.float32) / 255.0

        boundaries = extract_boundaries(loadmat(gt_dir / f"{image_id}.mat"))
        union, consensus = consensus_maps(boundaries)
        near_union = distance_transform_edt(~union) <= TOLERANCE * float(np.hypot(*union.shape))
        local_consensus = maximum_filter(consensus.astype(np.uint8), size=5, mode="constant") > 0
        ranks = {method: {"context": percentile_rank(contexts[method]),
                          "pre": percentile_rank(pre[method]),
                          "final": percentile_rank(final[method])} for method in ODS_THRESHOLDS}

        for method in ODS_THRESHOLDS:
            high = consensus
            eligible = high & (ranks[method]["pre"] >= 0.75)
            demoted = eligible & ((ranks[method]["pre"] - ranks[method]["final"]) >= 0.10)
            demotion_totals[method]["eligible"] += int(eligible.sum())
            demotion_totals[method]["demoted"] += int(demoted.sum())
            transition_rows.append({
                "image_id": image_id, "method": method,
                "high_consensus_pixels": int(high.sum()),
                "mean_high_consensus_context_rank": float(np.mean(ranks[method]["context"][high])) if high.any() else float("nan"),
                "mean_high_consensus_pre_nms_rank": float(np.mean(ranks[method]["pre"][high])) if high.any() else float("nan"),
                "mean_high_consensus_final_rank": float(np.mean(ranks[method]["final"][high])) if high.any() else float("nan"),
                "pre_top_quartile_high_consensus": int(eligible.sum()),
                "demoted_by_at_least_0p10_after_nms": int(demoted.sum()),
                "top_decile_pre_retention": float(np.mean(ranks[method]["final"][high & (ranks[method]["pre"] >= 0.90)] >= 0.90)) if np.any(high & (ranks[method]["pre"] >= 0.90)) else float("nan"),
            })

            count = int(np.count_nonzero(final[method] >= ODS_THRESHOLDS[method]))
            selected = selected_at_density(final[method], count)
            selected_near = selected & near_union
            neighborhood_counts = uniform_filter(selected.astype(float), size=5, mode="constant") * 25.0
            supported_gt = consensus & (neighborhood_counts > 0.5)
            duplicates = np.maximum(np.rint(neighborhood_counts[supported_gt]).astype(int) - 1, 0)
            multiplicity_totals[method]["selected"] += int(np.sum(np.rint(neighborhood_counts[supported_gt])))
            multiplicity_totals[method]["supported_gt"] += int(supported_gt.sum())
            multiplicity_totals[method]["duplicates"] += int(duplicates.sum())
            suppressed = (pre[method] > 0) & (final[method] == 0)
            suppression_rows.append({
                "image_id": image_id, "method": method, "ods_density_pixels": count,
                "selected_near_union": int(selected_near.sum()),
                "supported_high_consensus_pixels": int(supported_gt.sum()),
                "parallel_duplicate_count": int(duplicates.sum()),
                "mean_selected_multiplicity_per_supported_gt": float(np.sum(np.rint(neighborhood_counts[supported_gt]))) / max(int(supported_gt.sum()), 1),
                "suppressed_high_consensus": int(np.count_nonzero(suppressed & consensus)),
                "suppressed_near_union": int(np.count_nonzero(suppressed & near_union)),
                "suppressed_unsupported": int(np.count_nonzero(suppressed & ~near_union)),
            })

        pre_win = consensus & (ranks["stage20c"]["pre"] > ranks["incumbent"]["pre"])
        final_loss = ranks["stage20c"]["final"] < ranks["incumbent"]["final"]
        pre_loss = consensus & (ranks["stage20c"]["pre"] < ranks["incumbent"]["pre"])
        final_win = ranks["stage20c"]["final"] > ranks["incumbent"]["final"]
        swap_rows.append({"image_id": image_id, "high_consensus_pixels": int(consensus.sum()),
                          "stage20c_pre_win_final_loss": int(np.count_nonzero(pre_win & final_loss)),
                          "stage20c_pre_loss_final_win": int(np.count_nonzero(pre_loss & final_win)),
                          "contract": "within-image average ranks; high consensus is at least half of annotations"})

        early_inputs.append({"image_id": image_id, "final": final["stage20c"].copy(),
                             "pre": pre["stage20c"].copy(), "near_union": near_union.copy(),
                             "consensus": consensus.copy(), "local_consensus": local_consensus.copy()})

        if number - 1 in PREVIEW_POSITIONS:
            previews.append([image, union, consensus, contexts["incumbent"], contexts["stage20c"],
                             pre["incumbent"], pre["stage20c"], final["incumbent"], final["stage20c"]])

    pooled_scores = np.concatenate([row["final"].ravel() for row in early_inputs])
    pooled_count = max(1, int(np.ceil(pooled_scores.size * 0.01)))
    global_cutoff = float(np.partition(pooled_scores, -pooled_count)[-pooled_count])
    for values in early_inputs:
        score, pre_score = values["final"], values["pre"]
        early = score >= global_cutoff
        false = early & ~values["near_union"]
        own_cutoff = float(np.quantile(score, 0.99))
        local_best_pre = maximum_filter(np.where(values["consensus"], pre_score, -np.inf), size=5, mode="constant", cval=-np.inf)
        local_best_final = maximum_filter(np.where(values["consensus"], score, -np.inf), size=5, mode="constant", cval=-np.inf)
        competition = false & values["local_consensus"] & (local_best_pre > pre_score) & (local_best_final < score)
        scale = false & ~competition & (score < own_cutoff)
        unresolved = false & ~competition & ~scale
        early_rows.append({"image_id": values["image_id"], "global_score_cutoff": global_cutoff,
                           "within_image_top1pct_cutoff": own_cutoff, "early_pixels": int(early.sum()),
                           "early_false_positives": int(false.sum()),
                           "local_competition_errors": int(competition.sum()),
                           "score_scale_errors": int(scale.sum()), "unresolved_errors": int(unresolved.sum()),
                           "contract": "pooled global top 1%; mutually exclusive competition-first attribution; diagnostic, not Berkeley matching"})
        for key, source in (("false", false), ("competition", competition), ("scale", scale), ("unresolved", unresolved)):
            pooled_early[key] += int(source.sum())

    demotion_rates = {method: demotion_totals[method]["demoted"] / max(demotion_totals[method]["eligible"], 1) for method in ODS_THRESHOLDS}
    multiplicity = {method: multiplicity_totals[method]["selected"] / max(multiplicity_totals[method]["supported_gt"], 1) for method in ODS_THRESHOLDS}
    local_fraction = pooled_early["competition"] / max(pooled_early["false"], 1)
    components = {
        "high_consensus_demotion_component": float(np.clip((demotion_rates["stage20c"] - demotion_rates["incumbent"]) / DOMINANCE["demotion_scale"], 0, 1)),
        "local_error_attribution_component": float(np.clip(local_fraction / DOMINANCE["local_error_scale"], 0, 1)),
        "excess_multiplicity_component": float(np.clip((multiplicity["stage20c"] / max(multiplicity["incumbent"], 1e-12) - 1) / DOMINANCE["multiplicity_scale"], 0, 1)),
    }
    score = float(np.mean(list(components.values())))
    count_floor = int(sum(value >= DOMINANCE["component_floor"] for value in components.values()))
    dominant = bool(score >= DOMINANCE["dominance_score"] and count_floor >= DOMINANCE["minimum_components"])
    dominance_row = {**components, "competition_dominance_score": score,
                     "components_at_or_above_floor": count_floor, "competition_dominant": dominant,
                     "stage20c_demotion_rate": demotion_rates["stage20c"], "incumbent_demotion_rate": demotion_rates["incumbent"],
                     "local_competition_early_error_fraction": local_fraction,
                     "stage20c_near_gt_multiplicity": multiplicity["stage20c"], "incumbent_near_gt_multiplicity": multiplicity["incumbent"]}

    write_csv(OUT / "per_image_rank_transitions.csv", transition_rows)
    write_csv(OUT / "per_image_local_rank_swaps.csv", swap_rows)
    write_csv(OUT / "per_image_suppression_multiplicity.csv", suppression_rows)
    write_csv(OUT / "early_error_attribution.csv", early_rows)
    write_csv(OUT / "competition_dominance.csv", [dominance_row])
    write_panel_grid(OUT / "best_method_preview.png", previews)
    manifest = {"schema_version": 1, "split": "val", "include_incumbent": True, "methods": [{
        "name": "stage20c_dominant_pair_2additive_choquet",
        "export": {"script": "automation/stage22b_frozen_export.py", "args": ["--method", "stage20c_dominant_pair_2additive_choquet", "--image-dir", "{image_dir}", "--output-dir", "{output_dir}", "--split", "{split}"]},
    }]}
    save_json(OUT / "official_eval_manifest.json", manifest)
    summary = {
        "stage": "stage22d_local_competition_nms_rank_swap_diagnosis", "status": "completed",
        "scientific_experiment_index": "4/5", "architecture_changed": False, "detector_fitted": False,
        "matcher_rerun": False, "promotion_allowed": False, "protected_split_used": False,
        "berkeley_reference_reproduction_verified": False, "final_map_byte_checks": byte_checks,
        "competition_dominance_contract": DOMINANCE, "competition_dominance": dominance_row,
        "calibration_dominance_from_stage22c": prior["calibration_dominance"],
        "preview": {"file": "best_method_preview.png", "positions": [1, 50, 100],
                    "columns": ["input", "annotation union", "high consensus", "incumbent context", "Stage 20C context", "incumbent pre-NMS", "Stage 20C pre-NMS", "incumbent final", "Stage 20C final"], "documentary_only": True},
        "next_stage_rule": "mechanical Stage-22E branch selection from frozen calibration and competition scores; or stop if neither/tied",
    }
    save_json(OUT / "summary.json", summary)
    (OUT / "summary.md").write_text("# Stage 22D local competition / NMS diagnosis\n\nByte-verified frozen-pipeline rank transitions, local swaps, suppression/multiplicity, and mutually exclusive early-error attribution. All endpoints are descriptive and non-promotional.\n", encoding="utf-8")
    print("STAGE22D_LOCAL_COMPETITION_NMS_COMPLETE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
