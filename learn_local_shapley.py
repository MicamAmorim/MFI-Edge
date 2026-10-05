from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from math import factorial
from pathlib import Path
import argparse
import json
import os
import time

import numpy as np

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

from benchmark_uded import DEFAULT_UDED, load_uded, prepare
from benchmark_uded_quick import resize_items
from benchmark_uded_stage8_contextual import cv_threshold_score
from prepare_uded_runtime import prepare_uded
from src.ch_mfi import CHMFIConfig, run_ch_mfi
from src.context_maps import analyze_context

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "local_dev" / "shapley_descriptor_importance.json"


def ensure_uded(root: Path):
    if not (root / "test_pair.lst").exists():
        prepare_uded(root)
    return root


def masked_precomputed(pre, mask):
    g = np.asarray(mask, dtype=float).reshape(1, 1, -1)
    return [(w, np.asarray(X) * g, h) for w, X, h in pre]


def coalition_score(mask_int, n_features, items, cfg, thresholds, target):
    mask = np.array([(mask_int >> i) & 1 for i in range(n_features)], dtype=bool)
    if not mask.any():
        if target == "mfi":
            return 0.0
        local_cfg = CHMFIConfig(**{**cfg.__dict__, "controller": "localizer_only"})
        scores = [
            run_ch_mfi(d["pre_img"], local_cfg, precomputed=d["features"], context=d["ch_context"]).score
            for d in items
        ]
        return float(cv_threshold_score(scores, items, n_thresholds=thresholds, n_folds=3)["cv_F1"])

    scores = []
    for d in items:
        pre = masked_precomputed(d["features"], mask)
        r = run_ch_mfi(d["pre_img"], cfg, precomputed=pre, context=d["ch_context"])
        scores.append(r.mfi if target == "mfi" else r.score)
    return float(cv_threshold_score(scores, items, n_thresholds=thresholds, n_folds=3)["cv_F1"])


def exact_shapley_from_table(values, n):
    phi = np.zeros(n, dtype=float)
    nf = factorial(n)
    for i in range(n):
        bit = 1 << i
        for s in range(1 << n):
            if s & bit:
                continue
            k = int(s.bit_count())
            coef = factorial(k) * factorial(n - k - 1) / nf
            phi[i] += coef * (values[s | bit] - values[s])
    z = np.maximum(phi, 0.0)
    if z.sum() > 1e-12:
        z /= z.sum()
    else:
        z[:] = 1.0 / max(n, 1)
    return phi, z


def main():
    ap = argparse.ArgumentParser(description="Exact Shapley descriptor importance for the CH-MFI selection split")
    ap.add_argument("--uded-root", default=str(DEFAULT_UDED))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--max-side", type=int, default=256)
    ap.add_argument("--thresholds", type=int, default=21)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--target", choices=("mfi", "final"), default="final")
    args = ap.parse_args()

    workers = int(args.workers) if args.workers > 0 else min(8, max(1, (os.cpu_count() or 4) - 2))
    root = ensure_uded(Path(args.uded_root))
    raw = resize_items(load_uded(root), int(args.max_side))
    items, names = prepare(raw)
    items = items[0::2]  # selection split only; held-out never used for Shapley learning
    for d in items:
        d["ch_context"] = analyze_context(d["pre_img"])

    n = len(names)
    if n > 12:
        raise ValueError(f"Exact coalition enumeration is disabled for n={n}; use <=12 descriptors")

    cfg = CHMFIConfig(
        name="shapley_reference",
        hierarchy="global_local",
        operator_mode="conditional",
        within_measure={"kind": "power", "q": 0.2},
        controller="bilateral_exp" if args.target == "final" else "mfi_only",
        localizer_mode="adaptive",
        granularity=0.50,
    )

    total = 1 << n
    values = np.full(total, np.nan, dtype=float)
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {
            ex.submit(coalition_score, mask, n, items, cfg, args.thresholds, args.target): mask
            for mask in range(total)
        }
        for j, fut in enumerate(as_completed(futs), start=1):
            mask = futs[fut]
            values[mask] = float(fut.result())
            if j % 8 == 0 or j == total:
                print(f"SHAPLEY coalition {j}/{total}", flush=True)

    # Convert utility to improvement over empty coalition, matching cooperative-game semantics.
    baseline = float(values[0])
    utility = values - baseline
    phi, norm = exact_shapley_from_table(utility, n)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "target": args.target,
        "feature_names": list(names),
        "n_features": n,
        "selection_images": [d["id"] for d in items],
        "baseline_cv_F1": baseline,
        "shapley_values": phi.tolist(),
        "normalized_positive_shapley": norm.tolist(),
        "utility_full_coalition": float(utility[-1]),
        "workers": workers,
        "elapsed_s": time.perf_counter() - t0,
        "reference_config": cfg.__dict__,
        "note": "Learned only on UDED selection images. Held-out images are not used.",
    }
    out.write_text(json.dumps(payload, indent=2, default=float), encoding="utf-8")
    np.save(out.with_suffix(".coalition_utility.npy"), utility.astype(np.float32))
    print("SHAPLEY_DONE", json.dumps(payload, default=float), flush=True)


if __name__ == "__main__":
    main()
