#!/usr/bin/env python3
"""P0.1: draft H1/H2 specific GT-free parameter recipe manifest.

Reads only allowlisted Python SOURCE, pre-registration protocol.json and
(when --check is used) this project's own P0.1 draft. Never accesses
historical models/results, GT/H5, images, maps, predictions or F1.
Does NOT extract/fit/freeze model parameters. All unverified values NULL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = Path(r"F:\MFI-Edge-Data\MultiCue\paper_a_H1_H2_recipe_P0_1_DRAFT.json")
CODE_FILES = (
    "src/stage24_recertification_ops.py",
    "src/stage24_recertification_cv.py",
    "src/stage24_residual.py",
    "src/stage24_integrity.py",
    "src/stage23_descriptors.py",
    "src/stage24_strict_generalized_cf1f2.py",
    "src/postprocess.py",
    "src/paper_a_confirmation_paired_f1.py",
    "scripts/prepare_paper_a_h1h2_recipe_P0_1.py",
)
PROTOCOL = "docs/paper_a_confirmation/protocol.json"
EXPECTED = {
    "H1": (("halfdisc_distribution_contrast", "pmi_dependency_deficit"),
           "maximum", "equal_mean", "negative"),
    "H2": (("fh_region_boundary", "halfdisc_distribution_contrast",
            "structure_tensor_coherence"),
           "choquet_generalized_150", "equal_mean", "positive"),
}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40}$")
PROOF_KEYS = frozenset({
    "development_dataset_id", "split_role", "training_ids_sha256",
    "fitting_commit", "parameter_export_sha256",
    "no_confirmatory_overlap_attested",
})


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for data in iter(lambda: f.read(1048576), b""):
            h.update(data)
    return h.hexdigest()


def git_head(root: Path) -> str:
    p = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                       capture_output=True, text=True, check=False)
    head = p.stdout.strip()
    if p.returncode or not GIT_SHA.fullmatch(head):
        raise ValueError("Cannot establish exact Git source commit")
    return head


def code_provenance(root: Path) -> dict:
    result = {}
    for relative in (PROTOCOL, *CODE_FILES):
        path = root / relative
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Required code/protocol source missing or unsafe: " + relative)
        result[relative] = digest(path)
    return result


def read_protocol(root: Path) -> dict:
    path = root / PROTOCOL
    protocol = json.loads(path.read_text(encoding="utf-8"))
    if protocol.get("status") != "draft_not_frozen":
        raise ValueError("P0.1 may run only before protocol freeze")
    cases = protocol.get("hypotheses", [])
    if len(cases) != 2 or {x.get("id") for x in cases} != set(EXPECTED):
        raise ValueError("Unexpected number/identity of preregistered hypotheses")
    for x in cases:
        group, candidate, control, direction = EXPECTED[x["id"]]
        if (tuple(x.get("group", [])) != group
                or x.get("candidate") != candidate
                or x.get("control") != control
                or x.get("signed_prediction") != direction):
            raise ValueError("H1/H2 scientific contract drift: " + x["id"])
    return protocol


def empty_proof() -> dict:
    return {key: None for key in sorted(PROOF_KEYS)}


def new_draft(protocol: dict, source_hashes: dict, commit: str) -> dict:
    records = []
    for case in sorted(protocol["hypotheses"], key=lambda c: c["id"]):
        is_h2 = case["id"] == "H2"
        names = list(case["group"])
        records.append({
            "id": case["id"],
            "group": names,
            "preoutcome_feature": case["preoutcome_feature"],
            "signed_prediction": case["signed_prediction"],
            "membership": {
                "mode": "legacy_sigmoid",
                "midpoint": None,
                "scale": None,
                "fit_provenance": empty_proof(),
            },
            "candidate": {
                "family": case["candidate"],
                "n_inputs": len(names),
                "capacity": None if is_h2 else "NOT_APPLICABLE",
                "mobius": None if is_h2 else "NOT_APPLICABLE",
                "threshold": None,
                "capacity_fit_provenance": empty_proof() if is_h2 else "NOT_APPLICABLE",
                "threshold_fit_provenance": empty_proof(),
            },
            "control": {
                "family": "equal_mean",
                "n_inputs": len(names),
                "threshold": None,
                "threshold_fit_provenance": empty_proof(),
            },
        })
    return {
        "schema": "paper_a_h1h2_recipe_P0_1",
        "status": "DRAFT_VALUES_UNVERIFIED_NOT_FROZEN",
        "source_commit": commit,
        "source_sha256": source_hashes,
        "fixed_method_choices": {
            "task_proposal": "edges",
            "map_dtype": "float32",
            "thinning": "nms_image",
            "calibration": "legacy_sigmoid",
            "suppressor": "identity",
            "suppression_strength": 1.0,
            "matching_tolerance_ratio": 0.0075,
            "H2_gamma": 1.5,
        },
        "hypotheses": records,
        "no_scientific_artifacts_or_outcomes_read": True,
        "protocol_frozen": False,
    }


def _shape(actual: dict, expected: dict, context: str) -> None:
    if not isinstance(actual, dict) or set(actual) != set(expected):
        raise ValueError(f"{context}: unexpected/missing keys; F1 and results not permitted")


def _finite_list(value, count: int, context: str, missing: list) -> list[float] | None:
    if value is None:
        missing.append(context)
        return None
    if (not isinstance(value, list) or len(value) != count
            or any(type(x) not in (int, float) or not math.isfinite(x)
                   for x in value)):
        raise ValueError(f"{context}: require exactly {count} finite numbers")
    return [float(x) for x in value]


def _proof(proof, context: str, missing: list) -> None:
    _shape(proof, empty_proof(), context)
    for key in PROOF_KEYS:
        v = proof[key]
        if v is None:
            missing.append(context + "." + key)
        elif key == "split_role":
            if v != "development_train":
                raise ValueError(f"{context}: split_role must be development_train")
        elif key == "no_confirmatory_overlap_attested":
            if v is not True:
                raise ValueError(f"{context}: independent-training attestation must be true")
        elif key == "fitting_commit":
            if not isinstance(v, str) or not GIT_SHA.fullmatch(v):
                raise ValueError(f"{context}: invalid fitting_commit")
        elif key.endswith("_sha256"):
            if not isinstance(v, str) or not SHA256.fullmatch(v):
                raise ValueError(f"{context}: invalid {key}")
        elif key == "development_dataset_id":
            if not isinstance(v, str) or not v.strip():
                raise ValueError(f"{context}: dataset ID missing")
            if v.strip().lower() in {"multicue", "biped_train", "bipedv2_train"}:
                raise ValueError(f"{context}: cannot treat proposed confirmation source as training")
    # This proof structure still requires independent external verification.


def _threshold(value, context: str, missing: list) -> None:
    if value is None:
        missing.append(context)
    elif type(value) not in (float, int) or not math.isfinite(value) or not 0 < value <= 1:
        raise ValueError(f"{context}: threshold must be a finite float in (0,1]")


def _choquet(cap, mob, context: str, missing: list) -> None:
    cap = _finite_list(cap, 8, context + ".capacity", missing)
    mob = _finite_list(mob, 6, context + ".mobius", missing)
    if cap is None or mob is None:
        return
    if abs(cap[0]) > 1e-5 or abs(cap[-1] - 1) > 1e-5:
        raise ValueError(context + ": capacity must have mu(empty)=0, mu(full)=1")
    for mask in range(8):
        for i in range(3):
            if not mask & (1 << i) and cap[mask] > cap[mask | (1 << i)] + 1e-5:
                raise ValueError(context + ": capacity violates monotonicity")
        rebuilt = sum(mob[i] for i in range(3) if mask & (1 << i))
        for idx, (i, j) in enumerate(((0, 1), (0, 2), (1, 2))):
            if mask & (1 << i) and mask & (1 << j):
                rebuilt += mob[3 + idx]
        if abs(rebuilt - cap[mask]) > 1e-4:
            raise ValueError(context + ": capacity and Mobius coefficients disagree")


def validate(draft: dict, protocol: dict, hashes: dict, commit: str) -> dict:
    expected = new_draft(protocol, hashes, commit)
    _shape(draft, expected, "manifest")
    for key in ("schema", "status", "source_commit", "source_sha256",
                "fixed_method_choices", "no_scientific_artifacts_or_outcomes_read",
                "protocol_frozen"):
        if draft[key] != expected[key]:
            raise ValueError(f"Manifest's pinned source/method contract changed: {key}")
    if not isinstance(draft["hypotheses"], list) or len(draft["hypotheses"]) != 2:
        raise ValueError("Expected exactly H1 and H2")
    pending = []
    for rec, original in zip(draft["hypotheses"], expected["hypotheses"]):
        _shape(rec, original, "hypothesis")
        for key in ("id", "group", "preoutcome_feature", "signed_prediction"):
            if rec[key] != original[key]:
                raise ValueError("Modified H1/H2 feature/group/direction")
        for key in ("membership", "candidate", "control"):
            _shape(rec[key], original[key], rec["id"] + "." + key)
        identity = rec["id"]
        mem = rec["membership"]
        if mem["mode"] != "legacy_sigmoid":
            raise ValueError(identity + ": unsupported membership")
        n = len(rec["group"])
        midpoint = _finite_list(mem["midpoint"], n, identity + ".midpoint", pending)
        scale = _finite_list(mem["scale"], n, identity + ".scale", pending)
        if scale is not None and any(x <= 0 for x in scale):
            raise ValueError(identity + ": membership scale must be positive")
        _proof(mem["fit_provenance"], identity + ".membership_provenance", pending)
        for role in ("candidate", "control"):
            op = rec[role]
            ref = original[role]
            if op["family"] != ref["family"] or op["n_inputs"] != ref["n_inputs"]:
                raise ValueError(identity + ": changed family/arity for " + role)
            _threshold(op["threshold"], identity + "." + role + ".threshold", pending)
            _proof(op["threshold_fit_provenance"],
                   identity + "." + role + ".threshold_provenance", pending)
        cand = rec["candidate"]
        if identity == "H2":
            _choquet(cand["capacity"], cand["mobius"], "H2.choquet", pending)
            _proof(cand["capacity_fit_provenance"], "H2.capacity_provenance", pending)
        else:
            for k in ("capacity", "mobius", "capacity_fit_provenance"):
                if cand[k] != "NOT_APPLICABLE":
                    raise ValueError("H1 maximum must not contain fitted Choquet capacity")
    return {
        "status": ("P0_1_SCHEMA_COMPLETE_INDEPENDENT_AUDIT_REQUIRED"
                   if not pending else "P0_1_DRAFT_INCOMPLETE_NOT_FROZEN"),
        "pending_count": len(pending),
        "pending": sorted(pending),
        "no_GT_H5_F1_or_model_outputs_read": True,
        "protocol_frozen": False,
        "parameter_training_provenance_independently_verified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", type=Path,
                      help="Validate only a P0.1 draft, without modifying it")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    root = ROOT.resolve()
    protocol = read_protocol(root)
    hashes = code_provenance(root)
    commit = git_head(root)
    if args.check:
        path = args.check.expanduser().resolve()
        if not path.is_file() or path.suffix.lower() != ".json":
            parser.error("Provide an existing P0.1 JSON draft")
        data = json.loads(path.read_text(encoding="utf-8"))
        print(json.dumps(validate(data, protocol, hashes, commit),
                         ensure_ascii=False, indent=2))
        return 0
    path = args.output.expanduser().resolve()
    if (os.name == "nt" and path.drive.lower() == root.drive.lower()
            or path.suffix.lower() != ".json" or not path.parent.is_dir()):
        parser.error("Use a .json output in an existing directory on data drive F:")
    if path.exists():
        parser.error("Refusing to overwrite existing draft; supply --output new_file.json")
    draft = new_draft(protocol, hashes, commit)
    report = validate(draft, protocol, hashes, commit)
    tmp = path.with_suffix(".json.part")
    if tmp.exists():
        parser.error("Interrupted temporary draft exists; inspect first")
    with tmp.open("x", encoding="utf-8") as file:
        json.dump(draft, file, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    print(json.dumps({**report, "draft_path": str(path),
                      "source_commit": commit,
                      "hypotheses": [x["id"] for x in draft["hypotheses"]]},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
