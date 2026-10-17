from __future__ import annotations

"""Stage 18f fixed hierarchical triangle-partition context falsification."""

from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from scipy.io import loadmat, savemat

import run_stage17h_local_fractal_context as harness
from src.edge_signature import binary_auc, mutual_information_binary, population_masks
from src.triangle_partition_context import (
    AUTHOR_COMMIT,
    AUTHOR_PARAMETER_INDEX,
    AUTHOR_REPOSITORY,
    AUTHOR_TREE,
    WORKING_SIDE,
    prepare_author_block,
    project_author_response,
    response_diagnostics,
)


EXPERIMENT_ID = "stage18f_triangle_partition_context"
DEFAULT_OUT = ROOT / "results" / "local_dev" / EXPERIMENT_ID
AUTHOR_ROOT = ROOT / "vendor" / "triangles_edge_detection"
MATLAB_WRAPPER = ROOT / "stage18f_triangle_partition_matlab.m"
VARIANTS = ("compact_mfi", "compact_plus_triangle_partition")
ELIGIBILITY_AUC = 0.56


def _run(command: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if completed.stdout:
        print(completed.stdout, end="", flush=True)
    if completed.returncode != 0:
        raise RuntimeError(f"command failed ({completed.returncode}): {command[0]}")
    return completed.stdout


def _git(*args: str) -> str:
    command = ["git", "-c", f"safe.directory={AUTHOR_ROOT.resolve()}", "-C", str(AUTHOR_ROOT), *args]
    return _run(command).strip()


def _ensure_author_checkout() -> dict[str, object]:
    AUTHOR_ROOT.parent.mkdir(parents=True, exist_ok=True)
    if not (AUTHOR_ROOT / ".git").exists():
        _run(["git", "clone", "--filter=blob:none", "--no-checkout", AUTHOR_REPOSITORY, str(AUTHOR_ROOT)])
        _git("checkout", "--detach", AUTHOR_COMMIT)
    head = _git("rev-parse", "HEAD")
    tree = _git("rev-parse", "HEAD^{tree}")
    if head != AUTHOR_COMMIT or tree != AUTHOR_TREE:
        raise RuntimeError(f"unexpected triangle author checkout: head={head} tree={tree}")
    dirty = _git("status", "--porcelain")
    if dirty:
        raise RuntimeError("triangle author checkout is not clean")
    required = [
        "getPrm.m", "runIm.m", "Image.m", "Line.m", "TrianglesTree.m",
        "createLevelMatFileFunc_mex.mexw64",
        "nonMaximalSupressionPlusPlus_mex.mexw64",
        "updateRespMapFunc_mex.mexw64",
    ]
    missing = [name for name in required if not (AUTHOR_ROOT / name).exists()]
    if missing:
        raise RuntimeError(f"author checkout missing required files: {missing}")
    parameters = (AUTHOR_ROOT / "getPrm.m").read_text(encoding="utf-8", errors="strict")
    required_literals = [
        "prm.filterWidth = 2", "prm.minContrast = 8", "prm.minLength = 5",
        "prm.nmsThres = 0.5", "prm.varTestAlpha = 0.1",
        "prm.highestTurnAngle = 48", "prm.shapeScoreWeight = 0.001",
        "prm.radianScoreWeight = 0.0545", "prm.sigmaShape = 30",
        "prm.jLevel = 3", "prm.block = 129", "prm.sigma = 0.1",
        "prm.doNMS = true",
    ]
    absent = [literal for literal in required_literals if literal not in parameters]
    if absent:
        raise RuntimeError(f"author parameter contract changed: {absent}")
    return {
        "repository": AUTHOR_REPOSITORY,
        "commit": head,
        "tree": tree,
        "clean": True,
        "license": "no explicit source license located; ignored dependency is not redistributed",
    }


def _matlab_executable() -> Path:
    override = os.environ.get("MATLAB_EXE")
    candidate = Path(override) if override else Path(r"C:\Program Files\MATLAB\R2023a\bin\matlab.exe")
    if not candidate.exists():
        raise RuntimeError(f"MATLAB executable missing: {candidate}")
    return candidate


def _matlab_string(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace("'", "''")


def _author_maps(images: list[np.ndarray], labels: list[str]) -> list[tuple[np.ndarray, dict[str, float]]]:
    if len(images) != len(labels) or not images:
        raise ValueError("triangle batch requires equally sized nonempty images and labels")
    _ensure_author_checkout()
    temp_parent = ROOT / "results" / "automation"
    temp_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="stage18f_", dir=temp_parent) as temporary:
        work = Path(temporary)
        input_dir, output_dir, prefs = work / "inputs", work / "outputs", work / "prefs"
        input_dir.mkdir()
        output_dir.mkdir()
        prefs.mkdir()
        geometries = []
        for index, image in enumerate(images):
            block, geometry = prepare_author_block(image)
            geometries.append(geometry)
            savemat(input_dir / f"{index:04d}.mat", {"input_image": block}, do_compression=False)
        expression = (
            f"addpath('{_matlab_string(ROOT)}');"
            f"stage18f_triangle_partition_matlab('{_matlab_string(AUTHOR_ROOT)}',"
            f"'{_matlab_string(input_dir)}','{_matlab_string(output_dir)}');"
        )
        environment = dict(os.environ)
        environment["MATLAB_PREFDIR"] = str(prefs.resolve())
        started = time.perf_counter()
        _run([str(_matlab_executable()), "-batch", expression], env=environment)
        batch_elapsed = time.perf_counter() - started
        results = []
        for index, (label, geometry) in enumerate(zip(labels, geometries)):
            path = output_dir / f"{index:04d}.mat"
            if not path.exists():
                raise RuntimeError(f"author output missing for {label}")
            payload = loadmat(path)
            working = np.asarray(payload["response"], dtype=np.float64)
            author_seconds = float(np.asarray(payload["author_runtime_seconds"]).squeeze())
            evidence = project_author_response(working, geometry)
            if not np.all(np.isfinite(evidence)) or float(np.min(evidence)) < 0.0 or float(np.max(evidence)) > 1.0:
                raise RuntimeError(f"invalid triangle-partition evidence for {label}")
            diagnostics = response_diagnostics(evidence, geometry, author_seconds)
            diagnostics["working_response_sha256"] = hashlib.sha256(
                np.ascontiguousarray(working, dtype="<f8").tobytes()
            ).hexdigest()
            diagnostics["batch_wall_seconds_per_map"] = float(batch_elapsed / len(images))
            results.append((evidence, diagnostics))
        return results


def _synthetic_contract() -> dict[str, object]:
    side = WORKING_SIDE
    flat = np.full((side, side), 0.5, dtype=np.float64)
    vertical = np.full((side, side), 0.2, dtype=np.float64)
    vertical[:, side // 2 :] = 0.8
    horizontal = np.full((side, side), 0.2, dtype=np.float64)
    horizontal[side // 2 :, :] = 0.8
    maps = _author_maps(
        [flat, vertical, vertical.copy(), horizontal],
        ["flat", "vertical", "vertical_repeat", "horizontal"],
    )
    flat_map, vertical_map, repeat_map, horizontal_map = [entry[0] for entry in maps]
    vertical_column = int(np.argmax(np.sum(vertical_map, axis=0)))
    horizontal_row = int(np.argmax(np.sum(horizontal_map, axis=1)))
    return {
        "finite": bool(all(np.all(np.isfinite(entry[0])) for entry in maps)),
        "bounded": bool(all(float(np.min(entry[0])) >= 0.0 and float(np.max(entry[0])) <= 1.0 for entry in maps)),
        "flat_max": float(np.max(flat_map)),
        "vertical_max": float(np.max(vertical_map)),
        "horizontal_max": float(np.max(horizontal_map)),
        "vertical_peak_column": vertical_column,
        "horizontal_peak_row": horizontal_row,
        "vertical_peak_distance": int(abs(vertical_column - side // 2)),
        "horizontal_peak_distance": int(abs(horizontal_row - side // 2)),
        "repeat_max_abs_delta": float(np.max(np.abs(vertical_map - repeat_map))),
        "author_adapter": "non-finite author normalization output is mapped to zero before clipping",
    }


def _attach_cue_maps(items: list[dict], prefix: str = "STAGE18F_TRIANGLE") -> None:
    print(f"{prefix} batch_maps={len(items)}", flush=True)
    results = _author_maps([item["pre_img"] for item in items], [str(item["id"]) for item in items])
    for item, (cue, diagnostics) in zip(items, results):
        item["local_fractal"] = cue
        item["fractal_diagnostics"] = diagnostics
        item["fractal_runtime_seconds"] = float(diagnostics["author_runtime_seconds"])


def _fit_cue_spec(items: list[dict], seed: int, max_samples: int = 2500) -> dict:
    values, targets = [], []
    for item_no, item in enumerate(items):
        masks = population_masks(item)
        flat = np.asarray(item["local_fractal"], dtype=np.float64).ravel()
        for group_no, (group, target) in enumerate((("edge", True), ("texture", False))):
            ids = np.flatnonzero(np.asarray(masks[group], dtype=bool).ravel())
            if ids.size > int(max_samples):
                rng = np.random.default_rng(int(seed) + 1009 * item_no + 97 * group_no)
                ids = rng.choice(ids, size=int(max_samples), replace=False)
            if ids.size:
                values.append(flat[ids])
                targets.append(np.full(ids.size, target, dtype=bool))
    if not values:
        raise RuntimeError("no triangle-partition calibration samples were extracted")
    score = np.concatenate(values)
    target = np.concatenate(targets)
    auc = float(binary_auc(score, target))
    information = float(mutual_information_binary(score, target))
    edge_values, texture_values = score[target], score[~target]
    q25, q75 = np.quantile(score, [0.25, 0.75])
    raw_weight = max(auc - 0.5, 0.0) * (1.0 + information)
    eligible = bool(auc >= ELIGIBILITY_AUC and raw_weight > 0.0)
    return {
        "feature": "hierarchical_triangle_partition_response",
        "edge_direction": 1.0,
        "midpoint": float(0.5 * (np.median(edge_values) + np.median(texture_values))),
        "scale": float(max(q75 - q25, 1.0e-9)),
        "edge_median": float(np.median(edge_values)),
        "texture_median": float(np.median(texture_values)),
        "texture_auc": auc,
        "mutual_information": information,
        "raw_weight": float(raw_weight if eligible else 0.0),
        "eligible": eligible,
    }


def _diagnostic_row(item: dict) -> dict:
    values = item["fractal_diagnostics"]
    return {"image_id": item["id"], **values, "triangle_runtime_seconds": item["fractal_runtime_seconds"]}


def _write_official_manifest(out: Path) -> Path:
    manifest = {
        "schema_version": 1,
        "split": "val",
        "include_incumbent": True,
        "methods": [{
            "name": VARIANTS[1],
            "export": {
                "script": "run_stage18f_triangle_partition_context.py",
                "args": ["--export-bsds", "--image-dir", "{image_dir}", "--output-dir", "{output_dir}", "--split", "{split}"],
                "timeout_minutes": 360,
            },
        }],
    }
    path = out / "official_eval_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def _contract_record(provenance: dict[str, object]) -> dict[str, object]:
    return {
        **provenance,
        "input": "unchanged median-conditioned grayscale image",
        "working_geometry": "isotropic fit to 129x129 with symmetric reflected letterboxing",
        "projection": "remove letterbox and bilinearly restore native support",
        "author_entry_point": "runIm(block, false, 0)",
        "author_parameter_index": AUTHOR_PARAMETER_INDEX,
        "author_defaults": {
            "filter_width": 2, "minimum_contrast": 8, "minimum_length": 5,
            "nms_threshold": 0.5, "variance_test_alpha": 0.1,
            "highest_turn_angle": 48, "shape_score_weight": 0.001,
            "radian_score_weight": 0.0545, "shape_sigma": 30,
            "tree_level": 3, "noise_sigma": 0.1, "nms": True,
        },
        "output_adapter": "map non-finite values to zero, clip to [0,1], no other normalization",
        "eligibility_auc": ELIGIBILITY_AUC,
    }


def _install_harness(contract: dict[str, object]) -> dict[str, object]:
    provenance = _ensure_author_checkout()
    harness.DEFAULT_OUT = DEFAULT_OUT
    harness.VARIANTS = VARIANTS
    harness.ELIGIBILITY_AUC = ELIGIBILITY_AUC
    harness.OFFSETS = (WORKING_SIDE,)
    harness.SUPPORT_SIZE = "one fixed 129x129 reflected-letterbox author block"
    harness.synthetic_contract = lambda: contract
    harness._attach_local_fractal_maps = _attach_cue_maps
    harness._fit_cue_spec = _fit_cue_spec
    harness._diagnostic_row = _diagnostic_row
    harness._write_official_manifest = _write_official_manifest
    return provenance


def _rename(source: Path, target: Path) -> None:
    if source.exists():
        source.replace(target)


def _finalize_development(out: Path, provenance: dict[str, object]) -> None:
    _rename(out / "fractal_calibration.csv", out / "triangle_partition_calibration.csv")
    _rename(out / "fractal_diagnostics.csv", out / "triangle_partition_diagnostics.csv")
    path = out / "summary.json"
    summary = json.loads(path.read_text(encoding="utf-8"))
    summary.update({
        "stage": "18f-triangle-partition-context",
        "role": "generation_2_triangle_partition_context_falsification",
        "mechanism": {
            "description": "one positive context membership from the fixed author hierarchical triangle-partition faint-curve response",
            "implementation_fidelity": "immutable author detector on one fixed whole-image 129x129 block with disclosed repository raster adapter; not native-resolution exact reproduction",
            "parameters": _contract_record(provenance),
            "unchanged": ["five retained memberships", "distorted-Choquet gamma 0.55", "gate strength 2.0 and floor 0.10", "median-conditioned grayscale Scharr+NMS localizer"],
        },
        "files": ["summary.json", "variant_ranking.csv", "fold_results.csv", "per_image_metrics.csv", "triangle_partition_calibration.csv", "triangle_partition_diagnostics.csv", "best_method_preview.png", "official_eval_manifest.json"],
    })
    summary["visual_preview"]["columns"][-1] = "triangle_partition_cue"
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def _finalize_export(output_dir: Path, provenance: dict[str, object]) -> None:
    _rename(output_dir / "fractal_diagnostics.csv", output_dir / "triangle_partition_diagnostics.csv")
    path = output_dir / "export_manifest.json"
    metadata = json.loads(path.read_text(encoding="utf-8"))
    metadata.pop("fractal_contract", None)
    metadata["method"] = VARIANTS[1]
    metadata["triangle_partition_contract"] = _contract_record(provenance)
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _export_bsds(args: argparse.Namespace, provenance: dict[str, object]) -> int:
    names, compact, spec = harness._fit_full_candidate(args)
    image_paths = sorted(Path(args.image_dir).glob("*.jpg"))
    if not image_paths:
        raise RuntimeError(f"no BSDS JPG images found in {args.image_dir}")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Keep only the conditioned grayscale inputs during the author batch; the
    # larger retained feature tensors are reconstructed one image at a time.
    conditioned = []
    for index, path in enumerate(image_paths, start=1):
        print(f"STAGE18F_BSDS_PREP {index:03d}/{len(image_paths):03d} {path.stem}", flush=True)
        prepared, candidate_names = harness.prepare([{"id": path.stem, "img": harness.imread(path)}])
        if list(candidate_names) != list(names):
            raise RuntimeError(f"feature-name mismatch while preparing {path.stem}")
        conditioned.append(np.asarray(prepared[0]["pre_img"], dtype=np.float32).copy())
    cue_results = _author_maps(conditioned, [path.stem for path in image_paths])

    rows = []
    for index, (path, (cue, diagnostics)) in enumerate(zip(image_paths, cue_results), start=1):
        print(f"STAGE18F_BSDS_EXPORT {index:03d}/{len(image_paths):03d} {path.stem}", flush=True)
        prepared, candidate_names = harness.prepare([{"id": path.stem, "img": harness.imread(path)}])
        if list(candidate_names) != list(names):
            raise RuntimeError(f"feature-name mismatch while exporting {path.stem}")
        prepared[0]["local_fractal"] = cue
        prepared[0]["fractal_diagnostics"] = diagnostics
        prepared[0]["fractal_runtime_seconds"] = float(diagnostics["author_runtime_seconds"])
        incumbent, candidate = [maps[0] for maps in harness._score_pairs(prepared, names, compact, spec)]
        harness._save_soft_png(candidate, output_dir / f"{path.stem}.png")
        rows.append({
            **_diagnostic_row(prepared[0]),
            "mean_abs_score_delta": float(np.mean(np.abs(candidate - incumbent))),
            "support_equal": bool(np.array_equal(candidate > 0.0, incumbent > 0.0)),
        })
    harness.pd.DataFrame(rows).to_csv(output_dir / "triangle_partition_diagnostics.csv", index=False)
    metadata = {
        "method": VARIANTS[1],
        "dataset": "BSDS500",
        "split": args.split,
        "bsds_ground_truth_read": False,
        "native_resolution_output": True,
        "development_source": "UDED selection only",
        "output": "direct 8-bit soft PNG without export-time per-image normalization",
        "triangle_partition_contract": _contract_record(provenance),
        "membership_fit": spec,
        "localizer": "unchanged median-conditioned grayscale Scharr+NMS",
        "n_maps": len(image_paths),
    }
    (output_dir / "export_manifest.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return 0


def main() -> int:
    contract = _synthetic_contract()
    if not (
        contract["finite"] and contract["bounded"]
        and float(contract["flat_max"]) == 0.0
        and float(contract["vertical_max"]) > 0.0
        and float(contract["horizontal_max"]) > 0.0
        and int(contract["vertical_peak_distance"]) <= 16
        and int(contract["horizontal_peak_distance"]) <= 16
        and float(contract["repeat_max_abs_delta"]) == 0.0
    ):
        raise RuntimeError(f"triangle-partition synthetic contract failed: {contract}")
    provenance = _install_harness(contract)
    parser = argparse.ArgumentParser()
    parser.add_argument("--uded-root", default=str(harness.DEFAULT_UDED))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--max-side", type=int, default=256)
    parser.add_argument("--thresholds", type=int, default=41)
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--max-positive", type=int, default=10)
    parser.add_argument("--max-negative", type=int, default=8)
    parser.add_argument("--max-abs-corr", type=float, default=0.88)
    parser.add_argument("--seed", type=int, default=20261009)
    parser.add_argument("--export-bsds", action="store_true")
    parser.add_argument("--image-dir")
    parser.add_argument("--output-dir")
    parser.add_argument("--split", default="val")
    parser.add_argument("--max-side-development", type=int, default=256)
    args = parser.parse_args()
    if args.export_bsds:
        if not args.image_dir or not args.output_dir:
            parser.error("--export-bsds requires --image-dir and --output-dir")
        return _export_bsds(args, provenance)
    result = harness.run_experiment(args)
    _finalize_development(Path(args.out), provenance)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
