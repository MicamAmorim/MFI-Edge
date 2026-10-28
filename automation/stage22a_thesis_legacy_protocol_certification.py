from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "evaluation" / "legacy_thesis"
OUT = ROOT / "results" / "automation" / "stage22a_thesis_legacy_protocol_certification"
RUNTIME = OUT / "matlab_runtime"
MANIFEST = VENDOR / "SOURCE_MANIFEST.json"
STAGE21A_RUNTIME = ROOT / "results" / "automation" / "stage21a_protocol_certification" / "kitt_runtime"


def normalized_text_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    raw = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(raw).hexdigest()


def run(cmd: list[str], timeout: int = 900) -> dict:
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    return {"returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}


def find_matlab() -> Path | None:
    env = os.environ.get("MATLAB_EXE")
    candidates = [
        Path(env) if env else None,
        Path(r"C:\Program Files\MATLAB\R2023a\bin\matlab.exe"),
        Path(r"C:\Program Files\MATLAB\R2024a\bin\matlab.exe"),
        Path(r"C:\Program Files\MATLAB\R2024b\bin\matlab.exe"),
        Path(r"C:\Program Files\MATLAB\R2025a\bin\matlab.exe"),
    ]
    for p in candidates:
        if p and p.exists():
            return p
    which = shutil.which("matlab")
    return Path(which) if which else None


def resolve_matcher() -> Path | None:
    local = VENDOR / "external" / "estradaJepsonMatching.bckp.m"
    if local.exists():
        return local
    certified = STAGE21A_RUNTIME / "estradaJepsonMatching.m"
    if certified.exists():
        return certified
    return None


def missing_getboundaries_helpers(manifest: dict) -> list[str]:
    ext = VENDOR / "external"
    return [name for name in manifest["runtime_dependencies"]["getBoundaries_helpers"] if not (ext / name).exists()]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    hashes = []
    hash_ok = True
    for rec in manifest["core_files"]:
        p = VENDOR / rec["path"]
        actual = normalized_text_sha256(p)
        expected = rec["normalized_lf_sha256"]
        ok = actual == expected
        hashes.append({
            "path": rec["path"],
            "drive_sha256_provenance": rec["drive_sha256"],
            "expected_normalized_lf_sha256": expected,
            "actual_normalized_lf_sha256": actual,
            "ok": ok,
        })
        hash_ok = hash_ok and ok

    matcher = resolve_matcher()
    runtime_matcher = RUNTIME / "estradaJepsonMatching.m"
    if matcher is not None:
        shutil.copyfile(matcher, runtime_matcher)

    missing_helpers = missing_getboundaries_helpers(manifest)
    matlab = find_matlab()
    matlab_result = None

    if matlab is not None and matcher is not None:
        script = RUNTIME / "stage22a_microcases.m"
        script.write_text(r'''function stage22a_microcases(vendorDir,runtimeDir,outJson,runGetBoundaries)
addpath(vendorDir);
addpath(fullfile(vendorDir,'external'));
addpath(runtimeDir);

sol = false(64,64); sol(32,10:54)=true;
candExact = sol;
candShift = false(64,64); candShift(33,10:54)=true;
gt = {struct('Boundaries',sol)};
r1 = ComparisonResiduals('ejBCM-F',candExact,gt,0.025);
r2 = ComparisonResiduals('ejBCM-F',candShift,gt,0.025);

get_ok = false; get_err = 'helper sources not materialized'; nonzero = 0;
if runGetBoundaries
    [x,y] = meshgrid(1:64,1:64);
    soft = exp(-((y-32).^2)/(2*2.0^2));
    soft = soft .* (0.3 + 0.7*exp(-((x-32).^2)/(2*20^2)));
    try
        [~,b] = getBoundaries(soft,inf);
        nonzero = nnz(b);
        get_ok = nonzero > 0;
        get_err = '';
    catch ME
        get_err = getReport(ME,'basic','hyperlinks','off');
    end
end

S = struct();
S.exact = struct('precision',r1(1,1),'recall',r1(1,2),'F',r1(1,3));
S.shifted = struct('precision',r2(1,1),'recall',r2(1,2),'F',r2(1,3));
S.getBoundaries = struct('attempted',logical(runGetBoundaries),'ok',get_ok,'nonzero',nonzero,'error',get_err);
S.ej_pass = abs(r1(1,1)-1)<1e-12 && abs(r1(1,2)-1)<1e-12 && abs(r1(1,3)-1)<1e-12 && r2(1,3)>0;
fid=fopen(outJson,'w'); fwrite(fid,jsonencode(S),'char'); fclose(fid);
end
''', encoding="utf-8")
        result_json = OUT / "matlab_microcases.json"
        run_get = "true" if not missing_helpers else "false"
        expr = (
            f"addpath('{RUNTIME.as_posix()}');"
            f"stage22a_microcases('{VENDOR.as_posix()}','{RUNTIME.as_posix()}','{result_json.as_posix()}',{run_get});"
        )
        matlab_result = run([str(matlab), "-batch", expr])
        if result_json.exists():
            matlab_result["metrics"] = json.loads(result_json.read_text(encoding="utf-8"))

    ej_pass = bool(matlab_result and matlab_result.get("returncode") == 0 and matlab_result.get("metrics", {}).get("ej_pass"))
    get_pass = bool(matlab_result and matlab_result.get("returncode") == 0 and matlab_result.get("metrics", {}).get("getBoundaries", {}).get("ok"))

    summary = {
        "stage": "22A-thesis-legacy-protocol-certification",
        "scientific_experiment_index": "1/5",
        "reads_dataset": False,
        "scores_detector": False,
        "promotion_allowed": False,
        "source_hashes_ok": hash_ok,
        "matlab_found": str(matlab) if matlab else None,
        "matcher_source": str(matcher) if matcher else None,
        "missing_getBoundaries_helpers": missing_helpers,
        "ejBCM_microcases_pass": ej_pass,
        "getBoundaries_smoke_pass": get_pass,
        "hashes": hashes,
        "matlab": matlab_result,
        "legacy_contract": "continuous map -> thesis getBoundaries(map,inf) -> binary map -> ComparisonResiduals('ejBCM-F',...,0.025) -> per-human-GT precision/recall/F; thesis best-match summary keeps the largest F per image",
        "next_if_fully_certified": "stage22b_thesis_legacy_retrospective_benchmark",
        "harness_retry_if_helpers_missing": "materialize the historically sourced helper files named in SOURCE_MANIFEST.json without reading/scoring any dataset, rerun Stage 22A only, and do not consume another scientific-stage slot",
        "hard_budget": {"scientific_stages_max": 5, "final_stage": "22E", "no_sixth_experiment": True},
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE22A_THESIS_LEGACY_CERTIFICATION_COMPLETE")
    print(OUT / "summary.json")

    if not hash_ok or matlab is None or matcher is None or not ej_pass:
        return 1
    if missing_helpers or not get_pass:
        # Harness/source-materialization condition only. No dataset has been read.
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
