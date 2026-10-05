from __future__ import annotations

from pathlib import Path
import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
import webbrowser

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "webui"


def run(cmd, cwd=None, env=None):
    print("+", " ".join(map(str, cmd)), flush=True)
    return subprocess.Popen(cmd, cwd=cwd, env=env)


def main():
    ap = argparse.ArgumentParser(description="Start MFI-Edge local API + Next.js WebUI")
    ap.add_argument("--no-install", action="store_true", help="Do not run npm install when node_modules is missing")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--api-port", type=int, default=8000)
    ap.add_argument("--web-port", type=int, default=3000)
    args = ap.parse_args()

    npm = shutil.which("npm")
    if not npm:
        raise SystemExit("Node.js/npm was not found. Install Node.js 20+ and run again.")

    if not (WEB / "node_modules").exists() and not args.no_install:
        print("Installing WebUI dependencies (first run only)...", flush=True)
        subprocess.check_call([npm, "install"], cwd=WEB)

    env = os.environ.copy()
    env["NEXT_PUBLIC_MFI_API"] = f"http://127.0.0.1:{args.api_port}"
    env.setdefault("MFI_WEB_ORIGINS", f"http://localhost:{args.web_port},http://127.0.0.1:{args.web_port}")

    api = run([
        sys.executable, "-m", "uvicorn", "desktop_api:app",
        "--host", "127.0.0.1", "--port", str(args.api_port),
    ], cwd=ROOT, env=env)
    web = run([
        npm, "run", "dev", "--", "--hostname", "127.0.0.1", "--port", str(args.web_port),
    ], cwd=WEB, env=env)

    url = f"http://127.0.0.1:{args.web_port}"
    print(f"\nMFI-Edge WebUI: {url}")
    print(f"MFI-Edge API:   http://127.0.0.1:{args.api_port}/docs")
    print("Press Ctrl+C to stop both processes.\n")

    if not args.no_browser:
        time.sleep(2.0)
        webbrowser.open(url)

    try:
        while True:
            if api.poll() is not None:
                raise SystemExit(f"API exited with code {api.returncode}")
            if web.poll() is not None:
                raise SystemExit(f"WebUI exited with code {web.returncode}")
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        for p in (web, api):
            if p.poll() is None:
                try:
                    if os.name == "nt":
                        p.terminate()
                    else:
                        p.send_signal(signal.SIGTERM)
                except Exception:
                    pass
        for p in (web, api):
            try:
                p.wait(timeout=5)
            except Exception:
                if p.poll() is None:
                    p.kill()


if __name__ == "__main__":
    main()
