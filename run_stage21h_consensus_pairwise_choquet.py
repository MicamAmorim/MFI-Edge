from __future__ import annotations

"""Stage 21H: one consensus-ranked monotone 2-additive Choquet candidate."""

from pathlib import Path
import argparse
import hashlib
import json
import math
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from scipy import ndimage as ndi
from skimage.transform import resize

import run_stage19b_descriptor_relevance_atlas as atlas
import run_stage19d_aggregation_identification as identification
import run_stage20_frozen_queue_candidate as stage20
from benchmark_uded import DEFAULT_UDED
from src.consensus_rank_capacity import learn_pairwise_2additive


EXPERIMENT_ID = "stage21h_consensus_pairwise_choquet"
DESCRIPTORS = ("gabor4_s13", "semiglobal_changepoint")
PAIR_COUNT_PER_IMAGE = 512
BSDS_MAX_SIDE = 256
SEED = 20261028
CONTROL_BANK_SEED = stage20.SEED
_BSDS_TRAIN: list[dict] = []
_STAGE20_LEARN_BANKS = stage20.learn_banks


def _learn_control_banks(train_items, base_names, seed, max_positive, max_negative, max_abs_corr):
    """Keep the frozen compact control on its established bank-sampling stream."""
    control_seed = CONTROL_BANK_SEED + (int(seed) - SEED)
    return _STAGE20_LEARN_BANKS(
        train_items, base_names, control_seed,
        max_positive, max_negative, max_abs_corr,
    )


def _resize_train(image: np.ndarray, boundaries: list[np.ndarray]) -> tuple[np.ndarray, list[np.ndarray]]:
    h, w = boundaries[0].shape
    scale = min(1.0, BSDS_MAX_SIDE / max(h, w))
    if scale == 1.0:
        return image, boundaries
    nh, nw = max(8, round(h * scale)), max(8, round(w * scale))
    image2 = resize(image, (nh, nw, 3), order=1, mode="reflect", anti_aliasing=True, preserve_range=True)
    bounds2 = [resize(b.astype(np.uint8), (nh, nw), order=0, mode="edge", anti_aliasing=False, preserve_range=True) > 0.5 for b in boundaries]
    return image2, bounds2


def _consensus(boundaries: list[np.ndarray]) -> np.ndarray:
    supports = [ndi.distance_transform_edt(~np.asarray(b, bool)) <= 1.5 for b in boundaries]
    return np.mean(np.stack(supports), axis=0, dtype=np.float64)


def _load_bsds_train() -> list[dict]:
    atlas._verify_bsds_source()
    ids = [Path(path).stem for path in atlas._tree_paths("BSDS500/data/images/train") if path.lower().endswith(".jpg")]
    if len(ids) != 200:
        raise RuntimeError(f"expected 200 BSDS train images, got {len(ids)}")
    records = []
    for number, image_id in enumerate(ids, start=1):
        print(f"STAGE21H_BSDS_TRAIN {number:03d}/200 {image_id}", flush=True)
        image, boundaries = _resize_train(*atlas._load_bsds_train(image_id))
        pre = atlas.apply_conditioning(image, "median", size=3)
        incumbent = atlas._incumbent_maps(pre)
        change, _ = atlas.semiglobal_changepoint_evidence(pre)
        records.append({
            "id": image_id,
            "raw": np.stack([incumbent["gabor4_s13"], change], axis=-1).astype(np.float32),
            "target": _consensus(boundaries).astype(np.float32),
        })
    return records


def _ordered_pairs(x: np.ndarray, target: np.ndarray, count: int, seed: int) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(x, float).reshape(-1, x.shape[-1])
    y = np.asarray(target, float).reshape(-1)
    levels = np.unique(y)
    ordered = [(hi, lo) for hi in levels for lo in levels if hi > lo]
    if not ordered:
        raise RuntimeError("ranking target has no ordered levels")
    rng = np.random.default_rng(seed)
    high_rows, low_rows = [], []
    base, remainder = divmod(count, len(ordered))
    for pair_no, (hi, lo) in enumerate(ordered):
        take = base + int(pair_no < remainder)
        if take == 0:
            continue
        hi_idx, lo_idx = np.flatnonzero(y == hi), np.flatnonzero(y == lo)
        high_rows.append(x[rng.choice(hi_idx, size=take, replace=len(hi_idx) < take)])
        low_rows.append(x[rng.choice(lo_idx, size=take, replace=len(lo_idx) < take)])
    return np.concatenate(high_rows), np.concatenate(low_rows)


def _fit_candidate(items: list[dict], descriptors: tuple[str, ...], seed: int) -> dict:
    raw, target = stage20._training_samples(items, descriptors, seed)
    membership = identification._fit_memberships(raw, target)

    uded_hi, uded_lo = [], []
    for item_no, item in enumerate(items):
        tensor = np.stack([item["stage20_descriptors"][name] for name in descriptors], axis=-1)
        target_map = stage20._tolerant_target(item["gt"]).astype(float)
        token = hashlib.sha256(f"{seed}:21h:uded:{item_no}:{item['id']}".encode()).digest()
        hi, lo = _ordered_pairs(tensor, target_map, PAIR_COUNT_PER_IMAGE, int.from_bytes(token[:8], "little"))
        uded_hi.append(identification._apply_memberships(hi, membership))
        uded_lo.append(identification._apply_memberships(lo, membership))

    bsds_hi, bsds_lo = [], []
    for item_no, record in enumerate(_BSDS_TRAIN):
        token = hashlib.sha256(f"{seed}:21h:bsds:{item_no}:{record['id']}".encode()).digest()
        hi, lo = _ordered_pairs(record["raw"], record["target"], PAIR_COUNT_PER_IMAGE, int.from_bytes(token[:8], "little"))
        bsds_hi.append(identification._apply_memberships(hi, membership))
        bsds_lo.append(identification._apply_memberships(lo, membership))

    capacity = learn_pairwise_2additive(
        (np.concatenate(uded_hi), np.concatenate(uded_lo)),
        (np.concatenate(bsds_hi), np.concatenate(bsds_lo)),
        ridge=stage20.CAPACITY_RIDGE,
    )
    memberships = identification._apply_memberships(raw, membership)
    context = identification._choquet_from_table(memberships, np.asarray(capacity["capacity_table"], float))
    calibration = identification._fit_scalar_calibration(context, target)
    return {
        "descriptors": descriptors,
        "membership": membership,
        "capacity": capacity,
        "calibration": calibration,
        "training_samples": int(len(target)),
        "balanced_capacity_samples": int(capacity["uded_pairs"] + capacity["bsds_pairs"]),
    }


def _official_manifest(out: Path, experiment_id: str) -> Path:
    manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [{
            "name": experiment_id,
            "export": {
                "script": "automation/stage21h_consensus_pairwise_venv_launcher.py",
                "args": ["--export-bsds", "--image-dir", "{image_dir}", "--output-dir", "{output_dir}", "--split", "{split}"],
                "timeout_minutes": 360,
            },
        }],
    }
    path = out / "official_eval_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def _rewrite_summary(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    data["stage"] = EXPERIMENT_ID
    data["role"] = "single_stage21h_consensus_rank_candidate"
    data.pop("frozen_queue", None)
    data["candidate"].update({
        "aggregation": "monotone 2-additive Choquet fitted by equal-domain pairwise logistic ranking",
        "ranking_targets": "UDED outer-training tolerant boundary>background plus BSDS500-train higher>lower 1.5px annotator consensus",
        "pair_count_per_image_per_fit": PAIR_COUNT_PER_IMAGE,
        "bsds_train_images": 200,
        "single_candidate_budget": True,
    })
    data["promotion_rule"] = (
        "Conjunctive: overlap-clean UDED aggregate F1 delta >= +0.002, precision delta >= 0, "
        "recall delta >= -0.003, mean paired fold-F1 delta >= 0, at least 9/15 fold wins, "
        "15/15 converged capacity fits, exact score-support preservation, and completed standard-Berkeley "
        "BSDS500-validation ODS delta >= +0.002 with nonnegative OIS and AP deltas. Loose protocols cannot rescue failure."
    )
    data["stage21h_stop_rule"] = "This is the only Stage-21H candidate; failure ends Stage 21 in synthesis without automatic replacement."
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uded-root", default=str(DEFAULT_UDED))
    parser.add_argument("--out")
    parser.add_argument("--max-side", type=int, default=256)
    parser.add_argument("--thresholds", type=int, default=41)
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--max-positive", type=int, default=10)
    parser.add_argument("--max-negative", type=int, default=8)
    parser.add_argument("--max-abs-corr", type=float, default=0.88)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--export-bsds", action="store_true")
    parser.add_argument("--image-dir")
    parser.add_argument("--output-dir")
    parser.add_argument("--split", default="val")
    parser.add_argument("--max-side-development", type=int, default=256)
    args = parser.parse_args()
    global _BSDS_TRAIN
    _BSDS_TRAIN = _load_bsds_train()
    stage20._fit_candidate = _fit_candidate
    stage20._official_manifest = _official_manifest
    stage20.learn_banks = _learn_control_banks
    spec = {"experiment_id": EXPERIMENT_ID, "label": "consensus_pairwise_2additive_choquet", "descriptors": list(DESCRIPTORS), "order": 1}
    if args.export_bsds:
        if not args.image_dir or not args.output_dir:
            parser.error("--export-bsds requires --image-dir and --output-dir")
        code = stage20.export_bsds(args, spec)
        export_manifest = Path(args.output_dir) / "export_manifest.json"
        metadata = json.loads(export_manifest.read_text(encoding="utf-8"))
        metadata.update({
            "aggregation": "monotone 2-additive Choquet fitted by equal-domain pairwise logistic ranking",
            "development_source": "200 BSDS500-train images plus 14 overlap-clean UDED selection images",
            "consensus_target": "fraction of BSDS-train annotations within fixed 1.5px; higher levels ordered above lower levels",
            "pair_count_per_image": PAIR_COUNT_PER_IMAGE,
            "bsds_validation_ground_truth_read": False,
            "single_stage21h_candidate": True,
        })
        export_manifest.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return code
    code = stage20.run_experiment(args, spec)
    out = Path(args.out) if args.out else ROOT / "results" / "local_dev" / EXPERIMENT_ID
    _rewrite_summary(out / "summary.json")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
