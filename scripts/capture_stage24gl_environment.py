#!/usr/bin/env python3
"""Freeze the ACTUAL Stage24G-L Python environment without guessing versions.

Creates: environment.lock.txt (exact installed name==version list) and
environment_manifest.json (Python, OS, git HEAD, direct dependencies, SHA256).
It does not modify the venv, globally install packages, or fabricate a lock.
On resume, changed package versions cause a hard failure unless a new --out is
chosen. No credentials, environment variables or private paths are recorded.
"""
from __future__ import annotations
import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "numpy", "scipy", "scikit-image", "matplotlib", "pandas", "Pillow",
    "requests", "tqdm", "opencv-python",
)


def canonical(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def environment_lock():
    found = {}
    for dist in metadata.distributions():
        name = (dist.metadata.get("Name") or "").strip()
        version = str(dist.version).strip()
        if name and version:
            key = canonical(name)
            if key in found and found[key][1] != version:
                raise RuntimeError("Conflicting installed package versions: " + key)
            found[key] = (name, version)
    missing = sorted(canonical(n) for n in REQUIRED if canonical(n) not in found)
    if missing:
        raise RuntimeError("Missing scientific dependencies: " + ", ".join(missing) +
                           ". Install requirements.txt in the project .venv first.")
    lock = "".join(f"{key}=={value[1]}\n" for key, value in sorted(found.items()))
    direct = {canonical(p): found[canonical(p)][1] for p in REQUIRED}
    return lock, direct


def git_head():
    proc = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"], cwd=ROOT, text=True,
        capture_output=True, check=False,
    )
    if proc.returncode:
        raise RuntimeError("Stage24G-L must run in an actual Git checkout: " +
                           proc.stderr.strip())
    return proc.stdout.strip()


def capture(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    # Refuse system Python even if the user forgot to activate the venv.
    if not (Path(sys.prefix) / "pyvenv.cfg").exists() and not (
        Path(sys.executable).resolve().is_relative_to((ROOT / ".venv").resolve())
    ):
        raise RuntimeError("Use the project .venv interpreter, not system Python")
    lock, direct = environment_lock()
    lock_path = out / "environment.lock.txt"
    if lock_path.exists() and lock_path.read_text(encoding="utf-8") != lock:
        raise RuntimeError("Dependencies changed since Stage24G-L started. "
                           "Keep existing checkpoints; restore their environment "
                           "or choose a NEW --out directory.")
    manifest_path = out / "environment_manifest.json"
    identity = {
        "schema_version": 1,
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "python_abi": getattr(sys, "abiflags", ""),
        "platform_system": platform.system(),
        "platform_release": platform.release(),
        "platform_machine": platform.machine(),
        "direct_versions": direct,
        "package_count": len(lock.splitlines()),
        "environment_lock_sha256": hashlib.sha256(lock.encode("utf-8")).hexdigest(),
    }
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        if any(old.get(k) != v for k, v in identity.items()):
            raise RuntimeError("Python/OS/dependency environment changed since the "
                               "first run. Restore it or use a NEW --out directory.")
        return identity
    # Capture an audited reference, not an assumption that frozen version
    # numbers are universally installable on all platforms.
    manifest = {
        **identity,
        "git_head_at_first_run": git_head(),
        "lock_kind": "actual_environment_inventory_no_hashes",
        "lock_is_not_cross_platform": True,
        "pip_install_recommendation": "Do not change environment mid-campaign; "
                                      "use an isolated Windows .venv",
        "scope": "scientific Python and runtime provenance; MATLAB separately "
                 "pinned by evaluation/bsds_official/config.json",
    }
    lock_path.write_text(lock, encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True),
                             encoding="utf-8")
    return identity


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default=str(
        ROOT / "results/local_dev/stage24_paper_a_recertification"))
    args = p.parse_args()
    identity = capture(args.out)
    print("STAGE24GL_ENVIRONMENT_FROZEN",
          identity["environment_lock_sha256"], identity["python_version"],
          identity["platform_system"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
