from __future__ import annotations

from pathlib import Path
import argparse
import json
import math
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from skimage.io import imread

from src.classical_detectors import detector_score, canny_persistence
from src.conditioning import apply_conditioning
from src.evaluation import average_precision_from_pr, counts_to_prf, roc_auc, tolerant_counts
from src.fuzzy_measures import measure_registry
from src.hybrid import percentile_confidence, mfi_roi, hard_gate
from src.measure_learning import predict_context
from src.pipeline import precompute_multiscale_features, multiscale_from_precomputed
from src.postprocess import gradient_orientation, non_maximum_suppression

ROOT = Path(__file__).resolve().parent
DEFAULT_UDED = ROOT / "external" / "UDED"
MODEL_DIR = ROOT / "benchmark_outputs" / "stage5_measures"
OUT = ROOT / "benchmark_outputs" / "uded_stage5"
SCALES = (25, 13, 7, 5, 3)


def load_uded(root: Path, limit=None):
    pairs = json.loads((root / "test_pair.lst").read_text(encoding="utf-8"))
    if limit is not None:
        pairs = pairs[: int(limit)]
    items = []
    for idx, (ip, gp) in enumerate(pairs, start=1):
        img = imread(root / ip)
        gt = imread(root / gp)
        if gt.ndim == 3:
            gt = gt[..., 0]
        gt = np.asarray(gt)
        if np.issubdtype(gt.dtype, np.integer):
            gt = gt > (0.5 * np.iinfo(gt.dtype).max)
        else:
            gt = gt > 0.5
        items.append({"index": idx, "id": Path(ip).stem, "img_path": ip, "gt_path": gp,
                      "img": img, "gt": gt})
    return items


def prepare(items):
    out = []
    names = None
    for k, d in enumerate(items, start=1):
        print(f"PREP {k:02d}/{len(items)} {d['id']}", flush=True)
        t0 = time.perf_counter()
        pre_img = apply_conditioning(d["img"], "median", size=3)
        pre, names = precompute_multiscale_features(pre_img, SCALES, feature_mode="oriented")
        ori = gradient_orientation(pre_img, 1.0)
        sch = non_maximum_suppression(detector_score(pre_img, "scharr", 1.0), ori)
        sob = non_maximum_suppression(detector_score(pre_img, "sobel", 1.0), ori)
        prew = non_maximum_suppression(detector_score(pre_img, "prewitt", 1.0), ori)
        can = canny_persistence(pre_img)
        out.append({**d, "pre_img": pre_img, "features": pre, "orientation": ori,
                    "scharr": sch, "sobel": sob, "prewitt": prew,
                    "canny_persistence": can, "prepare_s": time.perf_counter() - t0})
    return out, names


def context_for(spec, d, context_model):
    # UDED has no degradation labels. Oracle routers are not deployable here.
    if spec.get("routing") == "estimated":
        return {"context_label": predict_context(d["pre_img"], context_model)}
    return {}


def _threshold_grid(scores, n=61):
    vals = np.concatenate([np.asarray(s, float)[np.isfinite(s)].ravel() for s in scores])
    if not vals.size:
        return np.array([0.0])
    return np.unique(np.quantile(vals, np.linspace(0.01, 0.995, int(n))))


def _variable_tol_curve(scores, gts, beta=1.0, n_thresholds=61, frac_diag=0.0075):
    thresholds = _threshold_grid(scores, n_thresholds)
    rows = []
    per_image = [[] for _ in scores]
    b2 = float(beta) ** 2
    for t in thresholds:
        mp = npred = mg = ngt = 0
        for i, (s, g) in enumerate(zip(scores, gts)):
            tol = max(1, int(round(float(frac_diag) * math.hypot(*g.shape))))
            cnt = tolerant_counts(np.asarray(s) >= float(t), g, tol)
            mp += cnt[0]; npred += cnt[1]; mg += cnt[2]; ngt += cnt[3]
            per_image[i].append(counts_to_prf(*cnt, beta=beta)[2])
        p = mp / max(npred, 1)
        r = mg / max(ngt, 1)
        f = (1 + b2) * p * r / max(b2 * p + r, 1e-12)
        rows.append((float(t), float(p), float(r), float(f)))
    arr = np.asarray(rows, float)
    bi = int(np.nanargmax(arr[:, 3]))
    ap = average_precision_from_pr(arr[:, 1], arr[:, 2])
    eligible = arr[:, 1] >= 0.5
    r50 = float(np.max(arr[eligible, 2])) if np.any(eligible) else 0.0
    return {"threshold": float(arr[bi, 0]), "precision": float(arr[bi, 1]),
            "recall": float(arr[bi, 2]), "ODS": float(arr[bi, 3]),
            "OIS": float(np.mean([max(v) if v else 0.0 for v in per_image])),
            "AP": float(ap), "R50": float(r50), "curve": arr}


def variable_tol_metrics(scores, gts, n_thresholds=61, frac_diag=0.0075):
    f1 = _variable_tol_curve(scores, gts, beta=1.0, n_thresholds=n_thresholds,
                             frac_diag=frac_diag)
    f05 = _variable_tol_curve(scores, gts, beta=0.5, n_thresholds=n_thresholds,
                              frac_diag=frac_diag)
    return {"ODS": f1["ODS"], "OIS": f1["OIS"], "AP": f1["AP"], "R50": f1["R50"],
            "ODS_threshold": f1["threshold"], "ODS_precision": f1["precision"],
            "ODS_recall": f1["recall"], "F05_ODS": f05["ODS"], "F05_OIS": f05["OIS"],
            "ROC_AUC": roc_auc(scores, gts), "curve": f1["curve"]}


def evaluate_measure(spec, items, context_model, roi_q, n_thresholds=61):
    clean = {k: v for k, v in spec.items() if k != "name"}
    scores, gts, covers, fracs, times = [], [], [], [], []
    per_image = []
    for d in items:
        t0 = time.perf_counter()
        _, bits, _ = multiscale_from_precomputed(
            d["features"], d["gt"].shape, family="CF1F2", F1="CL", F2="CL", q=0.1,
            refine_quantile=0.82, heterogeneity_quantile=0.82, dilation_radius=3,
            measure_spec=clean, measure_context=context_for(spec, d, context_model))
        conf = percentile_confidence(bits)
        roi, _ = mfi_roi(conf, float(roi_q), 0, already_confidence=True)
        score = hard_gate(d["scharr"], roi)
        dt = time.perf_counter() - t0
        gd = ndi.binary_dilation(d["gt"], iterations=2)
        cover = float(np.logical_and(roi, gd).sum() / max(gd.sum(), 1))
        scores.append(score); gts.append(d["gt"]); covers.append(cover)
        fracs.append(float(roi.mean())); times.append(dt)
        per_image.append({"id": d["id"], "roi_gt_coverage": cover,
                          "roi_fraction": float(roi.mean()), "runtime_s": dt})
    met = variable_tol_metrics(scores, gts, n_thresholds=n_thresholds)
    return ({**{k: v for k, v in met.items() if k != "curve"},
             "roi_gt_coverage": float(np.mean(covers)),
             "roi_fraction": float(np.mean(fracs)),
             "mean_runtime_s": float(np.mean(times))}, scores, met["curve"], per_image)


def evaluate_baseline(name, scores, gts, n_thresholds=61):
    met = variable_tol_metrics(scores, gts, n_thresholds=n_thresholds)
    return {"method": name, **{k: v for k, v in met.items() if k != "curve"}}


def save_preview(items, scores, threshold, outpath, title, n=8):
    n = min(int(n), len(items))
    fig, axes = plt.subplots(n, 4, figsize=(12, 3 * n))
    if n == 1:
        axes = np.asarray([axes])
    for axrow, d, s in zip(axes, items[:n], scores[:n]):
        pred = np.asarray(s) >= float(threshold)
        axrow[0].imshow(d["img"]); axrow[0].set_title(d["id"])
        axrow[1].imshow(d["gt"], cmap="gray"); axrow[1].set_title("UDED GT")
        axrow[2].imshow(s, cmap="inferno"); axrow[2].set_title("MFI-Edge-SCHARR score")
        axrow[3].imshow(pred, cmap="gray"); axrow[3].set_title("ODS mask")
        for ax in axrow: ax.axis("off")
    fig.suptitle(title); fig.tight_layout(); fig.savefig(outpath, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uded-root", default=str(DEFAULT_UDED))
    ap.add_argument("--model-dir", default=str(MODEL_DIR))
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--thresholds", type=int, default=61)
    args = ap.parse_args()
    uded_root = Path(args.uded_root); model_dir = Path(args.model_dir); out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    learned = json.loads((model_dir / "learned_measures.json").read_text(encoding="utf-8"))
    context_model = json.loads((model_dir / "context_router.json").read_text(encoding="utf-8"))
    validation = pd.read_csv(model_dir / "validation_best_per_measure.csv")
    roi_by_measure = dict(zip(validation.measure.astype(str), validation.roi_q.astype(float)))

    raw = load_uded(uded_root, limit=args.limit)
    items, names = prepare(raw)
    specs = measure_registry(len(names), learned=learned)
    specs = [s for s in specs if s.get("routing") != "oracle"]

    rows, score_cache, per_rows = [], {}, []
    for i, spec in enumerate(specs, start=1):
        name = spec["name"]; rq = float(roi_by_measure.get(name, 0.55))
        print(f"UDED MEASURE [{i}/{len(specs)}] {name} ROI={rq:.2f}", flush=True)
        met, scores, curve, per = evaluate_measure(spec, items, context_model, rq,
                                                   n_thresholds=args.thresholds)
        rows.append({"measure": name, "measure_kind": spec.get("kind", ""),
                     "synthetic_selected_roi_q": rq, **met})
        score_cache[name] = scores
        for d in per: per_rows.append({"measure": name, **d})

    ranking = pd.DataFrame(rows).sort_values(["ODS", "AP", "OIS", "F05_ODS"],
                                             ascending=False).reset_index(drop=True)
    ranking.to_csv(out / "uded_measure_ranking.csv", index=False)
    pd.DataFrame(per_rows).to_csv(out / "uded_per_image_roi.csv", index=False)

    gts = [d["gt"] for d in items]
    baseline_rows = [
        evaluate_baseline("Scharr+NMS", [d["scharr"] for d in items], gts, args.thresholds),
        evaluate_baseline("Sobel+NMS", [d["sobel"] for d in items], gts, args.thresholds),
        evaluate_baseline("Prewitt+NMS", [d["prewitt"] for d in items], gts, args.thresholds),
        evaluate_baseline("Canny-persistence", [d["canny_persistence"] for d in items], gts,
                          args.thresholds),
    ]
    pd.DataFrame(baseline_rows).sort_values("ODS", ascending=False).to_csv(
        out / "uded_classical_baselines.csv", index=False)

    top = ranking.iloc[0]; top_name = str(top.measure)
    save_preview(items, score_cache[top_name], float(top.ODS_threshold),
                 out / "uded_top_measure_preview.png",
                 f"UDED — {top_name}, ODS={top.ODS:.4f}, OIS={top.OIS:.4f}, AP={top.AP:.4f}", n=8)
    for name in ("power_q0.1", "power_q1.5", "sugeno_learned_sum0.60"):
        if name in score_cache:
            row = ranking[ranking.measure == name].iloc[0]
            save_preview(items, score_cache[name], float(row.ODS_threshold),
                         out / f"preview_{name.replace('.', 'p')}.png",
                         f"UDED — {name}, ODS={row.ODS:.4f}", n=6)

    summary = {"dataset": "UDED", "n_images": len(items), "source": "xavysp/UDED",
               "pipeline": "median3 -> oriented multiscale MFI -> synthetic-selected ROI -> Scharr+NMS",
               "aggregation": "CF1F2(CL,CL)", "scales": list(SCALES),
               "tolerance_protocol": "0.75% of each image diagonal, rounded to >=1 px; dilation proxy, not official bipartite BSDS matching",
               "selection_leakage": "fuzzy measures are fit on synthetic fit split; ROI q is selected on synthetic validation, not UDED",
               "top_measure": ranking.iloc[0].to_dict(), "baselines": baseline_rows}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=float), encoding="utf-8")

    print("\nUDED TOP 20")
    print(ranking.head(20)[["measure", "measure_kind", "synthetic_selected_roi_q", "ODS", "OIS",
                            "AP", "F05_ODS", "R50", "ROC_AUC", "roi_gt_coverage"]].to_string(index=False), flush=True)
    print("\nCLASSICAL BASELINES")
    print(pd.DataFrame(baseline_rows).sort_values("ODS", ascending=False).to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
