#!/usr/bin/env python3
"""P0 Paper A: static parameter provenance. No scientific data/result payloads.

Reads an explicit allowlist of Python SOURCE files and the preregistration
protocol. It merely stat()s three known historical output files; NEVER parses,
hashes or otherwise reads them, because historical models may contain F1.
No project modules imported, no GT/H5/images/maps/predictions/F1 accessed.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import subprocess

REPO = Path(__file__).resolve().parents[1]
OUTPUT = Path(r"F:\MFI-Edge-Data\MultiCue\paper_a_parameter_provenance_P0.json")
ALLOWLIST = (
    "run_stage24_paper_a_recertification.py",
    "src/stage24_recertification_ops.py",
    "src/stage24_recertification_cv.py",
    "src/stage24_residual.py",
    "src/stage24_integrity.py",
    "src/stage23_descriptors.py",
    "src/stage24_strict_generalized_cf1f2.py",
    "src/postprocess.py",
    "src/stage24_paper_a_runtime.py",
    "src/paper_a_confirmation_paired_f1.py",
)
FUNCTION_CALLS = {
    "run_stage24_paper_a_recertification.py": {
        "freeze_recipe": ("fit_aggregator", "choose_threshold", "serialize_model"),
        "verify_campaign_source_fingerprint": ("sha256_file",),
    },
    "src/stage24_recertification_ops.py": {
        "fit_aggregator": ("_sample_training", "capacity_coefficients", "capacity_from_mobius"),
        "apply_aggregator": ("choquet",),
        "calibrate_memberships": (),
        "thin_score": ("non_maximum_suppression",),
        "choose_threshold": ("canonical_threshold_candidates", "one_to_one_boundary_counts"),
        "serialize_model": (),
        "inference_recipe": ("apply_membership", "calibrate_memberships",
                             "apply_aggregator", "apply_suppressor", "thin_score"),
    },
    "src/stage24_recertification_cv.py": {
        "memberships_on_split": ("fit_membership",),
        "fit_and_score": ("fit_aggregator", "choose_threshold"),
    },
    "src/stage24_residual.py": {
        "fit_membership": ("_stack_gt",),
        "apply_membership": ("expit",),
    },
    "src/stage24_integrity.py": {
        "one_to_one_boundary_counts": ("exact_binary_gt",),
        "tolerance_pixels": (),
    },
    "src/stage23_descriptors.py": {"compute_descriptor": ()},
    "src/postprocess.py": {"non_maximum_suppression": ()},
}
ARTIFACT_PATHS_STAT_ONLY = (
    "results/local_dev/stage24_paper_a_recertification/frozen_models.json",
    "results/local_dev/stage24_paper_a_recertification/environment_manifest.json",
    "results/local_dev/stage24_paper_a_recertification/best_single_train_selected_fold.csv",
)
SEMANTIC_CHECKS = (
    ("choquet_training_and_gamma", "src/stage24_recertification_ops.py",
     "fit_aggregator", ("choquet_generalized_150", "1.5", "_sample_training")),
    ("legacy_sigmoid", "src/stage24_recertification_ops.py",
     "calibrate_memberships", ("legacy_sigmoid", "return m")),
    ("nms", "src/stage24_recertification_ops.py",
     "thin_score", ("non_maximum_suppression", "nms_image")),
    ("threshold_training_gt", "src/stage24_recertification_ops.py",
     "choose_threshold", ("gts", "canonical_threshold_candidates")),
    ("serialized_recipe", "src/stage24_recertification_ops.py",
     "serialize_model", ("membership", "aggregator", "calibration_mode", "thinning")),
    ("historical_models_have_f1", "run_stage24_paper_a_recertification.py",
     "freeze_recipe", ("fit_all_UDED_F1_NOT_HELDOUT", "frozen_models.json")),
)


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_source(source: str, required: dict) -> tuple[dict, dict]:
    parsed = ast.parse(source)
    nodes = {n.name: n for n in parsed.body if isinstance(
        n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    functions, segments = {}, {}
    for name, node in nodes.items():
        segments[name] = ast.get_source_segment(source, node) or ""
    for name, expected in required.items():
        node = nodes.get(name)
        if node is None:
            functions[name] = {"status": "MISSING_FUNCTION"}
            continue
        invoked = set()
        for item in ast.walk(node):
            if isinstance(item, ast.Call):
                f = item.func
                if isinstance(f, ast.Name):
                    invoked.add(f.id)
                elif isinstance(f, ast.Attribute):
                    invoked.add(f.attr)
        absent = sorted(set(expected) - invoked)
        functions[name] = {
            "status": "OK" if not absent else "MISSING_CALL",
            "line_start": node.lineno,
            "line_end": node.end_lineno,
            "function_sha256": hashlib.sha256(
                segments[name].encode("utf-8")).hexdigest(),
            "missing_expected_calls": absent,
        }
    return functions, segments


def metadata_only(path: Path, root: Path) -> dict:
    if path.is_symlink():
        raise ValueError("Refusing artifact symlink: " + str(path))
    if not path.exists():
        return {"exists": False, "bytes": None, "bytes_read": False, "sha256": None}
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Invalid historical artifact path")
    return {"exists": True, "bytes": path.stat().st_size,
            "bytes_read": False, "sha256": None}


def git_head(root: Path) -> str | None:
    p = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                       capture_output=True, text=True, check=False)
    return p.stdout.strip() if p.returncode == 0 else None


def audit(root: Path) -> dict:
    root = root.resolve()
    sources, segments = {}, {}
    for name in ALLOWLIST:
        path = root / name
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
            raise FileNotFoundError("Source missing or unsafe: " + name)
        content = path.read_text(encoding="utf-8")
        functions, parts = inspect_source(content, FUNCTION_CALLS.get(name, {}))
        sources[name] = {
            "source_sha256": checksum(path),
            "size_bytes": path.stat().st_size,
            "functions": functions,
        }
        segments[name] = parts
    checks = [{
        "id": label, "source": path, "function": fn,
        "status": "OK" if all(x in segments[path].get(fn, "")
                              for x in markers) else "DRIFT_REVIEW",
    } for label, path, fn, markers in SEMANTIC_CHECKS]
    drift = [c["id"] for c in checks if c["status"] != "OK"]
    drift += [path + ":" + func
              for path, entry in sources.items()
              for func, detail in entry["functions"].items()
              if detail["status"] != "OK"]

    protocol = json.loads((root / "docs/paper_a_confirmation/protocol.json")
                          .read_text(encoding="utf-8"))
    if protocol.get("status") != "draft_not_frozen":
        raise ValueError("Pre-freeze-only audit refuses frozen/changed protocol")
    artifacts = {name: metadata_only(root / name, root)
                 for name in ARTIFACT_PATHS_STAT_ONLY}
    return {
        "status": "P0_SOURCE_PROVENANCE_REVIEW_NOT_FROZEN",
        "utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_head(root),
        "source_contract_mismatches": sorted(set(drift)),
        "source_files": sources,
        "semantic_checks": checks,
        "historical_artifact_METADATA_ONLY": artifacts,
        "scientific_findings": [
            "choquet_generalized_150 is FITTED using TRAIN GT, gamma 1.5; H2-specific capacity not frozen by this audit",
            "legacy_sigmoid passes previously FITTED membership midpoint/scale",
            "NMS depends on image orientation at sigma=1.0; code hashes recorded",
            "choose_threshold reads training GT; confirmatory threshold(s) must be independently frozen",
            "historical frozen_models.json may include development F1 fields and is NOT read",
            "historical winner model need not be the H1/H2 predeclared operator",
        ],
        "remaining_gates": [
            "Prepare GT-free H1/H2-specific recipe records and hashes from permitted training sources",
            "Confirm H2 capacity/Mobius, membership fit, train lineage and per-operator thresholds",
            "Freeze equal_mean controls with identical descriptor input and training policy",
            "Pin NMS, suppressor identity, legacy_sigmoid and native-resolution matcher",
            "Audit GT edges encoding and multi-annotator contract on permitted data",
            "Certify scene-level independence and final cohort IDs before separate freeze",
        ],
        "protocol_status_unchanged": "draft_not_frozen",
        "research_artifact_payload_bytes_read": 0,
        "GT_H5_F1_maps_predictions_opened": False,
        "scientific_code_executed": False,
        "cohort_frozen": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    out = args.output.expanduser().resolve()
    if os.name == "nt" and out.drive.lower() == REPO.drive.lower():
        parser.error("Use F: output, not near-full project drive C:")
    if not out.parent.is_dir() or out.suffix.lower() != ".json":
        parser.error("Existing output parent and .json suffix required")
    if out.exists():
        parser.error("Previous P0 report exists: provide a new --output filename")
    report = audit(REPO)
    part = out.with_suffix(".json.part")
    if part.exists():
        parser.error("Interrupted prior temporary report exists; inspect before retry")
    with part.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    os.replace(part, out)
    print(json.dumps({
        "status": report["status"],
        "git_commit": report["git_commit"],
        "source_file_count": len(report["source_files"]),
        "source_contract_mismatches": report["source_contract_mismatches"],
        "historical_artifact_METADATA_ONLY": report["historical_artifact_METADATA_ONLY"],
        "remaining_gates": report["remaining_gates"],
        "GT_H5_F1_maps_predictions_opened": False,
        "output": str(out),
    }, ensure_ascii=False, indent=2))
    return 0 if not report["source_contract_mismatches"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
