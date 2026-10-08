from __future__ import annotations

"""Dataset-free fidelity audit for the Stage-15g texture/surround method."""

import csv
from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage15g_texture_surround_fidelity_preflight"


CONTRACT = [
    (
        "training_class",
        "resolved",
        "strictly untrained",
        "The article describes an analytic bio-inspired hierarchy and no fitted or learned model.",
    ),
    (
        "target_article_code",
        "missing",
        "no article-specific author code or supplement located",
        "Publisher, author-profile, repository, DOI, and indexed-web searches through 2026-10-08.",
    ),
    (
        "same_inventor_patent",
        "related_not_equivalent",
        "CN115830051A/B describes the same retina/V1 texture-gradient/V2 endpoint/V4 hierarchy",
        "The patent is not explicitly identified by the article as its executable implementation and reports BSDS/NYUDv2 rather than the article's BSDS500/MBDD pair.",
    ),
    (
        "official_related_repository",
        "related_not_equivalent",
        "DaipengYang7/BESD at eeb1f7eddcff0c998d8a96083f0579c7f1644b61",
        "The repository accompanies a different 2024/2025 Visual Computer paper and adds edge-segment construction plus feedback; it has no explicit license.",
    ),
    (
        "input_preprocessing",
        "partly_resolved",
        "square-root RGB preprocessing",
        "The patent and related BESD code agree, but article-specific executable provenance is absent.",
    ),
    (
        "retinal_channels",
        "partly_resolved",
        "balanced/unbalanced opponent, luminance, and local luminance-contrast channels",
        "The patent fixes opponent weights 1 and 0.5 and local radius 2.5; the target article implementation is not exposed.",
    ),
    (
        "crf_gaussian",
        "conflicting",
        "patent sigma 0.5; related BESD code uses sigma 1 with aspect 0.3",
        "An article-faithful Gaussian derivative cannot be selected without choosing between non-equivalent related sources.",
    ),
    (
        "orientation_schedule",
        "partly_resolved",
        "patent and related BESD code use 12 orientations",
        "The target article's complete fixed schedule and orientation convention are not independently exposed.",
    ),
    (
        "surround_kernel_geometry",
        "conflicting",
        "patent same-orientation sigmas 0.3/2.0; related BESD code uses 0.7/2.0",
        "Kernel support, centre exclusion, lateral construction, and border rules are output-affecting.",
    ),
    (
        "surround_weights",
        "missing",
        "patent leaves w1/w2/w3 symbolic; related BESD code uses +1/-1/-0.8",
        "The article-specific facilitation, lateral-inhibition, and full-inhibition weights cannot be certified.",
    ),
    (
        "texture_gradient_scales",
        "missing",
        "patent states multiple radii without fixing them; related BESD uses 3.5/5.5/8.5/12.5/17.5",
        "Using the repository radii would silently assume equivalence to a different paper.",
    ),
    (
        "texture_translation_and_borders",
        "ambiguous",
        "patent gives an analytic shift; related code discretizes and warp-translates",
        "Rounding, interpolation, padding, and sign conventions are not fixed for the target article.",
    ),
    (
        "nonlinear_response_control",
        "missing",
        "patent names H but does not fix it; related code clips at one seventh of each maximum and normalizes",
        "The target article's clipping and normalization path cannot be reconstructed faithfully.",
    ),
    (
        "v2_endpoint_modulation",
        "conflicting",
        "patent uses endpoint kernels with lengths 5 and 3 but leaves coefficient c unresolved; BESD performs segment linking",
        "The target article's endpoint inhibition cannot be substituted by the related repository's linking stage.",
    ),
    (
        "multiscale_and_channel_fusion",
        "missing",
        "related BESD uses four resized scales and fixed reciprocal weights; patent only specifies channel summation",
        "Scale schedule, resizing, per-channel normalization, and final fusion are not article-certified.",
    ),
    (
        "scalar_output_and_postprocessing",
        "missing",
        "no target implementation contract for NMS, normalization, thinning, or serialization",
        "A common-evaluator map cannot be exported without inventing output-affecting conventions.",
    ),
    (
        "reported_datasets_and_metrics",
        "documentary_only",
        "article reports BSDS500/MBDD and relative ODS improvements; patent reports BSDS ODS/OIS/AP 0.73/0.75/0.76 and NYUDv2",
        "The article and patent evaluation claims remain separate and protocol-unverified.",
    ),
    (
        "bsds_protocol",
        "ambiguous",
        "exact split, matcher, maxDist, thinning, threshold grid, annotation handling, and output convention unresolved",
        "Published numbers cannot be treated as matched to the repository's local validation path.",
    ),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    contract_path = OUT / "implementation_contract.csv"
    with contract_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["item", "status", "source_evidence", "fidelity_consequence"])
        writer.writerows(CONTRACT)

    blocking_states = {"missing", "ambiguous", "conflicting", "related_not_equivalent"}
    blocking = [item for item, status, _, _ in CONTRACT if status in blocking_states]
    summary = {
        "stage": "15g-texture-gradient-surround-fidelity-preflight",
        "role": "reproduction_fidelity_preflight",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sources": [
            {
                "citation": "Yang, Peng and Wu (2025), Edge Detection Using Texture Gradients and Surround Modulation",
                "doi": "10.1007/s11760-025-04339-6",
                "official_url": "https://link.springer.com/article/10.1007/s11760-025-04339-6",
                "relationship": "target_peer_reviewed_article",
            },
            {
                "citation": "Peng, Yang and Wu, Visual biomimetic edge detection method based on texture gradient adjustment",
                "publication": "CN115830051A / CN115830051B",
                "official_url": "https://patents.google.com/patent/CN115830051B/en",
                "relationship": "same_inventor_related_patent_not_proven_equivalent",
            },
            {
                "citation": "Yang, Peng and Wu, BESD author repository",
                "official_url": "https://github.com/DaipengYang7/BESD",
                "commit": "eeb1f7eddcff0c998d8a96083f0579c7f1644b61",
                "relationship": "official_code_for_different_related_paper_not_target_code",
            },
        ],
        "accessed": "2026-10-08",
        "architecture_changed": False,
        "detector_executed": False,
        "dataset_read": False,
        "protected_split_used": False,
        "training_class": "strictly_untrained",
        "implementation_fidelity": {
            "exact_author_code": "not_available_for_target_article",
            "faithful_reimplementation": "not_justified_from_public_contract",
            "related_besd_code": "not_equivalent_and_not_authorized_as_surrogate",
            "blocking_items": blocking,
        },
        "reported_metrics": {
            "target_article": "relative improvements only in publicly exposed article metadata; protocol unverified",
            "related_patent_bsds": {"ods": 0.73, "ois": 0.75, "ap": 0.76},
            "status": "documentary_sources_kept_separate",
        },
        "decision_rule": (
            "A Stage-15g detector run may be registered only if article-specific author code or "
            "primary-source clarification resolves every output-affecting blocking item. Otherwise "
            "Stage 15g closes fidelity-unresolved without combining the patent and BESD code, and "
            "the reproduction campaign advances to the registered Stage-15h literature checkpoint."
        ),
        "preflight_passed": False,
        "recommended_next_action": "close_stage15g_as_fidelity_unresolved_then_open_stage15h_checkpoint",
        "official_eval_manifest_omission": (
            "Required and justified: this is a deterministic non-image fidelity audit; it reads no "
            "dataset and emits no detector map."
        ),
        "artifacts": [str(contract_path.relative_to(ROOT)).replace("\\", "/")],
    }
    summary_path = OUT / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE15G_TEXTURE_SURROUND_FIDELITY_PREFLIGHT_COMPLETE")
    print(summary_path)
    print(contract_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
