#!/usr/bin/env python3
"""Apply documented visual same-scene decisions, without examining GT or computing F1.

Input is a pre-data BIPED TRAIN image audit CSV, with original SHA256 values.
Output stays local and is NOT a certified confirmatory cohort.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/local_dev/paper_a_confirmation_inventory/predata_audit"
DECISIONS = ROOT / "docs/paper_a_confirmation/visual_duplicate_decisions.csv"
REQUIRED_INPUT = {
    "dataset", "image_id", "relative_path", "sha256", "status", "near_image_flags"
}
REQUIRED_DECISIONS = {
    "image_a", "image_b", "decision", "representative", "excluded",
    "source", "review_date"
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_csv(path: Path, required: set[str]) -> tuple[list[dict], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        if not required.issubset(fields):
            raise ValueError(f"{path}: missing columns {sorted(required - set(fields))}")
        return list(reader), fields


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--audit", type=Path, default=BASE / "candidate_review.csv")
    ap.add_argument("--decisions", type=Path, default=DECISIONS)
    ap.add_argument("--out-dir", type=Path, default=BASE)
    args = ap.parse_args()

    rows, original_fields = load_csv(args.audit, REQUIRED_INPUT)
    choices, _ = load_csv(args.decisions, REQUIRED_DECISIONS)
    if len(rows) != 200:
        raise ValueError(f"Expected exactly 200 BIPED train candidates, got {len(rows)}")
    if len(choices) != 2:
        raise ValueError(f"Expected exactly 2 human-confirmed pairs, got {len(choices)}")

    by_id = {row["image_id"]: row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError("Candidate IDs are not unique")
    if any(row["dataset"] != "BIPEDv2_train" for row in rows):
        raise ValueError("Unexpected domain in audit CSV")
    if any(row["status"] not in {"REVIEW_NOT_CERTIFIED", "REVIEW_NEAR_DUPLICATE"}
           for row in rows):
        raise ValueError("Other blocking statuses exist: review before deduplication")

    kept_ids, discarded_ids, covered = set(), set(), set()
    evidence = []
    for pair in choices:
        a, b = pair["image_a"], pair["image_b"]
        keep, drop = pair["representative"], pair["excluded"]
        if pair["decision"] != "same_scene" or pair["source"] != "human_visual_review":
            raise ValueError("Only specifically confirmed same-scene visual decisions allowed")
        if not pair["review_date"].strip():
            raise ValueError("Missing human review date")
        if a == b or {a, b} != {keep, drop}:
            raise ValueError(f"Invalid keep/exclude pair {a}, {b}")
        if keep != min(a, b):
            raise ValueError(f"Representative must be lexicographically smaller: {keep}")
        if a not in by_id or b not in by_id:
            raise ValueError(f"Missing pair in audit CSV: {a} / {b}")
        if covered & {a, b}:
            raise ValueError("An image appears in more than one visual decision")
        covered |= {a, b}
        for left, right in ((a, b), (b, a)):
            record = by_id[left]
            if record["status"] != "REVIEW_NEAR_DUPLICATE":
                raise ValueError(f"Missing near-duplicate flag on {left}")
            if f"BIPED_train:{right}" not in record["near_image_flags"].split("|"):
                raise ValueError(f"Audit did not flag expected pair {left} / {right}")
        kept_ids.add(keep)
        discarded_ids.add(drop)
        evidence.append({"members": [a, b], "representative": keep,
                         "excluded_from_sampling": drop,
                         "image_sha256": {x: by_id[x]["sha256"] for x in (a, b)},
                         "source": "human visual assessment of images, not GT"})

    flagged = {r["image_id"] for r in rows if r["status"] == "REVIEW_NEAR_DUPLICATE"}
    if flagged != covered:
        raise ValueError(f"Other unreviewed visual alerts exist: {sorted(flagged - covered)}")

    output = []
    for row in rows:
        if row["image_id"] in discarded_ids:
            continue
        copy = dict(row)
        copy["visual_same_scene_review"] = (
            "REPRESENTATIVE_NOT_CERTIFIED"
            if row["image_id"] in kept_ids
            else "NO_DHASH_ALERT_NOT_CERTIFIED"
        )
        copy["confirmatory_eligibility"] = "PENDING_HISTORICAL_AND_SCENE_LINEAGE_AUDIT"
        output.append(copy)
    if len(output) != 198:
        raise AssertionError(f"Expected 198 post-dedup candidates, got {len(output)}")

    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    csvout = out / "biped_train_after_visual_dedup_candidates.csv"
    columns = original_fields + ["visual_same_scene_review", "confirmatory_eligibility"]
    with csvout.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(output)
    report = {
        "status": "VISUAL_DEDUP_COMPLETE_LINEAGE_AUDIT_PENDING",
        "original_images": len(rows),
        "confirmed_same_scene_pairs": len(choices),
        "excluded_for_sampling": sorted(discarded_ids),
        "retained_representatives": sorted(kept_ids),
        "remaining_not_certified": len(output),
        "candidate_csv": str(csvout),
        "audit_csv_sha256": sha256(args.audit),
        "decision_csv_sha256": sha256(args.decisions),
        "evidence": evidence,
        "warning": (
            "No GT or F1 was accessed. This is NOT a frozen or eligible cohort. "
            "Scene/sequence dependence, historical exposure, and second-domain "
            "independence are still pending."
        ),
    }
    report_path = out / "visual_dedup_summary.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False),
                           encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
