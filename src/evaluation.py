from __future__ import annotations
import numpy as np
from scipy import ndimage as ndi

EPS = 1e-12

def tolerant_counts(pred, gt, tol=2):
    """Fast BSDS-like tolerant boundary counts (not the official bipartite matcher)."""
    pred = np.asarray(pred, bool)
    gt = np.asarray(gt, bool)
    if tol > 0:
        dp = ndi.binary_dilation(pred, iterations=int(tol))
        dg = ndi.binary_dilation(gt, iterations=int(tol))
    else:
        dp, dg = pred, gt
    matched_pred = np.logical_and(pred, dg).sum()
    matched_gt = np.logical_and(gt, dp).sum()
    return int(matched_pred), int(pred.sum()), int(matched_gt), int(gt.sum())

def counts_to_prf(mp, npred, mg, ngt, beta=1.0):
    p = mp / max(npred, 1)
    r = mg / max(ngt, 1)
    b2 = beta * beta
    f = (1 + b2) * p * r / max(b2 * p + r, EPS)
    return float(p), float(r), float(f)

def tolerant_prf(pred, gt, tol=2, beta=1.0):
    return counts_to_prf(*tolerant_counts(pred, gt, tol), beta=beta)

def _thresholds_from_scores(scores, n=99):
    vals = np.concatenate([np.asarray(s, float)[np.isfinite(s)].ravel() for s in scores])
    if vals.size == 0:
        return np.array([0.0])
    qs = np.linspace(0.01, 0.995, n)
    return np.unique(np.quantile(vals, qs))

def pr_curve(scores, gts, tol=2, n_thresholds=99, beta=1.0):
    thresholds = _thresholds_from_scores(scores, n_thresholds)
    rows = []
    for t in thresholds:
        mp = npred = mg = ngt = 0
        for score, gt in zip(scores, gts):
            c = tolerant_counts(np.asarray(score) >= t, gt, tol)
            mp += c[0]; npred += c[1]; mg += c[2]; ngt += c[3]
        p, r, f = counts_to_prf(mp, npred, mg, ngt, beta=beta)
        rows.append((float(t), p, r, f))
    return np.asarray(rows, float)

def average_precision_from_pr(precision, recall):
    order = np.argsort(recall)
    r = np.asarray(recall)[order]
    p = np.asarray(precision)[order]
    p = np.maximum.accumulate(p[::-1])[::-1]
    r = np.concatenate([[0.0], r, [1.0]])
    p = np.concatenate([[p[0] if p.size else 0.0], p, [0.0]])
    return float(np.trapezoid(p, r))

def roc_auc(scores, gts):
    """Pixel ROC-AUC; supplemental only (class imbalance makes PR metrics preferable)."""
    y = np.concatenate([np.asarray(g, bool).ravel() for g in gts]).astype(np.uint8)
    s = np.concatenate([np.asarray(x, float).ravel() for x in scores])
    pos = s[y == 1]; neg = s[y == 0]
    if pos.size == 0 or neg.size == 0:
        return float("nan")
    from scipy.stats import rankdata
    ranks = rankdata(np.concatenate([pos, neg]), method="average")
    rpos = ranks[:pos.size].sum()
    auc = (rpos - pos.size * (pos.size + 1) / 2.0) / (pos.size * neg.size)
    return float(auc)

def benchmark_metrics(scores, gts, tol=2, n_thresholds=99, beta=1.0):
    """Return ODS, OIS, AP, R50, pixel ROC-AUC and their thresholds."""
    curve = pr_curve(scores, gts, tol=tol, n_thresholds=n_thresholds, beta=beta)
    best_idx = int(np.nanargmax(curve[:, 3]))
    ods_t, ods_p, ods_r, ods = curve[best_idx]
    image_best = []
    for s, g in zip(scores, gts):
        c = pr_curve([s], [g], tol=tol, n_thresholds=n_thresholds, beta=beta)
        image_best.append(float(np.max(c[:, 3])))
    ois = float(np.mean(image_best))
    ap = average_precision_from_pr(curve[:, 1], curve[:, 2])
    eligible = curve[:, 1] >= 0.5
    r50 = float(np.max(curve[eligible, 2])) if np.any(eligible) else 0.0
    auc = roc_auc(scores, gts)
    return {
        "ODS": float(ods), "ODS_threshold": float(ods_t),
        "ODS_precision": float(ods_p), "ODS_recall": float(ods_r),
        "OIS": ois, "AP": ap, "R50": r50, "ROC_AUC": auc,
        "curve": curve,
    }

def best_f1(score, gt, tol=2, n=60):
    m = benchmark_metrics([score], [gt], tol=tol, n_thresholds=n, beta=1.0)
    return {"F1":m["ODS"], "threshold":m["ODS_threshold"],
            "precision":m["ODS_precision"], "recall":m["ODS_recall"]}
