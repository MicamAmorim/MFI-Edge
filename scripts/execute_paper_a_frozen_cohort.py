#!/usr/bin/env python3
"""Post-freeze image->X1/Y1/X2/Y2 executor for Paper A.

DANGER ZONE: GT is accessed ONLY after the existing freeze guard succeeds,
AND the independently reviewed executor SHA and explicit GT-decoding policy
are authorized in freeze_approval.json. No self-certification. Fail closed.
No training, threshold fitting, sample selection or scene exclusions here.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
# Windows direct-script launches put scripts/, not the repository root, on
# sys.path. Native packages (src.*) require the repository root explicitly.
# Also works under python -I and does not modify the user's environment.
for module_root in (ROOT, ROOT / "scripts"):
    module_path = str(module_root)
    if module_path not in sys.path:
        sys.path.insert(0, module_path)
DATA = Path(r"F:\MFI-Edge-Data\MultiCue")
WORK = DATA / "paper_a_completion"
PROTOCOL = ROOT / "docs/paper_a_confirmation/protocol.json"
BIPED_IMAGES = ROOT / "datasets/BIPEDv2/edges/imgs/train/rgbr/real"
BIPED_GT = ROOT / "datasets/BIPEDv2/edges/edge_maps/train/rgbr/real"
BIN_POLICY = "STRICT_BINARY_0_1_OR_0_255_NATIVE_v1"
TAR_SHA = "8e5fdb2ff7343e4a55f110e9ffe189b2c81689cd326324e34c6c73562191819e"
TAR_REV = "f47b14959e9764c8aa854cb7958d54462c46f8ef"
GT_MEMBER = re.compile(r"^multicue/ground-truth/images/edges/(\d+_left_\d+)\.(\d+)\.png$")
MAX_GT = 20_000_000
MAX_ALL_GT = 1_000_000_000


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1 << 20), b""):
            h.update(part)
    return h.hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def safe_name(raw: str) -> str:
    p = PurePosixPath(raw.replace("\\", "/"))
    if (p.is_absolute() or ".." in p.parts or not p.parts
            or ":" in raw or raw.startswith(".")):
        raise ValueError("Unsafe relative filename: " + raw)
    return p.as_posix()


def authorized(work: Path) -> tuple[dict, dict, dict, list[dict]]:
    # This ordering is essential: NO GT filenames/payloads/metrics before gate.
    from paper_a_freeze_guard import validate_files
    recipe_path = work / "frozen_H1_H2_recipe.json"
    cohort_path = work / "frozen_cohort_manifest.csv"
    approval_path = work / "freeze_approval.json"
    gate = validate_files(PROTOCOL, recipe_path, cohort_path, approval_path)
    if gate["blockers"]:
        raise PermissionError("Confirmatory GT locked: " + "; ".join(gate["blockers"]))
    approval = read_json(approval_path)
    actual_source = digest(Path(__file__))
    if (approval.get("approved_executor_source_sha256") != actual_source or
            approval.get("executor_contract_independently_reviewed") is not True):
        raise PermissionError("Independent GT executor review/source SHA missing")
    if approval.get("gt_binary_decoding_contract") != BIN_POLICY:
        raise PermissionError("GT binary decoding must be explicitly approved before first access")
    recipe = read_json(recipe_path)
    cohort = read_csv(cohort_path)
    if len(cohort) != gate["frozen_cohort_count"]:
        raise ValueError("Frozen cohort count changed")
    if {r["dataset"] for r in cohort} != {"BIPED", "MultiCue"}:
        raise ValueError("Unexpected frozen dataset labels")
    return gate, approval, recipe, cohort


def load_original(row: dict) -> np.ndarray:
    dataset = row["dataset"]
    base = BIPED_IMAGES if dataset == "BIPED" else DATA / "source_frames_only"
    rel = safe_name(row["relative_path"])
    candidate = (base / rel).resolve()
    if not candidate.is_file() or not candidate.is_relative_to(base.resolve()):
        raise FileNotFoundError("Invalid frozen original: " + rel)
    if candidate.suffix.lower() not in {".png", ".bmp", ".jpg", ".jpeg"}:
        raise ValueError("Unsupported original image type")
    if digest(candidate) != row["image_sha256"].lower():
        raise ValueError("Frozen original SHA mismatch: " + rel)
    if candidate.stem != row["image_id"]:
        raise ValueError("Original filename / frozen cohort ID mismatch")
    with Image.open(candidate) as image:
        if image.format not in ("PNG", "JPEG", "BMP"):
            raise ValueError("Unexpected original image decoder")
        result = np.array(image.convert("RGB"))
    if min(result.shape[:2]) < 8 or result.dtype != np.uint8:
        raise ValueError("Original RGB geometry invalid")
    return result


def binary_annotation(path: Path, native: tuple[int, int]) -> np.ndarray:
    """STRICT contract; never resize, threshold soft GT or select a channel."""
    with Image.open(path) as image:
        if image.format != "PNG":
            raise ValueError("Expected lossless PNG GT")
        arr = np.asarray(image)
    if arr.ndim == 3:
        if arr.shape[2] not in (3, 4):
            raise ValueError("GT has unexpected channel count")
        if not np.array_equal(arr[..., :3], np.broadcast_to(arr[..., :1], arr[..., :3].shape)):
            raise ValueError("GT RGB channels differ; no implicit first-channel policy")
        if arr.shape[2] == 4 and not np.all(arr[..., 3] == 255):
            raise ValueError("GT non-opaque alpha unsupported")
        arr = arr[..., 0]
    if arr.ndim != 2 or arr.shape != native or arr.dtype != np.uint8:
        raise ValueError("GT not uint8 native 2-D geometry")
    vals = set(np.unique(arr).tolist())
    if not vals or not vals.issubset({0, 1}) and not vals.issubset({0, 255}):
        raise ValueError("GT is not exact binary 0/1 or 0/255; refuse ad hoc thresholding")
    if 0 not in vals or len(vals) == 1:
        raise ValueError("GT empty or fully foreground; stop for protocol review")
    return np.asarray(arr > 0, dtype=bool)


def biped_gt(row: dict) -> Path:
    img_id = row["image_id"]
    if not re.fullmatch(r"RGB_\d+", img_id):
        raise ValueError("Unexpected BIPED image ID")
    matches = [
        x for x in BIPED_GT.iterdir()
        if x.is_file() and x.stem == img_id and x.suffix.lower() == ".png"
    ]
    if len(matches) != 1:
        raise ValueError("Expected exactly one BIPED PNG GT: " + img_id)
    return matches[0]


def multicue_gt_names(cohort: list[dict]) -> dict[str, list[str]]:
    # This reads only the indexed TAR member NAMES, after signed freeze.
    source = read_csv(DATA / "multicue_h5_anchored_sequence_candidates.csv")
    by_id = {r["sequence_id"]: r for r in source}
    requested = {}
    paths = set()
    for row in cohort:
        if row["dataset"] != "MultiCue":
            continue
        key = row["image_id"]
        if key not in by_id or row["scene_group"] != by_id[key]["capture_prefix"]:
            raise ValueError("Frozen MultiCue capture prefix/sequence mismatch")
        if row["scene_group"] == "4113":
            raise ValueError("Previously exposed MultiCue capture 4113 forbidden")
        names = json.loads(by_id[key]["edges_png_names"])
        if len(names) != 6 or len(set(names)) != 6:
            raise ValueError("Exactly six separate MultiCue edges names required")
        for name in names:
            if safe_name(name) != name or not GT_MEMBER.fullmatch(name):
                raise ValueError("Invalid MultiCue edges GT member")
            if GT_MEMBER.fullmatch(name).group(1) != key or name in paths:
                raise ValueError("MultiCue annotation/image mismatch")
            paths.add(name)
        requested[key] = sorted(names)
    return requested


def materialize_gt_once(names: dict[str, list[str]], work: Path,
                        cohort_sha: str) -> dict[str, Path]:
    """Extract only approved edges GT after freeze. Checkpoint by file SHA."""
    expected = {name for row in names.values() for name in row}
    target = work / "frozen_gt_edges" / cohort_sha[:16]
    target.mkdir(parents=True, exist_ok=True)
    manifest = target / "EXTRACTION_MANIFEST.json"
    existing = read_json(manifest) if manifest.is_file() else {}
    if (existing.get("cohort_sha256") == cohort_sha and
            existing.get("archive_sha256") == TAR_SHA and
            set(existing.get("files", {})) == expected and
            all((target / Path(p).name).is_file() and
                digest(target / Path(p).name) == v["sha256"]
                for p, v in existing["files"].items())):
        return {p: target / Path(p).name for p in expected}
    archive = DATA / "multicue-dataset.tar.bz2"
    prov = read_json(DATA / "archive_provenance.json")
    if (prov.get("archive_sha256") != TAR_SHA or
            prov.get("repository_commit_sha") != TAR_REV or
            prov.get("official_lfs_sha256_verified") is not True or
            not archive.is_file() or archive.stat().st_size != 3575680805):
        raise ValueError("Unverified MultiCue source archive")
    # Reconfirm bytes once before decoding the protected GT archive.
    if digest(archive) != TAR_SHA:
        raise ValueError("MultiCue source TAR SHA mismatch")
    found = {}
    total = 0
    with tarfile.open(archive, mode="r|bz2") as tar:
        for member in tar:
            raw = member.name.removeprefix("./")
            if raw not in expected:
                continue
            if (not member.isfile() or member.size < 1 or
                    member.size > MAX_GT or raw in found):
                raise ValueError("GT archive member invalid: " + raw)
            total += member.size
            if total > MAX_ALL_GT:
                raise ValueError("GT extraction exceeds byte cap")
            output = target / Path(raw).name
            if output.exists():
                # On interrupted extraction there may be no final manifest.
                # Compare the local bytes against the *current archive member*
                # before reusing; never trust an unverified partial cache.
                stream = tar.extractfile(member)
                if stream is None:
                    raise ValueError("Cannot read GT source member")
                h = hashlib.sha256()
                size = 0
                with stream:
                    for block in iter(lambda: stream.read(1048576), b""):
                        size += len(block)
                        if size > MAX_GT:
                            raise ValueError("GT payload exceeds byte cap")
                        h.update(block)
                if size != member.size or digest(output) != h.hexdigest():
                    raise ValueError("Existing GT cache differs from verified TAR: " + str(output))
                found[raw] = {"sha256": h.hexdigest(), "size_bytes": size}
                continue
            tmp = output.with_suffix(output.suffix + ".part")
            if tmp.exists():
                raise ValueError("Partial GT cache from interrupted extraction: " + str(tmp))
            stream = tar.extractfile(member)
            if stream is None:
                raise ValueError("Cannot open authorized GT member")
            h = hashlib.sha256()
            size = 0
            with stream, tmp.open("xb") as f:
                for block in iter(lambda: stream.read(1048576), b""):
                    size += len(block)
                    if size > MAX_GT:
                        raise ValueError("GT payload exceeds byte cap")
                    h.update(block)
                    f.write(block)
            if size != member.size:
                raise ValueError("Incomplete GT payload")
            os.replace(tmp, output)
            found[raw] = {"sha256": h.hexdigest(), "size_bytes": size}
    if set(found) != expected:
        raise ValueError("Missing MultiCue annotations: " + str(len(expected - set(found))))
    content = {"archive_sha256": TAR_SHA, "cohort_sha256": cohort_sha, "files": found}
    temp = manifest.with_suffix(".pending")
    temp.write_text(json.dumps(content, indent=2), encoding="utf-8")
    os.replace(temp, manifest)
    return {name: target / Path(name).name for name in expected}


def checkpoint_one(row: dict, recipe: dict, executor_sha: str,
                   gt_paths: list[Path], checkpoint: Path) -> dict:
    """Each capture recorded exactly once, with hashes for resume."""
    if not all(p.is_file() and not p.is_symlink() for p in gt_paths):
        raise FileNotFoundError("Missing GT annotation files")
    gt_hashes = [digest(p) for p in gt_paths]
    key = {
        "image_sha256": row["image_sha256"].lower(),
        "gt_sha256": gt_hashes,
        "recipe_sha256": digest(WORK / "frozen_H1_H2_recipe.json"),
        "executor_sha256": executor_sha,
        "dataset": row["dataset"],
        "image_id": row["image_id"],
        "scene_group": row["scene_group"],
    }
    # Verify the original's actual bytes even when the descriptor checkpoint
    # is reused. The reviewed cohort digest must still match the disk file.
    original = load_original(row)
    if checkpoint.is_file():
        existing = read_json(checkpoint)
        if existing.get("inputs") != key:
            raise ValueError("Existing image checkpoint provenance changed")
        return existing["outcome"]
    from src.paper_a_prefreeze_map_adapter import predict_original_pregt
    from src.paper_a_confirmation_paired_f1 import evaluate_paired_binary
    predictions = predict_original_pregt(original, recipe).predictions
    masks = [binary_annotation(p, tuple(original.shape[:2])) for p in gt_paths]
    domain = row["dataset"]
    results = {}
    for tag in ("H1", "H2"):
        pred = predictions[tag]
        f1 = evaluate_paired_binary(pred.candidate, pred.control, masks,
                                    domain=domain)
        results["X1" if tag == "H1" else "X2"] = float(pred.feature)
        results["Y1" if tag == "H1" else "Y2"] = float(f1.delta_f1)
    outcome = {
        "dataset": domain, "image_id": row["image_id"],
        "scene_group": row["scene_group"], "image_sha256": row["image_sha256"].lower(),
        "X1": results["X1"], "Y1": results["Y1"],
        "X2": results["X2"], "Y2": results["Y2"],
    }
    tmp = checkpoint.with_suffix(".json.part")
    with tmp.open("x", encoding="utf-8") as f:
        json.dump({"inputs": key, "outcome": outcome}, f, ensure_ascii=False, indent=2)
    os.replace(tmp, checkpoint)
    return outcome


def main() -> int:
    # No CLI flags to override authorization, sample/threshold or decoding.
    gate, approval, recipe, cohort = authorized(WORK)
    outcomes = WORK / "certified_outcomes.csv"
    provenance = WORK / "certified_outcomes_provenance.json"
    if outcomes.exists() or provenance.exists():
        raise RuntimeError("Signed output already exists; refuse overwrite")
    source_sha = digest(Path(__file__))
    names = multicue_gt_names(cohort)
    ground = materialize_gt_once(names, WORK, gate["frozen_input_sha256"]["cohort_sha256"])
    checkpoint_dir = WORK / "frozen_capture_checkpoints" / gate["freeze_commit"][:16]
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for n, row in enumerate(cohort, 1):
        if row["dataset"] == "BIPED":
            gt = [biped_gt(row)]
        else:
            gt = [ground[name] for name in names[row["image_id"]]]
        key = hashlib.sha256((row["dataset"] + ":" + row["image_id"]).encode()).hexdigest()[:24]
        output = checkpoint_one(row, recipe, source_sha, gt, checkpoint_dir / (key + ".json"))
        records.append(output)
        print("[FROZEN] {}/{} {} {} OK".format(
            n, len(cohort), row["dataset"], row["image_id"]), flush=True)
    from analyze_paper_a_confirmed import OUTCOME_COLUMNS, check_outcomes
    check_outcomes([{k: str(r[k]) for k in OUTCOME_COLUMNS} for r in records], cohort)
    pending = outcomes.with_suffix(".csv.part")
    with pending.open("x", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTCOME_COLUMNS)
        writer.writeheader()
        writer.writerows(records)
    os.replace(pending, outcomes)
    # This attestation INHERITS a previously independently signed executor
    # SHA and exact policy. There is no auto-approval or discovery-data fit.
    record = {
        "schema_version": 1, "outcomes_csv_sha256": digest(outcomes),
        "freeze_commit": gate["freeze_commit"],
        "protocol_frozen_before_first_GT_access": True,
        "no_parameter_tuning_or_threshold_fitting_on_confirmatory_GT": True,
        "paired_evaluator_contract_independently_certified": True,
        "complete_per_capture_output": True,
        "evaluator_source_sha256": source_sha,
        "reviewed_by": approval["reviewed_by"],
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "inherited_independent_review_from": str(WORK / "freeze_approval.json"),
        "gt_decoding_policy": BIN_POLICY,
    }
    tmp = provenance.with_suffix(".json.part")
    with tmp.open("x", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    os.replace(tmp, provenance)
    print(json.dumps({
        "status": "FROZEN_EVALUATION_COMPLETE_INDEPENDENT_NUMERICAL_REVIEW_PENDING",
        "n": len(records), "outcomes_csv": str(outcomes),
        "outcomes_sha256": digest(outcomes), "provenance": str(provenance),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
