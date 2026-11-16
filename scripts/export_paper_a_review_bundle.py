#!/usr/bin/env python3
"""Paper A prefreeze metadata-only review bundle (NO GT, pixels, caches).

Whitelists exact known inventory/lineage/dossier files; never recursively
discovers data. No reading of archive, protected masks, H5 or F1. Includes
both SHA256 evidence and conspicuous 'NOT FROZEN' metadata.
"""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(r"F:\MFI-Edge-Data\MultiCue")
WORK = DATA / "paper_a_completion"
MAX_FILE_SIZE = 9_000_000
FILES = {
    "review/DOSSIE_CIENTIFICO_PRE_FREEZE.md": ("work", "DOSSIE_CIENTIFICO_PRE_FREEZE.md"),
    "review/REVISAO_CIENTIFICA_PRE_FREEZE.json": ("work", "REVISAO_CIENTIFICA_PRE_FREEZE.json"),
    "review/PROTOCOLO_220_PROPOSTA_NAO_CONGELADO.json": ("work", "PROTOCOLO_220_PROPOSTA_NAO_CONGELADO.json"),
    "review/COHORT_PROPOSAL_220_NOT_CERTIFIED.csv": ("work", "COHORT_PROPOSAL_220_NOT_CERTIFIED.csv"),
    "review/ONE_COMMAND_STATUS.json": ("work", "ONE_COMMAND_STATUS.json"),
    "review/NEXT_ACTIONS.md": ("work", "NEXT_ACTIONS.md"),
    "review/LAST_STATUS.json": ("work", "LAST_STATUS.json"),
    "review/signoff/NONCONFIRMATORY_GT_ENCODING_EVIDENCE.json": ("work", "scientific_signoff/NONCONFIRMATORY_GT_ENCODING_EVIDENCE.json"),
    "review/signoff/GT_PIXEL_ENCODING_DETAIL_PRE_FREEZE_v1.json": ("work", "scientific_signoff/GT_PIXEL_ENCODING_DETAIL_PRE_FREEZE_v1.json"),
    "review/signoff/GT_PIXEL_ENCODING_REVIEW_REQUIRED.md": ("work", "scientific_signoff/GT_PIXEL_ENCODING_REVIEW_REQUIRED.md"),
    "science/PARECER_CODEX_DUPLA_AUDITORIA_20261116.md": ("root", "docs/paper_a_confirmation/PARECER_CODEX_DUPLA_AUDITORIA_20261116.md"),
    "review/signoff/REVIEW_220_IMAGES_PENDING.csv": ("work", "scientific_signoff/REVIEW_220_IMAGES_PENDING.csv"),
    "review/signoff/REVIEWER_DECISION_REQUIRED.md": ("work", "scientific_signoff/REVIEWER_DECISION_REQUIRED.md"),
    "review/signoff/SIGNOFF_READINESS_NOT_APPROVAL.json": ("work", "scientific_signoff/SIGNOFF_READINESS_NOT_APPROVAL.json"),
    "review/signoff/P1_LINEAGE_METADATA_CROSSCHECK_NOT_APPROVED.json": ("work", "scientific_signoff/P1_LINEAGE_METADATA_CROSSCHECK_NOT_APPROVED.json"),
    "recipe/P1_DEVELOPMENT_RECIPE_UNATTESTED.json": ("root", "docs/paper_a_confirmation/P1_DEVELOPMENT_RECIPE_UNATTESTED.json"),
    "recipe/P1_DEVELOPMENT_FIT_20261116.md": ("root", "docs/paper_a_confirmation/P1_DEVELOPMENT_FIT_20261116.md"),
    "protocol/protocol_DRAFT.json": ("root", "docs/paper_a_confirmation/protocol.json"),
    "history/HISTORICAL_BIPED_ADJUDICATION.md": ("root", "docs/paper_a_confirmation/HISTORICAL_BIPED_ADJUDICATION_20261115.md"),
    "history/BIPED_visual_duplicate_decisions.csv": ("root", "docs/paper_a_confirmation/visual_duplicate_decisions.csv"),
    "history/BIPED_visual_dedup_summary.json": ("root", "results/local_dev/paper_a_confirmation_inventory/predata_audit/visual_dedup_summary.json"),
    "history/BIPED_stage13c_execution_summary.json": ("root", "results/automation/stage13c_biped_preflight/summary.json"),
    "history/historical_source_audit.json": ("root", "results/local_dev/paper_a_confirmation_inventory/predata_audit/historical_source_audit.json"),
    "history/BIPED_198_candidates.csv": ("root", "results/local_dev/paper_a_confirmation_inventory/predata_audit/biped_train_after_visual_dedup_candidates.csv"),
    "history/MULTICUE_EXACT_MUTUAL_RESCREEN_RESULT.md": ("root", "docs/paper_a_confirmation/MULTICUE_EXACT_MUTUAL_RESCREEN_RESULT_20261115.md"),
    "history/multicue_h5_sequence_summary.json": ("data", "multicue_h5_anchored_sequence_summary.json"),
    "history/multicue_100_sequence_names.csv": ("data", "multicue_h5_anchored_sequence_candidates.csv"),
    "history/multicue_annotation_task_name_contract.json": ("data", "multicue_annotation_task_name_contract_predata.json"),
    "history/multicue_source_frames_only_manifest.csv": ("data", "multicue_source_frames_only_manifest.csv"),
    "history/multicue_source_frames_only_summary.json": ("data", "multicue_source_frames_only_summary.json"),
    "history/multicue_image_only_overlap_summary.json": ("data", "multicue_image_only_overlap_summary.json"),
    "science/SAMPLE_SIZE_CONDITIONAL_DECISION.md": ("root", "docs/paper_a_confirmation/SAMPLE_SIZE_CONDITIONAL_DECISION_20261115.md"),
    "science/GT_EDGES_MULTIANNOTATOR_CONTRACT_PROPOSAL.md": ("root", "docs/paper_a_confirmation/GT_EDGES_MULTIANNOTATOR_CONTRACT_PROPOSAL.md"),
    "science/GT_PIXEL_ENCODING_PROSPECTIVE_v2_NOT_APPROVED.md": ("root", "docs/paper_a_confirmation/GT_PIXEL_ENCODING_PROSPECTIVE_v2_NOT_APPROVED.md"),
    "science/PARECER_CONSOLIDADO_PARA_FREEZE_20261116.md": ("root", "docs/paper_a_confirmation/PARECER_CONSOLIDADO_PARA_FREEZE_20261116.md"),
}
REQUIRED = {
    "review/DOSSIE_CIENTIFICO_PRE_FREEZE.md",
    "review/REVISAO_CIENTIFICA_PRE_FREEZE.json",
    "review/COHORT_PROPOSAL_220_NOT_CERTIFIED.csv",
    "recipe/P1_DEVELOPMENT_RECIPE_UNATTESTED.json",
    "protocol/protocol_DRAFT.json",
    "review/signoff/REVIEW_220_IMAGES_PENDING.csv",
    "review/signoff/REVIEWER_DECISION_REQUIRED.md",
    "review/signoff/SIGNOFF_READINESS_NOT_APPROVAL.json",
}


def assemble(root: Path = ROOT, data: Path = DATA, work: Path = WORK) -> dict:
    bases = {"root": root, "data": data, "work": work}
    if not all(Path(p).is_dir() for p in bases.values()):
        raise ValueError("Expected ROOT/F:/WORK directories are missing")
    if not isinstance(FILES, dict) or not REQUIRED.issubset(FILES):
        raise ValueError("Bundle allowlist incomplete")
    items, missing = {}, []
    for dest, (label, subpath) in FILES.items():
        if Path(dest).is_absolute() or ".." in Path(dest).parts:
            raise ValueError("Unsafe zip destination")
        source = (bases[label] / subpath)
        if (not source.is_file() or source.is_symlink() or
                source.stat().st_size > MAX_FILE_SIZE):
            if dest in REQUIRED:
                raise ValueError("Missing or unsafe required review input: " + str(source))
            missing.append(dest)
            continue
        raw = source.read_bytes()
        # Strict: only known small UTF-8 text artifacts can be copied.
        raw.decode("utf-8-sig")
        if not raw:
            raise ValueError("Empty metadata file: " + str(source))
        items[dest] = (raw, hashlib.sha256(raw).hexdigest())
    work.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "PRE_FREEZE_METADATA_REVIEW_ONLY_NOT_CERTIFIED",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "no_GT_H5_original_images_descriptor_maps_or_F1_included": True,
        "no_scientific_approval": True,
        "contained_file_sha256": {key: entry[1] for key, entry in sorted(items.items())},
        "optional_metadata_missing": missing,
        "read_scope": "Only pre-listed small UTF-8 CSV, MD and JSON metadata/lineage files",
    }
    archive = work / "PaperA_PRE_FREEZE_REVIEW_ONLY.zip"
    temporary = work / "PaperA_PRE_FREEZE_REVIEW_ONLY.zip.part"
    if temporary.exists():
        temporary.unlink()
    with zipfile.ZipFile(temporary, "x", compression=zipfile.ZIP_DEFLATED) as handle:
        for dest, (data_bytes, _) in sorted(items.items()):
            handle.writestr(dest, data_bytes)
        handle.writestr("MANIFEST.json", json.dumps(report, indent=2, ensure_ascii=False))
    with zipfile.ZipFile(temporary) as handle:
        for dest, (_, digest) in items.items():
            if hashlib.sha256(handle.read(dest)).hexdigest() != digest:
                raise RuntimeError("ZIP integrity verification failed: " + dest)
    temporary.replace(archive)
    return {
        "status": report["status"],
        "path": str(archive),
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "files_count": len(items),
        "optional_metadata_missing": missing,
    }


if __name__ == "__main__":
    print(json.dumps(assemble(), ensure_ascii=False, indent=2))
