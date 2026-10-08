from __future__ import annotations

"""Dataset-free source/runtime preflight for the pinned author QFrD code."""

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import traceback


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage15i_qfrd_runtime_preflight"
AUTHOR_ROOT = ROOT / "external" / "QFrD"
AUTHOR_REPOSITORY = "https://github.com/renhu9120/QFrD.git"
AUTHOR_COMMIT = "8dcc8d846e6dcbe1bc4b931b89f1c814f5f9a245"


def _run(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd or ROOT),
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return _run(["git", "-c", "safe.directory=*", *args], cwd=cwd)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _prepare_author_checkout(log: list[str]) -> dict[str, object]:
    if not AUTHOR_ROOT.exists():
        AUTHOR_ROOT.parent.mkdir(parents=True, exist_ok=True)
        clone = _git("clone", "--no-checkout", AUTHOR_REPOSITORY, str(AUTHOR_ROOT))
        log.extend(["CLONE", clone.stdout, clone.stderr])
        if clone.returncode != 0:
            raise RuntimeError(f"author clone failed with exit code {clone.returncode}")

    remote = _git("remote", "get-url", "origin", cwd=AUTHOR_ROOT)
    if remote.returncode != 0 or remote.stdout.strip() != AUTHOR_REPOSITORY:
        raise RuntimeError(
            "existing external/QFrD checkout does not have the preregistered origin"
        )

    status = _git("status", "--porcelain", cwd=AUTHOR_ROOT)
    if status.returncode != 0 or status.stdout.strip():
        raise RuntimeError("existing external/QFrD checkout is dirty; refusing to overwrite it")

    has_commit = _git("cat-file", "-e", f"{AUTHOR_COMMIT}^{{commit}}", cwd=AUTHOR_ROOT)
    if has_commit.returncode != 0:
        fetch = _git("fetch", "--depth", "1", "origin", AUTHOR_COMMIT, cwd=AUTHOR_ROOT)
        log.extend(["FETCH", fetch.stdout, fetch.stderr])
        if fetch.returncode != 0:
            raise RuntimeError(f"author commit fetch failed with exit code {fetch.returncode}")

    checkout = _git("checkout", "--detach", AUTHOR_COMMIT, cwd=AUTHOR_ROOT)
    log.extend(["CHECKOUT", checkout.stdout, checkout.stderr])
    if checkout.returncode != 0:
        raise RuntimeError(f"author checkout failed with exit code {checkout.returncode}")

    head = _git("rev-parse", "HEAD", cwd=AUTHOR_ROOT)
    if head.returncode != 0 or head.stdout.strip() != AUTHOR_COMMIT:
        raise RuntimeError("author checkout did not resolve to the pinned commit")

    tracked = _git("ls-files", "-z", cwd=AUTHOR_ROOT)
    if tracked.returncode != 0:
        raise RuntimeError("could not enumerate author-code files")
    rel_paths = sorted(item for item in tracked.stdout.split("\0") if item)
    files = []
    aggregate = hashlib.sha256()
    for rel in rel_paths:
        path = AUTHOR_ROOT / rel
        file_hash = _sha256(path)
        files.append({"path": rel.replace("\\", "/"), "sha256": file_hash, "bytes": path.stat().st_size})
        aggregate.update(rel.replace("\\", "/").encode("utf-8"))
        aggregate.update(b"\0")
        aggregate.update(file_hash.encode("ascii"))
        aggregate.update(b"\n")

    license_files = [
        item["path"]
        for item in files
        if Path(str(item["path"])).name.lower().startswith(("license", "copying"))
    ]
    return {
        "repository": AUTHOR_REPOSITORY,
        "commit": AUTHOR_COMMIT,
        "tracked_file_count": len(files),
        "tracked_manifest_sha256": aggregate.hexdigest(),
        "license_files": license_files,
        "files": files,
    }


def _source_contract() -> dict[str, object]:
    algo_path = AUTHOR_ROOT / "algorithm" / "alg_q_3_gfrcht_fft.py"
    core_path = AUTHOR_ROOT / "core" / "q_gfrcht.py"
    export_path = AUTHOR_ROOT / "main_1_Matlab_BSD.py"
    algo = algo_path.read_text(encoding="utf-8")
    core = core_path.read_text(encoding="utf-8")
    export = export_path.read_text(encoding="utf-8")
    checks = {
        "published_default_alpha_0p8": "alpha_1: float = 0.8" in algo,
        "published_theta_pi_over_2_via_alpha_2_1": "alpha_2: float = 1.0" in algo,
        "symmetric_mu_axis": "(0.0, 1.0, 1.0, 1.0)" in algo,
        "replicate_pad_64": "pad: int = 64" in algo and 'pre.pad_mode = "replicate"' in algo,
        "gaussian_sigma_2": "gauss_sigma: float = 2.0" in algo,
        "absolute_hysteresis_0p8_2p5": "low: float = 0.8" in algo and "high: float = 2.5" in algo,
        "soft_export_is_nms_map": "return pp.edge, pp.ang_crop, pp.thin_raw_crop" in algo,
        "export_clips_without_per_image_stretch": "prob_np = np.clip(prob_np, 0.0, 1.0)" in export,
        "code_applies_multiplier_on_right": "Qalpha = q_mul(Q, M_full)" in core,
    }
    return {
        "checks": checks,
        "all_expected_source_checks_passed": all(checks.values()),
        "paper_code_order_caveat": (
            "The paper's Figure 1, Equation 17, and Algorithm 1 describe left multiplication "
            "M(alpha,theta)Q, while pinned core/q_gfrcht.py computes q_mul(Q, M_full). "
            "Any later run is therefore labeled exact author-code reproduction, not an "
            "independent verification of exact paper/code algebraic equivalence."
        ),
        "stage14s_distinction": (
            "QFrD embeds native RGB as a pure quaternion, uses a single-axis quaternion FFT, "
            "couples fractional radial power alpha=0.8 with a full Hilbert rotation theta=pi/2, "
            "and applies the author's NMS pipeline. Stage 14s instead tested a fixed grayscale "
            "half-order isotropic spectral Riesz-gradient localizer."
        ),
    }


def _dependency_inventory() -> dict[str, object]:
    names = ["numpy", "cv2", "PIL", "matplotlib", "skimage", "torch", "torchvision"]
    available = {name: importlib.util.find_spec(name) is not None for name in names}
    versions: dict[str, str] = {}
    for name, present in available.items():
        if not present:
            continue
        try:
            module = __import__(name)
            versions[name] = str(getattr(module, "__version__", "unknown"))
        except Exception as exc:  # pragma: no cover - documentary path
            versions[name] = f"import_error: {exc!r}"
            available[name] = False
    return {
        "python": sys.version,
        "available": available,
        "versions": versions,
        "required_for_smoke": ["numpy", "PIL", "matplotlib", "skimage", "torch", "torchvision"],
    }


def _synthetic_smoke() -> dict[str, object]:
    import torch

    sys.path.insert(0, str(AUTHOR_ROOT))
    try:
        from algorithm.alg_q_3_gfrcht_fft import alg_gfrcht, default_gfrcht_config

        height, width = 48, 64
        yy, xx = torch.meshgrid(
            torch.linspace(0.0, 1.0, height, dtype=torch.float64),
            torch.linspace(0.0, 1.0, width, dtype=torch.float64),
            indexing="ij",
        )
        image = torch.stack(
            [
                (xx >= 0.48).to(torch.float64),
                (yy >= 0.55).to(torch.float64),
                (0.55 * xx + 0.45 * yy).clamp(0.0, 1.0),
            ],
            dim=-1,
        )
        cfg = default_gfrcht_config(
            device="cpu",
            dtype=torch.float64,
            alpha_1=0.8,
            alpha_2=1.0,
            pad=64,
            gauss_sigma=2.0,
            low=0.8,
            high=2.5,
        )
        first = alg_gfrcht(image, cfg)
        second = alg_gfrcht(image, cfg)
        edge1, angle1, soft1 = first
        edge2, angle2, soft2 = second
        tensors = [edge1, angle1, soft1, edge2, angle2, soft2]
        finite = all(bool(torch.isfinite(item).all()) for item in tensors)
        shapes = [list(item.shape) for item in tensors]
        repeat_equal = all(torch.equal(a, b) for a, b in zip(first, second))
        native_shape = all(tuple(item.shape) == (height, width) for item in tensors)
        return {
            "attempted": True,
            "passed": finite and repeat_equal and native_shape,
            "finite": finite,
            "repeat_bitwise_equal": repeat_equal,
            "native_shape": native_shape,
            "shapes": shapes,
            "edge_values": sorted(float(v) for v in torch.unique(edge1).cpu()),
            "soft_min": float(soft1.min().cpu()),
            "soft_max": float(soft1.max().cpu()),
            "soft_nonzero": int(torch.count_nonzero(soft1).cpu()),
        }
    finally:
        if sys.path and sys.path[0] == str(AUTHOR_ROOT):
            sys.path.pop(0)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    log: list[str] = []
    errors: list[str] = []
    try:
        source_manifest = _prepare_author_checkout(log)
        source_contract = _source_contract()
    except Exception as exc:
        errors.append(f"source_preflight: {exc!r}")
        log.append(traceback.format_exc())
        source_manifest = {}
        source_contract = {}

    dependencies = _dependency_inventory()
    required = dependencies["required_for_smoke"]
    missing = [name for name in required if not dependencies["available"].get(name, False)]
    if errors or missing:
        smoke = {
            "attempted": False,
            "passed": False,
            "reason": "source preflight failed" if errors else f"missing dependencies: {missing}",
        }
    else:
        try:
            smoke = _synthetic_smoke()
        except Exception as exc:
            errors.append(f"synthetic_smoke: {exc!r}")
            log.append(traceback.format_exc())
            smoke = {"attempted": True, "passed": False, "reason": repr(exc)}

    preflight_passed = bool(
        source_manifest
        and source_contract.get("all_expected_source_checks_passed")
        and smoke.get("passed")
    )
    source_manifest_path = OUT / "source_manifest.json"
    source_manifest_path.write_text(
        json.dumps(source_manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log_path = OUT / "runtime_preflight.log"
    log_path.write_text("\n".join(log), encoding="utf-8")

    summary = {
        "stage": "15i-qfrd-runtime-preflight",
        "role": "reproduction_dependency_preflight",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "detector_executed_on_dataset": False,
        "dataset_read": False,
        "protected_split_used": False,
        "training_class": "parameter_fixed_but_author_tuned",
        "implementation_fidelity": "exact_author_code_with_paper_code_multiplication_order_caveat",
        "paper": {
            "citation": "Huang, Hu and Lian (2026), Fractional Dirac Operators for Edge Detection",
            "doi": "10.3390/fractalfract10060412",
            "license": "CC BY 4.0 article",
            "reported_bsds500_test": {"ods": 0.6145, "ois": 0.6361, "ap": 0.5996},
            "reported_protocol": "Piotr Structured Edge Toolbox; exact local binary/commit not identified",
            "parameter_selection": (
                "alpha=0.8 selected from qualitative order comparisons; theta=pi/2 also supported "
                "by reported BSDS500 test ODS comparisons; mu is the symmetric RGB axis"
            ),
        },
        "author_code": source_manifest,
        "source_contract": source_contract,
        "dependencies": dependencies,
        "missing_dependencies": missing,
        "synthetic_smoke": smoke,
        "preflight_passed": preflight_passed,
        "errors": errors,
        "decision_rule": (
            "Only a passing immutable-source and deterministic synthetic smoke test may register "
            "one exact author-code BSDS500-validation reproduction at the published fixed defaults. "
            "A dependency failure permits only a runtime repair retry; no QFrD parameter, source "
            "byte, export convention, evaluator setting, or MFI architecture may change."
        ),
        "recommended_next_action": (
            "register_exact_qfrd_validation_reproduction"
            if preflight_passed
            else "repair_runtime_dependencies_then_repeat_same_dataset_free_preflight"
        ),
        "official_eval_manifest_omission": (
            "Required and justified: source/dependency audit plus fixed synthetic smoke only; "
            "no benchmark image or detector map is read or exported."
        ),
        "visual_preview_omission": (
            "Justified: dataset-free runtime smoke only; best_method_preview.png is mandatory "
            "for the later matched validation reproduction."
        ),
        "artifacts": [
            str(source_manifest_path.relative_to(ROOT)).replace("\\", "/"),
            str(log_path.relative_to(ROOT)).replace("\\", "/"),
        ],
    }
    summary_path = OUT / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAGE15I_QFRD_RUNTIME_PREFLIGHT_COMPLETE")
    print(summary_path)
    print(f"preflight_passed={preflight_passed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
