from __future__ import annotations

"""Stage 13a — frozen external transfer to BSDS500.

Purpose
-------
Evaluate the Stage-12d frozen representatives on an external dataset without
re-fitting feature banks or candidate hyperparameters on BSDS.  Candidate
thresholds come from UDED selection only.  The Scharr baseline threshold is
re-fitted on UDED selection only so all fixed-threshold comparisons are fair.

IMPORTANT: this script uses a consensus-thresholded BSDS ground truth and the
project's tolerant-dilation matcher.  It is an external-transfer diagnostic,
NOT the official Berkeley benchmark.  Official multi-annotator bipartite
matching remains a separate publication-grade stage.
"""

from pathlib import Path
import argparse
import json
import math
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

from benchmark_uded import DEFAULT_UDED, load_uded
from benchmark_uded_quick import resize_items
from benchmark_uded_stage7 import bootstrap_delta, fixed_eval, selection_metric, tolerance_error_map
from prepare_uded_runtime import prepare_uded
from run_stage12b_fuzzy_signature import prepare, membership_stack
from src.bipolar_fuzzy import (
    distorted_choquet,
    normalized_separable_bicapacity,
    ratio_control,
    context_gate,
)
from src.bsds import download_bsds_subset, load_image, load_gt
from src.classical_detectors import detector_score
from src.conditioning import apply_conditioning
from src.postprocess import gradient_orientation, non_maximum_suppression

ROOT = Path(__file__).resolve().parent
DEFAULT_FROZEN = ROOT / "results" / "local_dev" / "stage12d_bipolar_cv" / "frozen_candidates.json"
DEFAULT_BSDS = ROOT / "datasets" / "BSDS500"
DEFAULT_OUT = ROOT / "results" / "external" / "stage13a_bsds_transfer"


def list_bsds_ids(root: Path, split: str) -> list[str]:
    local = root / "images" / split
    if local.exists():
        ids = sorted(p.stem for p in local.glob("*.jpg"))
        if ids:
            return ids
    url = f"https://api.github.com/repos/BIDS/BSDS500/contents/BSDS500/data/images/{split}"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    ids = sorted(Path(x["name"]).stem for x in r.json() if str(x.get("name", "")).lower().endswith(".jpg"))
    if not ids:
        raise RuntimeError(f"No BSDS ids found for split={split}")
    return ids


def load_bsds_items(root: Path, split: str, consensus: float, limit: int | None, max_side: int):
    ids = list_bsds_ids(root, split)
    if limit is not None and int(limit) > 0:
        ids = ids[: int(limit)]
    download_bsds_subset(root, split=split, ids=ids)
    raw = []
    for k, iid in enumerate(ids, start=1):
        print(f"BSDS_LOAD {k:03d}/{len(ids)} {iid}", flush=True)
        img = load_image(root, iid, split=split)
        prob, gt = load_gt(root, iid, split=split, consensus=float(consensus))
        raw.append({"id": str(iid), "img": img, "gt": gt, "gt_prob": prob})
    return resize_items(raw, max_side=max_side)


def scharr_score(item):
    pre = apply_conditioning(item["img"], "median", size=3)
    ori = gradient_orientation(pre, 1.0)
    return non_maximum_suppression(detector_score(pre, "scharr", 1.0), ori).astype(np.float32)


def fit_uded_scharr_threshold(uded_root: Path, max_side: int, n_thresholds: int):
    if not (uded_root / "test_pair.lst").exists():
        prepare_uded(uded_root)
    raw = resize_items(load_uded(uded_root), max_side=max_side)
    selection = raw[0::2]
    scores = [scharr_score(d) for d in selection]
    pseudo_items = [{"id": d["id"], "gt": d["gt"]} for d in selection]
    fit = selection_metric(scores, pseudo_items, n_thresholds=n_thresholds)
    return float(fit["threshold"]), fit


def unique_frozen_candidates(frozen: dict):
    out = []
    seen = set()
    # Predeclared families only; overall may duplicate positive_control.
    for key in ("overall", "positive_control", "bicapacity", "ratio_control"):
        rec = frozen.get("candidates", {}).get(key)
        if not rec:
            continue
        cfg = rec["config"]
        name = str(cfg["name"])
        if name in seen:
            continue
        seen.add(name)
        out.append({"key": key, **rec})
    return out


def prepare_external_one(raw_item):
    items, base_names = prepare([raw_item])
    return items[0], base_names


def infer_candidate(item, base_names, positive, negative, cfg):
    pm, pw = membership_stack(item, base_names, positive, "edge")
    nm, nw = membership_stack(item, base_names, negative, "texture")

    gp = float(cfg["gamma_plus"])
    pos = distorted_choquet(pm, pw, gp)

    family = str(cfg["family"])
    if family == "positive_control":
        neg = np.zeros_like(pos, dtype=np.float32)
        ctx = pos
    else:
        gm = float(cfg["gamma_minus"])
        neg = distorted_choquet(nm, nw, gm)
        lam = float(cfg["lambda"])
        if family == "separable_bicapacity":
            ctx = normalized_separable_bicapacity(pos, neg, lam)
        elif family == "ratio_control":
            ctx = ratio_control(pos, neg, lam)
        else:
            raise ValueError(f"Unsupported frozen family: {family}")

    score = context_gate(item["scharr"], ctx, float(cfg["strength"]), float(cfg["floor"]))
    return pos.astype(np.float32), neg.astype(np.float32), np.asarray(ctx, np.float32), np.asarray(score, np.float32)


def save_preview(items, base_scores, candidate_payload, candidate_name, threshold, outpath: Path, n=6):
    n = min(int(n), len(items), len(base_scores), len(candidate_payload))
    fig, axes = plt.subplots(n, 8, figsize=(24, 3.0 * n))
    if n == 1:
        axes = np.asarray([axes])
    for row, d, bs, payload in zip(axes, items[:n], base_scores[:n], candidate_payload[:n]):
        pos, neg, ctx, score = payload
        pred = np.asarray(score) >= float(threshold)
        tol = max(1, int(round(.0075 * math.hypot(*d["gt"].shape))))
        err = tolerance_error_map(d["gt"], pred, tol)
        views = [
            (d["img"], f'{d["id"]}\nOriginal', None),
            (d["gt"], "Consensus GT", "gray"),
            (bs, "Scharr+NMS", "gray"),
            (pos, "Positive fuzzy", "inferno"),
            (neg, "Texture / anti", "magma"),
            (ctx, "Frozen context", "inferno"),
            (score, "Frozen gated score", "gray"),
            (err, "TP / FP / FN", None),
        ]
        for ax, (im, title, cmap) in zip(row, views):
            ax.imshow(im, cmap=cmap)
            ax.set_title(title)
            ax.axis("off")
    fig.suptitle(candidate_name)
    fig.tight_layout()
    fig.savefig(outpath, dpi=160, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frozen", default=str(DEFAULT_FROZEN))
    ap.add_argument("--bsds-root", default=str(DEFAULT_BSDS))
    ap.add_argument("--uded-root", default=str(DEFAULT_UDED))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--split", default="test", choices=("train", "val", "test"))
    ap.add_argument("--consensus", type=float, default=.5)
    ap.add_argument("--max-side", type=int, default=256)
    ap.add_argument("--thresholds", type=int, default=61)
    ap.add_argument("--bootstrap", type=int, default=5000)
    ap.add_argument("--limit", type=int, default=0, help="0 = all images; use only for smoke tests before the frozen test run")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    frozen_path = Path(args.frozen)
    if not frozen_path.exists():
        raise FileNotFoundError(
            f"Missing frozen Stage-12d candidates: {frozen_path}. Run Stage 12d first."
        )
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    positive = frozen["positive_bank"]
    negative = frozen["texture_negative_bank"]
    candidates = unique_frozen_candidates(frozen)

    baseline_threshold, baseline_fit = fit_uded_scharr_threshold(
        Path(args.uded_root), args.max_side, args.thresholds
    )
    print(f"STAGE13_BASELINE_UDED_THRESHOLD {baseline_threshold:.8f}", flush=True)

    raw_items = load_bsds_items(
        Path(args.bsds_root), args.split, args.consensus,
        None if int(args.limit) <= 0 else int(args.limit), args.max_side,
    )
    print(f"STAGE13_BSDS n={len(raw_items)} split={args.split}", flush=True)

    base_scores: list[np.ndarray] = []
    scores_by_name = {str(c["config"]["name"]): [] for c in candidates}
    preview_payload = {str(c["config"]["name"]): [] for c in candidates}
    eval_items = []
    base_names_ref = None
    runtimes = []

    for k, raw in enumerate(raw_items, start=1):
        t0 = time.perf_counter()
        item, base_names = prepare_external_one(raw)
        if base_names_ref is None:
            base_names_ref = list(base_names)
        elif list(base_names) != base_names_ref:
            raise RuntimeError("Descriptor order changed between BSDS images")
        base_scores.append(np.asarray(item["scharr"], np.float32))
        eval_items.append({"id": raw["id"], "gt": raw["gt"], "img": raw["img"]})
        for cand in candidates:
            cfg = cand["config"]
            name = str(cfg["name"])
            payload = infer_candidate(item, base_names, positive, negative, cfg)
            scores_by_name[name].append(payload[-1])
            if len(preview_payload[name]) < 6:
                preview_payload[name].append(payload)
        elapsed = time.perf_counter() - t0
        runtimes.append(elapsed)
        print(f"STAGE13_INFER {k:03d}/{len(raw_items)} {raw['id']} {elapsed:.3f}s", flush=True)

    base_fixed, base_counts, base_per = fixed_eval(base_scores, eval_items, baseline_threshold)
    base_diag = selection_metric(base_scores, eval_items, n_thresholds=args.thresholds)

    rows = [{
        "method": "Scharr+NMS",
        "family": "baseline",
        "threshold_source": "UDED selection only",
        "frozen_threshold": baseline_threshold,
        **{f"fixed_{k}": float(v) for k, v in base_fixed.items()},
        "delta_fixed_F1_vs_scharr": 0.0,
        "bootstrap_ci_low": 0.0,
        "bootstrap_ci_high": 0.0,
        "bootstrap_p_positive": 0.5,
        "diagnostic_ODS": float(base_diag["ODS"]),
        "diagnostic_OIS": float(base_diag["OIS"]),
        "diagnostic_AP": float(base_diag["AP"]),
    }]

    per_rows = [{"method": "Scharr+NMS", **x} for x in base_per]

    for i, cand in enumerate(candidates):
        cfg = cand["config"]
        name = str(cfg["name"])
        threshold = float(cand["threshold_fitted_on_all_selection"])
        fixed, counts, per = fixed_eval(scores_by_name[name], eval_items, threshold)
        boot = bootstrap_delta(base_counts, counts, n_boot=args.bootstrap, seed=20261300 + i)
        diag = selection_metric(scores_by_name[name], eval_items, n_thresholds=args.thresholds)
        rows.append({
            "method": name,
            "family": str(cfg["family"]),
            "threshold_source": "UDED selection frozen Stage-12d",
            "frozen_threshold": threshold,
            **{f"fixed_{k}": float(v) for k, v in fixed.items()},
            "delta_fixed_F1_vs_scharr": float(fixed["F1"] - base_fixed["F1"]),
            "bootstrap_ci_low": float(boot["delta_F1_ci95_low"]),
            "bootstrap_ci_high": float(boot["delta_F1_ci95_high"]),
            "bootstrap_p_positive": float(boot["p_delta_gt_0"]),
            "diagnostic_ODS": float(diag["ODS"]),
            "diagnostic_OIS": float(diag["OIS"]),
            "diagnostic_AP": float(diag["AP"]),
        })
        per_rows.extend({"method": name, **x} for x in per)
        save_preview(
            eval_items, base_scores, preview_payload[name], name, threshold,
            out / f"preview_{cfg['family']}.png",
        )

    metrics = pd.DataFrame(rows)
    metrics.to_csv(out / "external_metrics.csv", index=False)
    pd.DataFrame(per_rows).to_csv(out / "per_image_metrics.csv", index=False)

    summary = {
        "stage": "13a-bsds-frozen-transfer",
        "dataset": "BSDS500",
        "split": args.split,
        "n_images": len(eval_items),
        "max_side": int(args.max_side),
        "consensus_threshold": float(args.consensus),
        "candidate_source": str(frozen_path),
        "candidate_selection": "frozen before BSDS; no BSDS labels used for feature-bank, hyperparameter, or fixed-threshold fitting",
        "baseline_threshold_source": "UDED selection only",
        "baseline_uded_fit": {k: float(v) for k, v in baseline_fit.items()},
        "evaluation_warning": (
            "Consensus-thresholded BSDS GT + tolerant-dilation matcher at 0.75% diagonal. "
            "This is NOT official Berkeley bipartite matching. Diagnostic ODS/OIS use BSDS labels only for curve description and are not model-selection metrics."
        ),
        "mean_runtime_per_image_s": float(np.mean(runtimes)) if runtimes else 0.0,
        "total_inference_runtime_s": float(np.sum(runtimes)),
        "metrics": rows,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=float), encoding="utf-8")

    print("\nSTAGE13A_EXTERNAL_METRICS", flush=True)
    print(metrics.to_string(index=False), flush=True)
    print("STAGE13A_BSDS_TRANSFER_DONE", flush=True)


if __name__ == "__main__":
    main()
