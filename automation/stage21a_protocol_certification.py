from __future__ import annotations

"""Stage 21A protocol certification and implementation audit.

This is infrastructure work.  It scores no detector and reads no BSDS split.
It audits the pinned Berkeley path, verifies that the 2.5% sensitivity config
differs only in maxDist, and executes fixed synthetic Estrada-Jepson cases
through a hash-pinned public KITT implementation surface.
"""

from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage21a_protocol_certification"
OFFICIAL = ROOT / "evaluation" / "bsds_official"
MATLAB_DIR = OFFICIAL / "matlab"
KITT_DIR = OFFICIAL / "vendor" / "KITT"
KITT_URL = "https://github.com/giaracvi/KITT.git"
KITT_COMMIT = "d70bb66ef9ab6f5cea8ead528fe5ac15ac096baf"
EXPECTED_KITT_HASHES = {
    "estradaJepsonMatching.m": "b04f5770b2cfcfdc5e9b0cbb6d3ab4486c85bc145bdeef8067052bed3be6b96b",
    "estradaJepsonMatching.bckp.m": "409008932d70f31d60c8c83111cb32a09bddd7cc4e6dcae7cf101a3bc162b506",
    "oneToManyEJBC.m": "1e659122417c7984d144b6a110bdbb8ea629b08c875dccedd1267b237eecffbb",
    "ejmBasedBinaryImageCM.m": "5b1c621b81cd5af0780b0a5c4978696b3abb14841f6f9ae0365c2f0dc39aa677",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(cmd: list[str], *, timeout: int = 600, cwd: Path = ROOT) -> subprocess.CompletedProcess:
    result = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed ({result.returncode}): {cmd!r}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


def _git(*args: str, timeout: int = 600) -> subprocess.CompletedProcess:
    return _run(
        ["git", "-c", f"safe.directory={KITT_DIR.resolve()}", "-C", str(KITT_DIR), *args],
        timeout=timeout,
    )


def _ensure_kitt() -> dict:
    if not (KITT_DIR / ".git").exists():
        KITT_DIR.parent.mkdir(parents=True, exist_ok=True)
        _run(["git", "clone", "--no-checkout", KITT_URL, str(KITT_DIR)])
    else:
        dirty = _git("status", "--porcelain").stdout.strip()
        if dirty:
            raise RuntimeError(
                "ignored KITT checkout has local changes; refusing to overwrite them"
            )
    _git("fetch", "--depth", "1", "origin", KITT_COMMIT)
    _git("checkout", "--detach", KITT_COMMIT)
    head = _git("rev-parse", "HEAD").stdout.strip()
    if head != KITT_COMMIT:
        raise RuntimeError(f"KITT commit mismatch: {head}")

    boundary = KITT_DIR / "boundaryImageComparison"
    hashes = {name: _sha256(boundary / name) for name in EXPECTED_KITT_HASHES}
    if hashes != EXPECTED_KITT_HASHES:
        raise RuntimeError(f"KITT source hash mismatch: {hashes}")
    return {"repository": KITT_URL, "commit": head, "sha256": hashes}


def _matlab_executable(config: dict) -> Path:
    candidates = []
    if os.environ.get("MATLAB_EXE"):
        candidates.append(Path(os.environ["MATLAB_EXE"]))
    candidates.append(Path(str(config["matlab_executable"])))
    found = shutil.which("matlab") or shutil.which("matlab.exe")
    if found:
        candidates.append(Path(found))
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError("MATLAB executable not found")


def _matlab_quote(value: Path) -> str:
    return str(value.resolve()).replace("\\", "/").replace("'", "''")


def _audit_berkeley_sources(config: dict) -> dict:
    bsds = OFFICIAL / "vendor" / "BSDS500"
    edges = OFFICIAL / "vendor" / "pdollar_edges"
    bsds_head = _run(["git", "-C", str(bsds), "rev-parse", "HEAD"]).stdout.strip()
    edges_head = _run(["git", "-C", str(edges), "rev-parse", "HEAD"]).stdout.strip()
    if bsds_head != config["sources"]["bsds500"]["commit"]:
        raise RuntimeError("BSDS500 source commit mismatch")
    if edges_head != config["sources"]["pdollar_edges"]["commit"]:
        raise RuntimeError("pdollar source commit mismatch")

    benchmark = bsds / "bench" / "benchmarks"
    eval_file = benchmark / "evaluation_bdry_image.m"
    collect_file = benchmark / "collect_eval_bdry.m"
    correspond_source = bsds / "bench" / "source" / "correspondPixels.cc"
    random_source = bsds / "bench" / "source" / "Random.cc"
    kofn_source = bsds / "bench" / "source" / "kofn.cc"
    texts = {
        "evaluation": eval_file.read_text(encoding="utf-8", errors="replace"),
        "collection": collect_file.read_text(encoding="utf-8", errors="replace"),
        "correspond": correspond_source.read_text(encoding="utf-8", errors="replace"),
        "random": random_source.read_text(encoding="utf-8", errors="replace"),
        "kofn": kofn_source.read_text(encoding="utf-8", errors="replace"),
    }
    contracts = {
        "default_nthresh_99": "if nargin<4, nthresh = 99; end" in texts["evaluation"],
        "default_maxdist_0p0075": "if nargin<5, maxDist = 0.0075; end" in texts["evaluation"],
        "default_thinpb_true": "if nargin<6, thinpb = 1; end" in texts["evaluation"],
        "all_annotations_iterated": "for i = 1:numel(groundTruth)" in texts["evaluation"],
        "machine_match_union": "accP = accP | match1" in texts["evaluation"],
        "recall_counts_accumulated": "cntR(t) = cntR(t) + sum(match2(:)>0)" in texts["evaluation"],
        "threshold_counts_aggregated": "cntR_total = cntR_total + cntR" in texts["collection"],
        "maxdist_scaled_by_diagonal": "maxDist*idiag" in texts["correspond"],
        "clock_seed_request_present": "reseed (0);" in texts["random"],
        "random_k_of_n_sampling_present": "random" in texts["kofn"].lower(),
    }
    if not all(contracts.values()):
        raise RuntimeError(f"Berkeley source contract failed: {contracts}")
    return {
        "bsds500_commit": bsds_head,
        "pdollar_edges_commit": edges_head,
        "source_hashes_sha256": {
            "evaluation_bdry_image.m": _sha256(eval_file),
            "collect_eval_bdry.m": _sha256(collect_file),
            "correspondPixels.cc": _sha256(correspond_source),
            "Random.cc": _sha256(random_source),
            "kofn.cc": _sha256(kofn_source),
        },
        "contracts": contracts,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    standard_config_path = OFFICIAL / "config.json"
    sensitivity_config_path = OFFICIAL / "config_berkeley_0p025.json"
    standard_config = _load(standard_config_path)
    sensitivity_config = _load(sensitivity_config_path)

    changed_keys = sorted(
        key
        for key in set(standard_config) | set(sensitivity_config)
        if standard_config.get(key) != sensitivity_config.get(key)
    )
    sensitivity_ok = changed_keys == ["max_dist"] and sensitivity_config["max_dist"] == 0.025
    if not sensitivity_ok:
        raise RuntimeError(
            "Berkeley sensitivity config must differ from standard only in max_dist"
        )

    berkeley_audit = _audit_berkeley_sources(standard_config)
    stage15_protocol = _load(ROOT / "results" / "local_dev" / "stage15a_protocol_audit" / "summary.json")
    stage15_seed = _load(ROOT / "results" / "automation" / "stage15a_seed_determinism_diagnostic" / "summary.json")
    if stage15_protocol["reference_reproduction"]["passed"]:
        raise RuntimeError("Stage-15 provenance unexpectedly says the fixture passed")
    if not all(row["fixed_seed_repeat_max_abs_delta"] == 0 for row in stage15_seed["aggregate_tables"]):
        raise RuntimeError("Stage-15 fixed-seed causal diagnostic provenance changed")

    kitt = _ensure_kitt()
    boundary = KITT_DIR / "boundaryImageComparison"
    current_text = (boundary / "estradaJepsonMatching.m").read_text(
        encoding="utf-8", errors="replace"
    )
    public_head_defect = {
        "calls_isConnected": "isConnected(" in current_text,
        "defines_isConnected": "functionresult=isConnected" in current_text.replace(" ", ""),
    }
    if not public_head_defect["calls_isConnected"] or public_head_defect["defines_isConnected"]:
        raise RuntimeError("KITT public-head implementation audit no longer matches preregistration")

    runtime_dir = OUT / "kitt_runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        boundary / "estradaJepsonMatching.bckp.m",
        runtime_dir / "estradaJepsonMatching.m",
    )
    runtime_hash = _sha256(runtime_dir / "estradaJepsonMatching.m")
    if runtime_hash != EXPECTED_KITT_HASHES["estradaJepsonMatching.bckp.m"]:
        raise RuntimeError("runtime KITT matcher differs from shipped v1.00 backup")

    microcase_path = OUT / "estrada_jepson_microcases.json"
    matlab = _matlab_executable(standard_config)
    expression = (
        f"addpath('{_matlab_quote(MATLAB_DIR)}');"
        "stage21a_estrada_jepson_microcases("
        f"'{_matlab_quote(runtime_dir)}',"
        f"'{_matlab_quote(boundary)}',"
        f"'{_matlab_quote(microcase_path)}');"
    )
    matlab_run = _run([str(matlab), "-batch", expression], timeout=900)
    microcases = _load(microcase_path)
    if not microcases.get("all_passed", False):
        raise RuntimeError(f"Estrada-Jepson micro-case contract failed: {microcases}")

    certification = {
        "stage": "21a-protocol-certification",
        "role": "infrastructure_methodological_certification",
        "architecture_changed": False,
        "detector_scored": False,
        "bsds_split_read": False,
        "protected_split_used": False,
        "berkeley_standard": {
            "protocol": {
                "nthresh": 99,
                "max_dist": 0.0075,
                "thinpb": True,
                "all_human_annotations": True,
                "one_to_one_correspondence": True,
            },
            "source_audit": berkeley_audit,
            "reference_reproduction_verified": False,
            "reference_fixture": stage15_protocol["reference_reproduction"],
            "causal_diagnostic": {
                "fixed_seed": stage15_seed["fixed_seed"],
                "tables": stage15_seed["aggregate_tables"],
            },
            "exact_blocker": (
                "The pinned official matcher requests a clock seed and consumes "
                "random k-of-n samples. Its shipped fixture does not record RNG "
                "state. The unmodified Windows path therefore misses the registered "
                "1e-4 fixture bound and is not repeatable; a fixed-seed diagnostic "
                "is repeatable but does not reproduce the shipped tables and is "
                "forbidden for dataset scoring. Platform migration cannot recover "
                "the unrecorded reference RNG state."
            ),
        },
        "berkeley_maxdist_0p025_sensitivity": {
            "implemented": True,
            "config": str(sensitivity_config_path.relative_to(ROOT)).replace("\\", "/"),
            "parameter_only_changed_keys": changed_keys,
            "max_dist": sensitivity_config["max_dist"],
            "reference_reproduction_verified": False,
            "promotion_eligible": False,
        },
        "estrada_jepson_0p025": {
            "literature_definition": (
                "Directional proximity matching with no-intervening-contour and "
                "same-side constraints; precision and recall are computed by "
                "opposite directional matches. Target fuzzy literature uses all "
                "human annotations, 0.025 image-diagonal tolerance, union machine "
                "matches for precision, accumulated annotation recall, and F0.5."
            ),
            "kitt": kitt,
            "public_head_v1p01_defect": public_head_defect,
            "executed_surface": (
                "byte-identical KITT-shipped v1.00 backup matcher renamed only "
                "for MATLAB filename compatibility, with pinned oneToManyEJBC"
            ),
            "runtime_matcher_sha256": runtime_hash,
            "microcases": str(microcase_path.relative_to(ROOT)).replace("\\", "/"),
            "microcases_passed": True,
            "fidelity": (
                "best public KITT fidelity, not claimed exact to an unpublished "
                "target-paper private copy; Stage-21B rows must retain this caveat"
            ),
            "promotion_eligible": False,
        },
        "stage21a_stop_rule_satisfied": True,
        "stage21b_authorized_next": True,
        "official_eval_manifest_omission": (
            "Justified: Stage 21A is an evaluator/source audit with synthetic "
            "micro-cases; it generates no detector map and reads no BSDS split."
        ),
        "matlab": {
            "executable": str(matlab),
            "stdout_tail": "\n".join(matlab_run.stdout.splitlines()[-20:]),
        },
    }
    _save(OUT / "protocol_certification.json", certification)
    summary = {
        "stage": "stage21a_protocol_certification",
        "status": "completed",
        "stage21a_stop_rule_satisfied": True,
        "berkeley_reference_status": "reference_unverified_exact_rng_provenance_blocker",
        "berkeley_0p025_status": "implemented_parameter_only_variant",
        "estrada_jepson_0p025_status": "microcase_verified_best_public_kitt_fidelity",
        "architecture_changed": False,
        "detector_scored": False,
        "protected_split_used": False,
        "next_registered_stage": "stage21b_three_protocol_retrospective_benchmark",
        "details": "protocol_certification.json",
    }
    _save(OUT / "summary.json", summary)
    print("STAGE21A_PROTOCOL_CERTIFICATION_OK", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
