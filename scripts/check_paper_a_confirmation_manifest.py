#!/usr/bin/env python3
"""Pre-data eligibility guard for Paper A H1/H2. Does not read GT or compute F1."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / "docs/paper_a_confirmation/protocol.json"
COLUMNS = ["dataset", "image_id", "relative_path", "image_sha256",
           "independence_review", "prior_exposure_review", "scene_group", "notes"]
SHA = re.compile(r"^[0-9a-fA-F]{64}$")


def audit_protocol(path: Path):
    p = json.loads(path.read_text(encoding="utf-8"))
    assert p["status"] in {"draft_not_frozen", "frozen"}
    assert [h["id"] for h in p["hypotheses"]] == ["H1", "H2"]
    assert [h["signed_prediction"] for h in p["hypotheses"]] == ["negative", "positive"]
    assert p["inference"]["multiplicity"].lower().startswith("holm")
    assert p["exploratory_source"]["never_count_as_confirmatory"] is True
    assert p["cohort"]["no_GT_until_lock"] is True
    assert p["measures"]["image_gt_used_for_features"] is False
    assert p["inference"]["alpha_familywise"] == 0.05
    return p


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def audit_manifest(path: Path, p: dict, root: Path | None, require_frozen: bool):
    errors, warnings = [], []
    if require_frozen and p["status"] != "frozen":
        errors.append("Protocol not frozen: block confirmatory analysis")
    source_names = p["cohort"]["dataset_names"]
    if not source_names:
        errors.append("Dataset identities not frozen in protocol")
    with path.open(encoding="utf-8-sig", newline="") as f:
        rdr = csv.DictReader(f)
        if rdr.fieldnames != COLUMNS:
            errors.append(f"Expected columns: {','.join(COLUMNS)}")
            rows = []
        else:
            rows = list(rdr)
    seen_ids, seen_shas = set(), set()
    counts = Counter()
    discovery = set(p["exploratory_source"]["discovery_images"])
    for n, r in enumerate(rows, start=2):
        dataset, image_id = r["dataset"].strip(), r["image_id"].strip()
        sha = r["image_sha256"].strip().lower()
        path_text = r["relative_path"].strip()
        counts[dataset] += 1
        if not dataset or not image_id:
            errors.append(f"line {n}: missing dataset or ID")
        if source_names and dataset not in source_names:
            errors.append(f"line {n}: unregistered dataset {dataset}")
        if image_id in discovery:
            errors.append(f"line {n}: discovery UDED image excluded {image_id}")
        if (dataset, image_id) in seen_ids:
            errors.append(f"line {n}: duplicate dataset/image ID")
        seen_ids.add((dataset, image_id))
        if not SHA.fullmatch(sha):
            errors.append(f"line {n}: invalid SHA256")
        elif sha in seen_shas:
            errors.append(f"line {n}: duplicate content SHA256")
        seen_shas.add(sha)
        if r["independence_review"].strip().lower() != "pass":
            errors.append(f"line {n}: independence review not passed")
        if r["prior_exposure_review"].strip().lower() != "pass":
            errors.append(f"line {n}: prior exposure review not passed")
        if not r["scene_group"].strip():
            errors.append(f"line {n}: missing scene_group")
        if not path_text:
            errors.append(f"line {n}: empty relative path")
        else:
            q = Path(path_text)
            if q.is_absolute() or ".." in q.parts:
                errors.append(f"line {n}: unsafe relative path")
            elif root is not None:
                fp = root / q
                if not fp.is_file():
                    errors.append(f"line {n}: missing original {path_text}")
                elif SHA.fullmatch(sha) and file_hash(fp) != sha:
                    errors.append(f"line {n}: SHA256 mismatch {path_text}")
    if len(rows) < p["cohort"]["target_n_independent_images"]:
        errors.append("Less than preregistered target independent images")
    if len(counts) != p["cohort"]["required_domains"]:
        errors.append("Wrong number of domains")
    for d, n in counts.items():
        if n < p["cohort"]["min_n_per_domain"]:
            errors.append(f"Domain {d}: only {n} images")
    scene = Counter((r["dataset"].strip(), r["scene_group"].strip()) for r in rows)
    correlated = {str(k): n for k, n in scene.items() if n > 1}
    if correlated:
        warnings.append(f"Related scene groups detected (not proof of independent units): {len(correlated)}")
    if root is None:
        warnings.append("Original file content hashes not verified: provide --images-root to verify")
    # Deliberately no ground-truth access; historical dataset leakage cannot be proven from this manifest alone.
    warnings.append("Manual near-duplicate, historical-exposure and protocol-equivalence audits remain mandatory")
    return {"status": "PASS" if not errors else "BLOCKED", "n_images": len(rows),
            "per_domain": dict(counts), "errors": errors[:100], "warnings": warnings,
            "protocol_status": p["status"]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--images-root", type=Path)
    ap.add_argument("--protocol-only", action="store_true")
    ap.add_argument("--require-frozen", action="store_true")
    args = ap.parse_args()
    p = audit_protocol(args.protocol)
    if args.protocol_only:
        print(json.dumps({"protocol_status": p["status"], "hypotheses": ["H1", "H2"],
                          "ready_for_outcomes": p["status"] == "frozen"}, indent=2))
        return 0
    if not args.manifest:
        ap.error("--manifest required unless --protocol-only")
    results = audit_manifest(args.manifest, p, args.images_root, args.require_frozen)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if results["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
