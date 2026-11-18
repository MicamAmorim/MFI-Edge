"""Paper A methodology at a glance: modular community reproduction.

WARNING: this new adapter has not undergone end-to-end scientific validation.
It keeps all original experiment implementations and frozen data untouched.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

from .context import ROOT,Context,source_commit
from .datasets import acquire,acquire_multicue_official
from .execution import ReproductionError
from .stages import (
    extract_evidence, characterize_complementarity, compare_aggregators,
    check_transfer, verify_recertification_archive, replay_stage24_original,
    evaluate_frozen_hypotheses,
)
from .verification import evaluate_confirmatory_evidence
from .reporting import publish

def reproduce_scientific_method(ctx:Context,results:dict) -> None:
    """Explicit Stage23C → D → E → F → Stage24 → confirmatory H1/H2."""
    results["dataset_inventory"]=acquire(ctx)
    # MultiCue is a special case with an existing author-provided verified downloader.
    if ctx.download:
        results["multicue_acquisition"]=acquire_multicue_official(ctx)

    results["descriptor_evidence"]=extract_evidence(ctx)
    results["complementarity"]=characterize_complementarity(ctx)
    results["aggregator_landscape"]=compare_aggregators(ctx)
    results["bsds_validation_transfer"]=check_transfer(ctx)

    if ctx.allow_legacy:
        results["stage24"]=replay_stage24_original(ctx)
    else:
        results["stage24"]=verify_recertification_archive(ctx)
        results["stage24"]["status"]="ARCHIVE_ONLY_NOT_REGENERATED"

    results["confirmation_image_level"]=evaluate_frozen_hypotheses(ctx)
    results["confirmatory_numeric"]=evaluate_confirmatory_evidence(ctx)

def verify_published_evidence(ctx:Context,results:dict)->None:
    """No downloads, no model fitting: independently recompute descriptive H1/H2."""
    results["stage24"]=verify_recertification_archive(ctx)
    results["stage24"]["status"]="ARCHIVE_INTEGRITY_CHECKED_NOT_REGENERATED"
    results["confirmatory_numeric"]=evaluate_confirmatory_evidence(ctx)

def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode",choices=("verify","full"),default="verify")
    p.add_argument("--workdir",type=Path,default=ROOT/"reproduction-work")
    p.add_argument("--uded-root",type=Path)
    p.add_argument("--bsds-val",type=Path)
    p.add_argument("--datasets-config",type=Path,default=ROOT/"reproduction/datasets.json")
    p.add_argument("--no-download",action="store_true")
    p.add_argument("--deep",action="store_true",
                   help="Rerun exact 100000 permutation and 2000 bootstrap inference per hypothesis")
    p.add_argument("--allow-legacy-stage24",action="store_true",
                   help="DANGER: explicitly run unported original Stage24 with Git-staging side effects")
    args=p.parse_args(argv)
    work=args.workdir.expanduser().resolve()
    if work==ROOT or ROOT.is_relative_to(work):
        p.error("Workdir cannot be the repository itself or its ancestor")
    ctx=Context(
        work=work,
        uded=(args.uded_root or work/"datasets/UDED").expanduser().resolve(),
        bsds_val=(args.bsds_val or work/"datasets/BSDS500/data/images/val").expanduser().resolve(),
        config_file=args.datasets_config.expanduser().resolve(),
        download=not args.no_download and args.mode=="full",
        allow_legacy=args.allow_legacy_stage24,deep=args.deep,
    )
    result={"mode":args.mode,"commit":source_commit(),"status":"STARTED","stages":{},"errors":[]}
    try:
        if args.mode=="verify":
            verify_published_evidence(ctx,result["stages"])
            result["status"]="NUMERIC_REPLAY_COMPLETE_NOT_FULL_REPRODUCTION"
        else:
            reproduce_scientific_method(ctx,result["stages"])
            result["status"]="PARTIAL_IMAGE_REPRODUCTION_CONFIRMATION_NOT_PORTED"
    except (ReproductionError,ValueError,KeyError,FileNotFoundError,ImportError) as exc:
        result["status"]="INCOMPLETE_STOPPED_SAFELY"
        result["errors"].append(f"{type(exc).__name__}: {exc}")
    json_path,md_path=publish(ctx,result)
    print("Report:",md_path)
    print("JSON:",json_path)
    print("Status:",result["status"])
    return 0 if result["status"]=="NUMERIC_REPLAY_COMPLETE_NOT_FULL_REPRODUCTION" else 2

if __name__=="__main__":
    raise SystemExit(main())
