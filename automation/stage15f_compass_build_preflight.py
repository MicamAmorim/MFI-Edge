from __future__ import annotations

"""Dataset-free source/build preflight for the exact author Compass operator."""

from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import ssl
import subprocess
import tarfile
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage15f_compass_build_preflight"
AUTHOR_URL = "https://ai.stanford.edu/~ruzon/compass/ruzon.tar.gz"
ARCHIVE_SHA256 = "43e2ab843af620f5b6405843be0c5478b6953039c36b1e32b2a3ac725ddce7ea"
AUTHOR_VENDOR = (
    ROOT / "evaluation" / "bsds_official" / "vendor"
    / f"compass_author_{ARCHIVE_SHA256[:12]}"
)
MATLAB = Path(
    os.environ.get("MATLAB_EXE", r"C:\Program Files\MATLAB\R2023a\bin\matlab.exe")
)

SOURCE_HASHES = {
    "ruzon/DrawLine.m": "33ba308c6acf397eee661b2148b2584446e02cecaaacc902ff18eccae3cd6c97",
    "ruzon/Makefile": "b0872ee883e721235248df7fd6fc2d6d88701ed16091b2a502b6f302d53cc4f5",
    "ruzon/NMS.m": "590955fa1cac90aaa7d121a1e6115469f01d3ea857c809bdca5ee78c366c1a7e",
    "ruzon/PCorners.m": "722697f99e38a51feeeaa32b55511b2a384abacf64e9f03f7c0c87e8b4a31643",
    "ruzon/RGBLab.c": "48adfff7b1f1c2353f63dbcbd37652497169ddd65311c2090572c76c93c1024c",
    "ruzon/RuzonCompassPython.tar.gz": "3b88902f258558ec133f8e9192e5e5e732298db870097f444b87d7355da9283a",
    "ruzon/bs.c": "3c39f68e06df15a45191c2de1be5d67603bc6085b3d5d952d766b272f6c2892e",
    "ruzon/bs.h": "b09fed4f92d6f5d0af5b21aa6d335580871997974bb5a300dd3642651b8715d6",
    "ruzon/bsmex.c": "059540b1859e4223f3844ac8c27db7ba8ff6fbc4ddd905ff008108eecbb4485d",
    "ruzon/compass.c": "869369ff8f47ee06808c279069bd47fbd7bbe75f6205818df0495fbfad1700f1",
    "ruzon/compass.h": "b50c0bab3e51b7af5bf59810d5c1d686efa9e79f4609e43d550a0e69ab3b778d",
    "ruzon/compassmex.c": "b53502467cb223c215677cf41d89dacacfb479fd82673cf2878a73584bb94e8c",
    "ruzon/compassmex.m": "61d747fa0886b3280ee1979357acb56314761c0167552b796f33ead011aa1e08",
    "ruzon/emd.c": "992a3a017438cfe33a559d8b7a34dceb55a659bd78c56b2d8a2e82bc4b4820a0",
    "ruzon/emd.h": "38f5e689790d22ae02f544c5ed38d3253b81b0db4ed38a5b37737b051b04392d",
    "ruzon/gimage.m": "71155da186a5e766e1b8d5478c3995bdb0e63a240c987a11edd572d06b5c5b66",
    "ruzon/greycompass.c": "3c478f92ffa7b5066529b90bd89475c68b0dd0eeda48cdd31052e532b86db114",
    "ruzon/greycompass.h": "70a40f09d79ee50971a1a4f1db1935dd7ddd31290764bb2498f9de69f7d98f82",
    "ruzon/greycompassmex.c": "b1fbaa555af882a09b2be4162a6c38196c807a95549d0938e5d9d18ca23dd162",
    "ruzon/greycompassunix.c": "7f0d3f5a5dde2e472dc9abc72c5c547be7847a0bb4ff7bb80b96b9177cf5a166",
    "ruzon/i_file.c": "82d02c2257a1a3eede4fb6afff754003feb2aff5444d98d791cf878a60682406",
    "ruzon/i_main.c": "dd87ce170b5e880fe83f25ec35cc50dae589b29807e9c76082daaa313ca07df8",
    "ruzon/image.h": "f3ee33f07a5dc126f7446f5fc04a1df7fc4b0e75a3969b30c3b3694767d3be05",
    "ruzon/lib.h": "d10d8d0c2421b1145aae01b52d9df5d9ace3787c4cc063c59c10aa1c29168d56",
    "ruzon/maximize.m": "98ed15f72f850ba648961323bb3db85e1ea078eaff3a152206545fa8a7e75817",
    "ruzon/README": "2da1cd802a171004f76083cd1721fe6728b6a5cc16fd1f9c09c7e35e17e53048",
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _download() -> bytes:
    try:
        import certifi
        context = ssl.create_default_context(cafile=certifi.where())
    except ImportError:  # pragma: no cover - repository environment has certifi
        context = ssl.create_default_context()
    request = urllib.request.Request(AUTHOR_URL, headers={"User-Agent": "MFI-Edge/Stage15f"})
    with urllib.request.urlopen(request, context=context, timeout=90) as response:
        data = response.read()
    if _sha256(data) != ARCHIVE_SHA256:
        raise RuntimeError("downloaded Compass archive does not match registered SHA-256")
    return data


def _safe_extract(data: bytes) -> dict[str, str]:
    observed: dict[str, str] = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
        members = archive.getmembers()
        for member in members:
            parts = PurePosixPath(member.name).parts
            if member.name.startswith("/") or ".." in parts or member.issym() or member.islnk():
                raise RuntimeError(f"unsafe archive member: {member.name}")
            if member.isfile():
                payload = archive.extractfile(member).read()
                observed[member.name] = _sha256(payload)
        if observed != SOURCE_HASHES:
            raise RuntimeError("Compass archive member hashes do not match registration")
        AUTHOR_VENDOR.mkdir(parents=True, exist_ok=True)
        archive.extractall(AUTHOR_VENDOR, filter="data")
    return observed


def _matlab_quote(path: Path) -> str:
    return str(path.resolve()).replace("'", "''")


def _write_smoke_harness(source_dir: Path, build_dir: Path) -> Path:
    harness = OUT / "run_compass_smoke.m"
    src = _matlab_quote(source_dir)
    build = _matlab_quote(build_dir)
    harness.write_text(
        f"""try
build_dir = '{build}';
source_dir = '{src}';
if ~exist(build_dir, 'dir'), mkdir(build_dir); end
mex('-R2018a', '-outdir', build_dir, '-output', 'compassmex', ...
    fullfile(source_dir, 'compassmex.c'), fullfile(source_dir, 'compass.c'), ...
    fullfile(source_dir, 'bs.c'), fullfile(source_dir, 'RGBLab.c'), ...
    fullfile(source_dir, 'emd.c'));
addpath(build_dir);
I = zeros(64, 80, 3, 'uint8');
I(:, 41:end, 1) = 210; I(:, 41:end, 2) = 45; I(:, 41:end, 3) = 30;
I(:, 1:40, 1) = 25; I(:, 1:40, 2) = 95; I(:, 1:40, 3) = 190;
for r = 1:64
    for c = 1:80
        if mod(floor((r-1)/4) + floor((c-1)/4), 2) == 0
            I(r,c,:) = min(255, double(I(r,c,:)) + 25);
        end
    end
end
[S1,O1,A1,U1] = compassmex(I, 4, 1, 1, 180, 6, 10);
pause(0.05);
[S2,O2,A2,U2] = compassmex(I, 4, 1, 1, 180, 6, 10);
assert(isequal(size(S1), [41 57]));
assert(all(isfinite(S1(:))) && min(S1(:)) >= 0 && max(S1(:)) <= 1);
assert(all(isfinite(O1(:))) && all(isfinite(A1(:))) && all(isfinite(U1(:))));
fprintf('SMOKE_OK rows=%d cols=%d min=%.17g max=%.17g repeat_delta=%.17g orientation_repeat_delta=%.17g\\n', ...
    size(S1,1), size(S1,2), min(S1(:)), max(S1(:)), ...
    max(abs(S1(:)-S2(:))), max(abs(O1(:)-O2(:))));
catch ME
disp(getReport(ME, 'extended', 'hyperlinks', 'off'));
exit(1);
end
exit(0);
""",
        encoding="utf-8",
    )
    return harness


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    data = _download()
    observed = _safe_extract(data)
    source_dir = AUTHOR_VENDOR / "ruzon"
    build_dir = OUT / "matlab_build"
    harness = _write_smoke_harness(source_dir, build_dir)

    if not MATLAB.exists():
        completed = None
        output = f"MATLAB executable not found: {MATLAB}"
        returncode = None
    else:
        completed = subprocess.run(
            [str(MATLAB), "-batch", f"run('{_matlab_quote(harness)}')"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=1800,
            check=False,
        )
        output = completed.stdout or ""
        returncode = completed.returncode
    (OUT / "matlab_build_and_smoke.log").write_text(output, encoding="utf-8")
    passed = returncode == 0 and "SMOKE_OK" in output

    source_manifest = {
        "official_author_page": "https://ai.stanford.edu/~ruzon/compass/",
        "archive_url": AUTHOR_URL,
        "archive_sha256": ARCHIVE_SHA256,
        "archive_bytes": len(data),
        "archive_last_modified_documentary": "2004-12-02",
        "member_hashes": observed,
        "local_checkout": str(AUTHOR_VENDOR.relative_to(ROOT)).replace("\\", "/"),
        "license": "no explicit software license located in the archive or author page; ignored local dependency, not redistributed",
    }
    (OUT / "source_manifest.json").write_text(
        json.dumps(source_manifest, indent=2), encoding="utf-8"
    )
    summary = {
        "stage": "15f-compass-build-preflight",
        "role": "reproduction_dependency_preflight",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "detector_benchmark_executed": False,
        "dataset_read": False,
        "protected_split_used": False,
        "implementation_fidelity": "unmodified hash-verified author MATLAB/C MEX source with repository-local build/smoke harness",
        "source": source_manifest,
        "training_class": "strictly untrained",
        "registered_fixed_path": {
            "input": "native uint8 RGB; author conversion to CIE-Lab",
            "sigma": 4,
            "radius": 12,
            "spacing": 1,
            "angle_degrees": 180,
            "wedges_per_quarter": 6,
            "orientation_step_degrees": 15,
            "max_clusters": 10,
            "distance": "Earth Mover's Distance with the author's bounded CIE-Lab ground distance",
            "response": "maximum EMD strength S in [0,1]",
            "scale_rationale": "sigma=4 is the fixed full-image Compass setting reported for the CVPR 1999 Figure 7 comparison; selected before BSDS validation inspection",
            "future_serialization": "zero-pad the author-trimmed radius-12 border back to native size, then direct round(255*S) uint8 without per-image normalization",
        },
        "known_repeatability_risk": "compass.c calls srand(clock()) before randomized clustering; the smoke records, but does not suppress, fresh-call response deltas",
        "build": {
            "matlab": str(MATLAB),
            "returncode": returncode,
            "passed": passed,
            "smoke_line": next((line for line in output.splitlines() if "SMOKE_OK" in line), None),
            "log": str((OUT / "matlab_build_and_smoke.log").relative_to(ROOT)).replace("\\", "/"),
        },
        "decision_rule": (
            "If the unchanged source builds and emits finite bounded output, register one exact-response BSDS500-validation reproduction at the fixed published sigma-4 path. "
            "Record author RNG repeatability as provenance and do not fix its seed for dataset scoring. If only the external build harness fails, repair the harness without editing author bytes. If exact execution is infeasible, close Stage 15f fidelity-unresolved and advance to Stage 15g without a surrogate or parameter invention."
        ),
        "official_eval_manifest_omission": "Justified: dataset-free source/build preflight; no benchmark image or prediction map is generated.",
        "visual_preview_omission": "Justified: dataset-free synthetic smoke only; best_method_preview.png becomes mandatory for the later image reproduction.",
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("STAGE15F_COMPASS_BUILD_PREFLIGHT_COMPLETE")
    print(OUT / "summary.json")
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
