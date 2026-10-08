from __future__ import annotations

"""Dataset-free source and build preflight for the exact Stage-15d EDPF path."""

from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "automation" / "stage15d_edpf_build_preflight"
AUTHOR_REPOSITORY = "https://github.com/CihanTopal/ED_Lib.git"
AUTHOR_COMMIT = "69b8d081bd6d28192d816ec0ed02aff9186d73c1"
AUTHOR_VENDOR = (
    ROOT / "evaluation" / "bsds_official" / "vendor"
    / f"ed_lib_author_{AUTHOR_COMMIT[:12]}"
)
OPENCV_REPOSITORY = "https://github.com/opencv/opencv.git"
OPENCV_VERSION = "3.4.20"
# GitHub exposes 3.4.20 as an annotated tag. Keep both immutable object IDs:
# checking out the tag object peels it to the release commit in HEAD.
OPENCV_TAG_OBJECT = "404ca455aeed9d26946e281b0383829bd0c533b1"
OPENCV_COMMIT = "1eb1d4c3708f2bd95562cedd58d28461505c2d37"
OPENCV_VENDOR = (
    ROOT / "evaluation" / "bsds_official" / "vendor"
    / f"opencv_{OPENCV_VERSION.replace('.', '_')}_{OPENCV_TAG_OBJECT[:12]}"
)

# Hashes recorded from the immutable author commit before registration. This
# covers the complete ED/EDPF compilation surface plus license/build metadata.
AUTHOR_HASHES = {
    "CMakeLists.txt": "f8e13d7e1253e839225570b9fbf8f5be2e26f14b75cedf2d374a840c9464e8eb",
    "ED.cpp": "15b4d335fc41b4299cf88b657440525abb298e2a903b93f297b52ecabc631447",
    "ED.h": "fad25b6ad1a72213fd6cd5c5eac00fc1dc917fb43219544572b3444bfb24e66a",
    "EDCircles.cpp": "663016bca8cf506d50583d3b64dd201bf368b52b4946d88dd91f601df3b6d139",
    "EDCircles.h": "4fc7c3eb2911d646fb6edc72619b7116623da2267490f8aec0a22e4cc0b1a3f0",
    "EDColor.cpp": "47fe416d7c593adcb0a7c78f7c6187f61a91785c14ecef77d1558eb4f94ae670",
    "EDColor.h": "6f1e69d440f663167813685dd9baa1026fa73dd2916f5ff327506e6fccab816a",
    "EDLib.h": "5cfd855c9549c573146e398a31f2e9e5d2818ec3202f814affa242aea312d35c",
    "EDLines.cpp": "aade4e08356a6d153fa28b3d952439c9729a999c31e1044d5197c75dc0b04429",
    "EDLines.h": "35d140add73146cc3816ad16a6c575de6d56e133b7dc1f80ec15743b78518c47",
    "EDPF.cpp": "95c5a5b273fd8f06f455745dab00faeed6b431f8d2da3e305b587c55f1f5a222",
    "EDPF.h": "e41851f9bfbfa50589d1cdc85fe01011dff34c8a7c4b61f9c412afdddeaa3449",
    "LICENSE": "35badbf7de0c114cd20dcefe73593a3f58839f575d157048412436ceaea7949b",
    "NFA.cpp": "06b7f69aaaf224e5a6a87b8f708e6177c672959f688e1697e9580a5062fc85c5",
    "NFA.h": "7ed73912e1431b9dd57a9643e358eb2bc4e0044910b21bbd80b3d97391f87303",
    "README.md": "39321deac0e120d0800417de4e2f8794cabb477e21522189acdacc70ae826464",
}


def _run(command: list[str], *, cwd: Path = ROOT, timeout: float = 900) -> dict:
    try:
        completed = subprocess.run(
            command, cwd=cwd, text=True, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, timeout=timeout, check=False,
        )
        return {"command": command, "returncode": completed.returncode,
                "output": completed.stdout or ""}
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"command": command, "returncode": None, "output": repr(exc)}


def _git(*args: str, cwd: Path | None = None, timeout: float = 900) -> dict:
    prefix = ["-C", str(cwd)] if cwd is not None else []
    trust = ["-c", f"safe.directory={cwd.resolve().as_posix()}"] if cwd else []
    return _run(["git", *trust, *prefix, *args], timeout=timeout)


def _require_ok(result: dict, label: str) -> str:
    if result["returncode"] != 0:
        raise RuntimeError(f"{label} failed:\n{result['output'][-4000:]}")
    return str(result["output"]).strip()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ensure_author_source() -> dict:
    if not (AUTHOR_VENDOR / ".git").exists():
        AUTHOR_VENDOR.parent.mkdir(parents=True, exist_ok=True)
        if AUTHOR_VENDOR.exists():
            raise RuntimeError(
                f"incomplete author checkout exists without .git: {AUTHOR_VENDOR}"
            )
        _require_ok(
            _git("clone", "--no-checkout", AUTHOR_REPOSITORY, str(AUTHOR_VENDOR)),
            "author clone",
        )
        _require_ok(
            _git("checkout", "--detach", AUTHOR_COMMIT, cwd=AUTHOR_VENDOR),
            "author checkout",
        )

    head = _require_ok(_git("rev-parse", "HEAD", cwd=AUTHOR_VENDOR), "rev-parse")
    if head != AUTHOR_COMMIT:
        raise RuntimeError(f"author checkout is {head}, expected {AUTHOR_COMMIT}")
    dirty = _require_ok(
        _git("status", "--porcelain", "--untracked-files=no", cwd=AUTHOR_VENDOR),
        "source status",
    )
    if dirty:
        raise RuntimeError("tracked files in the author checkout were modified")
    observed = {name: _sha256(AUTHOR_VENDOR / name) for name in AUTHOR_HASHES}
    if observed != AUTHOR_HASHES:
        raise RuntimeError("pinned ED_Lib source hashes do not match registration")
    if not (AUTHOR_VENDOR / "LICENSE").read_text(encoding="utf-8").startswith("MIT License"):
        raise RuntimeError("pinned author license is not the registered MIT text")
    return {
        "repository": AUTHOR_REPOSITORY,
        "commit": head,
        "checkout": str(AUTHOR_VENDOR.relative_to(ROOT)).replace("\\", "/"),
        "tracked_clean": True,
        "hashes": observed,
        "license": "MIT",
    }


def _ensure_opencv_source() -> dict:
    """Resolve the author-documented OpenCV 3.4 dependency immutably."""
    if not (OPENCV_VENDOR / ".git").exists():
        OPENCV_VENDOR.parent.mkdir(parents=True, exist_ok=True)
        if OPENCV_VENDOR.exists():
            raise RuntimeError(
                f"incomplete OpenCV checkout exists without .git: {OPENCV_VENDOR}"
            )
        _require_ok(
            _git("clone", "--no-checkout", OPENCV_REPOSITORY, str(OPENCV_VENDOR)),
            "OpenCV clone",
        )
        _require_ok(
            _git("checkout", "--detach", OPENCV_TAG_OBJECT, cwd=OPENCV_VENDOR),
            "OpenCV checkout",
        )
    tag_object = _require_ok(
        _git("rev-parse", "3.4.20^{tag}", cwd=OPENCV_VENDOR),
        "OpenCV tag-object resolution",
    )
    if tag_object != OPENCV_TAG_OBJECT:
        raise RuntimeError(
            f"OpenCV tag object is {tag_object}, expected {OPENCV_TAG_OBJECT}"
        )
    head = _require_ok(_git("rev-parse", "HEAD", cwd=OPENCV_VENDOR), "OpenCV rev-parse")
    if head != OPENCV_COMMIT:
        raise RuntimeError(f"OpenCV checkout is {head}, expected {OPENCV_COMMIT}")
    dirty = _require_ok(
        _git("status", "--porcelain", "--untracked-files=no", cwd=OPENCV_VENDOR),
        "OpenCV source status",
    )
    if dirty:
        raise RuntimeError("tracked files in the OpenCV checkout were modified")
    return {
        "repository": OPENCV_REPOSITORY,
        "version": OPENCV_VERSION,
        "tag_object": tag_object,
        "commit": head,
        "checkout": str(OPENCV_VENDOR.relative_to(ROOT)).replace("\\", "/"),
        "tracked_clean": True,
        "role": "build dependency only; detector source and parameters unchanged",
    }


def _bootstrap_opencv() -> tuple[Path, dict]:
    source = _ensure_opencv_source()
    build_dir = OUT / "opencv_build"
    install_dir = OUT / "opencv_install"
    configure = _run([
        "cmake", "-S", str(OPENCV_VENDOR), "-B", str(build_dir),
        "-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_INSTALL_PREFIX={install_dir}",
        "-DBUILD_LIST=core,imgproc", "-DBUILD_SHARED_LIBS=OFF",
        "-DBUILD_TESTS=OFF", "-DBUILD_PERF_TESTS=OFF",
        "-DBUILD_EXAMPLES=OFF", "-DBUILD_opencv_apps=OFF",
        "-DBUILD_JAVA=OFF", "-DBUILD_opencv_python2=OFF",
        "-DBUILD_opencv_python3=OFF", "-DBUILD_opencv_world=OFF",
        "-DWITH_CUDA=OFF", "-DWITH_IPP=OFF", "-DWITH_OPENCL=OFF",
        "-DWITH_TBB=OFF", "-DWITH_ITT=OFF",
    ], timeout=1800)
    (OUT / "opencv_configure.log").write_text(configure["output"], encoding="utf-8")
    build = {"command": [], "returncode": None, "output": "configure did not pass"}
    if configure["returncode"] == 0:
        build = _run([
            "cmake", "--build", str(build_dir), "--config", "Release",
            "--target", "INSTALL", "--parallel", "2",
        ], timeout=7200)
    (OUT / "opencv_build.log").write_text(build["output"], encoding="utf-8")
    configs = sorted(install_dir.rglob("OpenCVConfig.cmake")) if install_dir.exists() else []
    # OpenCV 3.4's top-level Windows-pack dispatcher predates MSVC 19.4x and
    # cannot infer its vc runtime directory.  The build also installs the
    # direct static-package config, which contains the exact imported targets
    # produced by this compile and does not perform that obsolete dispatch.
    static_configs = [path for path in configs if path.parent.name == "staticlib"]
    if configure["returncode"] != 0 or build["returncode"] != 0 or not static_configs:
        raise RuntimeError(
            "pinned OpenCV dependency bootstrap failed; inspect opencv_configure.log "
            "and opencv_build.log"
        )
    config_dir = static_configs[0].parent
    source["cmake_config_dir"] = str(config_dir.relative_to(ROOT)).replace("\\", "/")
    source["config_selection"] = (
        "direct installed static-package config; bypasses the OpenCV 3.4 "
        "Windows-pack dispatcher that cannot classify MSVC 19.4x"
    )
    return config_dir, source


def _write_build_harness() -> tuple[Path, Path]:
    source_dir = OUT / "build_harness"
    build_dir = OUT / "build"
    source_dir.mkdir(parents=True, exist_ok=True)
    author = AUTHOR_VENDOR.resolve().as_posix()
    # Compile only the transitive author source surface needed by grayscale
    # EDPF; unrelated line/circle executables cannot become build blockers.
    sources = ["ED.cpp", "EDColor.cpp", "EDPF.cpp"]
    source_lines = "\n".join(f'  "${{AUTHOR_DIR}}/{name}"' for name in sources)
    cmake = f"""cmake_minimum_required(VERSION 3.16)
project(stage15d_edpf_preflight LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(OpenCV REQUIRED COMPONENTS core imgproc)
set(AUTHOR_DIR "{author}")
add_library(edlib_author STATIC
{source_lines}
)
target_include_directories(edlib_author PRIVATE "${{AUTHOR_DIR}}" ${{OpenCV_INCLUDE_DIRS}})
target_link_libraries(edlib_author PUBLIC ${{OpenCV_LIBS}})
add_executable(edpf_smoke smoke.cpp)
target_include_directories(edpf_smoke PRIVATE "${{AUTHOR_DIR}}" ${{OpenCV_INCLUDE_DIRS}})
target_link_libraries(edpf_smoke PRIVATE edlib_author ${{OpenCV_LIBS}})
"""
    smoke = r'''#include "EDPF.h"
#include <iostream>

int main() {
    cv::Mat input(64, 64, CV_8UC1, cv::Scalar(0));
    for (int y = 16; y < 48; ++y)
        for (int x = 16; x < 48; ++x) input.at<unsigned char>(y, x) = 220;
    EDPF first(input);
    EDPF second(input);
    cv::Mat a = first.getEdgeImage();
    cv::Mat b = second.getEdgeImage();
    double low = 0.0, high = 0.0;
    cv::minMaxLoc(a, &low, &high);
    if (a.type() != CV_8UC1 || a.size() != input.size()) return 2;
    if (!(low == 0.0 && (high == 0.0 || high == 255.0))) return 3;
    cv::Mat invalid = (a != 0) & (a != 255);
    if (cv::countNonZero(invalid) != 0) return 4;
    if (cv::norm(a, b, cv::NORM_INF) != 0.0) return 5;
    std::cout << "SMOKE_OK pixels=" << cv::countNonZero(a)
              << " min=" << low << " max=" << high << std::endl;
    return 0;
}
'''
    (source_dir / "CMakeLists.txt").write_text(cmake, encoding="utf-8")
    (source_dir / "smoke.cpp").write_text(smoke, encoding="utf-8")
    return source_dir, build_dir


def _python_opencv_contract() -> dict:
    try:
        import cv2
        return {
            "available": True,
            "version": cv2.__version__,
            "has_ximgproc": hasattr(cv2, "ximgproc"),
            "has_edge_drawing_binding": hasattr(
                getattr(cv2, "ximgproc", None), "createEdgeDrawing"
            ),
            "note": "Diagnostic only; never substituted for pinned author C++ source.",
        }
    except Exception as exc:  # pragma: no cover - environment diagnostic
        return {"available": False, "error": repr(exc)}


def main() -> int:
    global OUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--bootstrap-opencv", action="store_true")
    args = parser.parse_args()
    OUT = args.out if args.out.is_absolute() else ROOT / args.out
    OUT.mkdir(parents=True, exist_ok=True)
    source = _ensure_author_source()
    opencv_source = None
    opencv_dir = os.environ.get("OpenCV_DIR")
    if args.bootstrap_opencv:
        bootstrapped_dir, opencv_source = _bootstrap_opencv()
        opencv_dir = str(bootstrapped_dir)
    source_dir, build_dir = _write_build_harness()
    configure_command = [
        "cmake", "-S", str(source_dir), "-B", str(build_dir),
        "-DCMAKE_BUILD_TYPE=Release",
    ]
    if opencv_dir:
        configure_command.append(f"-DOpenCV_DIR={opencv_dir}")
    configure = _run(configure_command)
    (OUT / "cmake_configure.log").write_text(configure["output"], encoding="utf-8")

    build = {"command": [], "returncode": None, "output": "configure did not pass"}
    smoke = {"command": [], "returncode": None, "output": "build did not pass"}
    if configure["returncode"] == 0:
        build = _run([
            "cmake", "--build", str(build_dir), "--config", "Release",
            "--target", "edpf_smoke",
        ])
        if build["returncode"] == 0:
            candidates = [
                build_dir / "Release" / "edpf_smoke.exe",
                build_dir / "edpf_smoke.exe",
                build_dir / "edpf_smoke",
            ]
            executable = next((path for path in candidates if path.exists()), None)
            smoke = (
                _run([str(executable)], cwd=build_dir, timeout=120)
                if executable is not None
                else {"command": [], "returncode": None,
                      "output": "build passed but edpf_smoke executable was not found"}
            )
    (OUT / "cmake_build.log").write_text(build["output"], encoding="utf-8")
    (OUT / "smoke.log").write_text(smoke["output"], encoding="utf-8")

    passed = (
        configure["returncode"] == 0 and build["returncode"] == 0
        and smoke["returncode"] == 0 and "SMOKE_OK" in smoke["output"]
    )
    contract = {
        "source": source,
        "tools": {
            "git": shutil.which("git"),
            "cmake": shutil.which("cmake"),
            "opencv_dir": opencv_dir,
            "bootstrapped_opencv": opencv_source,
            "python_opencv": _python_opencv_contract(),
        },
        "author_implementation": {
            "training_class": "strictly untrained; fixed author implementation",
            "selected_variant": "grayscale EDPF constructed directly from a grayscale image",
            "fixed_code_path": "EDPF(src): ED(PREWITT_OPERATOR, gradThresh=11, anchorThresh=3), then chain-level Helmholtz validation",
            "validation_constants": "divForTestSegment=2.25 and EPSILON=1.0 are embedded author-code constants",
            "scalar_output": "getEdgeImage() returns the native CV_8UC1 binary edge map (0/255)",
            "parameter_policy": "no parameter exposure, search, calibration, or post-result tuning",
        },
        "build": {
            "configure_returncode": configure["returncode"],
            "build_returncode": build["returncode"],
            "smoke_returncode": smoke["returncode"],
            "smoke_output": smoke["output"].strip(),
            "passed": passed,
        },
    }
    contract_path = OUT / "dependency_contract.json"
    contract_path.write_text(json.dumps(contract, indent=2), encoding="utf-8")

    summary = {
        "stage": "15d-edpf-build-preflight",
        "role": "reproduction_dependency_preflight",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "architecture_changed": False,
        "detector_benchmark_executed": False,
        "dataset_read": False,
        "protected_split_used": False,
        "implementation_fidelity": "unmodified hash-verified author C++ sources with repository-local external build/smoke harness",
        "source": source,
        "opencv_dependency": opencv_source,
        "build_preflight_passed": passed,
        "dependency_contract": str(contract_path.relative_to(ROOT)).replace("\\", "/"),
        "decision_rule": (
            "Register one exact native-resolution BSDS500-validation EDPF reproduction "
            "only if the pinned unmodified author source builds and the deterministic "
            "binary-output smoke test passes. If not, repair only the repository-local "
            "dependency/build harness; do not substitute a reimplementation or tune EDPF."
        ),
        "future_matched_evaluation_plan": {
            "input": "native-resolution BSDS500-validation JPG decoded to author-required grayscale",
            "output": "native binary CV_8UC1 map serialized as 8-bit PNG without normalization or softening",
            "official_protocol": "all annotations, 99 thresholds, maxDist=0.0075, thinning, unchanged stochastic Windows matcher",
            "metric_caveat": "binary EDPF supplies one nontrivial operating point; report official ODS/OIS/AP but interpret threshold-curve/AP limitations explicitly",
            "preview": "sorted validation positions 1, 50, and 100; input, mean GT display, incumbent, exact EDPF",
        },
        "stage14t_distinction": (
            "Stage 14t attenuated connected upper-level components of the incumbent; "
            "EDPF constructs ED pixel chains and validates chain segments with the "
            "author Helmholtz/NFA implementation."
        ),
        "official_eval_manifest_omission": (
            "Required and justified: this dataset-free dependency/build preflight does "
            "not read BSDS or generate benchmark maps."
        ),
        "recommended_next_action_if_passed": "stage15d_edpf_exact_reproduction",
        "recommended_next_action_if_failed": "attachment-only dependency/build repair without dataset execution",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("STAGE15D_EDPF_BUILD_PREFLIGHT_COMPLETE")
    print(OUT / "summary.json")
    print(f"build_preflight_passed={passed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
