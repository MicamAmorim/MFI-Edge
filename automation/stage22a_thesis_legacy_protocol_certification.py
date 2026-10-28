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


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    RUNTIME.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    hashes = []
    hash_ok = True
    for rec in manifest["files"]:
        p = VENDOR / rec["path"]
        actual = sha256(p) if p.exists() else None
        ok = actual == rec["sha256"]
        hashes.append({"path": rec["path"], "expected": rec["sha256"], "actual": actual, "ok": ok})
        hash_ok = hash_ok and ok

    src_matcher = VENDOR / "external" / "estradaJepsonMatching.bckp.m"
    runtime_matcher = RUNTIME / "estradaJepsonMatching.m"
    shutil.copyfile(src_matcher, runtime_matcher)

    matlab = find_matlab()
    matlab_result = None
    if matlab is not None:
        script = RUNTIME / "stage22a_microcases.m"
        script.write_text(r'''function stage22a_microcases(vendorDir,runtimeDir,outJson)
addpath(vendorDir);
addpath(fullfile(vendorDir,'external'));
addpath(runtimeDir);

sol = false(64,64); sol(32,10:54)=true;
candExact = sol;
candShift = false(64,64); candShift(33,10:54)=true;
gt = {struct('Boundaries',sol)};
r1 = ComparisonResiduals('ejBCM-F',candExact,gt,0.025);
r2 = ComparisonResiduals('ejBCM-F',candShift,gt,0.025);

[x,y] = meshgrid(1:64,1:64);
soft = exp(-((y-32).^2)/(2*2.0^2));
soft = soft .* (0.3 + 0.7*exp(-((x-32).^2)/(2*20^2)));
get_ok = true; get_err = ''; nonzero = 0;
try
    [~,b] = getBoundaries(soft,inf);
    nonzero = nnz(b);
catch ME
    get_ok = false;
    get_err = getReport(ME,'basic','hyperlinks','off');
end

S = struct();
S.exact = struct('precision',r1(1,1),'recall',r1(1,2),'F',r1(1,3));
S.shifted = struct('precision',r2(1,1),'recall',r2(1,2),'F',r2(1,3));
S.getBoundaries = struct('ok',get_ok,'nonzero',nonzero,'error',get_err);
S.ej_pass = abs(r1(1,1)-1)<1e-12 && abs(r1(1,2)-1)<1e-12 && abs(r1(1,3)-1)<1e-12 && r2(1,3)>0;
fid=fopen(outJson,'w'); fwrite(fid,jsonencode(S),'char'); fclose(fid);
end
''', encoding="utf-8")
        result_json = OUT / "matlab_microcases.json"
        expr = (
            f"addpath('{RUNTIME.as_posix()}');"
            f"stage22a_microcases('{VENDOR.as_posix()}','{RUNTIME.as_posix()}','{result_json.as_posix()}');"
        )
        matlab_result = run([str(matlab), "-batch", expr])
        if result_json.exists():
            matlab_result["metrics"] = json.loads(result_json.read_text(encoding="utf-8"))

    ej_pass = bool(matlab_result and matlab_result.get("returncode") == 0 and matlab_result.get("metrics", {}).get("ej_pass"))
    get_pass = bool(matlab_result and matlab_result.get("returncode") == 0 and matlab_result.get("metrics", {}).get("getBoundaries", {}).get("ok") and matlab_result.get("metrics", {}).get("getBoundaries", {}).get("nonzero", 0) > 0)

    summary = {
        "stage": "22A-thesis-legacy-protocol-certification",
        "scientific_experiment_index": "1/5",
        "reads_dataset": False,
        "scores_detector": False,
        "promotion_allowed": False,
        "source_hashes_ok": hash_ok,
        "matlab_found": str(matlab) if matlab else None,
        "ejBCM_microcases_pass": ej_pass,
        "getBoundaries_smoke_pass": get_pass,
        "hashes": hashes,
        "matlab": matlab_result,
        "legacy_contract": "continuous map -> exact getBoundaries(map,inf) -> binary map -> ComparisonResiduals('ejBCM-F',...,0.025) -> per-GT precision/recall/F0.5",
        "next_if_pass": "stage22b_thesis_legacy_retrospective_benchmark",
        "hard_budget": {"scientific_stages_max": 5, "final_stage": "22E", "no_sixth_experiment": True},
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE22A_THESIS_LEGACY_CERTIFICATION_COMPLETE")
    print(OUT / "summary.json")

    if not hash_ok or matlab is None or not ej_pass:
        return 1
    return 0 if get_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
