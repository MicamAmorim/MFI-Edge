#!/usr/bin/env python3
"""Pre-freeze scientific evidence dossier from already existing metadata ONLY.

No archives, source pixels, GT, H5, F1, hash recomputation of descriptors,
fitting, rescreening, hypothesis tests or scientific auto-approval.
Produces a review dossier plus a proposal-only protocol diff. Does NOT
update protocol.json, frozen cohort, freeze approvals, or any test outcome.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(r"F:\MFI-Edge-Data\MultiCue")
WORK = DATA / "paper_a_completion"
PROTOCOL = ROOT / "docs/paper_a_confirmation/protocol.json"
P1 = ROOT / "docs/paper_a_confirmation/P1_DEVELOPMENT_RECIPE_UNATTESTED.json"
BIPED = ROOT / "results/local_dev/paper_a_confirmation_inventory/predata_audit/biped_train_after_visual_dedup_candidates.csv"
HISTORY = ROOT / "results/local_dev/paper_a_confirmation_inventory/predata_audit/historical_source_audit.json"
MULTI = DATA / "multicue_h5_anchored_sequence_candidates.csv"
PROPOSAL = WORK / "COHORT_PROPOSAL_220_NOT_CERTIFIED.csv"
P1_ORIGINAL = WORK / "devfit_20261116T031932_410335Z_recipe_UNATTESTED.json"
DOCS = {
    "P1": ROOT / "docs/paper_a_confirmation/P1_DEVELOPMENT_FIT_20261116.md",
    "BIPED": ROOT / "docs/paper_a_confirmation/HISTORICAL_BIPED_ADJUDICATION_20261115.md",
    "MultiCue": ROOT / "docs/paper_a_confirmation/MULTICUE_EXACT_MUTUAL_RESCREEN_RESULT_20261115.md",
    "Power": ROOT / "docs/paper_a_confirmation/SAMPLE_SIZE_CONDITIONAL_DECISION_20261115.md",
    "GT": ROOT / "docs/paper_a_confirmation/GT_EDGES_MULTIANNOTATOR_CONTRACT_PROPOSAL.md",
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            h.update(block)
    return h.hexdigest()


def metadata_json(p: Path) -> dict | None:
    if not p.is_file() or p.is_symlink() or p.stat().st_size > 4_000_000:
        return None
    obj = json.loads(p.read_text(encoding="utf-8"))
    return obj if isinstance(obj, dict) else None


def metadata_csv(p: Path) -> list[dict] | None:
    if not p.is_file() or p.is_symlink() or p.stat().st_size > 8_000_000:
        return None
    with p.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return None
        return list(reader)


def review_metadata(protocol: dict, recipe: dict, biped: list[dict],
                    multi: list[dict], proposal: list[dict] | None,
                    history: dict | None, p1_equal: bool | None) -> dict:
    if protocol.get("status") != "draft_not_frozen":
        # This script is intentionally only for pre-freeze documentation;
        # do not run a draft-protocol generator after a real freeze.
        raise ValueError("Refuse dossier generation from a non-draft protocol")
    if len(biped) != 198 or len({r["image_id"] for r in biped}) != 198:
        raise ValueError("BIPED dedup changed")
    if {"RGB_172", "RGB_222"} & {r["image_id"] for r in biped}:
        raise ValueError("Previously excluded BIPED duplicates present")
    if any(r.get("confirmatory_eligibility") !=
           "PENDING_HISTORICAL_AND_SCENE_LINEAGE_AUDIT" for r in biped):
        raise ValueError("BIPED candidate status not explicitly pending")
    if len(multi) != 100 or len({r["sequence_id"] for r in multi}) != 100:
        raise ValueError("MultiCue inventory changed")
    prefixes = {r["capture_prefix"] for r in multi}
    if len(prefixes) != 96 or "4113" not in prefixes:
        raise ValueError("MultiCue known history/layout mismatch")
    available = sorted(prefixes - {"4113"})
    if len(available) != 95:
        raise ValueError("Expected 95 provisional capture prefixes")
    # Reject a false/automatic "pass" in a DRAFT sample.
    planned_counts = {}
    if proposal is not None:
        if len(proposal) != 220:
            raise ValueError("Unexpected proposal size: not the pre-power-design 125+95")
        keys = {(r["dataset"], r["image_id"]) for r in proposal}
        if len(keys) != 220:
            raise ValueError("Repeated candidate in draft cohort")
        for r in proposal:
            if r.get("independence_review") != "pending" or \
               r.get("prior_exposure_review") != "pending":
                raise ValueError("Draft proposal has non-pending reviewer status")
            if r["dataset"] == "BIPED" and r["image_id"] in {"RGB_172", "RGB_222"}:
                raise ValueError("Confirmed BIPED duplicate in proposal")
            if r["dataset"] == "MultiCue" and r["scene_group"] == "4113":
                raise ValueError("Historically exposed MultiCue prefix in proposal")
            planned_counts[r["dataset"]] = planned_counts.get(r["dataset"], 0) + 1
        if planned_counts != {"BIPED": 125, "MultiCue": 95}:
            raise ValueError("Proposal composition changed")
        if len({(r["dataset"], r["scene_group"]) for r in proposal}) != 220:
            raise ValueError("Repeated provisional capture group in proposal")
    from src.paper_a_h1h2_inference_core import validate_fitted_recipe
    validate_fitted_recipe(recipe)
    overlaps = []
    for h in recipe.get("hypotheses", []):
        parts = [h.get("membership", {}).get("fit_provenance", {}),
                 h.get("candidate", {}).get("threshold_fit_provenance", {}),
                 h.get("control", {}).get("threshold_fit_provenance", {})]
        if h.get("id") == "H2":
            parts.append(h.get("candidate", {}).get("capacity_fit_provenance", {}))
        overlaps += [part.get("no_confirmatory_overlap_attested") for part in parts]
    if len(overlaps) != 7:
        raise ValueError("Unexpected P1 fitting record count; review")
    return {
        "status": "PRE_FREEZE_EVIDENCE_REVIEW_ONLY_NOT_AUTHORIZATION",
        "predata_scope": "Source/manifest metadata only; no protected image/GT or F1 read",
        "biped_candidates": 198,
        "biped_excluded_ids": ["RGB_172", "RGB_222"],
        "multi_sequences": 100,
        "multi_prefixes": 96,
        "multi_prefixes_provisionally_usable": len(available),
        "multi_excluded_prefix": "4113",
        "multi_gt_names_edges": 600,
        "multi_gt_names_boundaries": 500,
        "P1_structural_validity": "PASS_SYNTACTIC_ALGEBRAIC_ONLY",
        "P1_provenance_parts_without_overlap_attestation": sum(v is not True for v in overlaps),
        "P1_source_copy_sha256_verified_locally_now": p1_equal,
        "prior_history_report_available": history is not None,
        "history_report_status": history.get("status") if history else None,
        "history_report_branches": history.get("git_branches_checked") if history else None,
        "history_report_matches": len(history.get("metadata_candidate_matches", [])) if history else None,
        "cohort_proposal_present": proposal is not None,
        "cohort_proposal_counts": planned_counts,
        "declared_protocol_target_N": protocol.get("cohort", {}).get("target_n_independent_images"),
        "proposed_target_N": 220,
        "simulated_joint_power_rho_020": 0.823,
        "primary_task_proposal": "MultiCue edges: six separately matched GTs/one capture",
        "biped_gt_proposal": "one GT per image",
        "actual_GT_pixel_encoding_known": False,
        "frozen": False,
        "confirmatory_H1_H2_test_run": False,
        "human_or_independent_approval_issued": False,
    }


def proposed_protocol(protocol: dict) -> dict:
    obj = json.loads(json.dumps(protocol))
    obj["status"] = "draft_not_frozen"
    obj["freeze_commit"] = None
    obj["confirmatory_outcomes_opened"] = False
    obj["cohort"]["dataset_names"] = ["BIPED", "MultiCue"]
    obj["cohort"]["target_n_independent_images"] = 220
    obj["cohort"]["selection"] = (
        "PROPOSAL: 125 hash-sorted BIPED from audited independent candidate scenes; "
        "95 MultiCue, one per eligible capture prefix, excluding 4113. "
        "NO cohort selection until scene/prior-exposure review passes. "
        "If fewer than 95 MultiCue groups, rerun power for amended composition BEFORE freeze."
    )
    obj["cohort"]["power_analysis"] = (
        "PROPOSAL: synthetic joint power=0.823 under homogeneous |rho|=0.20, "
        "N=125+95, assuming true independent scenes. NOT empirical power, "
        "NOT valid if domain composition changes."
    )
    obj["measures"]["unit"] = "PROPOSED independent capture/scene, never annotator"
    obj["measures"]["ground_truth_contract_proposal"] = {
        "BIPED": "one original edge-map GT, actual encoding unverified",
        "MultiCue": "6 distinct edges GT per left final frame; boundaries exploratory only",
        "matching": "native geometry, 0.0075 diagonal, exact one-to-one, not official Berkeley",
        "aggregation": "mean per-reference F1 after matching, one paired delta per capture",
        "encoding": "PENDING INDEPENDENT VALIDATION on out-of-cohort reference",
        "empty_gt": "fail-closed and escalate; no silent post-outcome exclusion",
    }
    obj["inference"]["test"] = (
        "PROPOSAL: one-sided within-domain Spearman midranks, "
        "weighted mean rho with weights n_d-1, 100000 outcome "
        "permutations separately within each domain."
    )
    obj["inference"]["ties"] = (
        "Midranks within each domain; constant maps/undefined Spearman fail closed, "
        "pre-resolve policy from development-only data before freeze."
    )
    obj["inference"]["multiplicity"] = "Holm step-down across two primary tests"
    obj["pre_freeze_revision_disclaimer"] = (
        "REVIEW-ONLY draft; cannot be used as protocol.json; no reviewer approval."
    )
    return obj


def create_dossier(root: Path = ROOT, data: Path = DATA, work: Path = WORK) -> dict:
    # Defaults match existing local workstation and produce only review files.
    protocol = metadata_json(root / "docs/paper_a_confirmation/protocol.json")
    recipe_path = root / "docs/paper_a_confirmation/P1_DEVELOPMENT_RECIPE_UNATTESTED.json"
    recipe = metadata_json(recipe_path)
    biped = metadata_csv(root / "results/local_dev/paper_a_confirmation_inventory/predata_audit/biped_train_after_visual_dedup_candidates.csv")
    multi = metadata_csv(data / "multicue_h5_anchored_sequence_candidates.csv")
    proposal = metadata_csv(work / "COHORT_PROPOSAL_220_NOT_CERTIFIED.csv")
    history = metadata_json(root / "results/local_dev/paper_a_confirmation_inventory/predata_audit/historical_source_audit.json")
    if protocol is None or recipe is None or biped is None or multi is None:
        raise ValueError("Required existing metadata missing; do not reprocess images")
    old_p1 = work / "devfit_20261116T031932_410335Z_recipe_UNATTESTED.json"
    same = sha256(old_p1) == sha256(recipe_path) if old_p1.is_file() else None
    review = review_metadata(protocol, recipe, biped, multi, proposal, history, same)
    review["created_utc"] = datetime.now(timezone.utc).isoformat()
    review["protocol_sha256"] = sha256(root / "docs/paper_a_confirmation/protocol.json")
    review["versioned_recipe_sha256"] = sha256(recipe_path)
    review["biped_candidate_manifest_sha256"] = sha256(root / "results/local_dev/paper_a_confirmation_inventory/predata_audit/biped_train_after_visual_dedup_candidates.csv")
    review["multicue_index_sha256"] = sha256(data / "multicue_h5_anchored_sequence_candidates.csv")
    review["cohort_proposal_sha256"] = sha256(work / "COHORT_PROPOSAL_220_NOT_CERTIFIED.csv") if proposal is not None else None
    review["local_revision"] = "NO FREEZE OR CONFIRMATORY GT ACCESS"

    review["blockers"] = [
        "BIPED: operational Stage13c log/exposure and capture scene independence require independent adjudication. Historical source audit absence of matches is not proof.",
        "MultiCue: only 4113 overlap ruled out; independence beyond final-left frames and across scene prefixes requires review.",
        "P1: development-only fit structurally valid; 7 fitting provenance attestations are still unapproved. Do not promote by copying files.",
        "Ground truth: MultiCue edges and BIPED actual pixel encoding, annotator semantics, empty-mask policy and decoder must be independently validated from non-confirmatory material.",
        "Design: target 220 vs current protocol target 150, chosen within-domain estimator, rho minimum, missing/tied-policy must be reviewed and frozen in Git before access.",
        "Independent sign-off of code hash, frozen per-image manifest, protocol/recipe/approval required BEFORE accessing protected GT/F1.",
    ]
    work.mkdir(parents=True, exist_ok=True)
    out_json = work / "REVISAO_CIENTIFICA_PRE_FREEZE.json"
    out_md = work / "DOSSIE_CIENTIFICO_PRE_FREEZE.md"
    out_proposal = work / "PROTOCOLO_220_PROPOSTA_NAO_CONGELADO.json"
    lines = [
        "# Paper A — dossiê científico consolidado (sem abrir GT)",
        "", "**Status:** EM REVISÃO, NÃO CONGELADO. Este arquivo não autoriza resultados confirmatórios.",
        "", "## Evidências já verificadas",
        "", "- BIPED: 200 imagens iniciais; 2 descartadas (RGB_172 e RGB_222); 198 candidatas sem certificação de independência.",
        "- MultiCue: 100 sequências, 96 prefixos; prefixo 4113 excluído pela sobreposição UDED 09-MDBD-1C; no máximo 95 candidatos.",
        "- Auditoria geométrica histórica: 2.700 pares UDED × MultiCue concluídos, sem necessidade de reexecutar (ver documento versionado).",
        "- Nomes de anotação: 600 edges e 500 boundaries no MultiCue; conteúdo dos GTs não validado.",
        "- Receita P1 UDED-14: equações, Möbius/Choquet e limiares passaram pelo contrato estrutural; 7 provas de não sobreposição continuam sem atestado.",
        "- Avaliador F1 sintético: 10 testes passaram segundo execução já fornecida; não prova a codificação GT real.",
        "- Poder conjunto simulado, não observado: para 125 BIPED + 95 MultiCue, rho=0,20 homogêneo, 82,3%.",
        "", "## Checagens no material da workstation",
        "", "- Hash da receita P1 original F: versus cópia Git: " + (
            "IDÊNTICOS (comparação desta execução)" if same is True else
            "DIFERENTES — BLOQUEADO" if same is False else "original não acessível nesta execução"
        ),
        "- Auditoria de código BIPED histórica disponível: " + ("sim" if history else "não; consultar relatório original"),
        "- Planilha 125+95 provisória: " + ("presente; com 220 revisões pendentes" if proposal else "não localizada"),
        "- Protocolo atual: " + str(protocol["status"]) + "; N declarado " +
          str(protocol["cohort"]["target_n_independent_images"]) + "; N proposto 220.",
        "", "## Gates e decisões que não podem ser marcadas automaticamente",
        "",
    ]
    lines.extend("- [ ] " + item for item in review["blockers"])
    lines += [
        "", "## Recomendação do revisor técnico de código",
        "", "**NO-GO para primeira abertura de GT confirmatório.** A execução não falhou;",
        "as garantias de independência e semântica não estão documentadas em nível suficiente.",
        "O próximo ato é revisão independente da coorte/decodificador e freeze antes",
        "do primeiro cálculo real de F1 em BIPED ou MultiCue. Não usar resultados",
        "que venham de qualquer inspeção antecipada do conjunto protegido.",
        "", "## Referências rastreáveis",
        "", "- docs/paper_a_confirmation/P1_DEVELOPMENT_FIT_20261116.md",
        "- docs/paper_a_confirmation/HISTORICAL_BIPED_ADJUDICATION_20261115.md",
        "- docs/paper_a_confirmation/MULTICUE_EXACT_MUTUAL_RESCREEN_RESULT_20261115.md",
        "- docs/paper_a_confirmation/GT_EDGES_MULTIANNOTATOR_CONTRACT_PROPOSAL.md",
        "- docs/paper_a_confirmation/SAMPLE_SIZE_CONDITIONAL_DECISION_20261115.md",
        "- https://huggingface.co/datasets/Serrelab/multicue-boundary-detection",
        "", "### Arquivos do pacote",
        "", "- REVISAO_CIENTIFICA_PRE_FREEZE.json — verificações/pendências legíveis por máquina",
        "- PROTOCOLO_220_PROPOSTA_NAO_CONGELADO.json — proposta de edição; NÃO é o protocolo aprovado",
        "- COHORT_PROPOSAL_220_NOT_CERTIFIED.csv — seleção apenas provisória, SEM aprovação",
        "", "Todos os resultados reais H1/H2 continuam não calculados.",
    ]
    out_json.write_text(json.dumps(review, indent=2, ensure_ascii=False), encoding="utf-8")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out_proposal.write_text(json.dumps(proposed_protocol(protocol), indent=2, ensure_ascii=False), encoding="utf-8")
    return {"status": review["status"], "output": str(out_md),
            "protocol_proposal": str(out_proposal),
            "blockers": len(review["blockers"]),
            "P1_local_copy_sha256_equal": same,
            "actual_GT_read": False, "auto_approval": False}


def main() -> int:
    print(json.dumps(create_dossier(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
