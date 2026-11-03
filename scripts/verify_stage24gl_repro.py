#!/usr/bin/env python3
"""Independently verify published Stage24G-L ZIPs without local UDED/BSDS data.

Usage:
 python scripts/verify_stage24gl_repro.py --check-git
 python scripts/verify_stage24gl_repro.py --check-binary

Checks SHA256 of archives, CRC of every member, and SHA256 of uncompressed
file content against the source index. The Git package alone should be fully
verifiable by any reader, with no original datasets or local caches installed.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
GIT=ROOT/"results/paper_a_evidence/stage24gl/reproducibility"
BINARY=ROOT/"results/local_dev/stage24gl_binary_publication"


def digest_file(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def digest_member(z,member):
    h=hashlib.sha256()
    with z.open(member) as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def verify_shards(directory, expected, index):
    tested=set()
    for part in expected:
        path=directory/part["archive"]
        if not path.is_file():
            raise FileNotFoundError("Missing archive "+str(path))
        if path.stat().st_size!=int(part["bytes"]):
            raise RuntimeError("Archive size mismatch: "+str(path))
        if digest_file(path)!=part["sha256"]:
            raise RuntimeError("Archive SHA256 mismatch: "+str(path))
        with zipfile.ZipFile(path,"r") as z:
            if z.testzip() is not None:
                raise RuntimeError("Archive CRC failure: "+str(path))
            names=set(z.namelist())
            expected_members={r["member"] for r in index if r["archive"]==path.name}
            if names!=expected_members:
                raise RuntimeError("Archive member list mismatch: "+str(path))
            for row in index:
                if row["archive"]!=path.name:
                    continue
                info=z.getinfo(row["member"])
                if info.file_size!=int(row["bytes"]):
                    raise RuntimeError("Member size mismatch: "+row["member"])
                if digest_member(z,row["member"])!=row["sha256"]:
                    raise RuntimeError("Member SHA256 mismatch: "+row["member"])
                tested.add((row["archive"],row["member"]))
    if len(tested)!=len(index):
        raise RuntimeError("Not all source files are represented in ZIP manifest")
    return {"archives":len(expected),"verified_files":len(tested)}


def verify_git():
    manifest_path=GIT/"reproduction_manifest.json"
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    with (GIT/"source_to_archive.csv").open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=manifest["source_files"]:
        raise RuntimeError("Git archive file count mismatch")
    return verify_shards(GIT,manifest["parts"],rows)


def verify_binary():
    manifest=json.loads((BINARY/"binary_deposit_manifest.json").read_text(encoding="utf-8"))
    result=verify_shards(BINARY,manifest["assets"],manifest["files"])
    link=json.loads((GIT/"external_data_reference.json").read_text(encoding="utf-8"))
    if link["manifest_sha256"]!=digest_file(BINARY/"binary_deposit_manifest.json"):
        raise RuntimeError("Git-to-binary package manifest hash mismatch")
    if link["parts"]!=manifest["assets"]:
        raise RuntimeError("Git-to-binary part inventory mismatch")
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--check-git",action="store_true")
    group.add_argument("--check-binary",action="store_true")
    group.add_argument("--all",action="store_true")
    args=ap.parse_args()
    if args.check_git or args.all:
        print("STAGE24GL_GIT_REPRO_VERIFIED",verify_git())
    if args.check_binary or args.all:
        print("STAGE24GL_BINARY_REPRO_VERIFIED",verify_binary())


if __name__=="__main__":
    main()
