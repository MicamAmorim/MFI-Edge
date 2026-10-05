from __future__ import annotations

"""Stage 12b — fixed Scharr + fuzzy/non-additive signature evidence.

Questions
---------
1. Does a non-additive distorted-capacity Choquet aggregation exploit the
   Stage-11/12 signature better than the additive analytical score?
2. Is there useful texture/anti-edge evidence that should be aggregated in a
   separate bank and contrasted with positive boundary evidence?

All feature selection and hyperparameter ranking uses selection images only.
Held-out images are evaluated only for the top selection-ranked candidates with
frozen thresholds.  Scharr+NMS remains the localizer throughout this stage.
"""

from pathlib import Path
import argparse
import json
import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from benchmark_uded import DEFAULT_UDED, SCALES, load_uded
from benchmark_uded_quick import resize_items
from benchmark_uded_stage7 import bootstrap_delta, fixed_eval, selection_metric, tolerance_error_map
from benchmark_uded_stage8_contextual import cv_threshold_score
from prepare_uded_runtime import prepare_uded
from src.classical_detectors import detector_score
from src.conditioning import apply_conditioning
from src.edge_signature import EPS, GROUPS, correlation_matrix, pair_summary
from src.edge_signature_relational import extract_relational_samples, relational_signature_tensor
from src.pipeline import precompute_multiscale_features
from src.postprocess import gradient_orientation, non_maximum_suppression

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "local_dev" / "stage12b_fuzzy_signature"


def ensure_uded(root: Path):
    if not (root / "test_pair.lst").exists():
        prepare_uded(root)
    return root


def prepare(items):
    out = []
    names = None
    for k, d in enumerate(items, start=1):
        print(f"STAGE12B_PREP {k:02d}/{len(items)} {d['id']}", flush=True)
        pre_img = apply_conditioning(d["img"], "median", size=3)
        pre, names = precompute_multiscale_features(pre_img, SCALES, feature_mode="oriented_ms")
        ori = gradient_orientation(pre_img, 1.0)
        scharr = non_maximum_suppression(detector_score(pre_img, "scharr", 1.0), ori)
        out.append({**d, "pre_img": pre_img, "features": pre, "orientation": ori, "scharr": scharr})
    return out, names


def _select_bank(samples, desired_direction: float, max_features: int, max_abs_corr: float,
                 min_auc: float, exclude=()):
    """Select edge-oriented (+1) or texture-oriented (-1) edge-v-texture features."""
    tex = pair_summary(samples, "texture")
    rows = [r for r in tex if float(r["direction"]) == float(desired_direction)]
    rows.sort(key=lambda r: (float(r["auc_separation"]), float(r["mutual_information"])), reverse=True)
    corr = correlation_matrix(samples, hard_negative_groups=("texture",))
    idx = {n: i for i, n in enumerate(samples.feature_names)}
    edge_code, tex_code = GROUPS.index("edge"), GROUPS.index("texture")
    chosen = []
    excluded = set(str(x) for x in exclude)
    for r in rows:
        name = str(r["feature"])
        if name in excluded or float(r["auc_separation"]) < float(min_auc):
            continue
        j = idx[name]
        if any(abs(float(corr[j, idx[c["feature"]]])) > float(max_abs_corr) for c in chosen):
            continue
        ev = samples.X[samples.groups == edge_code, j]
        tv = samples.X[samples.groups == tex_code, j]
        em, tm = float(np.median(ev)), float(np.median(tv))
        q25, q75 = np.quantile(np.concatenate([ev, tv]), [.25, .75])
        scale = float(max(q75 - q25, .05))
        # Base weights derive only from threshold-free separation on selection.
        strength = max(float(r["auc_separation"]) - .5, 0.0) * (1.0 + float(r["mutual_information"]))
        chosen.append({
            "feature": name,
            "weight": float(strength),
            "edge_direction": float(desired_direction),
            "midpoint": float(.5 * (em + tm)),
            "scale": scale,
            "edge_median": em,
            "texture_median": tm,
            "texture_auc": float(r["auc_separation"]),
            "mutual_information": float(r["mutual_information"]),
        })
        if len(chosen) >= int(max_features):
            break
    z = sum(float(x["weight"]) for x in chosen) or 1.0
    for x in chosen:
        x["weight"] = float(x["weight"]) / z
    return chosen


def membership_stack(item, feature_names, spec, target="edge"):
    """Return HxWxK memberships and normalized singleton weights.

    target='edge' orients every feature toward boundary evidence.
    target='texture' orients it toward texture / anti-boundary evidence.
    """
    tensor, names = relational_signature_tensor(item, feature_names)
    index = {n: i for i, n in enumerate(names)}
    mus = []
    ws = []
    for row in spec:
        x = np.asarray(tensor[..., index[str(row["feature"])]], float)
        edge_direction = float(row["edge_direction"])
        direction = edge_direction if target == "edge" else -edge_direction
        z = direction * (x - float(row["midpoint"])) / max(float(row["scale"]), EPS)
        mu = 1.0 / (1.0 + np.exp(-np.clip(z, -20.0, 20.0)))
        mus.append(mu.astype(np.float32))
        ws.append(float(row["weight"]))
    if not mus:
        return np.empty((*tensor.shape[:2], 0), np.float32), np.empty(0, float)
    w = np.asarray(ws, float)
    w /= max(float(w.sum()), EPS)
    return np.stack(mus, axis=-1), w


def distorted_choquet(memberships: np.ndarray, weights: np.ndarray, gamma: float) -> np.ndarray:
    """Choquet integral using m(A)=(sum_{i in A} w_i)^gamma.

    gamma=1 is the additive weighted-mean control. gamma<1 rewards distributed
    support / redundancy tolerance; gamma>1 is more selective about coalitions.
    """
    X = np.asarray(memberships, float)
    if X.shape[-1] == 0:
        return np.zeros(X.shape[:2], np.float32)
    w = np.asarray(weights, float)
    w = w / max(float(w.sum()), EPS)
    order = np.argsort(X, axis=-1)
    xs = np.take_along_axis(X, order, axis=-1)
    ww = np.take_along_axis(np.broadcast_to(w, X.shape), order, axis=-1)
    suffix = np.flip(np.cumsum(np.flip(ww, axis=-1), axis=-1), axis=-1)
    cap = np.power(np.clip(suffix, 0.0, 1.0), float(gamma))
    prev = np.concatenate([np.zeros((*xs.shape[:-1], 1), dtype=float), xs[..., :-1]], axis=-1)
    out = np.sum((xs - prev) * cap, axis=-1)
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def combine_dual(pos, neg, kind: str, lam: float):
    p = np.asarray(pos, np.float32)
    n = np.asarray(neg, np.float32)
    l = float(lam)
    if kind == "product":
        return np.clip(p * (1.0 - np.clip(l * n, 0.0, 1.0)), 0.0, 1.0)
    if kind == "contrast":
        return np.clip(0.5 + 0.5 * (p - l * n), 0.0, 1.0)
    if kind == "ratio":
        # weak symmetric prior avoids unstable 0/0 in unstructured regions
        return np.clip((p + .05) / (p + l * n + .10), 0.0, 1.0)
    raise ValueError(kind)


def gate(localizer, context, strength: float, floor: float):
    c = np.clip(np.asarray(context, np.float32), 0.0, 1.0)
    g = float(floor) + (1.0 - float(floor)) * np.power(c, float(strength))
    return np.asarray(localizer, np.float32) * g.astype(np.float32)


def save_preview(items, pos_maps, neg_maps, ctx_maps, scores, threshold, outpath, title, n=6):
    n = min(int(n), len(items))
    fig, axes = plt.subplots(n, 8, figsize=(24, 3.0 * n))
    if n == 1:
        axes = np.asarray([axes])
    for row, d, p, nmap, c, s in zip(axes, items[:n], pos_maps[:n], neg_maps[:n], ctx_maps[:n], scores[:n]):
        pred = np.asarray(s) >= float(threshold)
        tol = max(1, int(round(.0075 * math.hypot(*d["gt"].shape))))
        err = tolerance_error_map(pred, d["gt"], tol)
        views = [
            (d["img"], d["id"], None),
            (d["gt"], "GT", "gray"),
            (d["scharr"], "Scharr+NMS", "gray"),
            (p, "Positive fuzzy", "inferno"),
            (nmap, "Texture / anti", "magma"),
            (c, "Combined context", "inferno"),
            (s, "Gated score", "gray"),
            (err, "TP / FP / FN", None),
        ]
        for ax, (im, ttl, cmap) in zip(row, views):
            ax.imshow(im, cmap=cmap); ax.set_title(ttl); ax.axis("off")
    fig.suptitle(title); fig.tight_layout(); fig.savefig(outpath, dpi=160, bbox_inches="tight"); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uded-root", default=str(DEFAULT_UDED))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--max-side", type=int, default=256)
    ap.add_argument("--thresholds", type=int, default=41)
    ap.add_argument("--max-positive", type=int, default=10)
    ap.add_argument("--max-negative", type=int, default=8)
    ap.add_argument("--max-abs-corr", type=float, default=.88)
    ap.add_argument("--bootstrap", type=int, default=5000)
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    raw = resize_items(load_uded(ensure_uded(Path(args.uded_root))), args.max_side)
    items, base_names = prepare(raw)
    selection_items, heldout_items = items[0::2], items[1::2]

    samples = extract_relational_samples(selection_items, base_names, 2500, seed=20261005)
    positive = _select_bank(samples, +1.0, args.max_positive, args.max_abs_corr, .56)
    negative = _select_bank(samples, -1.0, args.max_negative, args.max_abs_corr, .54,
                            exclude=[x["feature"] for x in positive])
    (out / "evidence_banks.json").write_text(json.dumps({
        "selection_only": True, "positive": positive, "texture_negative": negative,
    }, indent=2), encoding="utf-8")

    print("STAGE12B_BANKS", json.dumps({"positive": len(positive), "negative": len(negative)}), flush=True)

    def bank_data(split_items):
        pm, pw, nm, nw = [], None, [], None
        for d in split_items:
            a, aw = membership_stack(d, base_names, positive, "edge")
            b, bw = membership_stack(d, base_names, negative, "texture")
            pm.append(a); nm.append(b); pw = aw; nw = bw
        return pm, pw, nm, nw

    sel_pm, pw, sel_nm, nw = bank_data(selection_items)
    tst_pm, _, tst_nm, _ = bank_data(heldout_items)
    sel_scharr = [np.asarray(d["scharr"], np.float32) for d in selection_items]
    tst_scharr = [np.asarray(d["scharr"], np.float32) for d in heldout_items]

    base_cv = cv_threshold_score(sel_scharr, selection_items, n_thresholds=args.thresholds, n_folds=3)
    base_opt = selection_metric(sel_scharr, selection_items, args.thresholds)
    base_met, base_counts, _ = fixed_eval(tst_scharr, heldout_items, float(base_opt["threshold"]))

    gammas = (.55, .75, 1.0, 1.35, 1.75)
    floors = (.10, .25, .50)
    strengths = (1.0, 2.0)

    sel_pos = {g: [distorted_choquet(x, pw, g) for x in sel_pm] for g in gammas}
    tst_pos = {g: [distorted_choquet(x, pw, g) for x in tst_pm] for g in gammas}
    has_negative = len(negative) >= 2
    if has_negative:
        sel_neg = {g: [distorted_choquet(x, nw, g) for x in sel_nm] for g in gammas}
        tst_neg = {g: [distorted_choquet(x, nw, g) for x in tst_nm] for g in gammas}
    else:
        sel_neg = {g: [np.zeros_like(x) for x in sel_pos[g]] for g in gammas}
        tst_neg = {g: [np.zeros_like(x) for x in tst_pos[g]] for g in gammas}

    rows = []
    cache = {}

    # Single-bank fuzzy aggregation isolates the effect of non-additivity.
    for gamma in gammas:
        for a in strengths:
            for floor in floors:
                name = f"fuzzypos__g{gamma:g}__a{a:g}__floor{floor:g}"
                scores = [gate(l, c, a, floor) for l, c in zip(sel_scharr, sel_pos[gamma])]
                cv = cv_threshold_score(scores, selection_items, n_thresholds=args.thresholds, n_folds=3)
                opt = selection_metric(scores, selection_items, args.thresholds)
                rows.append({"name": name, "family": "positive", "gamma": gamma, "combine": "none",
                             "lambda": 0.0, "strength": a, "floor": floor,
                             "cv_F1": float(cv["cv_F1"]), "selection_ODS": float(opt["ODS"]),
                             "selection_AP": float(opt["AP"]), "selection_threshold": float(opt["threshold"])})
                cache[name] = (gamma, None, "none", 0.0, a, floor)

    # Dual bank is enabled only if selection contains independent texture-oriented features.
    if has_negative:
        for gamma in (.55, 1.0, 1.75):
            for kind in ("product", "contrast", "ratio"):
                for lam in (.35, .70, 1.0):
                    for a in strengths:
                        for floor in (.10, .25):
                            name = f"dual__g{gamma:g}__{kind}__l{lam:g}__a{a:g}__floor{floor:g}"
                            ctx = [combine_dual(p, n, kind, lam) for p, n in zip(sel_pos[gamma], sel_neg[gamma])]
                            scores = [gate(l, c, a, floor) for l, c in zip(sel_scharr, ctx)]
                            cv = cv_threshold_score(scores, selection_items, n_thresholds=args.thresholds, n_folds=3)
                            opt = selection_metric(scores, selection_items, args.thresholds)
                            rows.append({"name": name, "family": "dual", "gamma": gamma, "combine": kind,
                                         "lambda": lam, "strength": a, "floor": floor,
                                         "cv_F1": float(cv["cv_F1"]), "selection_ODS": float(opt["ODS"]),
                                         "selection_AP": float(opt["AP"]), "selection_threshold": float(opt["threshold"])})
                            cache[name] = (gamma, gamma, kind, lam, a, floor)

    ranking = pd.DataFrame(rows).sort_values(["cv_F1", "selection_ODS", "selection_AP"], ascending=False).reset_index(drop=True)
    ranking.to_csv(out / "selection_ranking.csv", index=False)

    held = []
    for ri, r in ranking.head(7).iterrows():
        gp, gn, kind, lam, a, floor = cache[str(r["name"])]
        pos = tst_pos[gp]
        if kind == "none":
            neg = [np.zeros_like(x) for x in pos]
            ctx = pos
        else:
            neg = tst_neg[gn]
            ctx = [combine_dual(p, n, kind, lam) for p, n in zip(pos, neg)]
        scores = [gate(l, c, a, floor) for l, c in zip(tst_scharr, ctx)]
        met, counts, _ = fixed_eval(scores, heldout_items, float(r["selection_threshold"]))
        boot = bootstrap_delta(base_counts, counts, n_boot=args.bootstrap, seed=13000 + int(ri))
        held.append({
            "selection_rank": int(ri) + 1, "name": str(r["name"]), "family": str(r["family"]),
            "cv_F1": float(r["cv_F1"]), "selection_ODS": float(r["selection_ODS"]),
            "heldout_precision": float(met["precision"]), "heldout_recall": float(met["recall"]),
            "heldout_F1": float(met["F1"]), "delta_F1_vs_scharr": float(met["F1"] - base_met["F1"]),
            "bootstrap_ci_low": float(boot["delta_F1_ci95_low"]),
            "bootstrap_ci_high": float(boot["delta_F1_ci95_high"]),
            "bootstrap_p_positive": float(boot["p_delta_gt_0"]),
            "selection_threshold": float(r["selection_threshold"]),
        })
        if ri == 0:
            save_preview(heldout_items, pos, neg, ctx, scores, float(r["selection_threshold"]),
                         out / "winner_preview.png", str(r["name"]))

    pd.DataFrame(held).to_csv(out / "heldout_top7.csv", index=False)
    summary = {
        "stage": "12b-fixed-scharr-fuzzy-signature",
        "feature_mode": "oriented_ms + relational signature",
        "selection_images": len(selection_items), "heldout_images": len(heldout_items),
        "positive_features": positive, "texture_negative_features": negative,
        "dual_enabled": bool(has_negative),
        "baseline": {"selection_cv_F1": float(base_cv["cv_F1"]), "selection_ODS": float(base_opt["ODS"]),
                     "selection_threshold": float(base_opt["threshold"]), "heldout": base_met},
        "selection_winner": ranking.iloc[0].to_dict() if len(ranking) else None,
        "heldout_selection_winner": held[0] if held else None,
        "note": "All feature banks and hyperparameters are selected on selection only; held-out is not used for reranking. gamma=1 is the additive-capacity control."
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=float), encoding="utf-8")
    print("STAGE12B_FUZZY_SIGNATURE_DONE")
    print(json.dumps(summary, indent=2, default=float))


if __name__ == "__main__":
    main()
