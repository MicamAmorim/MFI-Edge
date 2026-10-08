from __future__ import annotations

"""Dataset-free fidelity audit for the Stage-15h adaptive-surround method."""

import csv
from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage15h_adaptive_surround_fidelity_preflight"


CONTRACT = [
    (
        "training_class",
        "resolved",
        "strictly untrained analytic contour detector",
        "The target article describes fixed V1-inspired filtering, adaptive surround modulation, and multiscale integration without fitting a learned model.",
    ),
    (
        "target_article_code",
        "missing",
        "no article-specific author code, supplement, or executable archive located",
        "Publisher, DOI, author/profile, repository, and indexed-web searches through 2026-10-08 did not expose an implementation.",
    ),
    (
        "source_access_and_license",
        "restricted",
        "publisher preview is subscription content under exclusive Springer Nature rights",
        "The public abstract, metadata, figures, references, and result statement can support an audit, but not source redistribution or a complete implementation transcription.",
    ),
    (
        "input_and_preprocessing",
        "missing",
        "public material does not fix the complete input color space, dynamic range, conditioning, padding, or normalization path",
        "These choices change the CRF response, contrast estimate, adaptive gain, and exported score map.",
    ),
    (
        "orientation_surface",
        "partly_resolved",
        "a public figure caption exposes four butterfly receptive-field orientations at 45, 90, 135, and 180 degrees",
        "The angle set alone does not resolve kernel equations, phase, normalization, sampling support, sign convention, or response pooling.",
    ),
    (
        "crf_and_butterfly_receptive_fields",
        "missing",
        "public figures identify a butterfly geometry but do not expose a complete executable kernel contract",
        "Kernel scale, lobe support, centre/surround partition, discretization, border treatment, and response rectification cannot be certified.",
    ),
    (
        "adaptive_surround_rule",
        "missing",
        "the article states that high contrast yields stronger suppression and low contrast stronger facilitation",
        "The local-contrast statistic, neighbourhood, transfer function, transition point, gains, clipping, and interaction with orientation responses are not publicly fixed.",
    ),
    (
        "multiscale_schedule_and_fusion",
        "missing",
        "the article states multiscale surround modulation but public metadata does not fix the scale bank or fusion",
        "Scale count, receptive-field sizes, resizing rules, per-scale normalization, weights, and max/sum/selection policy cannot be invented for a faithful reproduction.",
    ),
    (
        "orientation_and_channel_fusion",
        "missing",
        "no complete public contract for orientation pooling or any color/luminance channel fusion",
        "A scalar boundary-strength map cannot be reconstructed without output-affecting choices.",
    ),
    (
        "scalar_output_and_postprocessing",
        "missing",
        "NMS, thinning, hysteresis/thresholding, normalization, and native-resolution serialization are unresolved",
        "The repository official evaluator requires a frozen dense map convention; selecting one would create a surrogate rather than a reproduction.",
    ),
    (
        "related_same_group_predecessor",
        "related_not_equivalent",
        "Fang, Cai and Fan (2025), DOI 10.1007/s11042-024-19666-y, describes a contrast-adaptive visual-pathway model",
        "That distinct method adds retinal color antagonism, LGN gain control and LIF processing and cannot supply missing parameters for the target article without an explicit equivalence statement.",
    ),
    (
        "reported_bsds_metric",
        "documentary_only",
        "average optimal F-score 0.703 on BSDS500",
        "The public record does not establish split, per-image versus dataset-wide optimization, matcher, tolerance, thinning, threshold grid, annotation handling, or output convention; it is not assumed to be Berkeley ODS.",
    ),
    (
        "reported_nyud_evaluation",
        "documentary_only",
        "the abstract reports further NYUD tests and generalization",
        "The RGB/RGB-D input, split, metric, evaluator, and fixed-output convention are not publicly resolved.",
    ),
    (
        "matched_bsds_validation_feasibility",
        "blocked_by_fidelity",
        "the common local evaluator is available but no faithful target map can be exported",
        "Running a hand-completed implementation would conflate missing method choices with detector performance and is forbidden.",
    ),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    contract_path = OUT / "implementation_contract.csv"
    with contract_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["item", "status", "source_evidence", "fidelity_consequence"])
        writer.writerows(CONTRACT)

    blocking_states = {
        "missing",
        "restricted",
        "related_not_equivalent",
        "blocked_by_fidelity",
    }
    blocking = [item for item, status, _, _ in CONTRACT if status in blocking_states]
    summary = {
        "stage": "15h-adaptive-surround-fidelity-preflight",
        "role": "reproduction_fidelity_preflight",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sources": [
            {
                "citation": "Zhang, Fan, Cai and Fang (2025), Contour detection model inspired by V1 surround modulation",
                "doi": "10.1007/s11760-024-03634-y",
                "official_url": "https://link.springer.com/article/10.1007/s11760-024-03634-y",
                "relationship": "target_peer_reviewed_article",
                "public_access": "subscription_preview_only",
            },
            {
                "citation": "Fang, Cai and Fan (2025), Contour extraction model introducing contrast adaptive characteristics based on visual pathway",
                "doi": "10.1007/s11042-024-19666-y",
                "official_url": "https://link.springer.com/article/10.1007/s11042-024-19666-y",
                "relationship": "same_group_related_predecessor_not_proven_equivalent",
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
            "related_predecessor": "not_equivalent_and_not_authorized_to_fill_missing_choices",
            "blocking_items": blocking,
        },
        "reported_metrics": {
            "bsds500_average_optimal_f_score": 0.703,
            "nyud": "generalization claim without a complete public metric contract",
            "status": "documentary_only_not_matched_to_local_berkeley_ods_ois_ap",
        },
        "decision_rule": (
            "A Stage-15h detector run may be registered only if article-specific author code or "
            "primary-source clarification resolves every output-affecting blocking item. Otherwise "
            "Stage 15h closes fidelity-unresolved without a surrogate and advances to the registered "
            "Stage-15i fractional-reference checkpoint."
        ),
        "preflight_passed": False,
        "recommended_next_action": "close_stage15h_as_fidelity_unresolved_then_open_stage15i_checkpoint",
        "official_eval_manifest_omission": (
            "Required and justified: this is a deterministic non-image fidelity audit; it reads no "
            "dataset and emits no detector map."
        ),
        "artifacts": [str(contract_path.relative_to(ROOT)).replace("\\", "/")],
    }
    summary_path = OUT / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE15H_ADAPTIVE_SURROUND_FIDELITY_PREFLIGHT_COMPLETE")
    print(summary_path)
    print(contract_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
