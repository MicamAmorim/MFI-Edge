#!/usr/bin/env python3
"""Local-only Paper A overnight runner. Never opens confirmatory GT or F1."""
from __future__ import annotations
import argparse
import ctypes
from datetime import datetime, timezone
import json
import os
import stat
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "experiment/paper-a-conditional-confirmation"
DATA = Path(r"F:\MFI-Edge-Data\MultiCue")
LOGS = DATA / "paper_a_overnight_codex"
AUDIT = DATA / "paper_a_prefreeze_combined_audit"
POLICY = ROOT / "docs/paper_a_confirmation/OVERNIGHT_CODEX_POLICY.md"
STATUS_MD = ROOT / "docs/paper_a_confirmation/NIGHTLY_PROGRESS.md"
ALLOWED_CODEX = frozenset({
    "docs/paper_a_confirmation/PAPER_A_MANUSCRIPT_DRAFT.md",
    "scripts/run_paper_a_prefreeze_one_shot.py",
    "tests/test_paper_a_prefreeze_one_shot.py",
    "scripts/audit_paper_a_uded14_cache_sidecars_P0_3.py",
    "tests/test_paper_a_uded14_cache_sidecars_P0_3.py",
    "scripts/package_paper_a_repro.py",
})
ALLOWED_COMMIT = ALLOWED_CODEX | {
    "docs/paper_a_confirmation/NIGHTLY_PROGRESS.md",
}

# Existing untracked scientific results are preserved and not staged.
BASELINE_UNTRACKED = None


def run(args, *, stdin=None, timeout=120, git_env=False):
    env = dict(os.environ)
    if git_env:
        env["GIT_TERMINAL_PROMPT"] = "0"
    proc = subprocess.run(args, cwd=ROOT, input=stdin, capture_output=True,
                          timeout=timeout, env=env, check=False)
    return proc.returncode, proc.stdout.decode("utf-8", "replace"), proc.stderr.decode("utf-8", "replace")


def git(*args, timeout=120):
    return run(["git", *args], git_env=True, timeout=timeout)


def git_head():
    rc, out, err = git("rev-parse", "HEAD")
    if rc:
        raise RuntimeError(err)
    return out.strip()


def git_status_entries():
    """Return NUL-safe status entries with untracked directories expanded."""
    p = subprocess.run(
        ["git", "status", "--porcelain", "-z", "--untracked-files=all"],
        cwd=ROOT, capture_output=True, timeout=90, check=False)
    if p.returncode:
        raise RuntimeError("git status unavailable")
    entries = []
    for item in p.stdout.split(b"\x00"):
        if not item:
            continue
        flag = item[:2].decode("ascii", "replace")
        if "R" in flag or "C" in flag:
            raise RuntimeError("Git renames/copies require manual review")
        entries.append((flag, os.fsdecode(item[3:]).replace("\\", "/")))
    return entries


def _fingerprint_untracked(path):
    """lstat only: no original scientific evidence content is read."""
    info = (ROOT / path).lstat()
    if not (stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode)):
        raise RuntimeError("Untracked path is not a regular file or symlink: " + path)
    return info.st_size, info.st_mtime_ns, info.st_mode


def capture_preexisting_untracked():
    """Allow existing untracked files only; tracked edits still fail closed."""
    global BASELINE_UNTRACKED
    entries = git_status_entries()
    dirty = [path for flag, path in entries if flag != "??"]
    if dirty:
        raise RuntimeError("Tracked/index edits require human review: " + repr(dirty[:12]))
    baseline = {
        path: _fingerprint_untracked(path)
        for flag, path in entries if flag == "??"
    }
    if len(baseline) != sum(flag == "??" for flag, _ in entries):
        raise RuntimeError("Duplicate untracked filenames")
    BASELINE_UNTRACKED = baseline
    print("[GIT] Preserving", len(baseline),
          "existing untracked files, without staging or deleting them.",
          flush=True)
    return baseline


def filter_status_changes(entries, baseline, fingerprint):
    """Ignore baseline untracked only when unchanged; protect all other paths."""
    current = {path for flag, path in entries if flag == "??"}
    missing = sorted(set(baseline) - current)
    if missing:
        raise RuntimeError("Preexisting untracked evidence disappeared: "
                           + repr(missing[:12]))
    fresh = []
    for flag, path in entries:
        if flag == "??" and path in baseline:
            if fingerprint(path) != baseline[path]:
                raise RuntimeError("Preexisting untracked evidence was modified: " + path)
        else:
            fresh.append(path)
    return sorted(set(fresh))


def changed():
    if BASELINE_UNTRACKED is None:
        raise RuntimeError("Record baseline untracked files before running Codex")
    return filter_status_changes(
        git_status_entries(), BASELINE_UNTRACKED, _fingerprint_untracked)


def scope_check(generated=False):
    rc, branch, err = git("branch", "--show-current")
    if rc or branch.strip() != BRANCH:
        raise RuntimeError("Wrong branch: " + branch + err)
    files = changed()
    allowed = ALLOWED_COMMIT if generated else ALLOWED_CODEX
    unexpected = [p for p in files if p not in allowed]
    if unexpected:
        raise RuntimeError("Protected/unrecognized modified paths: " + repr(unexpected))
    return files


def codex_exe():
    return shutil.which("codex") or shutil.which("codex.cmd")


def codex_exec_command(exe):
    """Compatible Codex exec syntax: approval policy belongs in config.

    Some CLI releases reject --ask-for-approval AFTER the exec subcommand.
    Keep the workspace sandbox and prohibit interactive approval prompts.
    """
    return [exe, "exec", "--sandbox", "workspace-write",
            "--config", 'approval_policy="never"',
            "--config", "model_reasoning_effort=medium", "-"]


def codex_pass(role, message, index):
    exe = codex_exe()
    if not exe:
        return {"status": "CODEX_UNAVAILABLE"}
    LOGS.mkdir(parents=True, exist_ok=True)
    name = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S") + f"_{index}_{role}"
    prompt = POLICY.read_text(encoding="utf-8") + "\n\nTASK:\n" + message + (
        "\nOnly edit explicitly allowed Codex files. Do not git commit/push, "
        "open GT/H5/F1, change protocol, train, refit or reprocess maps."
    )
    (LOGS / (name + ".prompt.txt")).write_text(prompt, encoding="utf-8")
    old_head = git_head()
    print("[CODEX] Starting", role, flush=True)
    try:
        cmd = codex_exec_command(exe)
        # Bytewise UTF-8 without BOM (avoids invalid Codex stdin encoding).
        rc, out, err = run(cmd, stdin=prompt.encode("utf-8"), timeout=1800)
        log = LOGS / (name + ".log")
        log.write_text((out + "\n--- STDERR ---\n" + err)[-400000:],
                       encoding="utf-8")
        if git_head() != old_head:
            raise RuntimeError("Codex committed independently; stop for review")
        files = scope_check()
        state = "OK" if rc == 0 else "CODEX_FAILED"
        print("[CODEX]", role, state, "edited", len(files), flush=True)
        return {"status": state, "returncode": rc, "log": str(log),
                "modified": files,
                "stderr_tail": err[-2000:] if rc else "",
                "stdout_tail": out[-1000:] if rc else ""}
    except Exception as exc:
        print("[CODEX]", role, "BLOCKED:", exc, flush=True)
        return {"status": "BLOCKED", "error": str(exc)}


def code_checks():
    tasks = [
        [sys.executable, "-m", "py_compile",
         "scripts/run_paper_a_prefreeze_one_shot.py",
         "scripts/package_paper_a_repro.py",
         "scripts/paper_a_overnight_agent.py"],
        [sys.executable, "tests/test_paper_a_prefreeze_one_shot.py"],
        [sys.executable, "tests/test_paper_a_overnight_agent.py"],
        ["git", "diff", "--check"],
    ]
    for cmd in tasks:
        rc, out, err = run(cmd, timeout=120)
        if rc:
            print("[CHECK] FAIL:", (out + err)[-1200:], flush=True)
            return False
    return True


def run_audit(attempt):
    LOGS.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    now = time.time()
    log = LOGS / ("technical_audit_" + str(attempt) + "_" + str(int(now)) + ".log")
    print("[AUDIT] Starting", attempt, flush=True)
    with log.open("wb") as dest:
        try:
            proc = subprocess.run(
                [sys.executable, "-u", "scripts/run_paper_a_prefreeze_one_shot.py"],
                cwd=ROOT, stdout=dest, stderr=subprocess.STDOUT,
                timeout=4200, check=False)
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            exit_code = 124
    report = None
    reportpath = None
    for path in sorted(AUDIT.glob("prefreeze_*.json"), reverse=True):
        if path.stat().st_mtime >= now - 2:
            report = json.loads(path.read_text(encoding="utf-8"))
            reportpath = str(path)
            break
    result = {
        "exit_code": exit_code, "status": report.get("status") if report else "NO_REPORT",
        "report": reportpath, "log": str(log),
        "failures": report.get("failures", []) if report else ["No report"],
        "SHA_verified": (report or {}).get("phases", {}).get(
            "P0_4_cache_SHA256", {}).get("matched", 0),
    }
    print("[AUDIT]", result["status"], "SHA", result["SHA_verified"], "/56", flush=True)
    return result


def write_progress(history):
    latest = history["audits"][-1]
    lines = [
        "# Paper A nightly autonomous report",
        "",
        "**Preconfirmatory draft: NO H1/H2 held-out results.**",
        "",
        "- Latest technical audit: " + latest["status"],
        "- Verified development cache hashes: " + str(latest["SHA_verified"]) + "/56.",
        "- Detailed audit JSON: " + str(latest["report"]),
        "- Codex invocations: " + str(len(history["codex"])),
        "- GT/H5/F1 confirmation opened: NO.",
        "- Research protocols frozen: NO (draft_not_frozen).",
        "",
        "## Pending scientific gates",
        "",
        "1. Independently attest training provenance and fit H1/H2 membership/capacity.",
        "2. Freeze four development-calibrated operator/control thresholds.",
        "3. Establish real GT edges decoder and annotator semantics on allowed source.",
        "4. Certify independent capture groups, N and registered statistic.",
        "5. Freeze protocol BEFORE new confirmatory outcome evaluation.",
        "",
        "## Controller errors",
        "",
    ]
    lines.extend("- " + x for x in history["errors"])
    if not history["errors"]:
        lines.append("- None registered by local controller.")
    STATUS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def commit_scoped(no_push=False):
    names = scope_check(generated=True)
    if not names:
        return {"status": "NO_CHANGES"}
    if not code_checks():
        return {"status": "FAILED_CHECKS"}
    rc, _, err = git("add", "--", *names)
    if rc:
        raise RuntimeError("Failed to stage: " + err)
    rc, out, _ = git("diff", "--cached", "--name-only")
    if rc or set(out.splitlines()) != set(names):
        raise RuntimeError("Unexpected staged paths")
    rc, _, err = git("diff", "--cached", "--check")
    if rc:
        raise RuntimeError("Git diff failed: " + err)
    rc, _, err = git("commit", "-m",
                     "paper-a: overnight prefreeze audit and manuscript update",
                     timeout=180)
    if rc:
        return {"status": "COMMIT_FAILED", "details": err[-1500:]}
    sha = git_head()
    if no_push:
        return {"status": "COMMITTED_NOT_PUSHED", "sha": sha}
    rc, out, err = git("push", "origin", "HEAD:refs/heads/" + BRANCH, timeout=240)
    return {"status": "PUSHED" if rc == 0 else "PUSH_FAILED", "sha": sha,
            "details": (out + err)[-1500:]}


def package():
    rc, out, err = run([sys.executable, "scripts/package_paper_a_repro.py"],
                       timeout=300)
    if rc:
        return {"status": "PACKAGE_FAILED", "error": (out + err)[-2000:]}
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"status": "PACKAGE_INVALID_OUTPUT", "output": out[-1500:]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skip-codex", action="store_true")
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--max-codex-calls", type=int, default=3)
    args = ap.parse_args()
    if os.name == "nt":
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
    history = {"started": datetime.now(timezone.utc).isoformat(),
               "audits": [], "codex": [], "errors": []}
    try:
        capture_preexisting_untracked()
        if scope_check() or changed():
            raise RuntimeError("Initial tracked worktree has unsafe changes")
        rc, remote, _ = git("remote", "get-url", "origin")
        if rc or "MicamAmorim/MFI-Edge" not in remote:
            raise RuntimeError("Wrong Git origin")
        current = run_audit(1)
        history["audits"].append(current)
        enabled = bool(codex_exe()) and not args.skip_codex
        attempts = 0
        while current["exit_code"] and enabled and attempts < min(2, args.max_codex_calls):
            instruction = (
                "Audit failed. Inspect exact log: " + current["log"]
                + ". Failures: " + json.dumps(current["failures"], ensure_ascii=False)
                + ". Fix ONLY safe audit scripts/tests, preserve strict checks."
            )
            step = codex_pass("audit_repair", instruction, attempts + 1)
            history["codex"].append(step)
            attempts += 1
            if step["status"] != "OK":
                history["errors"].append("Codex repair: " + step["status"])
                break
            if not code_checks():
                history["errors"].append("Unsafe/invalid Codex edits")
                break
            current = run_audit(attempts + 1)
            history["audits"].append(current)
        if current["exit_code"]:
            history["errors"].append("Technical audit incomplete: " + current["status"])
        if enabled and attempts < args.max_codex_calls:
            editorial = (
                "Improve ONLY docs/paper_a_confirmation/PAPER_A_MANUSCRIPT_DRAFT.md. "
                "Ground all claims in prespecified H1/H2, existing Stage24 docs, "
                "bibliography and audited metadata. Improve scientific English, "
                "figures/tables plan, reproducibility, methods, and limitations. "
                "Do NOT invent confirmatory F1, rho, p, DOI, or choose N/freeze."
            )
            editorial_result = codex_pass("manuscript", editorial, attempts + 1)
            history["codex"].append(editorial_result)
            if editorial_result["status"] != "OK":
                history["errors"].append(
                    "Codex editorial incomplete: " + editorial_result["status"]
                    + "; see " + str(editorial_result.get("log", "local Codex log")))
        try:
            scope_check()
            if (changed() and any(x.get("status") != "OK"
                                  for x in history["codex"])):
                raise RuntimeError(
                    "An unsuccessful Codex pass left edits; manual review required")
            write_progress(history)
            history["git"] = commit_scoped(args.no_push)
        except Exception as exc:
            history["git"] = {"status": "PROTECTED_GIT_BLOCK", "reason": str(exc)}
            history["errors"].append("Git: " + str(exc))
        if history["git"]["status"] in {
            "PROTECTED_GIT_BLOCK", "FAILED_CHECKS", "COMMIT_FAILED"
        }:
            history["package"] = {
                "status": "SKIPPED_UNVERIFIED_WORKTREE",
                "reason": "No package from unsafe or uncommitted source changes"
            }
        else:
            history["package"] = package()
        history["finished"] = datetime.now(timezone.utc).isoformat()
        final = DATA / "paper_a_overnight_LAST_STATUS.json"
        final.write_text(json.dumps(history, indent=2, ensure_ascii=False),
                         encoding="utf-8")
        print(json.dumps({
            "audit": current["status"],
            "git": history["git"]["status"],
            "repro_zip": history["package"].get("zip_path"),
            "last_status_json": str(final),
            "scientific_status": "draft_not_frozen",
            "codex": [step["status"] for step in history["codex"]],
            "errors": history["errors"],
        }, ensure_ascii=False, indent=2), flush=True)
        return 0 if (current["exit_code"] == 0
                     and history["package"].get("zip_path")
                     and history["git"]["status"] in (
                         "NO_CHANGES", "COMMITTED_NOT_PUSHED", "PUSHED", "PUSH_FAILED")
                     ) else 2
    except Exception as exc:
        print("[FATAL]", repr(exc), flush=True)
        return 2
    finally:
        if os.name == "nt":
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)


if __name__ == "__main__":
    raise SystemExit(main())
