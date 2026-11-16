#!/usr/bin/env python3
"""Validate already existing out-of-cohort GT encoding evidence and prepare
an UNSIGNED pre-freeze protocol preview, not a freeze or authorization.

Run directly as a script from PowerShell; avoids Windows PowerShell 5.1
quote mangling of an embedded multiline 'python -c' argument.
No protected GT, H5, maps, outcomes, training, F1, or new signoff.
"""
from __future__ import annotations

import json
from freeze_paper_a_from_independent_review import (
    prepare, verified_nonconfirmatory_gt_v2_evidence,
)
from paper_a_freeze_guard import GT_POLICY_V2


def main() -> int:
    samples = verified_nonconfirmatory_gt_v2_evidence()
    plan = prepare()
    if plan.get("scientific_signoff_issued") is not False:
        raise RuntimeError("Unexpected approval from a prefreeze preparation")
    if plan.get("status") != "REVIEWED_FREEZE_READY_ONLY_WHEN_SIGNED_AND_EVIDENCED":
        raise RuntimeError("Unexpected protocol preview status")
    print(json.dumps({
        "status": plan["status"],
        "gt_policy": GT_POLICY_V2,
        "gt_metadata_sha256": samples,
        "preview": plan["reviewed_protocol_candidate"],
        "template": plan["review_template"],
        "approved": False,
        "protected_confirmatory_GT_accessed": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
