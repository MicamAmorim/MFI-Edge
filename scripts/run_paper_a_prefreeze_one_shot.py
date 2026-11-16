#!/usr/bin/env python3
"""One-command Paper A pre-freeze technical audit; no model fitting or GT/F1.

Verifies existing code, P0.1 draft, development and MultiCue inventories,
cache sidecars and SHA256 of the 56 existing UDED-14 development NPY files.
Only NPY bytes are read (for SHA), NOT decoded as arrays. No images/H5/GT,
prediction/F1 outputs, experiment execution or checkpoint modifications.
"""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_paper_a_parameter_provenance_P0 import audit as audit_p0
from prepare_paper_a_h1h2_recipe_P0_1 import (
    code_provenance, git_head, read_protocol, validate as validate_p01)
from audit_paper_a_development_lineage_P0_2 import audit as audit_p02
from audit_paper_a_uded14_cache_sidecars_P0_3 import (
    CACHE, DESCRIPTORS, MANIFEST, PROVENANCE, audit_index, is_hash)
from check_paper_a_multicue_gt_task_names import validate_inventory

DATA = Path(r"F:\MFI-Edge-Data\MultiCue")
DRAFT = DATA / "paper_a_H1_H2_recipe_P0_1_DRAFT.json"
TESTS = (
    "test_paper_a_parameter_provenance_P0.py",
    "test_paper_a_h1h2_recipe_P0_1.py",
    "test_paper_a_development_lineage_P0_2.py",
    "test_paper_a_uded14_cache_sidecars_P0_3.py",
    "test_paper_a_multicue_gt_task_names.py",
    "test_paper_a_paired_f1_contract.py",
)
MAX_ARRAY_BYTES = 16 * 1024 * 1024


def hash_npy(path: Path) -> tuple[str, int]:
    if path.is_symlink() or not path.is_file() or path.suffix.lower() != ".npy":
        raise ValueError("Missing/unsafe NPY")
    before = path.stat()
    if not 128 < before.st_size <= MAX_ARRAY_BYTES:
        raise ValueError("Unexpected NPY size")
    h = hashlib.sha256()
    total = 0
    with path.open("rb") as handle:
        for part in iter(lambda: handle.read(1024 * 1024), b""):
            total += len(part)
            if total > MAX_ARRAY_BYTES:
                raise ValueError("NPY exceeds bounded hash limit")
            h.update(part)
    after = path.stat()
    if total != before.st_size or after.st_size != before.st_size or after.st_mtime_ns != before.st_mtime_ns:
        raise ValueError("NPY changed while being hashed")
    return h.hexdigest(), total


def validate_56(p03: dict, rows: list[dict]) -> dict:
    records = [v for v in p03["records"] if "image_id" in v]
    if len(records) != 56 or p03.get("matching_sidecar_and_npy_metadata") != 56:
        raise ValueError("P0.3 must pass 56/56 before hashing")
    refs = {(r["image_id"], r["descriptor_id"]): r for r in rows}
    if len(rows) != 182 or len(refs) != 182:
        raise ValueError("Historical descriptor manifest drift")
    seen_paths, results = set(), []
    for idx, r in enumerate(records, 1):
        key = (r["image_id"], r["descriptor_id"])
        expected = refs[key]["sha256"]
        raw = r["cache_npy_path"]
        p = Path(raw)
        base = (CACHE / key[1]).resolve()
        if (not is_hash(expected) or key[1] not in DESCRIPTORS or
            r["sidecar_count"] != 1 or
            r["sidecar_status"] != "METADATA_MATCH_ONLY" or
            r["metadata_sha_matches_manifest"] is not True or
            r["actual_npy_bytes_hashed"] is not False or
            not p.is_absolute() or p in seen_paths or
            not is_hash(p.stem) or p.parent != CACHE / key[1] or
            p.is_symlink() or p.resolve().parent != base or
            p.stat().st_size != r["cache_npy_bytes"]):
            raise ValueError("Invalid P0.3 approved cache path or provenance")
        seen_paths.add(p)
        actual, size = hash_npy(p)
        results.append({"image_id": key[0], "descriptor": key[1],
                        "bytes": size, "expected_sha256": expected,
                        "actual_sha256": actual, "match": actual == expected})
        print("[HASH] {}/56 {} {} {}".format(
            idx, key[0], key[1], "OK" if actual == expected else "MISMATCH"),
            flush=True)
    matched = sum(r["match"] for r in results)
    return {"status": "SHA256_56_OF_56_OK" if matched == 56 else "HASH_MISMATCH",
            "matched": matched, "total": 56, "individual": results,
            "npy_bytes_read": sum(r["bytes"] for r in results),
            "np_load_called": False}


def read_p03():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    with PROVENANCE.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    return audit_index(manifest, rows, CACHE), rows


def perform(data: Path, draft: Path) -> dict:
    results = {"tests": {}, "phases": {}, "failures": []}
    for name in TESTS:
        print("[TEST]", name, flush=True)
        try:
            p = subprocess.run([sys.executable, str(ROOT / "tests" / name)],
                               cwd=ROOT, capture_output=True, text=True,
                               check=False, timeout=150)
            results["tests"][name] = {"passed": p.returncode == 0,
                "returncode": p.returncode, "log_tail": (p.stdout + p.stderr)[-1500:]}
            if p.returncode:
                results["failures"].append("Unit test failed: " + name)
        except Exception as exc:
            results["failures"].append("Test " + name + ": " + repr(exc))
            results["tests"][name] = {"passed": False, "error": str(exc)}
        print("[TEST]", name, "OK" if results["tests"][name]["passed"]
              else "FAILED", flush=True)
    stages = (
        ("P0_source", lambda: {"status": "OK" if not audit_p0(ROOT)["source_contract_mismatches"] else "DRIFT"}),
        ("P0_1_draft", lambda: validate_p01(
            json.loads(draft.read_text(encoding="utf-8")), read_protocol(ROOT),
            code_provenance(ROOT), git_head(ROOT))),
        ("P0_2_development", lambda: {"status": audit_p02(ROOT, draft)["status"]}),
        ("MultiCue_name_layout", lambda: _multicue(data)),
        ("P0_3_sidecars", lambda: _sidecars()),
    )
    for key, operation in stages:
        print("[GATE]", key, flush=True)
        try:
            value = operation()
            results["phases"][key] = value
            if key == "P0_source" and value["status"] != "OK":
                results["failures"].append("P0 source contract drift")
        except Exception as exc:
            results["phases"][key] = {"status": "FAILED", "error": str(exc)}
            results["failures"].append(key + ": " + repr(exc))
    if results["phases"].get("P0_3_sidecars", {}).get("matching") == 56:
        print("[GATE] P0_4_cache_SHA256 (56 cache arrays)", flush=True)
        try:
            p03, rows = read_p03()
            result = validate_56(p03, rows)
            results["phases"]["P0_4_cache_SHA256"] = result
            if result["matched"] != 56:
                results["failures"].append("Some NPY SHA256 mismatched")
        except Exception as exc:
            results["phases"]["P0_4_cache_SHA256"] = {"status": "FAILED", "error": str(exc)}
            results["failures"].append("P0_4_cache_SHA256: " + repr(exc))
    else:
        results["failures"].append("P0.3 incomplete, cannot authenticate NPY bytes")
    results["status"] = ("TECHNICAL_AUDITS_OK_SCIENTIFIC_GATES_STILL_OPEN"
                         if not results["failures"] else "TECHNICAL_REVIEW_REQUIRED")
    results["scientific_pending"] = [
        "H1/H2 membership parameters and legitimate fit provenance",
        "H2 Choquet capacity/Mobius and provenance",
        "Four development-fitted thresholds for candidate/control",
        "GT edges content/encoding and multi-annotator F1 final contract",
        "Independence and prior exposure of every BIPED/MultiCue capture",
        "Final N, test and full pre-registration freeze commit",
    ]
    results["GT_H5_F1_or_confirmatory_data_opened"] = False
    results["new_training_or_descriptor_reprocessing"] = False
    results["cohort_frozen"] = False
    return results


def _multicue(root: Path):
    val = validate_inventory(root)
    return {"status": val["status"], "sequences": val["sequence_count"],
            "capture_prefixes": val["capture_prefix_count"],
            "maximum_candidate_prefixes": val["provisional_max_other_prefixes"],
            "held_prefix": val["historically_exposed_prefix_held"]}


def _sidecars():
    p03, _ = read_p03()
    return {"status": p03["status"],
            "matching": p03["matching_sidecar_and_npy_metadata"], "required": 56}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-root", type=Path, default=DATA)
    ap.add_argument("--draft", type=Path, default=DRAFT)
    ap.add_argument("--outdir", type=Path,
                    default=DATA / "paper_a_prefreeze_combined_audit")
    args = ap.parse_args()
    target = args.outdir.expanduser().resolve()
    if os.name == "nt" and target.drive.lower() == ROOT.drive.lower():
        ap.error("Use F: (data disk), not C: for reports")
    target.mkdir(exist_ok=True, parents=True)
    stamp = datetime.now(timezone.utc).strftime("prefreeze_%Y%m%dT%H%M%S_%fZ.json")
    final = target / stamp
    print("[START] One-shot read-only technical prefreeze audit", flush=True)
    report = perform(args.data_root, args.draft)
    report["git_commit"] = git_head(ROOT)
    report["completed_utc"] = datetime.now(timezone.utc).isoformat()
    tmp = final.with_suffix(".json.part")
    with tmp.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    os.replace(tmp, final)
    print(json.dumps({"status": report["status"],
        "passed_tests": sum(x["passed"] for x in report["tests"].values()),
        "test_groups": len(report["tests"]),
        "verified_cache_files": report["phases"].get("P0_4_cache_SHA256", {}).get("matched", 0),
        "failures": report["failures"],
        "report": str(final), "cohort_frozen": False},
        ensure_ascii=False, indent=2), flush=True)
    return 0 if not report["failures"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
