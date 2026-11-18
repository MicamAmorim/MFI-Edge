"""Human-readable comparison and traceable limitations."""
from __future__ import annotations
from pathlib import Path
from .context import Context,save

def publish(ctx:Context,report:dict)->tuple[Path,Path]:
    output=ctx.work/"reports"
    json_file=output/"paper_a_reproduction.json"
    md_file=output/"paper_a_reproduction.md"
    save(json_file,report)
    paragraphs=[
        "# Paper A — community reproduction report",
        "",
        "**Implementation status:** EXPERIMENTAL / NOT END-TO-END VALIDATED.",
        "",
        "**Mode:** "+report["mode"],
        "",
        "**Execution result:** "+report["status"],
        "",
        "**Repository commit:** "+report["commit"],
        "",
        "## Pipeline stages",
        "",
        "| Stage | Status |",
        "|---|---|",
    ]
    for name,value in report.get("stages",{}).items():
        status=value.get("status","completed") if isinstance(value,dict) else str(value)
        paragraphs.append("| "+name+" | "+str(status).replace("|","/")+" |")
    paragraphs+=["","## Confirmatory numerical comparison","",
                 "| Hypothesis | rho recomputed | mean delta F1 recomputed | Holm p (published unless deep mode) |",
                 "|---|---:|---:|---:|"]
    stats=report.get("stages",{}).get("confirmatory_numeric",{})
    for item in stats.get("hypotheses",[]):
        p=item.get("holm_p_recomputed",item.get("published_holm_p_NOT_RECOMPUTED_UNLESS_DEEP"))
        paragraphs.append(f"| {item['hypothesis']} | {item['rho_recomputed']:.9f} | {item['mean_delta_F1_recomputed']:+.9f} | {p:.9f} |")
    paragraphs+=["","## Scientific interpretation and limitations","",
        "- The modular code does not have a certified end-to-end reproduction.",
        "- Verify mode compares archival numeric data; it does NOT regenerate descriptors or GT matching.",
        "- Stage23 uses GT only in authorized exploratory development. BSDS500 validation is not protected blind test.",
        "- Stage24 uses a distinct protocol and its original legacy executor may be workstation-specific.",
        "- H1 and H2 original image-level confirmation was frozen locally and depends on byte-pinned images, scene reviews and historical source hashes.",
        "- BIPED48 is secondary and is NEVER counted in H1/H2 primary p-values.",
        "- An AI reviewer is not equivalent to independent human peer review.",
        "- Hash mismatch, missing scientific data, or different evaluators must not be silently bypassed.",
        "- Reproducing significant H1 correlation does not establish a better mean F1 or a working adaptive selector.",
        "",
        "## Errors and missing prerequisites",""]
    if report.get("errors"):
        paragraphs.extend(["- "+str(x) for x in report["errors"]])
    else:
        paragraphs.append("- No reported failure within the invoked steps (not a guarantee of full reproduction).")
    paragraphs+=["","See reproduction/README.md and the original scientific sources for the full scope.",""]
    md_file.parent.mkdir(parents=True,exist_ok=True)
    md_file.write_text("\n".join(paragraphs),encoding="utf-8")
    return json_file,md_file
