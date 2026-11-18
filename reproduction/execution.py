"""Auditable legacy command adapters, fail-closed rather than approximate science."""
import json
import os
from pathlib import Path
import subprocess
import sys

from .context import ROOT,Context,save

class ReproductionError(RuntimeError):
    pass

def require(path: Path, meaning: str) -> Path:
    if not path.exists():
        raise ReproductionError(f"{meaning} missing: {path}")
    return path

def command(ctx:Context,name:str,argv:list[str],python:bool=True)->dict:
    log=ctx.work/"logs"/(name+".log")
    log.parent.mkdir(parents=True,exist_ok=True)
    cmd=([sys.executable]+argv) if python else argv
    env=os.environ.copy()
    env.setdefault("MPLBACKEND","Agg")
    with log.open("w",encoding="utf-8") as fp:
        fp.write(json.dumps({"step":name,"command":cmd,"cwd":str(ROOT)})+"\n")
        fp.flush()
        try:
            result=subprocess.run(cmd,cwd=ROOT,env=env,stdout=fp,stderr=subprocess.STDOUT,check=False)
            code=result.returncode
        except OSError as exc:
            raise ReproductionError(f"{name}: cannot start: {exc}") from exc
    row={"step":name,"command":cmd,"exit_code":code,"log":str(log)}
    save(ctx.work/"checkpoints"/(name+".json"),row)
    if code!=0:
        raise ReproductionError(f"{name}: exited {code}; inspect {log}")
    return row
