#!/usr/bin/env bash
# Experimental Paper A wrapper; historical scientific code stays unchanged.
set -euo pipefail
HERE="$(cd -- "$(dirname -- "$0")" && pwd)"
cd "$HERE"
PYTHON_CMD=python3
if command -v python3.12 >/dev/null 2>&1; then PYTHON_CMD=python3.12; fi
if ! command -v "$PYTHON_CMD" >/dev/null 2>&1; then
  echo "Python 3.12+ not found; install Python with venv and pip." >&2
  exit 1
fi
VENV="$HERE/.venv-paper-a"
if [ ! -x "$VENV/bin/python" ]; then "$PYTHON_CMD" -m venv "$VENV"; fi
"$VENV/bin/python" -m pip install -r reproduction/requirements.txt
exec "$VENV/bin/python" -m reproduction.main "$@"
