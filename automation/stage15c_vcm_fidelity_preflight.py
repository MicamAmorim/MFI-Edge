from __future__ import annotations

"""Deterministic implementation-fidelity audit for the Stage-15c VCM paper."""

import csv
from datetime import datetime, timezone
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage15c_vcm_fidelity_preflight"


CONTRACT = [
    ("training_class", "resolved", "strictly untrained", "No fitting or learned model is specified."),
    ("input_colour_space", "resolved", "HSV / HDHSV ordering", "Paper equations 8-11."),
    ("quantization", "resolved", "8 levels", "Paper Section 2.2."),
    ("author_code", "missing", "none located", "Publisher, DOI, indexed web, and GitHub searches through 2026-10-08."),
    ("supplementary_material", "missing", "none exposed", "Primary publisher article exposes no implementation supplement."),
    ("window_size_R", "missing", "not reported", "Required by the adaptive local operator."),
    ("spatial_kernel_eta_s", "missing", "not reported", "Equation 3 names the kernel/scale without a fixed value or full discrete definition."),
    ("cooccurrence_sigma", "missing", "not reported", "Equations 4-5."),
    ("range_sigma_r", "missing", "not reported", "Equation 5."),
    ("distance_scale_d", "missing", "not reported", "Equations 1-2 and 6-7."),
    ("selection_threshold_T", "missing", "not reported", "Equations 1-2 and 6-7."),
    ("erosion_factor_S", "missing", "not reported", "Equation 7."),
    ("entropy_threshold_J", "ambiguous", "described but not fixed", "Section 2.2 introduces J, while later dilation equation 6 omits it."),
    ("hue_reference_h0", "missing", "not reported", "Equations 8-9 require the reference hue."),
    ("HSV_vector_coordinates", "ambiguous", "x/y conversion not defined", "HDHSV ordering names x and y but does not define their construction from S/V."),
    ("morphology_conventions", "ambiguous", "padding, ties, and vector +/- undefined", "Needed to discretize equations 10-14."),
    ("gradient_variant", "ambiguous", "g, g+, and g- all listed", "No fixed choice or combination is identified for BSDS."),
    ("scalar_output_map", "missing", "not reported", "Vector difference scalarization and channel norm are unspecified."),
    ("map_postprocessing", "missing", "not reported", "No normalization, NMS, thinning, or serialization convention is specified."),
    ("BSDS_split", "ambiguous", "test is described; scored split not explicitly bound", "Section 4.3 explains the split but does not state the evaluated file list."),
    ("BSDS_matcher", "ambiguous", "benchmark terminology only", "maxDist, thinning, annotation use, threshold grid, and evaluator version are absent."),
    ("reported_boundary_metrics", "documentary_only", "ODS/OIS/AP 0.76/0.79/0.77", "Table 5; protocol match is unverified."),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    contract_path = OUT / "implementation_contract.csv"
    with contract_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["item", "status", "paper_or_search_evidence", "fidelity_consequence"])
        writer.writerows(CONTRACT)

    blocking = [item for item, status, _, _ in CONTRACT if status in {"missing", "ambiguous"}]
    summary = {
        "stage": "15c-vector-cooccurrence-morphology-fidelity-preflight",
        "role": "reproduction_fidelity_preflight",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "citation": "Lu et al. (2021), Vector co-occurrence morphological edge detection for colour image",
            "doi": "10.1049/ipr2.12290",
            "primary_full_text": "https://ietresearch.onlinelibrary.wiley.com/doi/full/10.1049/ipr2.12290",
            "accessed": "2026-10-08",
        },
        "architecture_changed": False,
        "detector_executed": False,
        "dataset_read": False,
        "protected_split_used": False,
        "training_class": "strictly_untrained",
        "author_code_available": False,
        "implementation_fidelity": {
            "exact_author_code": "not_possible_from_public_materials",
            "faithful_reimplementation": "not_justified",
            "repository_surrogate": "possible_but_not_authorized_by_this_preflight",
            "blocking_items": blocking,
        },
        "reported_metrics": {
            "dataset_label": "BSDS500",
            "ods": 0.76,
            "ois": 0.79,
            "ap": 0.77,
            "status": "documentary_protocol_unverified",
        },
        "decision_rule": (
            "A detector run may be registered only if exact author code or sufficient fixed "
            "primary-source detail resolves every output-affecting blocking item without "
            "validation-driven choices. Otherwise Stage 15c closes as non-reproducible and "
            "the reproduction campaign advances without scoring a surrogate."
        ),
        "preflight_passed": False,
        "recommended_next_action": "close_stage15c_as_fidelity_unresolved_then_open_stage15d_ed_edpf_checkpoint",
        "official_eval_manifest_omission": (
            "Required and justified: this is a non-image fidelity audit; it reads no dataset "
            "and emits no detector map."
        ),
        "artifacts": [str(contract_path.relative_to(ROOT)).replace("\\", "/")],
    }
    summary_path = OUT / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE15C_VCM_FIDELITY_PREFLIGHT_COMPLETE")
    print(summary_path)
    print(contract_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
