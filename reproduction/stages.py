"""Readable scientific stages using original Stage23/Stage24 implementations.

No reimplementation or silent replacement of scientific algorithms.
"""
from pathlib import Path
from .context import ROOT,ARCHIVE,Context
from .execution import ReproductionError,command,require

def extract_evidence(ctx:Context):
    """Stage23C: 13 maps, original individual baselines and exact cache."""
    require(ctx.uded/"test_pair.lst","UDED test_pair.lst")
    return command(ctx,"stage23c_descriptors",
        ["run_stage23c_cached_uded_descriptor_baselines.py","--uded-root",str(ctx.uded)])

def characterize_complementarity(ctx:Context):
    """Stage23D: 78 pair relations, GT restricted to development."""
    return command(ctx,"stage23d_complementarity",
        ["run_stage23d_cached_complementarity_map.py","--uded-root",str(ctx.uded)])

def compare_aggregators(ctx:Context):
    """Stage23E: 15 evidence sets × 8 aggregation families."""
    return command(ctx,"stage23e_aggregators",
        ["run_stage23e_cached_descriptor_aggregator_landscape.py","--uded-root",str(ctx.uded)])

def check_transfer(ctx:Context):
    """Stage23F: only the original BSDS500 validation split, not its test split."""
    images=list(ctx.bsds_val.glob("*.jpg"))
    if len(images)!=100:
        raise ReproductionError(f"BSDS500 validation requires exactly 100 jpg files; got {len(images)} in {ctx.bsds_val}")
    return command(ctx,"stage23f_transfer",
        ["run_stage23f_literature_validation_frontier.py",
         "--uded-root",str(ctx.uded),"--image-dir",str(ctx.bsds_val)])

def verify_recertification_archive(ctx:Context):
    """Checks archived Stage24 numerical provenance, not pixel-level reproduction."""
    require(ARCHIVE/"reproducibility"/"reproduction_manifest.json","Stage24 archive manifest")
    return command(ctx,"stage24_archived_evidence",
        ["scripts/verify_stage24gl_repro.py","--check-git"])

def replay_stage24_original(ctx:Context):
    """Original runner has Windows paths and stages Git files after completion."""
    if not ctx.allow_legacy:
        raise ReproductionError("Stage24 full original runner has workstation/MATLAB/Git staging side effects. "
                                "Explicit --allow-legacy-stage24 required; see reproduction/README.md. "
                                "No fallback is scientifically equivalent.")
    return command(ctx,"stage24_original_unvalidated",
        ["run_stage24_paper_a_recertification.py","--phase","all"])

def evaluate_frozen_hypotheses(ctx:Context):
    """Historical H1/H2 evaluator is Windows-path/freeze specific.

    Do not rewrite its signed source or claim running it via a portable adapter.
    Numerical replay of published outcomes happens in verification module.
    """
    return {"status":"NOT_RERUN_FROM_RAW_IMAGES",
            "reason":"Original signed confirmation executor contains F: paths and source-hash freeze guard. "
                     "This portable adapter is not certified for byte-exact image-level rerun. "
                     "The original source is scripts/execute_paper_a_vsb100_successor.py."}
