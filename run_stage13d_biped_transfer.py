from __future__ import annotations

"""Stage 13d: frozen Stage-12d transfer to the BIPEDv2 test split.

The BIPED train split is unused. Candidate thresholds and configurations are
loaded from the frozen Stage-12d artifact; no BIPED labels set thresholds.
Metrics are fixed-threshold transfer diagnostics, not tuned benchmark scores.
"""

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

from benchmark_uded_stage7 import bootstrap_delta, fixed_eval
from run_stage13_bsds_transfer import (
    DEFAULT_FROZEN,
    fit_uded_scharr_threshold,
    infer_candidate,
    prepare_external_one,
    unique_frozen_candidates,
)

ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT / "datasets" / "BIPEDv2"
DEFAULT_OUT = ROOT / "results" / "external" / "stage13d_biped_transfer"


def load_test_items(root: Path):
    image_dir = root / "edges" / "imgs" / "test" / "rgbr"
    gt_dir = root / "edges" / "edge_maps" / "test" / "rgbr"
    images = sorted(p for p in image_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    gt_by_stem = {p.stem: p for p in gt_dir.iterdir() if p.suffix.lower() in {".png", ".bmp", ".jpg", ".jpeg"}}
    if len(images) != 50 or len(gt_by_stem) != 50 or any(p.stem not in gt_by_stem for p in images):
        raise RuntimeError("BIPEDv2 test split must contain exactly 50 paired image/GT files")
    items = []
    for path in images:
        with Image.open(path) as im:
            image = np.asarray(im.convert("RGB"))
        gt_path = gt_by_stem[path.stem]
        with Image.open(gt_path) as im:
            gt = np.asarray(im.convert("L"))
        if image.shape[:2] != (720, 1280) or gt.shape != (720, 1280):
            raise RuntimeError(f"Unexpected BIPED resolution for {path.name}: {image.shape}, {gt.shape}")
        items.append({"id": path.stem, "img": image, "gt": (gt >= 128)})
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=str(DEFAULT_DATA))
    ap.add_argument("--frozen", default=str(DEFAULT_FROZEN))
    ap.add_argument("--uded-root", default=None)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--thresholds", type=int, default=61)
    ap.add_argument("--bootstrap", type=int, default=5000)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    frozen_path = Path(args.frozen)
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    candidates = unique_frozen_candidates(frozen)
    if not candidates:
        raise RuntimeError("Frozen Stage-12d artifact contains no representatives")
    uded_root = Path(args.uded_root) if args.uded_root else None
    # Only the Scharr comparator needs a fitted threshold; fit it on UDED, never BIPED.
    from benchmark_uded import DEFAULT_UDED
    baseline_threshold, baseline_fit = fit_uded_scharr_threshold(
        uded_root or DEFAULT_UDED, 256, args.thresholds
    )
    raw_items = load_test_items(Path(args.data_root))
    positive, negative = frozen["positive_bank"], frozen["texture_negative_bank"]
    scores = {str(c["config"]["name"]): [] for c in candidates}
    baseline_scores, eval_items, runtimes = [], [], []
    base_names_ref = None
    for k, raw in enumerate(raw_items, 1):
        t0 = time.perf_counter()
        item, base_names = prepare_external_one(raw)
        if base_names_ref is not None and list(base_names) != base_names_ref:
            raise RuntimeError("Descriptor order changed between BIPED images")
        base_names_ref = list(base_names)
        baseline_scores.append(np.asarray(item["scharr"], np.float32))
        eval_items.append({"id": raw["id"], "gt": raw["gt"]})
        for cand in candidates:
            cfg = cand["config"]
            scores[str(cfg["name"])].append(infer_candidate(item, base_names, positive, negative, cfg)[-1])
        elapsed = time.perf_counter() - t0
        runtimes.append(elapsed)
        print(f"STAGE13D_INFER {k:02d}/50 {raw['id']} {elapsed:.3f}s", flush=True)

    base_fixed, base_counts, base_per = fixed_eval(baseline_scores, eval_items, baseline_threshold)
    rows = [{"method": "Scharr+NMS", "family": "baseline", "threshold_source": "UDED selection only",
             "frozen_threshold": baseline_threshold, **{f"fixed_{k}": float(v) for k, v in base_fixed.items()},
             "delta_fixed_F1_vs_scharr": 0.0, "bootstrap_ci_low": 0.0, "bootstrap_ci_high": 0.0,
             "bootstrap_p_positive": 0.5}]
    per_rows = [{"method": "Scharr+NMS", **x} for x in base_per]
    for i, cand in enumerate(candidates):
        cfg = cand["config"]
        name = str(cfg["name"])
        threshold = float(cand["threshold_fitted_on_all_selection"])
        fixed, counts, per = fixed_eval(scores[name], eval_items, threshold)
        boot = bootstrap_delta(base_counts, counts, n_boot=args.bootstrap, seed=20261340 + i)
        rows.append({"method": name, "family": str(cfg["family"]),
                     "threshold_source": "UDED selection frozen Stage-12d", "frozen_threshold": threshold,
                     **{f"fixed_{k}": float(v) for k, v in fixed.items()},
                     "delta_fixed_F1_vs_scharr": float(fixed["F1"] - base_fixed["F1"]),
                     "bootstrap_ci_low": float(boot["delta_F1_ci95_low"]),
                     "bootstrap_ci_high": float(boot["delta_F1_ci95_high"]),
                     "bootstrap_p_positive": float(boot["p_delta_gt_0"])})
        per_rows.extend({"method": name, **x} for x in per)
    pd.DataFrame(rows).to_csv(out / "external_metrics.csv", index=False)
    pd.DataFrame(per_rows).to_csv(out / "per_image_metrics.csv", index=False)
    summary = {"stage": "13d-biped-frozen-transfer", "dataset": "BIPEDv2", "split": "test",
               "n_images": len(eval_items), "resolution": [1280, 720], "training_split_used": False,
               "candidate_source": str(frozen_path), "baseline_threshold_source": "UDED selection only",
               "threshold_policy": "All reported metrics use frozen thresholds; no BIPED threshold selection or tuning.",
               "evaluation_warning": "Single-annotator BIPED edge-map fixed-threshold diagnostics; not numerically interchangeable with BSDS multi-annotator boundary metrics.",
               "mean_runtime_per_image_s": float(np.mean(runtimes)), "total_inference_runtime_s": float(np.sum(runtimes)),
               "baseline_uded_fit": {k: float(v) for k, v in baseline_fit.items()}, "metrics": rows}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=float), encoding="utf-8")
    print("STAGE13D_BIPED_TRANSFER_DONE", flush=True)


if __name__ == "__main__":
    main()
