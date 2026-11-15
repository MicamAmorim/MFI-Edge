#!/usr/bin/env python3
"""Pre-data historical exposure reconnaissance. Does not inspect GT or F1.

Reads:
* SHA256 and image IDs from an existing BIPED pre-data inventory CSV
* filenames and image-provenance metadata in archived research manifests
* SOURCE CODE lines across local Git branches mentioning BIPED/RGB IDs

This is a conservative source/lineage audit. It never proves non-exposure.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/local_dev/paper_a_confirmation_inventory/predata_audit"
SOURCE_PATTERNS = ("*.py", "*.ps1", "*.bat", "*.sh", "*.yml", "*.yaml", "*.toml")
SOURCE_QUERY = r"BIPED|RGB_[0-9]{2,}|edges[/\\]imgs[/\\]train"
MAX_SOURCE_LINE = 190
FILE_SIZE_LIMIT = 8_000_000
METADATA_NAMES = ("manifest", "provenance", "lineage", "dataset_fingerprint")


def call_git(repo: Path, args: list[str]) -> tuple[int, str]:
    cmd = ["git", "-C", str(repo), *args]
    process = subprocess.run(cmd, text=True, encoding="utf-8",
                             errors="replace", stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, check=False)
    if process.returncode not in {0, 1}:
        raise RuntimeError(f"Git error {process.returncode}: {process.stderr[-1000:]}")
    return process.returncode, process.stdout


def refs(repo: Path) -> list[str]:
    rc, raw = call_git(repo, [
        "for-each-ref", "--format=%(refname:short)",
        "refs/remotes/origin"
    ])
    entries = sorted(set(x for x in raw.splitlines()
                         if x.strip() and not x.endswith("/HEAD")))
    if not entries:
        raise RuntimeError("No origin/* references available; git fetch origin first")
    return entries


def read_candidates(path: Path) -> tuple[dict, dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 198:
        raise ValueError(f"Expected 198 visually deduplicated candidates, got {len(rows)}")
    allowed = {"image_id", "sha256", "confirmatory_eligibility"}
    if not rows or not allowed.issubset(rows[0]):
        raise ValueError("Unexpected deduplicated candidate schema")
    ids = {r["image_id"]: r for r in rows}
    hashes = {r["sha256"].lower(): r["image_id"] for r in rows}
    if len(ids) != 198 or len(hashes) != 198:
        raise ValueError("Repeated IDs or hashes in candidate inventory")
    if any(r["confirmatory_eligibility"] != "PENDING_HISTORICAL_AND_SCENE_LINEAGE_AUDIT"
           for r in rows):
        raise ValueError("Candidate manifest was previously modified/promoted")
    if {"RGB_172", "RGB_222"} & set(ids):
        raise ValueError("Confirmed duplicate exclusions unexpectedly still present")
    return ids, hashes


def git_source_audit(repo: Path, image_ids: set[str], max_findings: int):
    findings = []
    matches = set()
    branch_counts = {}
    seen = 0
    for ref in refs(repo):
        rc, raw = call_git(repo, [
            "grep", "-I", "-n", "-i", "-E", SOURCE_QUERY, ref, "--",
            *SOURCE_PATTERNS
        ])
        if rc == 1:
            branch_counts[ref] = 0
            continue
        lines = raw.splitlines()
        branch_counts[ref] = len(lines)
        for line in lines:
            # git grep output: "ref:path:line_number:code".
            parts = line.split(":", 3)
            if len(parts) != 4:
                continue
            _, filename, line_number, code = parts
            found_ids = sorted(set(re.findall(r"RGB_[0-9]{2,}", code)) & image_ids)
            key = (filename, line_number, code.strip())
            # Deduplicate repeated code across branches while retaining the first ref.
            if key in matches:
                continue
            matches.add(key)
            seen += 1
            if len(findings) < max_findings:
                findings.append({
                    "ref_first_seen": ref,
                    "path": filename,
                    "line_number": line_number,
                    "mentions_candidate_ids": found_ids,
                    "mentions_train": "train" in code.lower(),
                    "source_excerpt": code.strip()[:MAX_SOURCE_LINE],
                    "meaning": "Source-code reference only; execution and outcome use not established"
                })
    return findings, branch_counts, seen


def metadata_audit(repo: Path, image_ids: set[str], known_sha_to_id: dict,
                   max_findings: int):
    root = repo / "results/paper_a_evidence"
    findings, checked, oversized = [], 0, 0
    if not root.is_dir():
        return findings, checked, oversized
    id_regex = re.compile(r"\bRGB_[0-9]{2,}\b")
    for file in sorted(root.rglob("*")):
        if not file.is_file() or file.suffix.lower() not in {".json", ".jsonl", ".csv"}:
            continue
        if not any(token in file.stem.lower() for token in METADATA_NAMES):
            continue
        if file.stat().st_size > FILE_SIZE_LIMIT:
            oversized += 1
            continue
        checked += 1
        # Only image identifiers and content hashes are extracted. No scores are parsed.
        contents = file.read_text(encoding="utf-8-sig", errors="replace")
        ids = sorted(set(id_regex.findall(contents)) & image_ids)
        sha_refs = sorted(set(sha for sha in known_sha_to_id if sha in contents.lower()))
        if ids or sha_refs:
            if len(findings) < max_findings:
                findings.append({
                    "path": file.relative_to(repo).as_posix(),
                    "candidate_ids_mentioned": ids,
                    "candidate_sha_matched_ids": [known_sha_to_id[sha] for sha in sha_refs],
                    "interpretation": "Image ID/content hash recorded historically: review exposure"
                })
    return findings, checked, oversized


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-root", type=Path, default=ROOT)
    ap.add_argument("--candidates", type=Path,
                    default=BASE / "biped_train_after_visual_dedup_candidates.csv")
    ap.add_argument("--out", type=Path, default=BASE / "historical_source_audit.json")
    ap.add_argument("--max-findings", type=int, default=300)
    args = ap.parse_args()

    repo = args.repo_root.resolve()
    ids, hashes = read_candidates(args.candidates)
    source, counts, nsource = git_source_audit(repo, set(ids), args.max_findings)
    meta, checked, skipped = metadata_audit(repo, set(ids), hashes, args.max_findings)
    report = {
        "status": "HISTORY_SOURCE_AUDIT_ONLY_NOT_CERTIFIED",
        "candidate_count": len(ids),
        "candidate_inventory_sha256": hashlib.sha256(
            args.candidates.read_bytes()).hexdigest(),
        "git_branches_checked": len(counts),
        "branch_source_match_counts": counts,
        "unique_source_references": nsource,
        "source_references": source,
        "research_metadata_files_checked": checked,
        "metadata_large_files_skipped": skipped,
        "metadata_candidate_matches": meta,
        "cohort_confirmatory_eligible": False,
        "interpretation": (
            "Source references alone do not establish executed runs; absence of matches "
            "does not establish non-exposure on this machine, historic local branches, "
            "untracked results, other workstations or past experimental decisions."
        ),
        "next_checks": [
            "Review any source mentions of BIPED train and whether historical runs used it",
            "Review scene/sequence dependence beyond the two visually verified pairs",
            "Record a per-image reviewer decision and independent second-domain inventory",
            "Complete power analysis and fix evaluator/calibration before freezing protocol",
        ],
        "read_scope": (
            "Only Git source text, image IDs and hashes from local metadata files; "
            "no original image decoded by this script, no GT read, no F1 inspected"
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    print(json.dumps({
        "status": report["status"], "candidate_count": len(ids),
        "git_branches_checked": len(counts),
        "unique_source_references": nsource,
        "research_metadata_files_checked": checked,
        "metadata_candidate_matches": meta,
        "output": str(args.out),
        "cohort_confirmatory_eligible": False,
        "warning": report["interpretation"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
