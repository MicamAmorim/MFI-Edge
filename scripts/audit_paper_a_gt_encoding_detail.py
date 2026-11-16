#!/usr/bin/env python3
"""GT encoding evidence ONLY from previously recorded out-of-cohort PNGs.
BIPED test (3), MultiCue excluded 4113 (12); no F1, freeze, or approval.
"""
from __future__ import annotations
import hashlib
import io
import json
import os
from pathlib import Path, PureWindowsPath
import re
import tarfile
from datetime import datetime, timezone

import numpy as np
from PIL import Image
from paper_a_nonconfirmatory_gt_format import (
    ARCHIVE_PROV, BIPED_GT, MAX_MASK_BYTES, OUT, SOURCE, TARGET)

RESULT = OUT.parent / "GT_PIXEL_ENCODING_DETAIL_PRE_FREEZE_v1.json"
NOTES = OUT.parent / "GT_PIXEL_ENCODING_REVIEW_REQUIRED.md"
SHA = re.compile(r"^[0-9a-f]{64}$")
BIPED_NAME = re.compile(r"^RGB_\d+\.png$")
ARCHIVE_HASH = "8e5fdb2ff7343e4a55f110e9ffe189b2c81689cd326324e34c6c73562191819e"


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def select_previous_samples(raw: bytes) -> tuple[list[dict], list[dict]]:
    report = json.loads(raw)
    if (report.get("schema_version") != 1 or
        report.get("status") != "GT_FORMAT_SAMPLE_OBSERVED_NOT_INDEPENDENTLY_CERTIFIED" or
        report.get("only_nonconfirmatory_GT_opened") is not True or
        report.get("protected_confirmatory_GT_opened") is not False or
        report.get("confirmation_F1_computed") is not False):
        raise ValueError("Unverified prior out-of-cohort evidence")
    biped, multi = report.get("BIPED_samples"), report.get("MultiCue_samples")
    if not isinstance(biped, list) or not isinstance(multi, list) or len(biped)!=3 or len(multi)!=12:
        raise ValueError("Previously verified sample list differs")
    seen = set()
    for record in biped:
        path = str(record.get("source_file", "")).replace("\\", "/")
        filename = PureWindowsPath(path).name
        if (not BIPED_NAME.fullmatch(filename) or
            "/edges/edge_maps/test/rgbr/" not in path.lower() or
            "/train/" in path.lower()):
            raise ValueError("BIPED sample outside approved test split")
        identity = ("BIPED", filename)
        if identity in seen:
            raise ValueError("Duplicate test GT")
        seen.add(identity)
    for record in multi:
        name = str(record.get("source_file", "")).removeprefix("./")
        if not TARGET.fullmatch(name) or ("MultiCue", name) in seen:
            raise ValueError("MultiCue sample not from excluded capture 4113")
        seen.add(("MultiCue", name))
    for record in biped + multi:
        if not SHA.fullmatch(str(record.get("file_sha256", ""))):
            raise ValueError("Missing source GT SHA-256")
    return biped, multi


def pixel_summary(raw: bytes, old: dict) -> dict:
    if not 20 <= len(raw) <= MAX_MASK_BYTES or digest(raw) != old["file_sha256"]:
        raise ValueError("PNG bytes differ from verified nonconfirmatory evidence")
    with Image.open(io.BytesIO(raw)) as im:
        if im.format != "PNG" or im.size[0]*im.size[1] > 6_000_000:
            raise ValueError("Unexpected PNG geometry/format")
        mode = im.mode
        arr = np.asarray(im)
    if (list(arr.shape) != old["shape"] or str(arr.dtype) != old["dtype"] or
        mode != old["pil_mode"] or arr.ndim != 2 or
        arr.dtype not in (np.uint8, np.uint16)):
        raise ValueError("Mask format changed or unsupported")
    values, counts = np.unique(arr, return_counts=True)
    pairs = sorted(zip(values.tolist(), counts.tolist()), key=lambda p:(-p[1], p[0]))
    count_map = dict(zip(values.tolist(), counts.tolist()))
    return {
        "source_file": old["source_file"], "sha256": old["file_sha256"],
        "dtype": str(arr.dtype), "mode": mode, "shape": list(arr.shape),
        "total_pixels": int(arr.size),
        "nonzero_pixels": int(np.count_nonzero(arr)),
        "distinct_values": len(values),
        "min_value": int(values[0]), "max_value": int(values[-1]),
        "all_values_if_at_most_32": [int(v) for v in values] if len(values)<=32 else None,
        "top_32_values": [{"value":int(v), "count":int(n)} for v,n in pairs[:32]],
        "selected_counts": {str(v):int(count_map.get(v,0))
                            for v in (0,1,254,255,256,65280,65535)},
        "scientific_decoding_approved": False,
    }


def collect(biped: list[dict], multi: list[dict],
            biped_dir: Path = BIPED_GT, tar_path: Path = SOURCE,
            provenance_path: Path = ARCHIVE_PROV) -> tuple[list[dict], list[dict]]:
    biped_result = []
    for item in biped:
        name = PureWindowsPath(item["source_file"]).name
        path = biped_dir / name
        if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_MASK_BYTES:
            raise FileNotFoundError("Recorded BIPED test mask missing: "+name)
        biped_result.append(pixel_summary(path.read_bytes(), item))

    if (not tar_path.is_file() or tar_path.is_symlink() or
        tar_path.stat().st_size != 3575680805 or
        not provenance_path.is_file() or provenance_path.is_symlink()):
        raise ValueError("Original MultiCue archive/provenance unavailable")
    prov = json.loads(provenance_path.read_text(encoding="utf-8"))
    if (prov.get("official_lfs_sha256_verified") is not True or
        prov.get("archive_sha256") != ARCHIVE_HASH):
        raise ValueError("Unverified MultiCue archive provenance")
    expected = {x["source_file"].removeprefix("./"): x for x in multi}
    found = {}
    with tarfile.open(tar_path, mode="r|bz2") as tar:
        for entry in tar:
            name = entry.name.removeprefix("./")
            if name not in expected:
                continue
            if (not TARGET.fullmatch(name) or not entry.isfile() or
                entry.size < 20 or entry.size > MAX_MASK_BYTES or name in found):
                raise ValueError("Unsafe or duplicate excluded sample")
            stream = tar.extractfile(entry)
            if stream is None:
                raise ValueError("GT member unavailable")
            raw = stream.read(MAX_MASK_BYTES+1)
            if len(raw) != entry.size:
                raise ValueError("GT member size mismatch")
            found[name] = pixel_summary(raw, expected[name])
            if len(found) == len(expected):
                break
    if set(found) != set(expected):
        raise ValueError("Not all recorded excluded 4113 samples found")
    return biped_result, [found[k] for k in expected]


def run() -> dict:
    if not OUT.is_file() or OUT.is_symlink():
        raise ValueError("Original nonconfirmatory report missing")
    source_raw = OUT.read_bytes()
    biped, multi = select_previous_samples(source_raw)
    if RESULT.exists():
        old = json.loads(RESULT.read_text(encoding="utf-8"))
        if (old.get("schema_version") != 1 or
            old.get("source_report_sha256") != digest(source_raw) or
            not NOTES.is_file()):
            raise RuntimeError("Existing detail does not match this source; manual review")
        return {"status":"REUSED_NONCONFIRMATORY_DETAIL_NOT_CERTIFIED",
                "report":str(RESULT), "review":str(NOTES),
                "sha256":digest(RESULT.read_bytes())}
    if NOTES.exists() or RESULT.with_suffix(".json.part").exists():
        raise RuntimeError("Unexpected existing review or interrupted report")
    biped_result, multi_result = collect(biped, multi)
    report = {
        "schema_version": 1,
        "status": "NONCONFIRMATORY_GT_PIXEL_ENCODING_DETAIL_NOT_CERTIFIED",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_report_sha256": digest(source_raw),
        "sample_counts": {"BIPED_test":len(biped_result), "MultiCue_excluded_4113":len(multi_result)},
        "BIPED_test":biped_result, "MultiCue_excluded_4113":multi_result,
        "excluded_capture_only":True, "confirmatory_GT_accessed":False,
        "F1_computed":False, "no_threshold_selected":True,
        "requires_independent_encoding_review":True,
        "archive_sha256_previously_verified":ARCHIVE_HASH,
    }
    RESULT.parent.mkdir(parents=True,exist_ok=True)
    stage=RESULT.with_suffix(".json.part")
    with stage.open("xb") as stream:
        stream.write((json.dumps(report,indent=2,ensure_ascii=False)+"\n").encode("utf-8"))
    os.replace(stage,RESULT)
    with NOTES.open("x",encoding="utf-8",newline="\n") as stream:
        stream.write(
            "# Paper A — diagnóstico de codificação GT não confirmatório\n\n"
            "**NÃO É APROVAÇÃO OU FREEZE.** Reinspecionados apenas 3 GTs BIPED test "
            "e 12 GTs do prefixo MultiCue 4113 (excluído), com SHA confrontado.\n\n"
            "## Para revisão científica independente\n\n"
            "1. Identificar a semântica de 254/255 (BIPED) e dos valores de 16 bits (MultiCue).\n"
            "2. Validar polaridade, níveis de confiança, canais e relação com documentação da fonte.\n"
            "3. Decidir uma única política prospectiva de decodificação e máscaras vazias.\n"
            "4. Testar o decoder proposto em material não confirmatório e revisar código + SHA.\n"
            "5. Congelar a decisão antes do primeiro acesso confirmatório.\n\n"
            "As frequências observadas não autorizam remapeamento automático nem "
            "certificam todas as máscaras da coorte 125+95.\n")
    return {"status":report["status"],"report":str(RESULT),
            "review":str(NOTES),"sha256":digest(RESULT.read_bytes())}


if __name__=="__main__":
    print(json.dumps(run(),indent=2,ensure_ascii=False))
