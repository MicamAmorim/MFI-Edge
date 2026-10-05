from __future__ import annotations

"""Stage 12a — fixed-Scharr + analytical context-signature gate pilot.

Purpose
-------
Test the hypothesis suggested by Stage 11b:
  * signature evidence is better at deciding whether a structure is boundary-like
    versus texture;
  * Scharr+NMS remains the precise localizer.

The signature is discovered on selection images only.  Held-out images are used
once with frozen signature parameters, gate parameters and threshold selected on
the selection split.  The logistic model remains diagnostic and is not used here.
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
from src.edge_signature import GROUPS, correlation_matrix, pair_summary
from src.edge_signature_relational import extract_relational_samples, relational_signature_tensor, signature_map_from_spec
from src.pipeline import precompute_multiscale_features
from src.postprocess import gradient_orientation, non_maximum_suppression

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "local_dev" / "stage12_signature_gate"
EPS = 1e-9


def ensure_uded(root: Path):
    if not (root / "test_pair.lst").exists():
        prepare_uded(root)
    return root


def prepare(items):
    out = []
    names = None
    for k, d in enumerate(items, start=1):
        print(f"STAGE12_PREP {k:02d}/{len(items)} {d['id']}", flush=True)
        pre_img = apply_conditioning(d["img"], "median", size=3)
        pre, names = precompute_multiscale_features(pre_img, SCALES, feature_mode="oriented_ms")
        ori = gradient_orientation(pre_img, 1.0)
        scharr = non_maximum_suppression(detector_score(pre_img, "scharr", 1.0), ori)
        out.append({**d, "pre_img": pre_img, "features": pre, "orientation": ori, "scharr": scharr})
    return out, names


def select_context_signature(samples, max_features=10, max_abs_corr=.88):
    """Select edge-v-texture features only; near-edge is intentionally excluded.

    Stage 11b showed that near-edge pixels are primarily a localization ambiguity
    population.  Stage 12a uses the signature only as a semantic/context gate.
    """
    tex = pair_summary(samples, "texture")
    rows = sorted(tex, key=lambda r: (float(r["auc_separation"]), float(r["mutual_information"])), reverse=True)
    corr = correlation_matrix(samples, hard_negative_groups=("texture",))
    idx = {n: i for i, n in enumerate(samples.feature_names)}
    edge_code, tex_code = GROUPS.index("edge"), GROUPS.index("texture")
    chosen = []
    for r in rows:
        name = str(r["feature"])
        j = idx[name]
        if float(r["auc_separation"]) < .56:
            continue
        if any(abs(float(corr[j, idx[c["feature"]]])) > float(max_abs_corr) for c in chosen):
            continue
        ev = samples.X[samples.groups == edge_code, j]
        tv = samples.X[samples.groups == tex_code, j]
        em, tm = float(np.median(ev)), float(np.median(tv))
        direction = 1.0 if em >= tm else -1.0
        q25, q75 = np.quantile(np.concatenate([ev, tv]), [.25, .75])
        scale = float(max(q75 - q25, .05))
        strength = max(float(r["auc_separation"]) - .5, 0.0)
        strength *= 1.0 + float(r["mutual_information"])
        chosen.append({
            "feature": name,
            "weight": strength,
            "direction": direction,
            "midpoint": .5 * (em + tm),
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


def gate_score(localizer, context, kind, strength, floor):
    l = np.asarray(localizer, np.float32)
    c = np.asarray(context, np.float32)
    a = float(strength)
    f = float(floor)
    if kind == "multiply":
        gate = f + (1.0 - f) * np.power(np.clip(c, 0, 1), a)
        return l * gate
    if kind == "centered":
        # Can suppress and mildly boost while preserving localizer ordering when a is small.
        gate = np.clip(1.0 + a * (c - .5), f, 2.0)
        return l * gate
    if kind == "exp":
        gate = np.exp(np.clip(a * (c - .5), -2.0, 2.0))
        gate = np.maximum(gate, f)
        return l * gate
    raise ValueError(kind)


def save_preview(items, contexts, scores, threshold, outpath, title, n=6):
    n = min(n, len(items))
    fig, axes = plt.subplots(n, 6, figsize=(18, 3.0 * n))
    if n == 1:
        axes = np.asarray([axes])
    for row, d, c, s in zip(axes, items[:n], contexts[:n], scores[:n]):
        pred = np.asarray(s) >= float(threshold)
        tol = max(1, int(round(.0075 * math.hypot(*d["gt"].shape))))
        err = tolerance_error_map(pred, d["gt"], tol)
        views = [
            (d["img"], d["id"], None),
            (d["gt"], "GT", "gray"),
            (d["scharr"], "Scharr+NMS", "gray"),
            (c, "Context signature", "inferno"),
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
    ap.add_argument("--max-features", type=int, default=10)
    ap.add_argument("--max-abs-corr", type=float, default=.88)
    ap.add_argument("--bootstrap", type=int, default=5000)
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    raw = resize_items(load_uded(ensure_uded(Path(args.uded_root))), args.max_side)
    items, base_names = prepare(raw)
    selection_items, heldout_items = items[0::2], items[1::2]

    selection_samples = extract_relational_samples(selection_items, base_names, 2500, seed=20261005)
    spec = select_context_signature(selection_samples, args.max_features, args.max_abs_corr)
    (out / "context_signature.json").write_text(json.dumps({"selection_only": True, "features": spec}, indent=2), encoding="utf-8")

    sel_context = [signature_map_from_spec(d, base_names, spec) for d in selection_items]
    test_context = [signature_map_from_spec(d, base_names, spec) for d in heldout_items]
    sel_scharr = [np.asarray(d["scharr"], np.float32) for d in selection_items]
    test_scharr = [np.asarray(d["scharr"], np.float32) for d in heldout_items]

    base_cv = cv_threshold_score(sel_scharr, selection_items, n_thresholds=args.thresholds, n_folds=3)
    base_opt = selection_metric(sel_scharr, selection_items, args.thresholds)
    base_met, base_counts, _ = fixed_eval(test_scharr, heldout_items, float(base_opt["threshold"]))

    configs = [("multiply", a, f) for a in (.5, 1.0, 2.0) for f in (.25, .5, .75)]
    configs += [("centered", a, .25) for a in (.25, .5, .75, 1.0)]
    configs += [("exp", a, .25) for a in (.25, .5, 1.0)]

    rows = []
    cache = {}
    for kind, a, floor in configs:
        name = f"siggate__{kind}__a{a:g}__floor{floor:g}"
        scores = [gate_score(l, c, kind, a, floor) for l, c in zip(sel_scharr, sel_context)]
        cv = cv_threshold_score(scores, selection_items, n_thresholds=args.thresholds, n_folds=3)
        opt = selection_metric(scores, selection_items, args.thresholds)
        rows.append({"name": name, "kind": kind, "strength": a, "floor": floor,
                     "cv_F1": float(cv["cv_F1"]), "selection_ODS": float(opt["ODS"]),
                     "selection_AP": float(opt["AP"]), "selection_threshold": float(opt["threshold"])})
        cache[name] = (kind, a, floor)

    ranking = pd.DataFrame(rows).sort_values(["cv_F1", "selection_ODS", "selection_AP"], ascending=False).reset_index(drop=True)
    ranking.to_csv(out / "selection_ranking.csv", index=False)

    held = []
    for ri, r in ranking.head(5).iterrows():
        kind, a, floor = cache[str(r["name"])]
        scores = [gate_score(l, c, kind, a, floor) for l, c in zip(test_scharr, test_context)]
        met, counts, _ = fixed_eval(scores, heldout_items, float(r["selection_threshold"]))
        boot = bootstrap_delta(base_counts, counts, n_boot=args.bootstrap, seed=12000 + int(ri))
        held.append({"selection_rank": int(ri) + 1, "name": str(r["name"]),
                     "cv_F1": float(r["cv_F1"]), "selection_ODS": float(r["selection_ODS"]),
                     "heldout_precision": float(met["precision"]), "heldout_recall": float(met["recall"]),
                     "heldout_F1": float(met["F1"]), "delta_F1_vs_scharr": float(met["F1"] - base_met["F1"]),
                     "bootstrap_ci_low": float(boot["delta_F1_ci95_low"]),
                     "bootstrap_ci_high": float(boot["delta_F1_ci95_high"]),
                     "bootstrap_p_positive": float(boot["p_delta_gt_0"]),
                     "selection_threshold": float(r["selection_threshold"])})
        if ri == 0:
            save_preview(heldout_items, test_context, scores, float(r["selection_threshold"]), out / "winner_preview.png", str(r["name"]))

    pd.DataFrame(held).to_csv(out / "heldout_top5.csv", index=False)
    summary = {
        "stage": "12a-fixed-scharr-signature-gate",
        "feature_mode": "oriented_ms + relational signature",
        "selection_images": len(selection_items), "heldout_images": len(heldout_items),
        "context_features": spec,
        "baseline": {"selection_cv_F1": float(base_cv["cv_F1"]), "selection_ODS": float(base_opt["ODS"]),
                     "selection_threshold": float(base_opt["threshold"]), "heldout": base_met},
        "selection_winner": ranking.iloc[0].to_dict(),
        "heldout_selection_winner": held[0] if held else None,
        "note": "Context signature and gate hyperparameters selected on selection only; held-out is not used for re-ranking."
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2, default=float), encoding="utf-8")
    print("STAGE12_SIGNATURE_GATE_DONE")
    print(json.dumps(summary, indent=2, default=float))


if __name__ == "__main__":
    main()
