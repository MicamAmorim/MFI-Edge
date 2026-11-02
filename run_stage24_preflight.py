from __future__ import annotations

"""Stage 24R0 mandatory Evaluation Integrity Repair preflight."""

from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
import tempfile
import numpy as np

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from src.stage24_integrity import load_float_artifact, one_to_one_boundary_counts, resize_score_to_native, save_float_artifact

OUT_DEFAULT = ROOT / "results/local_dev/stage24r0_evaluation_integrity_preflight"


def _case(name, ok, detail=""):
    return {"name": name, "passed": bool(ok), "detail": detail}


def run_synthetic_checks():
    checks = []
    gt = np.zeros((32, 32), bool); gt[16, 6:26] = True
    c = one_to_one_boundary_counts(gt, gt, tolerance_px=0)
    checks.append(_case("perfect_match", c.tp == 20 and c.fp == 0 and c.fn == 0 and c.f1 == 1.0, str(c.to_dict())))
    shifted = np.zeros_like(gt); shifted[17, 6:26] = True
    c = one_to_one_boundary_counts(shifted, gt, tolerance_px=1)
    checks.append(_case("one_pixel_shift_within_tolerance", c.tp == 20 and c.fp == 0 and c.fn == 0, str(c.to_dict())))
    thick = np.zeros_like(gt)
    for r in (14, 15, 16, 17, 18): thick[r, 6:26] = True
    c = one_to_one_boundary_counts(thick, gt, tolerance_px=2)
    checks.append(_case("thick_prediction_not_multiply_rewarded", c.tp == 20 and c.pred_count == 100 and c.fp == 80 and abs(c.precision - .2) < 1e-12, str(c.to_dict())))
    fragmented = np.zeros_like(gt); fragmented[16, 6:16] = True
    c = one_to_one_boundary_counts(fragmented, gt, tolerance_px=0)
    checks.append(_case("fragmentation_reduces_recall", c.tp == 10 and c.fn == 10 and abs(c.recall - .5) < 1e-12, str(c.to_dict())))
    empty = np.zeros_like(gt)
    c1 = one_to_one_boundary_counts(empty, gt, tolerance_px=1)
    c2 = one_to_one_boundary_counts(empty, empty, tolerance_px=1)
    c3 = one_to_one_boundary_counts(gt, empty, tolerance_px=1)
    checks += [
        _case("empty_prediction", c1.tp == 0 and c1.fn == 20 and c1.f1 == 0.0, str(c1.to_dict())),
        _case("empty_both", c2.f1 == 1.0, str(c2.to_dict())),
        _case("empty_gt_with_prediction", c3.tp == 0 and c3.fp == 20 and c3.f1 == 0.0, str(c3.to_dict())),
    ]
    original_gt = np.zeros((41, 57), bool); original_gt[8:32, 28] = True
    score = np.linspace(0, 1, 15 * 21, dtype=np.float32).reshape(15, 21)
    registered = resize_score_to_native(score, original_gt.shape)
    checks.append(_case("geometry_contract_score_to_native_gt", registered.shape == original_gt.shape and original_gt.shape == (41, 57), f"score {score.shape}->{registered.shape}; GT untouched"))
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "map.npy"
        identity = {"image_id": "synthetic", "inference_shape": [15, 21], "evaluation_shape": [41, 57], "dtype": "float32"}
        save_float_artifact(p, registered.astype(np.float32), identity)
        loaded = load_float_artifact(p, identity)
        checks.append(_case("float_artifact_roundtrip", np.array_equal(loaded, registered.astype(np.float32)), "bitwise float32 round-trip"))
        try: load_float_artifact(Path(td) / "map.png")
        except (ValueError, FileNotFoundError): checks.append(_case("quantized_input_rejected", True, "PNG rejected"))
        else: checks.append(_case("quantized_input_rejected", False, "PNG accepted unexpectedly"))
    return checks


def _run_unit_tests():
    """Run Stage-24 tests via filesystem discovery with repo root on PYTHONPATH.

    This avoids collisions with unrelated installed top-level ``tests`` packages,
    does not require tests/__init__.py, and guarantees ``from src...`` resolves in
    the subprocess on Windows as well as POSIX environments.
    """
    tests_dir = ROOT / "tests"
    test_file = tests_dir / "test_stage24_integrity.py"
    if not test_file.is_file():
        return _case("unit_test_suite", False, f"missing {test_file.relative_to(ROOT)}")

    cmd = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        str(tests_dir),
        "-p",
        "test_stage24_integrity.py",
        "-v",
    ]
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(ROOT) if not existing else str(ROOT) + os.pathsep + existing
    p = subprocess.run(cmd, cwd=str(ROOT), env=env, text=True, capture_output=True)
    detail = "command: " + " ".join(cmd) + "\nPYTHONPATH=" + env["PYTHONPATH"] + "\n" + p.stdout + "\n" + p.stderr
    return _case("unit_test_suite", p.returncode == 0, detail[-6000:])


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--out", default=str(OUT_DEFAULT)); args = parser.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    checks = run_synthetic_checks()
    checks.append(_run_unit_tests())
    official_files = [ROOT / "evaluation/bsds_official/run_official_bsds.py", ROOT / "evaluation/bsds_official/matlab/evaluate_bsds_official.m", ROOT / "evaluation/bsds_official/config.json"]
    checks.append(_case("official_bsds_path_present", all(x.is_file() for x in official_files), "; ".join(str(x.relative_to(ROOT)) for x in official_files)))
    failed = [x for x in checks if not x["passed"]]
    summary = {
        "status": "completed" if not failed else "failed", "stage": "24R0", "role": "evaluation_integrity_preflight",
        "ground_truth_policy": "native bytes/geometry; never resized", "training_target_policy": "exact GT only; tolerance is matcher-only",
        "internal_matcher": "maximum-cardinality one-to-one Euclidean proximity", "bsds_final_metric_policy": "official Berkeley MATLAB evaluator only",
        "scientific_artifact_policy": "floating .npy; quantized PNG is export/visualization only", "checks": checks, "blockers": [x["name"] for x in failed],
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2)); return 0 if not failed else 2


if __name__ == "__main__": raise SystemExit(main())
