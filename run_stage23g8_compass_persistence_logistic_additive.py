from __future__ import annotations

"""Stage 23G8: exact Compass plus persistence via nonnegative logistic addition."""

from pathlib import Path
import argparse
import hashlib
import json
import sys

import numpy as np
import pandas as pd
from PIL import Image
from scipy.special import expit

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from automation.visual_report import write_panel_grid
from benchmark_uded_stage7 import fixed_eval, selection_metric
from benchmark_uded_stage8_contextual import aggregate_counts
from run_stage12d_bipolar_cv import _make_repeated_folds
from run_stage23e_cached_descriptor_aggregator_landscape import _fit_logistic, _fit_membership, _membership, _target
from run_stage23g7_compass_persistence_gap_diagnosis import _load_bsds, _load_uded, _sha256
from src.measure_learning import balanced_sample

EXPERIMENT_ID = "stage23g8_compass_persistence_logistic_additive"
OUT = ROOT / "results/local_dev" / EXPERIMENT_ID
SEED = 20261031
MAX_SAMPLES = 30000


def _fit(targets, cues, items, indices, seed):
    raw = np.concatenate([
        np.stack([targets[int(i)], cues[int(i)]], axis=-1).reshape(-1, 2)
        for i in indices
    ])
    y = np.concatenate([_target(items[int(i)]["gt"]).ravel() for i in indices]).astype(float)
    membership = _fit_membership(raw, y)
    sampled_x, sampled_y = balanced_sample(_membership(raw, membership), y, MAX_SAMPLES, seed)
    beta, ok = _fit_logistic(sampled_x, sampled_y)
    if not ok or not np.all(np.isfinite(beta)) or np.any(beta[1:] < -1e-12):
        raise RuntimeError("nonnegative logistic fit failed")
    payload = {"membership_midpoint": membership["midpoint"].tolist(),
               "membership_scale": membership["scale"].tolist(), "beta": beta.tolist()}
    payload["model_sha256"] = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return membership, beta, payload


def _apply(target, cue, membership, beta):
    x = _membership(np.stack([target, cue], axis=-1), membership)
    score = expit(beta[0] + x @ beta[1:])
    return np.asarray(x[..., 1], np.float32), np.asarray(np.clip(score, 0, 1), np.float32)


def _png(path: Path, score: np.ndarray) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    value = np.clip(np.rint(np.asarray(score, float) * 255), 0, 255).astype(np.uint8)
    temporary = path.with_suffix(path.suffix + ".tmp")
    Image.fromarray(value, mode="L").save(temporary, format="PNG"); temporary.replace(path)
    return _sha256(path)


def main() -> int:
    global OUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT)); parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args(); OUT = Path(args.out)
    if args.smoke:
        target = np.linspace(0, 1, 64, dtype=np.float32).reshape(8, 8)
        cue = np.flipud(target); items = [{"gt": target > .55}]
        membership, beta, _ = _fit([target], [cue], items, np.array([0]), SEED)
        _, score = _apply(target, cue, membership, beta)
        assert score.shape == target.shape and np.all(np.isfinite(score)) and score.min() >= 0 and score.max() <= 1
        assert np.all(beta[1:] >= 0)
        print("STAGE23G8_COMPASS_PERSISTENCE_LOGISTIC_SMOKE_OK"); return 0

    OUT.mkdir(parents=True, exist_ok=True)
    ui, ut, uc, up = _load_uded(); bi, bt, bc, bp = _load_bsds()
    if len(up) != 14 or len(bp) != 100 or not all(bool(x["cache_hit"]) for x in up + bp):
        raise RuntimeError("expected 114 exact persistence cache hits")
    counts = {"compass": [], "candidate": []}; fold_rows, image_rows, model_rows = [], [], []
    first_membership, first_candidate = {}, {}
    for repeat, fold, train, valid in _make_repeated_folds(len(ui), 3, 5, SEED):
        fit_seed = SEED + 10000 * repeat + 100 * fold + 1
        membership, beta, model = _fit(ut, uc, ui, train, fit_seed)
        train_candidate = [_apply(ut[int(i)], uc[int(i)], membership, beta)[1] for i in train]
        valid_applied = [_apply(ut[int(i)], uc[int(i)], membership, beta) for i in valid]
        valid_candidate = [x[1] for x in valid_applied]
        baseline_threshold = float(selection_metric([ut[int(i)] for i in train], [ui[int(i)] for i in train], 41)["threshold"])
        candidate_threshold = float(selection_metric(train_candidate, [ui[int(i)] for i in train], 41)["threshold"])
        baseline_metric, baseline_counts, baseline_images = fixed_eval([ut[int(i)] for i in valid], [ui[int(i)] for i in valid], baseline_threshold)
        candidate_metric, candidate_counts, candidate_images = fixed_eval(valid_candidate, [ui[int(i)] for i in valid], candidate_threshold)
        counts["compass"].extend(baseline_counts); counts["candidate"].extend(candidate_counts)
        fold_rows.append({"repeat": repeat + 1, "fold": fold + 1, "compass_threshold": baseline_threshold,
                          "candidate_threshold": candidate_threshold, "model_sha256": model["model_sha256"],
                          "fit_success": True, "beta_intercept": beta[0], "beta_compass": beta[1],
                          "beta_persistence": beta[2], "compass_precision": baseline_metric["precision"],
                          "compass_recall": baseline_metric["recall"], "compass_F1": baseline_metric["F1"],
                          "candidate_precision": candidate_metric["precision"], "candidate_recall": candidate_metric["recall"],
                          "candidate_F1": candidate_metric["F1"], "delta_F1": candidate_metric["F1"] - baseline_metric["F1"]})
        model_rows.append({"domain": "UDED_outer_fold", "repeat": repeat + 1, "fold": fold + 1,
                           "fit_seed": fit_seed, **model})
        for position, index in enumerate(valid):
            i = int(index); b, c = baseline_images[position], candidate_images[position]
            image_rows.append({"repeat": repeat + 1, "fold": fold + 1, "image_id": ui[i]["id"],
                               "compass_F1": b["F1"], "candidate_F1": c["F1"], "delta_F1": c["F1"] - b["F1"]})
            if repeat == 0:
                first_membership[i], first_candidate[i] = valid_applied[position]

    aggregate = {name: aggregate_counts(value) for name, value in counts.items()}
    delta = {key: aggregate["candidate"][key] - aggregate["compass"][key] for key in ("precision", "recall", "F1")}
    fold_frame = pd.DataFrame(fold_rows); wins = int((fold_frame.delta_F1 > 0).sum())
    mean_fold_delta = float(fold_frame.delta_F1.mean())
    uded_pass = bool(delta["F1"] >= .002 and delta["precision"] >= -.003 and delta["recall"] >= -.003
                     and mean_fold_delta > 0 and wins >= 9 and len(fold_frame) == 15 and fold_frame.fit_success.all())

    all_indices = np.arange(len(ui)); membership, beta, final_model = _fit(ut, uc, ui, all_indices, SEED + 900001)
    model_rows.append({"domain": "all_overlap_clean_UDED_for_BSDS", "repeat": 0, "fold": 0,
                       "fit_seed": SEED + 900001, **final_model})
    bsds_applied = [_apply(target, cue, membership, beta) for target, cue in zip(bt, bc)]
    bsds_memberships, bsds_candidate = [x[0] for x in bsds_applied], [x[1] for x in bsds_applied]
    provenance = {x["image_id"]: x for x in bp}; hash_rows, map_rows = [], []
    for item, score in zip(bi, bsds_candidate):
        path = OUT / "frozen_maps" / EXPERIMENT_ID / f"{item['id']}.png"; sidecar = path.with_suffix(".json")
        source = provenance[item["id"]]
        identity = {"image_id": item["id"], "formula": "stage23e_nonnegative_logistic_additive",
                    "compass_png_sha256": source["compass_png_sha256"], "cue_cache_key": source["cue_cache_key"],
                    "cue_artifact_sha256": source["cue_artifact_sha256"], "model_sha256": final_model["model_sha256"]}
        hit = False
        if path.is_file() and sidecar.is_file():
            prior = json.loads(sidecar.read_text(encoding="utf-8"))
            if prior.get("identity") != identity or prior.get("png_sha256") != _sha256(path):
                raise RuntimeError(f"frozen candidate provenance mismatch: {item['id']}")
            png_hash, hit = prior["png_sha256"], True
        else:
            png_hash = _png(path, score); payload = {"identity": identity, "png_sha256": png_hash}
            temporary = sidecar.with_suffix(".json.tmp"); temporary.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8"); temporary.replace(sidecar)
        hash_rows.append({"method": EXPERIMENT_ID, "image_id": item["id"], "png_sha256": png_hash, "cache_hit": hit})
        map_rows.append({**identity, "png_sha256": png_hash, "cache_hit": hit})

    previews = []
    for items, targets, memberships, candidates, positions in (
        (ui, ut, first_membership, first_candidate, (0, 6, 13)),
        (bi, bt, {i: x for i, x in enumerate(bsds_memberships)}, {i: x for i, x in enumerate(bsds_candidate)}, (0, 49, 99)),
    ):
        for i in positions:
            previews.append([items[i]["img"], items[i]["gt"], targets[i], memberships[i], candidates[i]])
    preview = write_panel_grid(OUT / "best_method_preview.png", previews, panel_height=112, panel_width=112, gap=2)
    fold_frame.to_csv(OUT / "fold_results.csv", index=False); pd.DataFrame(image_rows).to_csv(OUT / "per_image_metrics.csv", index=False)
    pd.DataFrame(model_rows).to_csv(OUT / "model_provenance.csv", index=False); pd.DataFrame(up + bp).to_csv(OUT / "frozen_input_provenance.csv", index=False)
    pd.DataFrame(hash_rows).to_csv(OUT / "frozen_map_hashes.csv", index=False)
    with (OUT / "map_provenance.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for row in map_rows: handle.write(json.dumps(row, sort_keys=True) + "\n")
    export_args = ["--image-dir", "{image_dir}", "--output-dir", "{output_dir}", "--split", "{split}"]
    official = {"schema_version": 1, "split": "val", "include_incumbent": True, "methods": [
        {"name": "exact_author_compass", "export": {"script": "automation/stage23g6_compass_frozen_bsds_export.py", "args": export_args}},
        {"name": EXPERIMENT_ID, "export": {"script": "automation/stage23g8_frozen_bsds_export.py", "args": export_args}}],
        "stage23_note": "Compare exact Compass with the single preregistered persistence/logistic intervention; report operational ODS/OIS and ranking AP separately."}
    (OUT / "official_eval_manifest.json").write_text(json.dumps(official, indent=2), encoding="utf-8")
    summary = {"status": "completed", "experiment_id": EXPERIMENT_ID, "detector_runs": 0,
               "descriptor_computations": 0, "cache_hits": 114, "protected_lineage_bytes_read": False,
               "uded": {"compass": aggregate["compass"], "candidate": aggregate["candidate"], "delta": delta,
                        "mean_fold_F1_delta": mean_fold_delta, "fold_wins": wins, "n_folds": 15,
                        "fit_successes": int(fold_frame.fit_success.sum()), "gate_pass": uded_pass},
               "bsds_candidate_maps": len(hash_rows), "candidate_map_cache_hits": int(sum(bool(x["cache_hit"]) for x in hash_rows)),
               "final_model_sha256": final_model["model_sha256"], "incumbent_changed": False,
               "decision_semantics": "Official exact-Compass comparison separates operational ODS/OIS from ranking AP; complete eligibility also requires the frozen UDED gate.",
               "visual_preview": {"path": preview.relative_to(ROOT).as_posix(), "selection": "UDED 1/7/14 then BSDS val 1/50/100",
                                  "panel_order": ["input", "GT union", "exact Compass", "persistence membership", "nonnegative logistic candidate"],
                                  "optimization_use": "documentary only"}}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE23G8_COMPASS_PERSISTENCE_LOGISTIC_ADDITIVE_COMPLETED"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
