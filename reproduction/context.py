"""Paths, artifact identity and safe result writing for community reproduction."""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
import os

ROOT = Path(__file__).resolve().parents[1]
CONFIRMATION = ROOT / "docs/paper_a_confirmation/successor_vsb100_20261117"
ARCHIVE = ROOT / "results/paper_a_evidence/stage24gl"

@dataclass(frozen=True)
class Context:
    work: Path
    uded: Path
    bsds_val: Path
    config_file: Path
    download: bool
    multicue_download_requested: bool
    allow_legacy: bool
    deep: bool

def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024*1024), b""):
            sha.update(chunk)
    return sha.hexdigest()

def save(path: Path, value) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+".tmp."+str(os.getpid()))
    try:
        with temp.open("x",encoding="utf-8") as fp:
            json.dump(value,fp,indent=2,ensure_ascii=False,allow_nan=False)
            fp.write("\n");fp.flush();os.fsync(fp.fileno())
        temp.replace(path)
    finally:
        temp.unlink(missing_ok=True)

def source_commit() -> str:
    import subprocess
    p=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True,check=False)
    return p.stdout.strip() if p.returncode==0 else "UNAVAILABLE"
