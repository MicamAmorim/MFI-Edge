from __future__ import annotations

"""Learn descriptor Shapley values separately for local image regimes.

This is deliberately selection-only.  The utility is a regime-restricted pixel
F1 proxy (GT is dilated by one pixel); it is used for feature attribution/gating,
not reported as the official boundary benchmark metric.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from math import factorial
from pathlib import Path
import argparse
import json
import os

import numpy as np
from scipy import ndimage as ndi

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

from benchmark_uded import DEFAULT_UDED, load_uded, prepare
from benchmark_uded_quick import resize_items
from prepare_uded_runtime import prepare_uded
from src.ch_mfi_v2 import CHMFIv2Config, run_ch_mfi_v2
from src.context_maps import analyze_context, regime_soft_weights

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "local_dev" / "regime_shapley.json"
REGIMES = ("clean", "texture", "blur", "noise")


def ensure_uded(root: Path):
    if not (root / "test_pair.lst").exists():
        prepare_uded(root)
    return root


def _masked_pre(pre, mask):
    g = np.asarray(mask, float).reshape(1, 1, -1)
    return [(w, np.asarray(X) * g, h) for w, X, h in pre]


def _regime_f1(scores, items, regime: str, n_thresholds: int = 21):
    vals = np.concatenate([np.asarray(s, float).ravel() for s in scores])
    thr = np.unique(np.quantile(vals[np.isfinite(vals)], np.linspace(0.05, 0.98, int(n_thresholds))))
    best = 0.0
    for t in thr:
        tp = fp = fn = 0.0
        for s, d in zip(scores, items):
            rw = np.asarray(d["regime_weights"][regime], float)
            mask = rw >= 0.40
            gt = ndi.binary_dilation(np.asarray(d["gt"], bool), iterations=1)
            pred = np.asarray(s) >= float(t)
            # Soft membership weighting prevents hard regime boundaries dominating attribution.
            w = rw * mask
            tp += float(np.sum(w * (pred & gt)))
            fp += float(np.sum(w * (pred & ~gt)))
            fn += float(np.sum(w * (~pred & gt)))
        p = tp / max(tp + fp, 1e-12)
        r = tp / max(tp + fn, 1e-12)
        f = 2.0 * p * r / max(p + r, 1e-12)
        best = max(best, f)
    return float(best)


def coalition_utility(mask_int, n_features, items, cfg, regime, thresholds, target):
    mask = np.array([(mask_int >> i) & 1 for i in range(n_features)], dtype=bool)
    if not mask.any():
        return 0.0
    scores = []
    for d in items:
        r = run_ch_mfi_v2(
            d["pre_img"], cfg,
            precomputed=_masked_pre(d["features"], mask),
            context=d["ch_context"],
        )
        scores.append(r.mfi if target == "mfi" else r.score)
    return _regime_f1(scores, items, regime, thresholds)


def exact_shapley(values, n):
    phi = np.zeros(n, float)
    nf = factorial(n)
    for i in range(n):
        bit = 1 << i
        for s in range(1 << n):
            if s & bit:
                continue
            k = int(s.bit_count())
            coef = factorial(k) * factorial(n-k-1) / nf
            phi[i] += coef * (values[s | bit] - values[s])
    pos = np.maximum(phi, 0.0)
    if pos.sum() <= 1e-12:
        pos[:] = 1.0
    pos /= pos.sum()
    return phi, pos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uded-root", default=str(DEFAULT_UDED))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--max-side", type=int, default=256)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--thresholds", type=int, default=21)
    ap.add_argument("--target", choices=("mfi", "final"), default="final")
    ap.add_argument("--regimes", default="all", help="all or comma separated clean,texture,blur,noise")
    args = ap.parse_args()

    workers = args.workers or min(8, max(1, (os.cpu_count() or 4)-2))
    root = ensure_uded(Path(args.uded_root))
    raw = resize_items(load_uded(root), int(args.max_side))
    items, names = prepare(raw)
    items = items[0::2]  # selection only
    for d in items:
        d["ch_context"] = analyze_context(d["pre_img"])
        d["regime_weights"] = regime_soft_weights(d["ch_context"])

    n = len(names)
    if n > 12:
        raise ValueError("exact regime Shapley intentionally limited to <=12 descriptors")
    regimes = REGIMES if args.regimes == "all" else tuple(x.strip() for x in args.regimes.split(",") if x.strip())
    cfg = CHMFIv2Config(
        name="regime_shapley_reference",
        hierarchy="global_local",
        operator_mode="conditional",
        aggregation_variant="standard",
        within_measure={"kind":"power", "q":0.2},
        controller="bilateral_exp" if args.target == "final" else "mfi_only",
        localizer_mode="adaptive",
        granularity=0.5,
    )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "target": args.target,
        "feature_names": list(names),
        "selection_images": [d["id"] for d in items],
        "utility": "regime-weighted pixel F1 proxy; selection-only; not official boundary ODS",
        "regimes": {},
    }

    for regime in regimes:
        if regime not in REGIMES:
            raise ValueError(regime)
        cache_path = out.with_name(out.stem + f".{regime}.coalitions.npy")
        total = 1 << n
        values = np.full(total, np.nan, float)
        if cache_path.exists():
            old = np.load(cache_path)
            if old.shape == values.shape:
                values[:] = old
        pending = [m for m in range(total) if not np.isfinite(values[m])]
        with ThreadPoolExecutor(max_workers=int(workers)) as ex:
            futs = {
                ex.submit(coalition_utility, m, n, items, cfg, regime, args.thresholds, args.target): m
                for m in pending
            }
            for j, fut in enumerate(as_completed(futs), start=1):
                m = futs[fut]
                values[m] = float(fut.result())
                if j % 8 == 0 or j == len(pending):
                    np.save(cache_path, values.astype(np.float32))
                    print(f"REGIME_SHAPLEY {regime} {j}/{len(pending)}", flush=True)
        utility = values - float(values[0])
        phi, norm = exact_shapley(utility, n)
        payload["regimes"][regime] = {
            "shapley_values": phi.tolist(),
            "normalized_positive_shapley": norm.tolist(),
            "full_coalition_utility": float(utility[-1]),
        }
        out.write_text(json.dumps(payload, indent=2, default=float), encoding="utf-8")

    print("REGIME_SHAPLEY_DONE", out, flush=True)


if __name__ == "__main__":
    main()
