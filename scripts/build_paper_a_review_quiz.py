#!/usr/bin/env python3
"""Create a fully local Paper A review quiz from SHA-verified ORIGINAL images.

198 BIPED train candidates + the 95 proposed MultiCue captures = 293
original-image thumbnails. This process NEVER reads ground truth, masks, H5,
descriptor maps, F1, predictions, scientific outcomes or freeze approval.
It never chooses a new cohort, writes signoffs or publishes any images to Git.
"""
from __future__ import annotations

from collections import Counter
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil

from PIL import Image, ImageOps, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
DATA=Path(r"F:\MFI-Edge-Data\MultiCue")
WORK=DATA/"paper_a_completion"
SIGNOFF=WORK/"scientific_signoff"
FRONT=ROOT/"tools/paper_a_revisao"
BIPED=ROOT/"datasets/BIPEDv2/edges/imgs/train/rgbr/real"
MULTICUE=DATA/"source_frames_only"
CANDIDATES=ROOT/"results/local_dev/paper_a_confirmation_inventory/predata_audit/biped_train_after_visual_dedup_candidates.csv"
REVIEW=SIGNOFF/"REVIEW_220_IMAGES_PENDING.csv"
P1=SIGNOFF/"P1_LINEAGE_METADATA_CROSSCHECK_NOT_APPROVED.json"
TEMPLATE=SIGNOFF/"FINAL_INDEPENDENT_REVIEW.template.json"
OUT=SIGNOFF/"QUIZ_VISUAL_LOCAL_293"
EXPECTED_GROUPS=[
 ["RGB_236","RGB_241","RGB_238","RGB_240","RGB_242"],
 ["RGB_256","RGB_258","RGB_255","RGB_257"],
 ["RGB_031","RGB_030","RGB_032","RGB_028"],
 ["RGB_188","RGB_184","RGB_185"],
 ["RGB_220","RGB_221"],
 ["RGB_022","RGB_021"],
 ["RGB_013","RGB_014"],
 ["RGB_147","RGB_146"],
 ["RGB_088","RGB_093"],
 ["RGB_091","RGB_089"],
 ["RGB_104","RGB_103"],
 ["RGB_105","RGB_106"],
 ["RGB_023","RGB_024"],
 ["RGB_068","RGB_069"],
 ["RGB_208","RGB_209"],
 ["RGB_197","RGB_196"],
 ["RGB_217","RGB_218"],
 ["RGB_251","RGB_249"],
 ["RGB_112","RGB_113"],
 ["RGB_194","RGB_193"],
 ["RGB_115","RGB_114"],
 ["RGB_176","RGB_177"],
]
SHA64=re.compile(r"^[a-f0-9]{64}$")
IMAGE_BASE=re.compile(r"^[A-Za-z0-9_-]+\.(jpg|jpeg|png|bmp)$",re.I)
REVIEW_COLUMNS=("dataset","image_id","relative_path","image_sha256",
 "independence_review","prior_exposure_review","scene_group","notes",
 "reviewer_independence_decision","reviewer_prior_exposure_decision",
 "evidence_for_both_decisions","reviewer_name","reviewed_utc","historical_attention")
SCIENCE=[
 ("GT_BIPED","GT BIPED: 254/255","Os GT BIPED test fora da coorte apresentaram uint8 {0,254,255}. Interpretar 254/255 como borda exige justificativa documental.",
  "É defensável interpretar 254 e 255 como bordas, com evidência primária para esta versão do BIPED?",
  "GT_PIXEL_ENCODING_DETAIL_PRE_FREEZE_v1.json; GT_PIXEL_ENCODING_PROSPECTIVE_v2_NOT_APPROVED.md"),
 ("GT_MULTICUE","GT MultiCue: 65535","12 amostras do grupo excluído 4113 tinham uint16 {0,65535}; GT de confirmação permanece fechado.",
  "A semântica 65535 como borda foi justificada documentalmente para a edição do MultiCue?",
  "GT_PIXEL_ENCODING_DETAIL_PRE_FREEZE_v1.json; documentação de origem"),
 ("GT_MULTIANNOTATOR","Seis anotações por captura","A proposta agrega os seis F1 de edges por captura MultiCue, sem pseudorreplicação.",
  "A unidade amostral e a média dos seis F1 foram justificadas antes de ver resultados?",
  "GT_EDGES_MULTIANNOTATOR_CONTRACT_PROPOSAL.md"),
 ("STAGE13C","Uso histórico de máscaras Stage13c","O preflight leu GT train para conferência de dimensões; isto não comprova ajuste de operadores, nem ausência de exposição.",
  "O histórico distingue claramente inspeção técnica e ajustes dirigidos por GT train?",
  "BIPED_stage13c_execution_summary.json; scripts Stage13c/13d"),
 ("BIPED_UNIVERSE","Universo BIPED completo","As 198 candidatas podem ser examinadas nesta versão, incluindo 73 fora da seleção inicial.",
  "Após examinar as 198 imagens, há um conjunto suficiente de cenas distintas e elegíveis?",
  "BIPED_198_candidates.csv; atlas local original-only"),
 ("MULTICUE_SCENE","95 capturas MultiCue","O grupo 4113 foi excluído; 4108 tem alerta de múltiplas sequências.",
  "A independência de 95 capturas e suas sequências está documentada?",
  "multicue_100_sequence_names.csv; multicue_image_only_overlap_summary.json"),
 ("UDED_LINEAGE","Ausência de sobreposição com UDED-14","Os hashes dos originais não coincidem, mas isso não prova ausência de cenas visualmente repetidas.",
  "A exposição histórica e a independência visual UDED-14 versus os 220 originais foram demonstradas?",
  "P1_LINEAGE_METADATA_CROSSCHECK_NOT_APPROVED.json; documentos históricos"),
 ("SAMPLE_SIZE","N definitivo e poder","N=220, mix 125+95, é uma proposta; a independência real pode reduzir o N.",
  "O tamanho final, o poder e a contingência por exclusões foram aprovados antes de resultados?",
  "SAMPLE_SIZE_CONDITIONAL_DECISION.md; protocolo"),
 ("INFERENCE","Inferência confirmatória","H1 prevê rho negativo, H2 positivo; Spearman bloqueado por domínio, 100 mil permutações e ajuste Holm.",
  "As direções, testes, empates, dados ausentes e unidade de análise estão fixados adequadamente?",
  "FROZEN_PROTOCOL_BYTES_TO_REVIEW_NOT_ACTIVE.json"),
 ("GT_EDGE_CASES","Casos de GT degenerado e freeze","Política v2 falha fechada para máscaras inesperadas, sem ajuste após resultados.",
  "As regras para máscara vazia/constante, exclusões e alteração de protocolo são aceitáveis?",
  "GT_PIXEL_ENCODING_PROSPECTIVE_v2_NOT_APPROVED.md; executor v2"),
]


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_csv_exact(path: Path, *, limit: int=6_000_000) -> tuple[list[dict],bytes]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size>limit:
        raise ValueError("Metadata CSV unsafe or missing: "+str(path))
    raw=path.read_bytes()
    import io
    with io.StringIO(raw.decode("utf-8-sig"),newline="") as stream:
        reader=csv.DictReader(stream)
        rows=list(reader)
    return rows,raw


def read_json_exact(path: Path) -> tuple[dict,bytes]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size>4_000_000:
        raise ValueError("Metadata JSON unsafe or missing: "+str(path))
    raw=path.read_bytes()
    return json.loads(raw.decode("utf-8-sig")),raw


def inspect_sources(*, candidates=CANDIDATES, review=REVIEW, p1=P1, template=TEMPLATE) -> dict:
    cand,raw_cand=read_csv_exact(candidates)
    cohort,raw_review=read_csv_exact(review)
    audit,raw_p1=read_json_exact(p1)
    signoff,raw_template=read_json_exact(template)
    if len(cand)!=198 or len(cohort)!=220 or tuple(cohort[0])!=REVIEW_COLUMNS:
        raise ValueError("Expected 198 BIPED candidates and exact 220 review rows")
    if Counter(r["dataset"] for r in cohort)!={"BIPED":125,"MultiCue":95}:
        raise ValueError("Initial selected cohort must be 125+95")
    if signoff.get("reviewed_cohort_sheet_sha256")!=sha_bytes(raw_review):
        raise ValueError("Review template does not bind exact 220-row CSV bytes")
    if not audit.get("all_seven_training_digests_match") or len(audit.get("P1_seven_proofs",[]))!=7:
        raise ValueError("P1 evidence incomplete")
    if not signoff.get("approved_runtime_sources_sha256"):
        raise ValueError("Review template missing bound runtime sources")
    if signoff.get("approved_for_first_confirmatory_outcome_access") is not False:
        raise ValueError("This tool cannot run from an approved/signed review template")
    selected={(x["dataset"],x["image_id"]):x for x in cohort}
    selected_biped={k[1] for k in selected if k[0]=="BIPED"}
    all_items=[]
    ids=set(); hashes=set()
    for item in cand:
        iid,sha,relative=item["image_id"],item["sha256"].lower(),item["relative_path"]
        if item.get("dataset")!="BIPEDv2_train":
            raise ValueError("Unexpected BIPED source split")
        if not re.fullmatch(r"RGB_\d+",iid) or not SHA64.fullmatch(sha):
            raise ValueError("Malformed BIPED ID/SHA")
        if (iid in ids) or sha in hashes:
            raise ValueError("Duplicate BIPED image identity")
        ids.add(iid);hashes.add(sha)
        initial=selected.get(("BIPED",iid))
        if initial and (initial["image_sha256"].lower()!=sha or initial["relative_path"]!=relative):
            raise ValueError("BIPED selected image drift")
        all_items.append({
            "dataset":"BIPED","id":iid,"sha256":sha,"relative_path":relative,
            "in_initial_cohort":bool(initial),"scene_group":initial["scene_group"] if initial else iid,
            "warning":(initial or {}).get("historical_attention") or
              item.get("near_image_flags") or "BIPED_ALTERNATIVE_REQUIRES_SCENE_AND_EXPOSURE_REVIEW",
        })
    if len(selected_biped)!=125 or not selected_biped.issubset(ids):
        raise ValueError("125 BIPED originals not found in complete candidate inventory")
    for item in cohort:
        if item["dataset"]!="MultiCue":continue
        iid=item["image_id"];sha=item["image_sha256"].lower()
        if not re.fullmatch(r"\d+_left_\d+",iid) or not SHA64.fullmatch(sha):
            raise ValueError("Malformed MultiCue identity/SHA")
        if sha in hashes or ("MultiCue",iid) in selected and item["relative_path"]!=iid+".png":
            raise ValueError("MultiCue original mismatch")
        hashes.add(sha)
        all_items.append({
            "dataset":"MultiCue","id":iid,"sha256":sha,"relative_path":item["relative_path"],
            "in_initial_cohort":True,"scene_group":item["scene_group"],
            "warning":item["historical_attention"],
        })
    if len(all_items)!=293 or Counter(x["dataset"] for x in all_items)!={"BIPED":198,"MultiCue":95}:
        raise ValueError("Unexpected visual review universe")
    by_id={x["id"]:x for x in all_items if x["dataset"]=="BIPED"}
    groups=[]
    union=set()
    for index,ids_group in enumerate(EXPECTED_GROUPS,1):
        for iid in ids_group:
            if iid not in by_id or not by_id[iid]["in_initial_cohort"] or iid in union:
                raise ValueError("BIPED ORB suspect-group does not match reviewed original selection")
            union.add(iid)
        groups.append({"id":f"CANDIDATE_SCENE_{index:02d}","ids":ids_group,
                       "warning":"ORB/RANSAC visual triage only; requires reviewer adjudication",
                       "panel":f"assets/groups/G{index:02d}.jpg"})
    if len(union)!=52:
        raise ValueError("Expected 52 flagged BIPED selected originals")
    claims=[{"id":r["hypothesis"]+"."+r["fitted_part"],
             "training_hash":r["training_ids_sha256"],
             "commit":r["fitting_commit"],
             "title":r["hypothesis"]+" — "+r["fitted_part"],
             "question":"A origem do treinamento, a ausência de sobreposição e a exposição histórica estão demonstradas por evidência verificável?"}
            for r in audit["P1_seven_proofs"]]
    return {
        "items":all_items,"groups":groups,"p1":claims,
        "science":[dict(zip(("id","title","description","question","source"),x)) for x in SCIENCE],
        "meta":{"candidate_sha256":sha_bytes(raw_cand),
                "cohort_sheet_sha256":sha_bytes(raw_review),
                "p1_evidence_sha256":sha_bytes(raw_p1),
                "review_template_sha256":sha_bytes(raw_template),
                "training_ids_sha256":audit["training_ids_hash_recomputed"],
                "initial_selected_n":220,
                "visual_candidates_n":293,
                "no_confirmatory_gt_used":True,
                "scientific_signoff_issued":False,
                "review_status":"HUMAN_REVIEW_PENDING_NOT_FROZEN"}
    }


def original_source(item: dict, biped: Path, multicue: Path) -> Path:
    base=biped if item["dataset"]=="BIPED" else multicue
    rel=item["relative_path"]
    if not IMAGE_BASE.fullmatch(rel) or Path(rel).stem!=item["id"]:
        raise ValueError("Unsafe original-image file name: "+str(rel))
    path=base/rel
    if (not path.is_file() or path.is_symlink() or not
        path.resolve().is_relative_to(base.resolve()) or not 0 < path.stat().st_size < 40_000_000):
        raise ValueError("Original image missing/unsafe: "+str(path))
    return path


def generate(*, biped=BIPED, multicue=MULTICUE, output=OUT,
             frontend=FRONT, sources=None) -> dict:
    data=sources if sources is not None else inspect_sources()
    if len(data["items"])!=293:
        raise ValueError("Visual review requires all 293 candidates")
    idset=set()
    for row in data["items"]:
        key=(row["dataset"],row["id"])
        if key in idset:raise ValueError("Repeated review record")
        idset.add(key)
    input_fingerprint=sha_bytes(json.dumps({
        "meta":data["meta"],"items":[(r["dataset"],r["id"],r["sha256"])
                                    for r in data["items"]],
        "groups":data["groups"]},sort_keys=True,ensure_ascii=False).encode())
    stage=output.with_name(output.name+"_IN_PROGRESS")
    if output.exists():
        m=output/"MANIFEST.json"
        if not m.is_file():raise RuntimeError("Existing visual review folder without manifest")
        prior=json.loads(m.read_text(encoding="utf-8"))
        if prior.get("input_fingerprint")!=input_fingerprint:
            raise RuntimeError("Review input changed. Archive prior quiz and export answers before creating a new snapshot")
        for i in prior.get("images",[]):
            f=output/i["thumbnail"]
            if not f.is_file() or f.is_symlink() or sha_bytes(f.read_bytes())!=i["thumbnail_sha256"]:
                raise RuntimeError("Previously generated image altered: "+str(f))
        if len(prior["images"])!=293:
            raise RuntimeError("Previous visual review is incomplete")
        # Recheck the ORIGINALS as well as cached thumbnails. A valid old
        # thumbnail is not evidence that the underlying dataset stayed fixed.
        for item in data["items"]:
            path=original_source(item,biped,multicue)
            if sha_bytes(path.read_bytes())!=item["sha256"]:
                raise RuntimeError("Original image SHA drift since atlas generation: "+item["id"])
        reused=True
        images=prior["images"]
    else:
        if stage.exists():
            raise RuntimeError("Interrupted visual review stage exists: "+str(stage))
        (stage/"assets/images").mkdir(parents=True)
        (stage/"assets/groups").mkdir(parents=True)
        images=[]
        for row in data["items"]:
            path=original_source(row,biped,multicue)
            raw=path.read_bytes()
            if sha_bytes(raw)!=row["sha256"]:
                raise ValueError("Original SHA256 mismatch: "+row["id"])
            with Image.open(path) as source:
                if source.format not in ("JPEG","PNG","BMP") or source.width*source.height>30_000_000:
                    raise ValueError("Unsupported source format/image resolution")
                rgb=ImageOps.exif_transpose(source).convert("RGB")
                rgb.thumbnail((740,440),Image.Resampling.LANCZOS)
                dest=f"assets/images/{row['dataset']}_{row['id']}.jpg"
                (stage/dest).parent.mkdir(parents=True,exist_ok=True)
                rgb.save(stage/dest,format="JPEG",quality=82,optimize=True,exif=b"")
            images.append({**row,"thumbnail":dest,
                           "thumbnail_sha256":sha_bytes((stage/dest).read_bytes())})
        image_by_id={r["id"]:r for r in images if r["dataset"]=="BIPED"}
        for group in data["groups"]:
            cards=[]
            for iid in group["ids"]:
                thumb=stage/image_by_id[iid]["thumbnail"]
                with Image.open(thumb) as im:
                    card=Image.new("RGB",(420,300),"#f4f7fa")
                    tile=im.copy();tile.thumbnail((400,258))
                    card.paste(tile,((420-tile.width)//2,9+(258-tile.height)//2))
                    ImageDraw.Draw(card).text((12,275),iid,fill="#11263e")
                    cards.append(card)
            cols=2;rows=(len(cards)+1)//2
            panel=Image.new("RGB",(cols*420,rows*300),"#dce6ec")
            for n,card in enumerate(cards):
                panel.paste(card,((n%2)*420,(n//2)*300))
            panel.save(stage/group["panel"],format="JPEG",quality=86)
        report={"schema":"paper_a_local_visual_quiz_293_v1",
                "input_fingerprint":input_fingerprint,
                "cohort_sheet_sha256":data["meta"]["cohort_sheet_sha256"],
                "images":[{"dataset":r["dataset"],"id":r["id"],
                           "thumbnail":r["thumbnail"],"thumbnail_sha256":r["thumbnail_sha256"],
                           "original_sha256":r["sha256"]} for r in images],
                "no_GT_H5_F1_descriptor_or_predictions_read":True,
                "no_approval_or_freeze_issued":True}
        (stage/"MANIFEST.json").write_text(
            json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        stage.rename(output)
        reused=False
    # User-editable answers live in localStorage / explicit downloads, never
    # in generated HTML. Refresh frontend without removing any browser answers.
    # On both fresh and reused builds, rehydrate complete source and cohort
    # metadata. The slim manifest alone is not the UI's data model.
    by_thumb={(r["dataset"],r["id"]):r for r in images}
    browser_items=[]
    for row in data["items"]:
        cached=by_thumb.get((row["dataset"],row["id"]))
        if cached is None or cached["original_sha256"]!=row["sha256"]:
            raise RuntimeError("Review image/manifest identity drift")
        source_path=original_source(row,biped,multicue)
        browser_items.append({
            **row,
            "thumbnail":cached["thumbnail"],
            "thumbnail_sha256":cached["thumbnail_sha256"],
            "original_href":source_path.as_uri(),
        })
    present={**data,"items":browser_items}
    raw_json=json.dumps(present,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")
    html_source=(frontend/"index.template.html").read_text(encoding="utf-8")
    if html_source.count("__REVIEW_DATA_JSON__")!=1:
        raise RuntimeError("Review template data insertion marker ambiguous")
    html_text=html_source.replace("__REVIEW_DATA_JSON__",raw_json)
    for original,dest in (("app.js","app.js"),("style.css","style.css")):
        payload=(frontend/original).read_bytes()
        p=output/dest
        temp=p.with_suffix(p.suffix+".pending")
        temp.write_bytes(payload)
        os.replace(temp,p)
    target=output/"index.html"
    tmp=output/"index.html.pending"
    tmp.write_text(html_text,encoding="utf-8")
    os.replace(tmp,target)
    return {
        "status":"LOCAL_293_IMAGE_QUIZ_READY_NOT_SIGNED",
        "html":str(target),"images":len(images),"selected":220,
        "biped_alternates":73,"suspected_scene_groups":22,
        "reused_sha_checked_thumbnails":reused,
        "cohort_sheet_sha256":data["meta"]["cohort_sheet_sha256"],
        "GT_opened":False,"freeze_authorized":False,
    }


if __name__=="__main__":
    print(json.dumps(generate(),ensure_ascii=False,indent=2))
