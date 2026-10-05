from __future__ import annotations

from pathlib import Path
import argparse
import io
import shutil
import time
import urllib.request
import zipfile

URL = "https://github.com/xavysp/UDED/archive/refs/heads/main.zip"


def download(out: Path, retries: int = 3):
    out = out.resolve()
    if (out / "test_pair.lst").exists():
        print(f"UDED already ready at {out}", flush=True)
        return out

    if out.exists():
        shutil.rmtree(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    last = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(URL, headers={"User-Agent": "MFI-Edge/Stage8"})
            with urllib.request.urlopen(req, timeout=90) as resp:
                payload = resp.read()
            with zipfile.ZipFile(io.BytesIO(payload)) as zf:
                names = zf.namelist()
                root = names[0].split("/", 1)[0]
                tmp = out.parent / f".{out.name}-extract"
                if tmp.exists():
                    shutil.rmtree(tmp)
                zf.extractall(tmp)
                extracted = tmp / root
                shutil.move(str(extracted), str(out))
                shutil.rmtree(tmp, ignore_errors=True)
            if not (out / "test_pair.lst").exists():
                raise FileNotFoundError(f"downloaded archive has no test_pair.lst at {out}")
            print(f"UDED downloaded to {out} ({len(payload)} bytes)", flush=True)
            return out
        except Exception as exc:
            last = exc
            print(f"UDED download attempt {attempt}/{retries} failed: {exc}", flush=True)
            if out.exists():
                shutil.rmtree(out, ignore_errors=True)
            time.sleep(2 * attempt)
    raise RuntimeError(f"Could not prepare UDED after {retries} attempts: {last}")


def prepare_uded(out: Path, retries: int = 3):
    """Backward/forward compatible alias used by local and cloud runners."""
    return download(Path(out), retries=retries)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/UDED")
    ap.add_argument("--retries", type=int, default=3)
    args = ap.parse_args()
    download(Path(args.out), args.retries)


if __name__ == "__main__":
    main()
