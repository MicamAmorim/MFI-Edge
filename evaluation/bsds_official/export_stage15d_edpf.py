from __future__ import annotations

"""Export exact author-code EDPF maps for the Stage-15d reproduction.

The adapter verifies the immutable ED_Lib checkout, compiles the unmodified
author translation units against the already-preflighted pinned OpenCV 3.4.20
static artifacts, and supplies only batch I/O plus output validation. It never
reads BSDS ground truth or changes an EDPF parameter.
"""

from pathlib import Path
import argparse
import csv
import hashlib
import json
import subprocess
import time

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
AUTHOR_REPOSITORY = "https://github.com/CihanTopal/ED_Lib.git"
AUTHOR_COMMIT = "69b8d081bd6d28192d816ec0ed02aff9186d73c1"
AUTHOR_VENDOR = (
    ROOT / "evaluation" / "bsds_official" / "vendor"
    / f"ed_lib_author_{AUTHOR_COMMIT[:12]}"
)
OPENCV_REPOSITORY = "https://github.com/opencv/opencv.git"
OPENCV_VERSION = "3.4.20"
OPENCV_TAG_OBJECT = "404ca455aeed9d26946e281b0383829bd0c533b1"
OPENCV_COMMIT = "1eb1d4c3708f2bd95562cedd58d28461505c2d37"
OPENCV_VENDOR = (
    ROOT / "evaluation" / "bsds_official" / "vendor"
    / f"opencv_3_4_20_{OPENCV_TAG_OBJECT[:12]}"
)
OPENCV_INSTALL = (
    ROOT / "results" / "automation" / "stage15d_edpf_build_preflight_retry7"
    / "opencv_install"
)
BUILD_DIR = ROOT / "automation" / "runtime" / "stage15d_edpf_exporter_build"

AUTHOR_HASHES = {
    "ED.cpp": "15b4d335fc41b4299cf88b657440525abb298e2a903b93f297b52ecabc631447",
    "ED.h": "fad25b6ad1a72213fd6cd5c5eac00fc1dc917fb43219544572b3444bfb24e66a",
    "EDColor.cpp": "47fe416d7c593adcb0a7c78f7c6187f61a91785c14ecef77d1558eb4f94ae670",
    "EDColor.h": "6f1e69d440f663167813685dd9baa1026fa73dd2916f5ff327506e6fccab816a",
    "EDPF.cpp": "95c5a5b273fd8f06f455745dab00faeed6b431f8d2da3e305b587c55f1f5a222",
    "EDPF.h": "e41851f9bfbfa50589d1cdc85fe01011dff34c8a7c4b61f9c412afdddeaa3449",
    "LICENSE": "35badbf7de0c114cd20dcefe73593a3f58839f575d157048412436ceaea7949b",
}


def _run(command: list[str], *, cwd: Path = ROOT, timeout: float = 1800) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    if result.returncode:
        tail = "\n".join((result.stdout or "").splitlines()[-100:])
        raise RuntimeError(
            f"command failed with exit code {result.returncode}: {command!r}\n{tail}"
        )
    return result.stdout or ""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str, cwd: Path) -> str:
    return _run(
        [
            "git", "-c", f"safe.directory={cwd.resolve().as_posix()}",
            "-C", str(cwd), *args,
        ],
        timeout=300,
    ).strip()


def _verify_dependencies() -> dict:
    if not AUTHOR_VENDOR.exists():
        raise FileNotFoundError(
            "pinned ED_Lib checkout is missing; rerun the registered Stage-15d "
            "build preflight rather than substituting another implementation"
        )
    if _git("rev-parse", "HEAD", cwd=AUTHOR_VENDOR) != AUTHOR_COMMIT:
        raise RuntimeError("ED_Lib checkout is not at the registered author commit")
    if _git("status", "--porcelain", "--untracked-files=no", cwd=AUTHOR_VENDOR):
        raise RuntimeError("tracked ED_Lib author files were modified")
    observed = {name: _sha256(AUTHOR_VENDOR / name) for name in AUTHOR_HASHES}
    if observed != AUTHOR_HASHES:
        raise RuntimeError("ED_Lib source hashes do not match the registration")

    if not OPENCV_VENDOR.exists() or not OPENCV_INSTALL.exists():
        raise FileNotFoundError(
            "the pinned OpenCV preflight dependency is missing; do not replace it "
            "with an unregistered system package"
        )
    if _git("rev-parse", "HEAD", cwd=OPENCV_VENDOR) != OPENCV_COMMIT:
        raise RuntimeError("OpenCV checkout is not at the registered peeled commit")
    if _git("status", "--porcelain", "--untracked-files=no", cwd=OPENCV_VENDOR):
        raise RuntimeError("tracked OpenCV dependency files were modified")

    artifacts = [
        "zlib.lib", "libjpeg-turbo.lib", "libwebp.lib", "libpng.lib",
        "libtiff.lib", "libjasper.lib", "IlmImf.lib", "opencv_core3420.lib",
        "opencv_imgproc3420.lib", "opencv_imgcodecs3420.lib",
    ]
    artifact_hashes = {}
    for name in artifacts:
        path = OPENCV_INSTALL / "staticlib" / name
        if not path.exists():
            raise FileNotFoundError(f"preflighted OpenCV artifact missing: {path}")
        artifact_hashes[name] = _sha256(path)
    return {"author_hashes": observed, "opencv_artifact_hashes": artifact_hashes}


def _write_build_harness() -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    author = AUTHOR_VENDOR.resolve().as_posix()
    install = OPENCV_INSTALL.resolve().as_posix()
    dependencies = [
        ("opencv_zlib", "zlib.lib", ""),
        ("opencv_jpeg", "libjpeg-turbo.lib", ""),
        ("opencv_webp", "libwebp.lib", ""),
        ("opencv_png", "libpng.lib", "opencv_zlib"),
        ("opencv_tiff", "libtiff.lib", "opencv_zlib"),
        ("opencv_jasper", "libjasper.lib", ""),
        ("opencv_openexr", "IlmImf.lib", "opencv_zlib"),
        ("opencv_core", "opencv_core3420.lib", "opencv_zlib"),
        ("opencv_imgproc", "opencv_imgproc3420.lib", "opencv_core"),
        (
            "opencv_imgcodecs", "opencv_imgcodecs3420.lib",
            "opencv_core;opencv_imgproc;opencv_jpeg;opencv_webp;opencv_png;"
            "opencv_tiff;opencv_jasper;opencv_openexr;opencv_zlib",
        ),
    ]
    imports = [f'set(OPENCV_INSTALL "{install}")']
    for target, filename, links in dependencies:
        imports.extend([
            f"add_library({target} STATIC IMPORTED)",
            f"set_target_properties({target} PROPERTIES",
            f'  IMPORTED_LOCATION "${{OPENCV_INSTALL}}/staticlib/{filename}"',
        ])
        if links:
            imports.append(f'  INTERFACE_LINK_LIBRARIES "{links}"')
        imports.append(")")
    cmake = f'''cmake_minimum_required(VERSION 3.16)
cmake_policy(SET CMP0091 NEW)
project(stage15d_edpf_exporter LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
{chr(10).join(imports)}
set(AUTHOR_DIR "{author}")
add_executable(stage15d_edpf_export
  export.cpp
  "${{AUTHOR_DIR}}/ED.cpp"
  "${{AUTHOR_DIR}}/EDColor.cpp"
  "${{AUTHOR_DIR}}/EDPF.cpp"
)
target_include_directories(stage15d_edpf_export PRIVATE
  "${{AUTHOR_DIR}}" "${{OPENCV_INSTALL}}/include")
target_link_libraries(stage15d_edpf_export PRIVATE
  opencv_imgcodecs opencv_imgproc opencv_core)
'''
    source = r'''#include "EDPF.h"
#include <opencv2/imgcodecs.hpp>
#include <chrono>
#include <fstream>
#include <iostream>
#include <string>

int main(int argc, char** argv) {
    if (argc != 4) return 2;
    std::ifstream manifest(argv[1]);
    std::ofstream runtimes(argv[3]);
    if (!manifest || !runtimes) return 3;
    runtimes << "image_id,seconds,edge_pixels,total_pixels\n";
    std::string image_path;
    while (std::getline(manifest, image_path)) {
        if (image_path.empty()) continue;
        cv::Mat input = cv::imread(image_path, cv::IMREAD_GRAYSCALE);
        if (input.empty() || input.type() != CV_8UC1) return 4;
        auto started = std::chrono::steady_clock::now();
        EDPF detector(input);
        cv::Mat edges = detector.getEdgeImage();
        double seconds = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - started).count();
        if (edges.type() != CV_8UC1 || edges.size() != input.size()) return 5;
        cv::Mat invalid = (edges != 0) & (edges != 255);
        if (cv::countNonZero(invalid) != 0) return 6;
        size_t slash = image_path.find_last_of("/\\");
        size_t dot = image_path.find_last_of('.');
        std::string id = image_path.substr(slash + 1, dot - slash - 1);
        std::string output = std::string(argv[2]) + "/" + id + ".png";
        if (!cv::imwrite(output, edges)) return 7;
        runtimes << id << "," << seconds << "," << cv::countNonZero(edges)
                 << "," << edges.total() << "\n";
        std::cout << "STAGE15D_EDPF_EXPORT " << id << std::endl;
    }
    return 0;
}
'''
    (BUILD_DIR / "CMakeLists.txt").write_text(cmake, encoding="utf-8")
    (BUILD_DIR / "export.cpp").write_text(source, encoding="utf-8")


def _build_exporter() -> tuple[Path, str]:
    _write_build_harness()
    configure = _run([
        "cmake", "-S", str(BUILD_DIR), "-B", str(BUILD_DIR / "build"),
        "-DCMAKE_BUILD_TYPE=Release",
    ])
    build = _run([
        "cmake", "--build", str(BUILD_DIR / "build"), "--config", "Release",
        "--target", "stage15d_edpf_export",
    ], timeout=3600)
    candidates = [
        BUILD_DIR / "build" / "Release" / "stage15d_edpf_export.exe",
        BUILD_DIR / "build" / "stage15d_edpf_export.exe",
        BUILD_DIR / "build" / "stage15d_edpf_export",
    ]
    executable = next((path for path in candidates if path.exists()), None)
    if executable is None:
        raise FileNotFoundError("the exact EDPF export executable was not produced")
    return executable, "\n".join((configure + build).splitlines()[-40:])


def export_edpf_maps(image_dir: Path, output_dir: Path, *, split: str) -> dict:
    image_dir = image_dir.resolve()
    output_dir = output_dir.resolve()
    image_paths = sorted(image_dir.glob("*.jpg"))
    if not image_paths:
        raise RuntimeError(f"no BSDS JPG images found in {image_dir}")
    dependency_hashes = _verify_dependencies()
    executable, build_log_tail = _build_exporter()
    output_dir.mkdir(parents=True, exist_ok=True)
    image_manifest = output_dir / "input_manifest.txt"
    image_manifest.write_text(
        "\n".join(path.resolve().as_posix() for path in image_paths) + "\n",
        encoding="utf-8",
    )
    runtime_csv = output_dir / "per_image_runtime.csv"
    started = time.perf_counter()
    stdout = _run(
        [str(executable), str(image_manifest), str(output_dir), str(runtime_csv)],
        timeout=4 * 60 * 60,
    )
    elapsed = time.perf_counter() - started

    map_hashes = {}
    for image_path in image_paths:
        prediction_path = output_dir / f"{image_path.stem}.png"
        if not prediction_path.exists():
            raise RuntimeError(f"missing EDPF map: {prediction_path}")
        with Image.open(image_path) as image, Image.open(prediction_path) as prediction:
            if prediction.mode != "L" or prediction.size != image.size:
                raise RuntimeError(f"invalid EDPF map contract: {prediction_path}")
            values = set(prediction.getdata())
            if not values.issubset({0, 255}):
                raise RuntimeError(f"EDPF map is not native binary output: {prediction_path}")
        map_hashes[image_path.stem] = _sha256(prediction_path)
    (output_dir / "map_hashes.json").write_text(
        json.dumps(map_hashes, indent=2), encoding="utf-8"
    )
    with runtime_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != len(image_paths):
        raise RuntimeError("EDPF runtime table is incomplete")

    manifest = {
        "method": "EDPF (Akinlar and Topal, IJPRAI 2012)",
        "implementation_fidelity": (
            "exact unmodified author C++ detector with repository batch-I/O harness"
        ),
        "training_class": "strictly untrained; fixed author implementation",
        "author_repository": AUTHOR_REPOSITORY,
        "author_commit": AUTHOR_COMMIT,
        "author_license": "MIT",
        "author_hashes": dependency_hashes["author_hashes"],
        "opencv_dependency": {
            "repository": OPENCV_REPOSITORY,
            "version": OPENCV_VERSION,
            "tag_object": OPENCV_TAG_OBJECT,
            "commit": OPENCV_COMMIT,
            "artifact_hashes": dependency_hashes["opencv_artifact_hashes"],
        },
        "dataset": "BSDS500",
        "split": split,
        "bsds_ground_truth_read": False,
        "native_resolution": True,
        "input_decode": "OpenCV IMREAD_GRAYSCALE",
        "output": "native author CV_8UC1 binary map serialized unchanged as PNG",
        "parameter_policy": "no exposed parameters, fitting, search, or calibration",
        "n_maps": len(image_paths),
        "total_detector_seconds": sum(float(row["seconds"]) for row in rows),
        "total_export_wall_seconds": elapsed,
        "build_log_tail": build_log_tail,
        "stdout_tail": "\n".join(stdout.splitlines()[-30:]),
    }
    (output_dir / "export_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--split", default="val")
    args = parser.parse_args()
    export_edpf_maps(Path(args.image_dir), Path(args.output_dir), split=args.split)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
