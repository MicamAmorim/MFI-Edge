from __future__ import annotations

"""Learn compact scale-specific fuzzy measures on the UDED selection split.

The learner is deliberately lightweight and transparent:
- singleton relevance at each scale comes from descriptor-vs-GT ranking AUC;
- pair interaction estimates reward complementary pairs and penalize redundant
  highly correlated pairs;
- a regularized 2-additive capacity is built from those terms;
- additive and distorted-probability alternatives are exported as controls.

These learned measures are exploratory and must later be repeated on a larger
training split such as BSDS500 train/val before publication claims.
"""

from pathlib import Path
import argparse
import json

import numpy as np
from scipy import ndimage as ndi

from benchmark_uded import DEFAULT_UDED, load_uded, prepare
from benchmark_uded_quick import resize_items
from prepare_uded_runtime import prepare_uded
from src.advanced_fuzzy_v2 import regularized_pair_capacity
from src.ch_mfi import distorted_probability_capacity

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "local_dev" / "scale_capacity_bank.json"


def ensure_uded(root: Path):
    if not (root / "test_pair.lst").exists():
        prepare_uded(root)
    return root


def binary_auc(score, target):
    s = np.asarray(score, float).ravel()
    y = np.asarray(target, bool).ravel()
    finite = np.isfinite(s)
    s, y = s[finite], y[finite]
    np1 = int(y.sum()); nn = int((~y).sum())
    if np1 == 0 or nn == 0:
        return 0.5
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty_like(order, dtype=float)
    ranks[order] = np.arange(1, len(s)+1, dtype=float)
    # Mann-Whitney U / (n_pos*n_neg)
    u = float(ranks[y].sum() - np1*(np1+1)/2.0)
    return float(np.clip(u / (np1*nn), 0.0, 1.0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uded-root", default=str(DEFAULT_UDED))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--max-side", type=int, default=256)
    ap.add_argument("--pair-strength", type=float, default=0.35)
    ap.add_argument("--shrinkage", type=float, default=0.70)
    args = ap.parse_args()

    root = ensure_uded(Path(args.uded_root))
    raw = resize_items(load_uded(root), int(args.max_side))
    items, names = prepare(raw)
    items = items[0::2]  # selection only
    scales = [int(x[0]) for x in items[0]["features"]]
    payload = {
        "feature_names": list(names),
        "selection_images": [d["id"] for d in items],
        "method": "descriptor AUC + pair complementarity/redundancy; selection-only",
        "scales": {},
    }

    for si, scale in enumerate(scales):
        Xs = []
        Ys = []
        for d in items:
            X = np.asarray(d["features"][si][1], float)
            gt = ndi.binary_dilation(np.asarray(d["gt"], bool), iterations=1)
            # Balanced sampling prevents the massive background from dominating correlations.
            pos = np.argwhere(gt)
            neg = np.argwhere(~gt)
            rng = np.random.default_rng(1000 + scale + len(Xs))
            if len(neg) > max(len(pos)*4, 2000):
                neg = neg[rng.choice(len(neg), size=max(len(pos)*4, 2000), replace=False)]
            ids = np.vstack([pos, neg]) if len(pos) else neg
            Xs.append(X[ids[:,0], ids[:,1], :])
            Ys.append(gt[ids[:,0], ids[:,1]])
        Xall = np.concatenate(Xs, axis=0)
        yall = np.concatenate(Ys, axis=0)

        auc = np.array([binary_auc(Xall[:,j], yall) for j in range(Xall.shape[1])], float)
        relevance = np.maximum(auc - 0.5, 0.0) + 1e-4
        relevance /= relevance.sum()
        corr = np.corrcoef(Xall, rowvar=False)
        corr = np.nan_to_num(corr)
        pairs = np.zeros_like(corr)

        for i in range(Xall.shape[1]):
            for j in range(i+1, Xall.shape[1]):
                joint = binary_auc(0.5*(Xall[:,i] + Xall[:,j]), yall)
                complement = max(0.0, joint - max(auc[i], auc[j]))
                redundancy = max(0.0, corr[i,j]) * min(relevance[i], relevance[j])
                val = float(args.pair_strength) * (2.0*complement - redundancy)
                pairs[i,j] = pairs[j,i] = val

        pair_spec = regularized_pair_capacity(relevance, pairs, shrinkage=float(args.shrinkage))
        additive = {"kind":"additive", "weights": relevance.tolist()}
        distorted = distorted_probability_capacity(relevance, gamma=0.85)
        payload["scales"][str(scale)] = {
            "descriptor_auc": auc.tolist(),
            "weights": relevance.tolist(),
            "correlation": corr.tolist(),
            "raw_pair_interactions": pairs.tolist(),
            "additive": additive,
            "distorted_gamma0.85": distorted,
            "regularized_pair": pair_spec,
        }
        print(f"SCALE_CAPACITY scale={scale} weights={np.round(relevance,4).tolist()}", flush=True)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, default=float), encoding="utf-8")
    print("SCALE_CAPACITY_DONE", out, flush=True)


if __name__ == "__main__":
    main()
