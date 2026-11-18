"""Pinned dataset acquisition where legally and technically available.

Dataset entries without approved archive URL+SHA are documented as manual.
Original scene/image hashes remain authoritative; never substitute samples.
"""
from pathlib import Path
import json
import shutil
import urllib.request

from .context import ROOT, Context, digest
from .execution import ReproductionError,command

def acquire(ctx: Context)->dict:
    spec=json.loads(ctx.config_file.read_text(encoding="utf-8"))
    found={}
    for name,entry in spec["datasets"].items():
        path=(ctx.work/"datasets"/entry["relative_path"]).resolve()
        if path.exists():
            if path.is_file() and entry.get("sha256") and digest(path)!=entry["sha256"]:
                raise ReproductionError(f"{name}: dataset hash differs; refusing replacement")
            found[name]={"status":"PRESENT", "path":str(path),"verified_sha":bool(entry.get("sha256") and path.is_file())}
            continue
        url,sha=entry.get("download_url"),entry.get("sha256")
        if ctx.download and url and sha:
            if not url.startswith("https://") or len(sha)!=64:
                raise ReproductionError(f"{name}: only pinned HTTPS archives with full SHA256")
            path.parent.mkdir(parents=True,exist_ok=True)
            temporary=path.with_suffix(path.suffix+".partial")
            try:
                req=urllib.request.Request(url,headers={"User-Agent":"MFI-Edge-PaperA-Reproduction/0.1"})
                with urllib.request.urlopen(req,timeout=60) as src,temporary.open("xb") as out:
                    shutil.copyfileobj(src,out)
                if digest(temporary)!=sha:
                    raise ReproductionError(f"{name}: downloaded SHA256 mismatch; refusing dataset")
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)
            found[name]={"status":"DOWNLOADED_SHA256_VERIFIED","path":str(path)}
        else:
            found[name]={"status":"NEEDS_PINNED_SOURCE_OR_MANUAL_DOWNLOAD",
                         "expected":str(path),"reference":entry.get("source_page",""),
                         "instruction":entry.get("instruction","")}
    return found

def acquire_multicue_official(ctx:Context)->dict:
    """Reuse existing project downloader; no invented mirrored dataset source."""
    folder=ctx.work/"datasets"/"MultiCue"
    archive=folder/"multicue-dataset.tar.bz2"
    if archive.is_file():
        return {"status":"ALREADY_PRESENT","path":str(archive)}
    if not ctx.download:
        return {"status":"MISSING","expected":str(archive)}
    # External package necessary; failure is reported, never bypassed.
    folder.mkdir(parents=True,exist_ok=True)
    command(ctx,"download_multicue",
            ["scripts/acquire_paper_a_multicue_archive.py",
             "--destination",str(folder),"--download"])
    if not archive.is_file():
        raise ReproductionError("MultiCue downloader returned without the pinned archive")
    return {"status":"DOWNLOADED_BY_ORIGINAL_VERIFIED_DOWNLOADER","path":str(archive)}
