#!/usr/bin/env python3
"""ONLY generate an unsigned N219 scientific-freeze preview; never freeze.

A dedicated Python entrypoint avoids fragile PowerShell -> python -c quoting.
Importing the historical freeze module does not execute its CLI; ONLY its
prepare() function is called, after checking that no signed review/freeze
approval exists. No confirmatory outcomes, images, GT, H5 or F1 are opened.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from freeze_paper_a_from_independent_review import (
    PROTOCOL, SIGNED, WORK, prepare,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-import-only",
        action="store_true",
        help="Validate script imports; do not read metadata or generate files",
    )
    args = parser.parse_args()
    if args.check_import_only:
        print("A219_PREVIEW_IMPORTS_OK_NO_ACTION")
        return 0

    if SIGNED.exists() or (WORK / "freeze_approval.json").exists():
        raise PermissionError(
            "Scientific review/signoff or freeze approval already exists; "
            "no unsigned preview can be regenerated"
        )
    if not PROTOCOL.is_file() or PROTOCOL.is_symlink():
        raise FileNotFoundError("Active versioned scientific protocol missing/unsafe")
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    if (
        protocol.get("status") != "draft_not_frozen"
        or protocol.get("confirmatory_outcomes_opened") is not False
    ):
        raise PermissionError(
            "Active scientific protocol is not an untouched, unfrozen draft"
        )
    result = prepare()  # NEVER attempt_freeze()
    if (
        result.get("scientific_signoff_issued") is not False
        or result.get("status")
        != "REVIEWED_FREEZE_READY_ONLY_WHEN_SIGNED_AND_EVIDENCED"
    ):
        raise PermissionError("Unsigned A219 preview returned an unexpected state")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
