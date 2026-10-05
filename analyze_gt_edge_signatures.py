from __future__ import annotations

"""Stage 11 — discover a generalizable edge signature from GT-labelled examples.

The goal is *not* to train the final detector.  We use GT to characterize which
image-derived properties distinguish true edges from hard negatives, freeze a
small analytical signature on the selection split, and evaluate that signature
on the held-out split.  A logistic model is reported only as a diagnostic upper
bound on the information content of the discovered descriptors.
"""

from pathlib import Path
import argparse
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from benchmark_uded import DEFAULT_UDED, load_uded, prepare
from benchmark_uded_quick import resize_items
from prepare_uded_runtime import prepare_uded
from src.edge_signature import (
    GROUPS,
    analytical_signature_score,
    correlation_matrix,
    diagnostic_metrics,
    extract_signature_samples,
    feature_group_statistics,
    fit_logistic_diagnostic,
    logistic_score,
    pair_summary,
    select_candidate_signature,
)

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "local_dev" / "edge_signature"


def ensure_uded(root: Path):
    if not (root / "test_pair.lst").exists():
        prepare_uded(root)
    return root


def _write_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, default=lambda x: x.tolist() if hasattr(x, "tolist") else float(x)), encoding="utf-8")


def _plot_top_distributions(samples, summary_df: pd.DataFrame, top_features, out: Path):
    n = min(8, len(top_features))
    if n == 0:
        return
    fig, axes = plt.subplots(n, 1, figsize=(9, 2.6 * n), squeeze=False)
    for ax, feature in zip(axes[:, 0], top_features[:n]):
        j = samples.feature_names.index(feature)
        for gi, group in enumerate(GROUPS):
            vals = samples.X[samples.groups == gi, j]
            if len(vals) == 0:
                continue
            ax.hist(vals, bins=45, density=True, histtype="step", linewidth=1.4, label=group)
        ax.set_title(feature)
        ax.set_ylabel("density")
        ax.legend(loc="upper right", fontsize=8)
    axes[-1, 0].set_xlabel("feature value")
    fig.tight_layout()
    fig.savefig(out / "top_feature_distributions.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def _plot_cross_scale_auc(pair_df: pd.DataFrame, out: Path):
    rows = pair_df[(pair_df.negative_group == "texture") & pair_df.feature.str.contains(r"_s(25|13|7|5|3)$", regex=True)].copy()
    if rows.empty:
        return
    rows["scale"] = rows.feature.str.extract(r"_s(25|13|7|5|3)$").astype(int)
    rows["base"] = rows.feature.str.replace(r"_s(25|13|7|5|3)$", "", regex=True)
    piv = rows.pivot_table(index="base", columns="scale", values="auc_separation", aggfunc="max")
    piv = piv.reindex(columns=[25, 13, 7, 5, 3])
    fig, ax = plt.subplots(figsize=(9, max(4, 0.48 * len(piv))))
    im = ax.imshow(piv.values, aspect="auto", vmin=0.5, vmax=max(0.75, float(np.nanmax(piv.values))))
    ax.set_xticks(np.arange(len(piv.columns)), [str(x) for x in piv.columns])
    ax.set_yticks(np.arange(len(piv.index)), list(piv.index))
    ax.set_xlabel("scale")
    ax.set_title("Edge vs texture: per-scale AUC separation")
    fig.colorbar(im, ax=ax, label="max(AUC, 1-AUC)")
    fig.tight_layout()
    fig.savefig(out / "cross_scale_auc.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def _plot_correlation(samples, chosen, out: Path):
    if not chosen:
        return
    names = [x["feature"] for x in chosen]
    ids = [samples.feature_names.index(x) for x in names]
    corr = correlation_matrix(samples)[np.ix_(ids, ids)]
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(corr, vmin=-1.0, vmax=1.0)
    ax.set_xticks(np.arange(len(names)), names, rotation=60, ha="right")
    ax.set_yticks(np.arange(len(names)), names)
    ax.set_title("Candidate-signature correlation")
    fig.colorbar(im, ax=ax, label="correlation")
    fig.tight_layout()
    fig.savefig(out / "candidate_signature_correlation.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def _report(out: Path, args, names, sel, test, pair_df, chosen, analytical_train, analytical_test,
            linear_train, linear_test, logistic_model):
    tex = pair_df[pair_df.negative_group == "texture"].sort_values("auc_separation", ascending=False)
    near = pair_df[pair_df.negative_group == "near_edge"].sort_values("auc_separation", ascending=False)
    lines = [
        "# Stage 11 — Edge Signature Discovery",
        "",
        "## Purpose",
        "",
        "Use GT only as a scientific instrument to discover image-derived properties of true boundaries. The proposed detector remains image-only at inference time. The held-out split is not used to choose the signature.",
        "",
        "## Protocol",
        "",
        f"- Dataset: UDED ({len(sel.counts_per_image)} selection images + {len(test.counts_per_image)} held-out images)",
        f"- Max image side: {args.max_side}px",
        f"- Maximum sampled pixels per population/image: {args.max_samples_per_group}",
        "- Populations: exact GT edge, near-edge non-GT, far high-gradient texture, far easy background",
        f"- Candidate signature selected from selection split only; max |correlation|={args.max_abs_corr:.2f}",
        "- Logistic regression is a diagnostic upper bound only; it is not the proposed MFI-Edge detector.",
        "",
        "## Candidate analytical signature",
        "",
        "| Feature | Weight | Direction | Edge median | Hard-neg median | Edge-v-texture AUC | Edge-v-near AUC |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in chosen:
        lines.append(
            f"| {r['feature']} | {r['weight']:.4f} | {r['direction']:+.0f} | {r['edge_median']:.4f} | {r['hard_negative_median']:.4f} | {r['texture_auc']:.4f} | {r['near_auc']:.4f} |"
        )
    lines += [
        "",
        "## Generalization diagnostics",
        "",
        "| Score | Selection AUC | Selection AP | Held-out AUC | Held-out AP |",
        "|---|---:|---:|---:|---:|",
        f"| Analytical signature | {analytical_train['auc']:.4f} | {analytical_train['ap']:.4f} | {analytical_test['auc']:.4f} | {analytical_test['ap']:.4f} |",
    ]
    if linear_train is not None:
        lines.append(
            f"| Logistic diagnostic | {linear_train['auc']:.4f} | {linear_train['ap']:.4f} | {linear_test['auc']:.4f} | {linear_test['ap']:.4f} |"
        )
    lines += [
        "",
        "## Strongest individual properties: edge vs texture",
        "",
        "| Feature | AUC separation | AP | MI | Cohen d |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, r in tex.head(15).iterrows():
        lines.append(f"| {r.feature} | {r.auc_separation:.4f} | {r.ap_oriented:.4f} | {r.mutual_information:.4f} | {r.cohens_d:.3f} |")
    lines += [
        "",
        "## Strongest individual properties: edge vs near-edge negatives",
        "",
        "| Feature | AUC separation | AP | MI | Cohen d |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, r in near.head(15).iterrows():
        lines.append(f"| {r.feature} | {r.auc_separation:.4f} | {r.ap_oriented:.4f} | {r.mutual_information:.4f} | {r.cohens_d:.3f} |")
    lines += [
        "",
        "## Interpretation rule",
        "",
        "Do not promote a feature merely because it performs well on UDED selection. A property becomes a candidate for Stage 12 only if it: (1) separates edge from texture/near-edge, (2) survives held-out directionally, (3) is not redundant with a stronger feature, and later (4) remains useful across BSDS/BIPED or another independent dataset.",
        "",
        "## Files",
        "",
        "- `descriptor_pairwise_summary.csv` — AUC/AP/MI/effect size for each feature against hard-negative classes",
        "- `group_statistics.csv` — distribution summary for all four populations",
        "- `candidate_signature.json` — selection-frozen analytical membership specification",
        "- `diagnostic_results.json` — held-out analytical and logistic diagnostic results",
        "- `population_counts.csv` — sampled population sizes by image",
        "- `top_feature_distributions.png`, `cross_scale_auc.png`, `candidate_signature_correlation.png` — visual diagnostics",
        "",
        "## Next decision",
        "",
        "If the analytical signature generalizes, Stage 12 should convert its stable properties into explicit fuzzy memberships/capacities and rerun the CH-MFI ablation grid. If only the logistic diagnostic generalizes, the information is present but our analytical aggregation is inadequate. If neither generalizes, the descriptor space itself needs revision before another large sweep.",
    ]
    (out / "SIGNATURE_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uded-root", default=str(DEFAULT_UDED))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--max-side", type=int, default=256)
    ap.add_argument("--max-samples-per-group", type=int, default=2500)
    ap.add_argument("--candidate-features", type=int, default=8)
    ap.add_argument("--max-abs-corr", type=float, default=0.92)
    ap.add_argument("--no-linear-diagnostic", action="store_true")
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    root = ensure_uded(Path(args.uded_root))

    raw = resize_items(load_uded(root), int(args.max_side))
    prepared, feature_names = prepare(raw)
    selection_items = prepared[0::2]
    heldout_items = prepared[1::2]
    print(f"SIGNATURE_PREP selection={len(selection_items)} heldout={len(heldout_items)} features={len(feature_names)}", flush=True)

    selection = extract_signature_samples(selection_items, feature_names, args.max_samples_per_group, seed=20261005)
    heldout = extract_signature_samples(heldout_items, feature_names, args.max_samples_per_group, seed=20261006)
    if selection.feature_names != heldout.feature_names:
        raise RuntimeError("selection and heldout signature feature spaces differ")

    pd.DataFrame(selection.counts_per_image).assign(split="selection").to_csv(out / "population_counts_selection.csv", index=False)
    pd.DataFrame(heldout.counts_per_image).assign(split="heldout").to_csv(out / "population_counts_heldout.csv", index=False)
    pd.concat([
        pd.DataFrame(selection.counts_per_image).assign(split="selection"),
        pd.DataFrame(heldout.counts_per_image).assign(split="heldout"),
    ], ignore_index=True).to_csv(out / "population_counts.csv", index=False)

    group_df = pd.DataFrame(feature_group_statistics(selection))
    group_df.to_csv(out / "group_statistics.csv", index=False)
    texture_rows = pair_summary(selection, "texture")
    near_rows = pair_summary(selection, "near_edge")
    background_rows = pair_summary(selection, "background")
    pair_df = pd.DataFrame(texture_rows + near_rows + background_rows)
    pair_df.to_csv(out / "descriptor_pairwise_summary.csv", index=False)

    chosen = select_candidate_signature(
        selection, texture_rows, near_rows,
        max_features=int(args.candidate_features),
        max_abs_corr=float(args.max_abs_corr),
    )
    candidate_payload = {
        "dataset": "UDED",
        "selection_only": True,
        "feature_mode": "oriented + Stage11 structural descriptors",
        "max_side": int(args.max_side),
        "population_definition": {
            "edge": "exact GT pixels",
            "near_edge": "non-GT pixels within 2 px morphological neighborhood",
            "texture": "outside 4 px GT neighborhood; top 15% finest-scale gradient",
            "background": "outside 4 px GT neighborhood; bottom 35% finest-scale gradient",
        },
        "features": chosen,
    }
    _write_json(out / "candidate_signature.json", candidate_payload)

    sel_analytical_score = analytical_signature_score(selection.X, selection.feature_names, chosen)
    tst_analytical_score = analytical_signature_score(heldout.X, heldout.feature_names, chosen)
    analytical_train = diagnostic_metrics(selection, sel_analytical_score)
    analytical_test = diagnostic_metrics(heldout, tst_analytical_score)

    logistic_model = None
    linear_train = linear_test = None
    if not args.no_linear_diagnostic:
        print("SIGNATURE_LOGISTIC fitting diagnostic upper bound...", flush=True)
        logistic_model = fit_logistic_diagnostic(selection)
        linear_train = diagnostic_metrics(selection, logistic_score(selection, logistic_model))
        linear_test = diagnostic_metrics(heldout, logistic_score(heldout, logistic_model))

    diagnostic = {
        "analytical_signature_selection": analytical_train,
        "analytical_signature_heldout": analytical_test,
        "logistic_selection": linear_train,
        "logistic_heldout": linear_test,
        "logistic_success": None if logistic_model is None else bool(logistic_model["success"]),
        "logistic_message": None if logistic_model is None else str(logistic_model["message"]),
    }
    if logistic_model is not None:
        order = np.argsort(-np.abs(np.asarray(logistic_model["weights"], float)))[:20]
        diagnostic["logistic_top_coefficients"] = [
            {"feature": selection.feature_names[int(i)], "coefficient": float(logistic_model["weights"][int(i)])}
            for i in order
        ]
    _write_json(out / "diagnostic_results.json", diagnostic)

    np.savez_compressed(
        out / "signature_samples_compact.npz",
        selection_X=selection.X,
        selection_groups=selection.groups,
        heldout_X=heldout.X,
        heldout_groups=heldout.groups,
        feature_names=np.asarray(selection.feature_names, dtype=object),
    )

    top_names = [x["feature"] for x in chosen]
    _plot_top_distributions(selection, group_df, top_names, out)
    _plot_cross_scale_auc(pair_df, out)
    _plot_correlation(selection, chosen, out)
    _report(out, args, feature_names, selection, heldout, pair_df, chosen,
            analytical_train, analytical_test, linear_train, linear_test, logistic_model)

    print("SIGNATURE_CANDIDATE", [x["feature"] for x in chosen], flush=True)
    print("SIGNATURE_ANALYTICAL_SELECTION", json.dumps(analytical_train), flush=True)
    print("SIGNATURE_ANALYTICAL_HELDOUT", json.dumps(analytical_test), flush=True)
    if linear_test is not None:
        print("SIGNATURE_LOGISTIC_SELECTION", json.dumps(linear_train), flush=True)
        print("SIGNATURE_LOGISTIC_HELDOUT", json.dumps(linear_test), flush=True)
    print("EDGE_SIGNATURE_DONE", out, flush=True)


if __name__ == "__main__":
    main()
