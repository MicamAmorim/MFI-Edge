from __future__ import annotations

"""Dataset-free immutable-source/runtime preflight for exact Crisp Boundaries."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import traceback


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage23g2_pmi_exact_runtime_preflight"
AUTHOR_ROOT = ROOT / "external" / "crisp-boundaries"
AUTHOR_REPOSITORY = "https://github.com/phillipi/crisp-boundaries.git"
AUTHOR_COMMIT = "ee2d76e98340313a8f92e1b65064a9b4ea90ac77"
MATLAB = Path(
    os.environ.get("MATLAB_EXE", r"C:\Program Files\MATLAB\R2023a\bin\matlab.exe")
)
BUILD_CODE_ROOT = OUT / f"build_worktree_{AUTHOR_COMMIT[:12]}" / "Code"


def _run(
    args: list[str], *, cwd: Path | None = None, timeout: int | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd or ROOT),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def _git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    command = ["git"]
    if cwd is not None:
        command.extend(["-c", f"safe.directory={cwd.resolve()}"])
    command.extend(args)
    return _run(command, cwd=cwd)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _matlab_quote(path: Path) -> str:
    return str(path.resolve()).replace("'", "''")


def _prepare_author_checkout(log: list[str]) -> dict[str, object]:
    created = False
    if not AUTHOR_ROOT.exists():
        AUTHOR_ROOT.parent.mkdir(parents=True, exist_ok=True)
        clone = _git("clone", "--no-checkout", AUTHOR_REPOSITORY, str(AUTHOR_ROOT))
        log.extend(["CLONE", clone.stdout, clone.stderr])
        if clone.returncode != 0:
            raise RuntimeError(f"author clone failed with exit code {clone.returncode}")
        created = True
    if not (AUTHOR_ROOT / ".git").exists():
        raise RuntimeError("external/crisp-boundaries exists but is not a Git checkout")

    remote = _git("remote", "get-url", "origin", cwd=AUTHOR_ROOT)
    if remote.returncode != 0 or remote.stdout.strip() != AUTHOR_REPOSITORY:
        raise RuntimeError("existing author checkout does not have the registered origin")
    line_endings = _git("config", "core.autocrlf", "false", cwd=AUTHOR_ROOT)
    if line_endings.returncode != 0:
        raise RuntimeError("could not freeze author-checkout line-ending policy")
    has_commit = _git("cat-file", "-e", f"{AUTHOR_COMMIT}^{{commit}}", cwd=AUTHOR_ROOT)
    if has_commit.returncode != 0:
        fetch = _git("fetch", "--depth", "1", "origin", AUTHOR_COMMIT, cwd=AUTHOR_ROOT)
        log.extend(["FETCH", fetch.stdout, fetch.stderr])
        if fetch.returncode != 0:
            raise RuntimeError(f"author commit fetch failed with exit code {fetch.returncode}")
    if not created:
        status = _git("status", "--porcelain", cwd=AUTHOR_ROOT)
        if status.returncode != 0 or status.stdout.strip():
            raise RuntimeError("existing author checkout is dirty; refusing to overwrite it")

    checkout = _git("checkout", "--detach", AUTHOR_COMMIT, cwd=AUTHOR_ROOT)
    log.extend(["CHECKOUT", checkout.stdout, checkout.stderr])
    if checkout.returncode != 0:
        raise RuntimeError(f"author checkout failed with exit code {checkout.returncode}")
    head = _git("rev-parse", "HEAD", cwd=AUTHOR_ROOT)
    if head.returncode != 0 or head.stdout.strip() != AUTHOR_COMMIT:
        raise RuntimeError("author checkout did not resolve to the registered commit")

    tracked = _git("ls-files", "-z", cwd=AUTHOR_ROOT)
    if tracked.returncode != 0:
        raise RuntimeError("could not enumerate author-code files")
    rel_paths = sorted(item for item in tracked.stdout.split("\0") if item)
    aggregate = hashlib.sha256()
    files: list[dict[str, object]] = []
    for rel in rel_paths:
        path = AUTHOR_ROOT / rel
        file_hash = _sha256(path)
        normalized = rel.replace("\\", "/")
        files.append({"path": normalized, "sha256": file_hash, "bytes": path.stat().st_size})
        aggregate.update(normalized.encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(file_hash.encode("ascii"))
        aggregate.update(b"\n")

    license_path = AUTHOR_ROOT / "License.txt"
    license_text = license_path.read_text(encoding="utf-8", errors="replace")
    license_checks = {
        "copyright_phillip_isola": "Copyright (c) Phillip Isola" in license_text,
        "three_redistribution_conditions": all(f"{index}." in license_text for index in (1, 2, 3)),
        "as_is_disclaimer": "THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS''" in license_text,
    }
    return {
        "repository": AUTHOR_REPOSITORY,
        "commit": AUTHOR_COMMIT,
        "tracked_file_count": len(files),
        "tracked_manifest_sha256": aggregate.hexdigest(),
        "license_path": "License.txt",
        "license_sha256": _sha256(license_path),
        "license_class": "BSD-3-Clause-style author license",
        "license_checks": license_checks,
        "all_license_checks_passed": all(license_checks.values()),
        "files": files,
    }


def _source_contract() -> dict[str, object]:
    environment = (AUTHOR_ROOT / "Code" / "setEnvironment.m").read_text(
        encoding="utf-8", errors="replace"
    )
    entry = (AUTHOR_ROOT / "Code" / "findBoundaries.m").read_text(
        encoding="utf-8", errors="replace"
    )
    evaluation = (AUTHOR_ROOT / "Code" / "eval" / "evaluation_script.m").read_text(
        encoding="utf-8", errors="replace"
    )
    checks = {
        "entry_is_find_boundaries": "function [E,E_oriented,Ws] = findBoundaries(I,type)" in entry,
        "color_and_variance_features": "{'color','var'}" in environment,
        "three_image_scales": "opts.num_scales = 3;" in environment,
        "pmi_rho_1p25": "opts.joint_exponent = 1.25;" in environment,
        "kde_model": "opts.model_type = 'kde';" in environment,
        "spectral_globalization": "opts.globalization_method = 'spectral_clustering';" in environment,
        "one_hundred_eigenvectors": "opts.spectral_clustering.nvec = 100;" in environment,
        "paper_path_disables_pmi_approximation": bool(
            re.search(
                r"case\s+'MS_algorithm_from_paper'.*?opts\.approximate_PMI\s*=\s*false;",
                environment,
                flags=re.DOTALL,
            )
        ),
        "author_evaluation_lists_paper_path": "MS_algorithm_from_paper" in evaluation,
    }
    return {
        "checks": checks,
        "all_expected_source_checks_passed": all(checks.values()),
        "registered_path": "MS_algorithm_from_paper",
        "training_class": "unsupervised-data-estimated; fixed author parameters tuned on BSDS500 train",
        "stage18j_distinction": (
            "The full author path estimates color/variance KDE affinities and performs multiscale "
            "spectral globalization. Stage 18j used only a bounded discrete grayscale PMI-deficit map."
        ),
    }


def _prepare_build_surface(source_manifest: dict[str, object]) -> dict[str, object]:
    if not BUILD_CODE_ROOT.exists():
        BUILD_CODE_ROOT.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(AUTHOR_ROOT / "Code", BUILD_CODE_ROOT)

    verified = 0
    for item in source_manifest["files"]:
        rel = str(item["path"])
        if not rel.startswith("Code/"):
            continue
        build_path = BUILD_CODE_ROOT / rel.removeprefix("Code/")
        if not build_path.is_file() or _sha256(build_path) != item["sha256"]:
            raise RuntimeError(f"build-surface source mismatch: {rel}")
        verified += 1
    return {
        "path": str(BUILD_CODE_ROOT.relative_to(ROOT)).replace("\\", "/"),
        "verified_author_source_files": verified,
        "policy": "persistent result-local copy; author checkout remains byte-clean; compiled outputs are reusable",
    }


def _write_matlab_harness() -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    harness = OUT / "run_pmi_exact_smoke.m"
    code = _matlab_quote(BUILD_CODE_ROOT)
    out = _matlab_quote(OUT)
    harness.write_text(
        f"""try
code_root = '{code}';
out_root = '{out}';
cd(code_root);
addpath(genpath(code_root));
[xx, yy] = meshgrid(linspace(0, 1, 36), linspace(0, 1, 36));
I = zeros(36, 36, 3, 'uint8');
I(:,:,1) = uint8(255 * (0.15 + 0.70 * (xx >= 0.5)));
I(:,:,2) = uint8(255 * (0.10 + 0.75 * (yy >= 0.55)));
I(:,:,3) = uint8(255 * min(1, 0.15 + 0.45 * xx + 0.35 * yy));
build_attempted = false;
try
    [Ec, Eoc] = findBoundaries(I, 'compile_test');
catch
    build_attempted = true;
    previous = pwd;
    cleanup = onCleanup(@() cd(previous));
    cd(fullfile(code_root, 'toolboxes', '@kde', 'mex'));
    makemex_kde;
    cd(previous);
    [Ec, Eoc] = findBoundaries(I, 'compile_test');
end
assert(isequal(size(Ec), [36 36]));
assert(size(Eoc,1) == 36 && size(Eoc,2) == 36);
assert(all(isfinite(Ec(:))) && all(isfinite(Eoc(:))));
tic;
[Ep, Eop] = findBoundaries(I, 'MS_algorithm_from_paper');
paper_runtime = toc;
assert(isequal(size(Ep), [36 36]));
assert(size(Eop,1) == 36 && size(Eop,2) == 36);
assert(all(isfinite(Ep(:))) && all(isfinite(Eop(:))));
assert(nnz(Ep) > 0 && nnz(Eop) > 0);
fid = fopen(fullfile(out_root, 'compile_test_output.bin'), 'wb');
assert(fid >= 0); fwrite(fid, Ec, 'double'); fwrite(fid, Eoc, 'double'); fclose(fid);
fid = fopen(fullfile(out_root, 'paper_path_output.bin'), 'wb');
assert(fid >= 0); fwrite(fid, Ep, 'double'); fwrite(fid, Eop, 'double'); fclose(fid);
fprintf(['PMI_SMOKE_OK build_attempted=%d compile_min=%.17g compile_max=%.17g ' ...
    'paper_min=%.17g paper_max=%.17g paper_nonzero=%d oriented_nonzero=%d ' ...
    'paper_runtime_seconds=%.17g orientations=%d\\n'], ...
    build_attempted, min(Ec(:)), max(Ec(:)), min(Ep(:)), max(Ep(:)), ...
    nnz(Ep), nnz(Eop), paper_runtime, size(Eop,3));
catch ME
disp(getReport(ME, 'extended', 'hyperlinks', 'off'));
exit(1);
end
exit(0);
""",
        encoding="utf-8",
    )
    return harness


def _run_matlab_smoke(log: list[str]) -> dict[str, object]:
    harness = _write_matlab_harness()
    if not MATLAB.exists():
        return {
            "attempted": False,
            "passed": False,
            "reason": f"MATLAB executable not found: {MATLAB}",
            "harness": str(harness.relative_to(ROOT)).replace("\\", "/"),
        }
    started = time.perf_counter()
    completed = _run(
        [str(MATLAB), "-batch", f"run('{_matlab_quote(harness)}')"],
        cwd=ROOT,
        timeout=5400,
    )
    elapsed = time.perf_counter() - started
    output = (completed.stdout or "") + (completed.stderr or "")
    log.extend(["MATLAB", output])
    smoke_line = next((line for line in output.splitlines() if "PMI_SMOKE_OK" in line), None)
    compile_output = OUT / "compile_test_output.bin"
    paper_output = OUT / "paper_path_output.bin"
    outputs_exist = compile_output.is_file() and paper_output.is_file()
    return {
        "attempted": True,
        "passed": completed.returncode == 0 and smoke_line is not None and outputs_exist,
        "matlab": str(MATLAB),
        "returncode": completed.returncode,
        "wall_seconds": elapsed,
        "smoke_line": smoke_line,
        "harness": str(harness.relative_to(ROOT)).replace("\\", "/"),
        "compile_output_sha256": _sha256(compile_output) if compile_output.is_file() else None,
        "paper_output_sha256": _sha256(paper_output) if paper_output.is_file() else None,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    log: list[str] = []
    errors: list[str] = []
    try:
        source_manifest = _prepare_author_checkout(log)
        source_contract = _source_contract()
        build_surface = _prepare_build_surface(source_manifest)
    except Exception as exc:
        errors.append(f"source_preflight: {exc!r}")
        log.append(traceback.format_exc())
        source_manifest = {}
        source_contract = {}
        build_surface = {}

    if errors:
        smoke = {"attempted": False, "passed": False, "reason": "source preflight failed"}
    else:
        try:
            smoke = _run_matlab_smoke(log)
        except Exception as exc:
            errors.append(f"matlab_smoke: {exc!r}")
            log.append(traceback.format_exc())
            smoke = {"attempted": True, "passed": False, "reason": repr(exc)}

    preflight_passed = bool(
        source_manifest
        and source_manifest.get("all_license_checks_passed")
        and source_contract.get("all_expected_source_checks_passed")
        and smoke.get("passed")
    )
    source_path = OUT / "source_manifest.json"
    source_path.write_text(
        json.dumps(source_manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log_path = OUT / "runtime_preflight.log"
    log_path.write_text("\n".join(log), encoding="utf-8")
    summary = {
        "status": "completed" if preflight_passed else "failed",
        "experiment_id": "stage23g2_pmi_exact_runtime_preflight",
        "role": "reproduction_dependency_preflight",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset_access": "none",
        "detector_benchmark_executed": False,
        "protected_split_used": False,
        "architecture_changed": False,
        "target": "Isola et al. Crisp Boundary Detection using PMI",
        "implementation_fidelity": "exact pinned author code under an external synthetic/runtime harness",
        "paper": {
            "citation": "Isola, Zoran, Krishnan and Adelson (ECCV 2014)",
            "doi": "10.1007/978-3-319-10578-9_52",
            "project_page": "https://web.mit.edu/phillipi/crisp_boundaries/",
            "reported_role": "BSDS500 test headline is documentary and separate from future development reproduction",
        },
        "author_code": source_manifest,
        "source_contract": source_contract,
        "build_surface": build_surface,
        "synthetic_smoke": smoke,
        "preflight_passed": preflight_passed,
        "errors": errors,
        "decision_rule": (
            "Only a complete provenance/build/exact-paper-path synthetic pass may register one "
            "development reproduction on overlap-clean UDED selection and BSDS500 validation. "
            "A harness/dependency failure permits only an identical repair retry."
        ),
        "recommended_next_action": (
            "register_exact_pmi_development_reproduction"
            if preflight_passed
            else "repair_runtime_harness_or_close_target_if_author_source_change_is_required"
        ),
        "official_eval_manifest_omission": "Dataset-free source/build/synthetic smoke only; no benchmark map exists.",
        "visual_preview_omission": "Dataset-free synthetic smoke only; a fixed preview is mandatory for any later dataset run.",
        "artifacts": [
            str(source_path.relative_to(ROOT)).replace("\\", "/"),
            str(log_path.relative_to(ROOT)).replace("\\", "/"),
            str((OUT / "run_pmi_exact_smoke.m").relative_to(ROOT)).replace("\\", "/"),
        ],
    }
    summary_path = OUT / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("STAGE23G2_PMI_EXACT_RUNTIME_PREFLIGHT_COMPLETE")
    print(summary_path)
    print(f"preflight_passed={preflight_passed}")
    return 0 if preflight_passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
