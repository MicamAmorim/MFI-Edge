#!/usr/bin/env python3
"""Make a local, GT-FREE 220-original contact atlas for independent scene review.

Reads ONLY the exact 220 source RGB originals named in the pending review CSV.
Validates source SHA256 before showing thumbnails. No GT, TAR, H5, F1, maps,
train/calibration, outcomes, scoring, decisions or scientific signoff.
Does not create/update reviewer decision CSV. Never publishes images to Git.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
from pathlib import Path
import re
import zipfile

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(r"F:\MFI-Edge-Data\MultiCue")
WORK = DATA / "paper_a_completion"
SHEET = WORK / "scientific_signoff/REVIEW_220_IMAGES_PENDING.csv"
BIPED = ROOT / "datasets/BIPEDv2/edges/imgs/train/rgbr/real"
MULTICUE = DATA / "source_frames_only"
FINAL = WORK / "scientific_signoff/ATLAS_220_ORIGINAIS_SEM_GT"
ZIP = WORK / "PaperA_ATLAS_220_ORIGINAIS_SEM_GT.zip"
SAFE = re.compile(r"^[A-Za-z0-9_-]{2,80}$")
HEX = re.compile(r"^[a-f0-9]{64}$")
IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".bmp"}
MAX_ORIGINAL_BYTES = 40_000_000
EXPECTED_COLS = (
    "dataset", "image_id", "relative_path", "image_sha256",
    "independence_review", "prior_exposure_review", "scene_group", "notes",
    "reviewer_independence_decision", "reviewer_prior_exposure_decision",
    "evidence_for_both_decisions", "reviewer_name", "reviewed_utc",
    "historical_attention",
)


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_rows(sheet: Path) -> list[dict]:
    if not sheet.is_file() or sheet.is_symlink() or sheet.stat().st_size > 2_000_000:
        raise ValueError("Invalid pending scene review metadata")
    with sheet.open(newline="", encoding="utf-8-sig") as inp:
        reader = csv.DictReader(inp)
        if tuple(reader.fieldnames or ()) != EXPECTED_COLS:
            raise ValueError("Review CSV schema drift")
        rows = list(reader)
    if len(rows) != 220:
        raise ValueError("Expected exactly 220 proposed captures")
    seen=set();groups=set();counts={"BIPED":0,"MultiCue":0}
    for r in rows:
        ds,iid,sha,group = [r[k] for k in ("dataset","image_id","image_sha256","scene_group")]
        if (ds not in counts or not SAFE.fullmatch(iid) or
            not SAFE.fullmatch(group) or not HEX.fullmatch(sha) or
            r["independence_review"]!="pending" or
            r["prior_exposure_review"]!="pending"):
            raise ValueError("Unexpected provisional scene identity or approval")
        if (ds,iid) in seen or (ds,group) in groups:
            raise ValueError("Duplicate scene/group")
        seen.add((ds,iid));groups.add((ds,group))
        counts[ds]+=1
    if counts != {"BIPED":125,"MultiCue":95}:
        raise ValueError("Wrong proposal domain mix")
    return rows


def safe_source(row: dict, biped: Path = BIPED,
                multicue: Path = MULTICUE) -> Path:
    base=biped if row["dataset"]=="BIPED" else multicue if row["dataset"]=="MultiCue" else None
    if base is None:
        raise ValueError("Unknown domain")
    rel=row["relative_path"]
    # The proposal's source_frames_only and BIPED image roots contain
    # exactly these basename files: never accept directories or traversal.
    if (not isinstance(rel,str) or not re.fullmatch(r"[A-Za-z0-9_-]+\.(?:jpg|jpeg|png|bmp)",rel,re.I)):
        raise ValueError("Review original path must be a basename")
    if Path(rel).stem != row["image_id"]:
        raise ValueError("Source basename and reviewed ID disagree")
    source=base / rel
    if not source.is_file() or source.is_symlink() or not source.resolve().is_relative_to(base.resolve()):
        raise ValueError("Review original missing/unsafe: "+str(source))
    if not 0 < source.stat().st_size <= MAX_ORIGINAL_BYTES:
        raise ValueError("Original image outside file-size bound")
    return source


def gallery_html(data: list[dict]) -> str:
    entries=[]
    for i,r in enumerate(data):
        flag="attention" if any(x in r["historical_attention"]
            for x in ("DUPLICATE_PAIR","REPEATED_PREFIX")) else ""
        item=(
            f'<figure class="{flag}"><img loading="lazy" '
            f'src="{html.escape(r["thumbnail"],quote=True)}" '
            f'alt="Original {html.escape(r["image_id"],quote=True)}">'
            f'<figcaption><b>{html.escape(r["dataset"])} · '
            f'{html.escape(r["image_id"])}</b><br>'
            f'Cenário: {html.escape(r["scene_group"])}<br>'
            f'<small>SHA original: {html.escape(r["original_sha256"][:16])}…</small><br>'
            f'<small>{html.escape(r["historical_attention"])}</small></figcaption></figure>'
        )
        entries.append(item)
    header='''<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<title>Paper A - Atlas de originais SEM GT - REVISAO PENDENTE</title>
<style>body{font:14px system-ui,sans-serif;margin:22px;background:#111822;color:#e8edf4}
h1{font-size:23px}.warning{background:#29313b;border:1px solid #8d9095;
padding:12px;border-radius:8px;max-width:1100px;line-height:1.6}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:14px}
figure{margin:0;padding:8px;background:#202a35;border:1px solid #344354;
border-radius:8px}figure.attention{border:2px solid #f0a34c}
img{width:100%;aspect-ratio:16/9;object-fit:contain;background:#05090f}
figcaption{margin:9px 4px;line-height:1.6;overflow-wrap:anywhere}
small{color:#c5cdd9}</style>
<h1>Paper A — Atlas visual de 220 originais SEM GT</h1>
<p class="warning"><strong>APENAS PARA REVISÃO INDEPENDENTE.</strong>
Nenhuma imagem foi marcada como PASS. Miniaturas de originais, sem ground truth,
sem mapas, sem F1 e sem resultados. Validar independência de cenas, exposições
históricas e relatórios de sequência; registrar decisão individual na planilha
REVIEW_220_IMAGES_PENDING.csv. Contorno âmbar indica atenção prioritária
documentada (não reprovação automática).</p><div class="grid">
'''
    return header+"\n".join(entries)+"</div></html>\n"


def build(*, sheet: Path = SHEET, biped: Path = BIPED,
          multicue: Path = MULTICUE, final: Path = FINAL,
          archive: Path = ZIP) -> dict:
    raw_sheet=sheet.read_bytes()
    rows=read_rows(sheet)
    expected_hash=sha_bytes(raw_sheet)
    manifest_file=final/"MANIFEST.json"
    if final.exists():
        if not manifest_file.is_file():
            raise RuntimeError("Existing atlas without manifest; inspect manually")
        meta=json.loads(manifest_file.read_text(encoding="utf-8"))
        if (meta.get("schema")!="paper_a_gt_free_original_atlas_v1"
            or meta.get("source_review_sheet_sha256")!=expected_hash
            or len(meta.get("images",[]))!=220):
            raise RuntimeError("Atlas from another review snapshot; refuse overwrite")
        for record in meta["images"]:
            p=final/record["thumbnail"]
            if not p.is_file() or p.is_symlink() or sha_bytes(p.read_bytes())!=record["thumbnail_sha256"]:
                raise RuntimeError("Existing atlas thumbnail altered: "+str(p))
    else:
        temp=final.with_name(final.name+"_IN_PROGRESS")
        if temp.exists():
            raise RuntimeError("Incomplete atlas exists; manual reconciliation required")
        (temp/"thumbnails").mkdir(parents=True, exist_ok=False)
        images=[]
        for row in rows:
            source=safe_source(row,biped,multicue)
            raw=source.read_bytes()
            if sha_bytes(raw)!=row["image_sha256"]:
                raise ValueError("Original image SHA mismatch: "+row["image_id"])
            with Image.open(source) as im:
                if im.format not in ("PNG","JPEG","BMP") or im.width*im.height>30_000_000:
                    raise ValueError("Unexpected original image decoder or dimensions")
                rgb=ImageOps.exif_transpose(im).convert("RGB")
                rgb.thumbnail((800,450),Image.Resampling.LANCZOS)
                filename=hashlib.sha256(
                    (row["dataset"]+":"+row["image_id"]).encode()).hexdigest()[:20]+".jpg"
                dest=temp/"thumbnails"/filename
                rgb.save(dest,format="JPEG",quality=78,optimize=True,exif=b"")
            images.append({
                "dataset":row["dataset"],"image_id":row["image_id"],
                "scene_group":row["scene_group"],"original_sha256":row["image_sha256"],
                "historical_attention":row["historical_attention"],
                "thumbnail":"thumbnails/"+filename,
                "thumbnail_sha256":sha_bytes(dest.read_bytes()),
                "human_independent_review_complete":False,
            })
        report={
            "schema":"paper_a_gt_free_original_atlas_v1",
            "source_review_sheet_sha256":expected_hash,
            "images":images,
            "gt_h5_f1_descriptor_maps_opened":False,
            "no_auto_scene_approval":True,
        }
        (temp/"MANIFEST.json").write_text(
            json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        (temp/"index.html").write_text(gallery_html(images),encoding="utf-8")
        temp.rename(final)
        meta=report
    if archive.exists():
        raise RuntimeError("Existing atlas ZIP not overwritten; inspect before retry")
    # Separate original-image atlas from the mandatory METADATA-ONLY freeze ZIP.
    with zipfile.ZipFile(archive,"x",compression=zipfile.ZIP_STORED) as z:
        for rel in ("MANIFEST.json","index.html"):
            z.write(final/rel,rel)
        for record in meta["images"]:
            z.write(final/record["thumbnail"],record["thumbnail"])
    return {
        "status":"ORIGINAL_IMAGE_ATLAS_READY_HUMAN_REVIEW_REQUIRED",
        "images":220,"folder":str(final),"atlas_zip":str(archive),
        "atlas_sha256":sha_bytes(archive.read_bytes()),
        "signed_or_frozen":False,"GT_opened":False,
    }


if __name__=="__main__":
    print(json.dumps(build(),ensure_ascii=False,indent=2))
