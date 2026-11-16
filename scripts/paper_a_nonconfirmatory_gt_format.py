#!/usr/bin/env python3
"""One-time nonconfirmatory GT format audit; never open protected cohort GT.

BIPED: author-designated *test* masks only (not Paper A BIPED train).
MultiCue: the previously excluded 4113 capture prefix ONLY (not 95 candidate
capture prefixes). This is a format/semantics preflight, NOT approval of actual
confirmatory GT, not F1 and not a replacement for independent review.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import re
import tarfile
from datetime import datetime,timezone

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
DATA=Path(r"F:\MFI-Edge-Data\MultiCue")
OUT=DATA/"paper_a_completion"/"scientific_signoff"/"NONCONFIRMATORY_GT_ENCODING_EVIDENCE.json"
SOURCE=DATA/"multicue-dataset.tar.bz2"
ARCHIVE_PROV=DATA/"archive_provenance.json"
BIPED_GT=ROOT/"datasets/BIPEDv2/edges/edge_maps/test/rgbr"
TARGET=re.compile(r"^multicue/ground-truth/images/edges/4113_left_\d+\.\d+\.png$")
BIPED_LIMIT=3
MULTICUE_LIMIT=12
MAX_MASK_BYTES=20_000_000


def digest(p:Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()


def inspect_png(raw:bytes, name:str) ->dict:
    if len(raw)>MAX_MASK_BYTES or len(raw)<20:
        raise ValueError("Unexpected GT size: "+name)
    with Image.open(io.BytesIO(raw)) as im:
        if im.format!="PNG":
            raise ValueError("GT is not lossless PNG: "+name)
        arr=np.asarray(im)
        im_mode=im.mode
        dims=[int(x) for x in arr.shape]
    if arr.dtype!=np.uint8:
        summary={"unique_values":None,"all_channels_equal":False,"alpha_opaque":False}
    elif arr.ndim==2:
        summary={"unique_values":[int(x) for x in np.unique(arr)[:32]],
                 "all_channels_equal":True,"alpha_opaque":True}
    elif arr.ndim==3 and arr.shape[-1] in (3,4):
        summary={"unique_values":[int(x) for x in np.unique(arr[...,:3])[:32]],
                 "all_channels_equal":bool(np.array_equal(arr[...,0],arr[...,1])
                                           and np.array_equal(arr[...,1],arr[...,2])),
                 "alpha_opaque":bool(arr.shape[-1]==3 or np.all(arr[...,3]==255))}
    else:
        summary={"unique_values":None,"all_channels_equal":False,"alpha_opaque":False}
    vals=summary["unique_values"]
    strict=(arr.dtype==np.uint8 and (arr.ndim==2 or
            (arr.ndim==3 and arr.shape[-1] in (3,4) and
             summary["all_channels_equal"] and summary["alpha_opaque"]))
            and vals is not None and
            (set(vals)=={0,1} or set(vals)=={0,255}))
    return {"source_file":name,"file_sha256":hashlib.sha256(raw).hexdigest(),
            "bytes":len(raw),"pil_mode":im_mode,"shape":dims,
            "dtype":str(arr.dtype),"values_first_32":vals,
            "all_channels_equal":summary["all_channels_equal"],
            "alpha_opaque":summary["alpha_opaque"],
            "strict_decoder_sample_compatible":bool(strict)}


def inspect_files(root:Path,limit:int) ->list[dict]:
    files=sorted(p for p in root.glob("*.png") if p.is_file() and not p.is_symlink())
    return [inspect_png(p.read_bytes(),str(p)) for p in files[:limit]]


def inspect_multicue() -> tuple[list[dict],dict]:
    # Historical provenance metadata only; the expensive TAR is streamed once
    # with an exact excluded-prefix allowlist and no traversal/extraction.
    if not ARCHIVE_PROV.is_file() or not SOURCE.is_file():
        return [],{"status":"EXCLUDED_SAMPLE_SOURCE_MISSING"}
    prior=json.loads(ARCHIVE_PROV.read_text(encoding="utf-8"))
    if prior.get("official_lfs_sha256_verified") is not True:
        return [],{"status":"ARCHIVE_PREVIOUS_HASH_VERIFICATION_MISSING"}
    source_sha=prior.get("archive_sha256")
    if not isinstance(source_sha,str) or len(source_sha)!=64:
        return [],{"status":"ARCHIVE_PROVENANCE_INCOMPLETE"}
    if SOURCE.stat().st_size!=3575680805:
        return [],{"status":"ARCHIVE_EXPECTED_SIZE_MISMATCH"}
    found=[]
    with tarfile.open(SOURCE,mode="r|bz2") as archive:
        for member in archive:
            name=member.name.removeprefix("./")
            if not TARGET.fullmatch(name):
                continue
            if not member.isfile() or member.size>MAX_MASK_BYTES:
                raise ValueError("Invalid excluded GT archive member")
            if len(found)>=MULTICUE_LIMIT:
                break
            stream=archive.extractfile(member)
            if stream is None:
                raise ValueError("Excluded GT member unavailable")
            raw=stream.read(MAX_MASK_BYTES+1)
            if len(raw)!=member.size:
                raise ValueError("Incomplete excluded GT sample")
            found.append(inspect_png(raw,name))
    return found,{"status":"EXCLUDED_GROUP_ONLY_SAMPLED","archive_sha256_historically_verified":source_sha,
                  "not_rehashed_entire_3_5GB_archive_this_run":True}


def run() -> dict:
    OUT.parent.mkdir(parents=True,exist_ok=True)
    if OUT.exists():
        existing=json.loads(OUT.read_text(encoding="utf-8"))
        if existing.get("schema_version")==1 and existing.get(
                "only_nonconfirmatory_GT_opened") is True:
            print("[REUSE] nonconfirmatory GT format report")
            return {"status":"REUSED_FORMAT_EVIDENCE_NOT_SCIENTIFIC_CERTIFICATION",
                    "path":str(OUT),"sha256":digest(OUT)}
        raise ValueError("Existing GT format report unexpected; never overwrite")
    # BIPED train GT directory is deliberately never referenced in this script.
    biped=inspect_files(BIPED_GT,BIPED_LIMIT)
    multicue,provenance=inspect_multicue()
    report={
        "schema_version":1,
        "status":"GT_FORMAT_SAMPLE_OBSERVED_NOT_INDEPENDENTLY_CERTIFIED",
        "created_utc":datetime.now(timezone.utc).isoformat(),
        "only_nonconfirmatory_GT_opened":True,
        "BIPED_split":"test (not used in Paper A N125 BIPED train cohort)",
        "MultiCue_capture_prefix":"4113 excluded from Paper A confirmation",
        "BIPED_samples":biped,
        "MultiCue_samples":multicue,
        "MultiCue_archive_provenance":provenance,
        "sample_counts":{"BIPED":len(biped),"MultiCue":len(multicue)},
        "all_sampled_masks_pass_proposed_strict_decoder":bool(biped and multicue and
            all(x["strict_decoder_sample_compatible"] for x in biped+multicue)),
        "protected_confirmatory_GT_opened":False,
        "confirmation_F1_computed":False,
        "scientific_GT_semantics_approval":False,
        "requires_independent_validation":"Samples do not establish encoding across all 220 frozen originals."
    }
    OUT.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    return {"status":report["status"],"path":str(OUT),"sha256":digest(OUT),
            "sample_counts":report["sample_counts"],
            "strict_decoder_samples_pass":report["all_sampled_masks_pass_proposed_strict_decoder"]}


if __name__=="__main__":
    print(json.dumps(run(),indent=2,ensure_ascii=False))
