#!/usr/bin/env python3
"""Paper A: POST-QUIZ reconciliation + metadata-only historical audit.

Only reads an exported quiz HTML/JSON and existing pre-freeze metadata.
NEVER accesses protected GT/H5/F1/maps, executes an experiment, updates the
cohort/protocol, fills signoffs, or considers a clicked answer scientific proof.
Writes an independent review workspace; never overwrites user answers.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
WORK = Path(r"F:\MFI-Edge-Data\MultiCue\paper_a_completion")
SIGNOFF = WORK / "scientific_signoff"
CANDIDATES = ROOT / "results/local_dev/paper_a_confirmation_inventory/predata_audit/biped_train_after_visual_dedup_candidates.csv"
SHA64 = re.compile(r"^[a-f0-9]{64}$")
REVIEW_SCHEMA = "paper_a_human_local_visual_review_293_v1"
_ALLOWED = {"SAME", "DIFFERENT", "UNSURE"}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class ReportScriptParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.capture = False
        self.chunks = []
    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("id") == "report-data":
            self.capture = True
    def handle_endtag(self, tag):
        if tag == "script" and self.capture:
            self.capture = False
    def handle_data(self, data):
        if self.capture:
            self.chunks.append(data)


def load_quiz_report(path: Path) -> tuple[dict, str]:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= 12_000_000:
        raise ValueError("Invalid exported quiz HTML/JSON; choose the user's exact file")
    raw = path.read_bytes()
    if path.suffix.lower() == ".json":
        doc = json.loads(raw.decode("utf-8-sig"))
    elif path.suffix.lower() in {".html", ".htm"}:
        parser = ReportScriptParser()
        parser.feed(raw.decode("utf-8-sig"))
        if len(parser.chunks) != 1:
            raise ValueError("No unique original embedded report-data JSON; export from the quiz")
        doc = json.loads(parser.chunks[0])
    else:
        raise ValueError("Use exported PaperA_RELATORIO_293_*.html or PaperA_QUIZ_293_*.json")
    if (doc.get("schema") != REVIEW_SCHEMA or
            doc.get("scientific_signoff_granted") is not False or
            doc.get("protected_GT_access_authorized") is not False):
        raise ValueError("Unexpected quiz schema or authorization: fail closed")
    captures = doc.get("capture_reviews")
    groups = doc.get("group_reviews")
    if not isinstance(captures, list) or not isinstance(groups, list) or len(captures)!=293 or len(groups)!=22:
        raise ValueError("This review must contain exactly 293 captures and 22 initial groups")
    if Counter(r.get("dataset") for r in captures) != {"BIPED":198,"MultiCue":95}:
        raise ValueError("Unexpected source dataset mix")
    ids = set()
    for row in captures:
        key=(row["dataset"],row.get("image_id"))
        if key in ids or not SHA64.fullmatch(str(row.get("original_sha256",""))):
            raise ValueError("Duplicate or malformed captured image / SHA")
        ids.add(key)
    if sum(x.get("in_initial_cohort") is True for x in captures)!=220:
        raise ValueError("220-row provisional cohort not present in exported quiz")
    if len(doc.get("P1_seven_review",[]))!=7 or len(doc.get("methodological_review",[]))!=10:
        raise ValueError("P1/methodology questions missing")
    return doc,digest(raw)


def verify_sources(doc: dict, *, signoff: Path=SIGNOFF, candidates: Path=CANDIDATES) -> dict:
    paths = {
        "cohort_sheet_sha256":signoff/"REVIEW_220_IMAGES_PENDING.csv",
        "candidate_sha256":candidates,
        "p1_evidence_sha256":signoff/"P1_LINEAGE_METADATA_CROSSCHECK_NOT_APPROVED.json",
        "review_template_sha256":signoff/"FINAL_INDEPENDENT_REVIEW.template.json",
    }
    matched = {}
    for name,path in paths.items():
        if not path.is_file() or path.is_symlink() or path.stat().st_size > 6_000_000:
            raise ValueError("Metadata source not available: "+str(path))
        actual = digest(path.read_bytes())
        if doc.get("source_sha256",{}).get(name) != actual:
            raise ValueError("Report and current metadata differ: "+name+
                             ". Archive the original report; do not silently merge revisions")
        matched[name] = {"sha256":actual,"path":str(path)}
    p1=json.loads(paths["p1_evidence_sha256"].read_text(encoding="utf-8"))
    if (p1.get("all_seven_training_digests_match") is not True or
            p1.get("all_seven_provenance_fields_internally_consistent") is not True or
            len(p1.get("P1_seven_proofs",[]))!=7):
        raise ValueError("Existing P1 metadata no longer satisfies technical preflight")
    return {"matched":matched,"p1":p1}


def reconcile_tasks(doc: dict) -> tuple[list[dict], dict]:
    imgs={(r["dataset"],r["image_id"]):r for r in doc["capture_reviews"]}
    directed=defaultdict(dict)
    for row in doc["capture_reviews"]:
        for other,decision in (row.get("pairReviews") or {}).items():
            if decision not in _ALLOWED:
                raise ValueError("Invalid comparison answer")
            target=(row["dataset"],other)
            if target not in imgs or other==row["image_id"]:
                raise ValueError("Unrecognized same-dataset comparison partner")
            pair=(row["dataset"],)+tuple(sorted((row["image_id"],other)))
            directed[pair][row["image_id"]] = decision
    tasks=[];conflicted=set()
    def task(kind,dataset,ids,reason,choices,details,group=None):
        key=kind+"__"+dataset+"__"+"__".join(ids)
        tasks.append({"id":key,"type":kind,"dataset":dataset,"images":list(ids),
                      "reason":reason,"original_answers":details,
                      "choices":choices,"group":group,
                      "status":"HUMAN_RECONCILIATION_REQUIRED"})
    for (dataset,a,b),given in sorted(directed.items()):
        values=set(given.values())
        if len(values)>1:
            conflicted.add((dataset,a,b))
            task("PAIR_CONFLICT",dataset,[a,b],
                 "O mesmo par recebeu respostas diferentes em sentidos opostos.",
                 [["SAME","Sim, mesmo lugar"],["DIFFERENT","Não, lugares diferentes"],
                  ["UNSURE","Não consigo decidir"]],
                 {k:given.get(k,"NOT_REVIEWED") for k in (a,b)})
    image_conflicts=[]
    for key,row in sorted(imgs.items()):
        known=[other for other,val in (row.get("pairReviews") or {}).items() if val=="SAME"]
        if row.get("scene")=="PASS" and known:
            image_conflicts.append(key)
            task("IMAGE_PASS_SAME",row["dataset"],[row["image_id"],known[0]],
                 "A imagem foi marcada sem repetição, mas há comparação declarando 'mesmo lugar'.",
                 [["GROUP","Há repetição: precisa agrupar"],["NO_MATCH","Comparação SAME foi equivocada"],
                  ["UNSURE","Não consigo decidir"]],
                 {"capture_scene":row["scene"],"same_compared_ids":known})
    group_issues=[]
    for g in doc["group_reviews"]:
        text=str(g.get("evidence","")).lower()
        decision=g.get("decision")
        contradict=(decision=="DISTINCT" and ("mesma cena" in text or "mesmo lugar" in text))
        ambiguous=(decision=="SUBGROUPS" and
                   len(g.get("sameAsFirst") or [])>=1 and
                   ";" in str(g.get("subgroups","")) and
                   (g.get("sameAsFirst") or []) !=
                     [x for x in g.get("sameAsFirst") or [] if x in g.get("subgroups","").split(";")[0]])
        if contradict or ambiguous:
            group_issues.append(g["id"])
            task("GROUP_CONTRADICTION" if contradict else "GROUP_SUBGROUPS",
                 "BIPED",g["image_ids"],
                 "Decisão distinta contradiz comentário 'mesma cena'." if contradict
                 else "A seleção dos checkboxes não coincide com a descrição dos subgrupos.",
                 [["ONE","Todas mostram o mesmo lugar"],["DISTINCT","Todas são lugares distintos"],
                  ["SUBGROUPS","Há subgrupos (descrever)"],["UNSURE","Não consigo decidir"]],
                 {"decision":decision,"evidence":g.get("evidence",""),
                  "sameAsFirst":g.get("sameAsFirst",[]),"subgroups":g.get("subgroups","")},
                 group=g["id"])
    repeated_multicue=[]
    for (dataset,a,b),given in sorted(directed.items()):
        if dataset=="MultiCue" and "SAME" in given.values():
            repeated_multicue.append([a,b])
            if (dataset,a,b) not in conflicted:
                task("MULTICUE_SAME",dataset,[a,b],
                     "Capturas MultiCue diferentes foram indicadas como mesmo lugar.",
                     [["SAME","Sim, mesmo lugar"],["DIFFERENT","Não, lugares distintos"],
                      ["UNSURE","Não consigo decidir"]],
                     given)
    same_pairs=[(dataset,a,b) for (dataset,a,b),votes in directed.items()
                if set(votes.values())=={"SAME"}]
    # Transitive connected components are a screening aid, NOT independent samples.
    parents={}
    def find(x):
        parents.setdefault(x,x)
        if parents[x]!=x:
            parents[x]=find(parents[x])
        return parents[x]
    for ds,a,b in same_pairs:
        x=(ds,a);y=(ds,b);parents[find(x)]=find(y)
    components=defaultdict(list)
    for member in parents:
        components[find(member)].append(member)
    grouped=[{"dataset":root[0],
              "ids":sorted(x[1] for x in members),
              "selected_count":sum(imgs[x].get("in_initial_cohort") is True for x in members)}
             for root,members in components.items() if len(members)>1]
    grouped.sort(key=lambda g:(g["dataset"],-g["selected_count"],g["ids"]))
    summary={"reconcile_tasks":len(tasks),"directional_pair_conflicts":len(conflicted),
             "pass_with_same_comparison":len(image_conflicts),
             "group_question_conflicts":len(group_issues),
             "multicue_same_pairs":len(repeated_multicue),
             "consistent_same_pairs":len(same_pairs),
             "same_pair_components_provisional":len(grouped),
             "historical_unchecked_captures":sum(r.get("exposure")=="UNCERTAIN" for r in doc["capture_reviews"]),
             "p1_claims_without_file_reference":sum(not any(ch in (r.get("evidence") or "") for ch in ("/","\\",".json",".md",".csv","sha256","commit"))
                       for r in doc["P1_seven_review"] if r.get("decision")=="SUPPORTED"),
             "science_claims_without_file_reference":sum(not any(ch in (r.get("evidence") or "") for ch in ("/","\\",".json",".md",".csv","sha256","commit"))
                       for r in doc["methodological_review"] if r.get("decision")=="SUPPORTED"),
             "preview_only":True,"reconciled_or_independent":False}
    return tasks,{"summary":summary,"same_pair_components":grouped,
                  "repeated_multicue":repeated_multicue}


def historical_matrix(metadata: dict, *, zip_path: Path) -> dict:
    p1=metadata["p1"]
    entry={
        "P1_exact_14_image_training_digest_rebuilt":p1.get("all_seven_training_digests_match") is True,
        "P1_seven_source_fields_consistent":p1.get("all_seven_provenance_fields_internally_consistent") is True,
        "P1_seven_no_confirmatory_overlap_attested":
             all(x.get("no_confirmatory_overlap_attested") is True for x in p1["P1_seven_proofs"]),
        "P1_external_lineage_attested":p1.get("all_seven_externally_attested") is True,
        "history_git_code_scan":"NOT_VERIFIED_IN_THIS_RUN",
        "stage13c_train_gt_preflight_access":"NOT_VERIFIED_IN_THIS_RUN",
        "confirmatory_outcome_access":"NOT_PERFORMED_BY_THIS_SCRIPT",
        "scientific_approval":"NOT_GRANTED",
    }
    evidence={}
    if zip_path.is_file() and not zip_path.is_symlink() and zip_path.stat().st_size < 70_000_000:
        with zipfile.ZipFile(zip_path) as z:
            for name in ("history/historical_source_audit.json",
                         "history/BIPED_stage13c_execution_summary.json"):
                if name not in z.namelist():continue
                if z.getinfo(name).file_size > 8_000_000:
                    raise ValueError("Unexpected oversized historical metadata in packet")
                raw=z.read(name);obj=json.loads(raw)
                evidence[name]={"sha256":digest(raw),"status":obj.get("status") or obj.get("stage")}
                if name.endswith("historical_source_audit.json"):
                    entry["history_git_code_scan"]=obj.get("status","UNCLASSIFIED")+"; CODE/REFERENCE SCAN ONLY, NOT EXECUTION ATTESTATION"
                else:
                    entry["stage13c_train_gt_preflight_access"]="YES, TRAIN GT DIMENSION CHECK NOT PERFORMANCE TEST"
    return {"metadata_checks":entry,"review_only_evidence":evidence,
            "unresolved":"Historical execution/exposure and visual overlap require source-level review; metadata hash matches are not scientific signoffs."}


def visual_html(report: dict) -> str:
    payload=json.dumps(report,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")
    template=r"""<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Paper A | Reconciliação visual pós-quiz</title>
<style>body{font:14px/1.55 system-ui;margin:0;background:#eef3f7;color:#192c41}
header{background:#17324a;color:white;padding:26px max(20px,calc((100vw - 1100px)/2))}
header h1{margin:5px 0;font-size:27px}header p{color:#c3d5e0}
main{max-width:1100px;padding:20px;margin:auto}.card{background:white;border:1px solid #c9d9e4;border-radius:13px;padding:19px;margin:17px 0}
h2{font-size:19px;margin:4px 0}.muted{color:#526779}.banner{background:#fff4df;padding:15px;border-left:4px solid #d09c43;border-radius:8px}
.images{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:10px;margin:14px 0}.images figure{margin:0;background:#f5f9fb;padding:7px;text-align:center}
.images img{width:100%;height:190px;object-fit:contain}.images figcaption{font-weight:700}
.choices{display:flex;gap:8px;flex-wrap:wrap;margin:11px 0}.choice,.btn{padding:10px 13px;border:1px solid #bdceda;border-radius:9px;background:white;font:inherit;cursor:pointer}
.choice.active{background:#e3f7f9;border:2px solid #117b95}.btn{background:#137c96;color:white;font-weight:700}
textarea{width:100%;box-sizing:border-box;min-height:65px;border:1px solid #c4d5df;border-radius:9px;padding:9px;font:inherit}
code{font:12px/1.5 ui-monospace,monospace;word-break:break-all}#progress{font-weight:bold}
@media(max-width:650px){header{padding:15px}.images img{height:140px}}
</style>
<header><h1>Paper A — Reconciliação pós-quiz</h1><p>Somente pendências; suas 293 respostas originais permanecem inalteradas. Sem GT, métricas, freeze ou aprovação científica.</p></header>
<main><div class="banner"><strong>Revisão restrita às contradições encontradas</strong><p id="progress">Preparando...</p><p>Esta página não altera a coorte. Responda sobre o local fotografado e use “Não sei” sempre que necessário. Ao concluir, exporte o JSON e envie-o junto do relatório original.</p></div>
<div id="tasks"></div><div class="card"><h2>Consolidar decisões</h2><p>O relatório histórico separado mostra quais dados já foram verificados e quais ainda exigem comprovação documental.</p><button class="btn" id="export">Exportar reconciliação JSON</button></div>
</main><script id="data" type="application/json">__DATA__</script>
<script>(()=>{
const D=JSON.parse(document.getElementById("data").textContent);
const key="PaperA_reconciliacao_"+D.report_sha256;
const saved=JSON.parse(localStorage.getItem(key)||"{}");
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const label=t=>({"PAIR_CONFLICT":"Comparações diferentes para o mesmo par","IMAGE_PASS_SAME":"Resposta geral contradiz uma comparação","GROUP_CONTRADICTION":"Grupo com comentário contraditório","GROUP_SUBGROUPS":"Subgrupos anotados de duas formas","MULTICUE_SAME":"Possível repetição MultiCue"})[t]||t;
const outer=document.getElementById("tasks");
for(const t of D.tasks){
 const v=saved[t.id]||{};
 let s='<section class="card" id="'+esc(t.id)+'"><small>'+esc(t.dataset)+' · '+esc(label(t.type))+'</small><h2>'+esc(t.images.join(" × "))+'</h2><p class="muted">'+esc(t.reason)+'</p>';
 s+='<div class="images">'+t.images.map(id=>'<figure><img loading="lazy" src="../QUIZ_VISUAL_LOCAL_293/assets/images/'+esc(t.dataset)+'_'+esc(id)+'.jpg" alt="'+esc(id)+'"><figcaption>'+esc(id)+'</figcaption></figure>').join("")+'</div>';
 s+='<p class="muted">Resposta original: <code>'+esc(JSON.stringify(t.original_answers))+'</code></p><div class="choices">';
 for(const [value,text] of t.choices){s+='<button type="button" class="choice '+(v.decision===value?'active':'')+'" data-id="'+esc(t.id)+'" data-value="'+esc(value)+'">'+esc(text)+'</button>'}
 s+='</div><label>Observação (se necessário)<textarea data-note="'+esc(t.id)+'" placeholder="Explique o que diferencia os lugares, ou descreva os subgrupos.">'+esc(v.note||"")+'</textarea></label></section>';
 outer.insertAdjacentHTML("beforeend",s);
}
function progress(){document.getElementById("progress").textContent=
 Object.values(saved).filter(v=>v&&v.decision).length+" / "+D.tasks.length+" decisões registradas";}
outer.addEventListener("click",e=>{
 const b=e.target.closest("[data-id]");if(!b)return;
 const id=b.dataset.id;const v=saved[id]||{note:""};v.decision=b.dataset.value;saved[id]=v;
 localStorage.setItem(key,JSON.stringify(saved));
 for(const x of outer.querySelectorAll("button[data-id]"))if(x.dataset.id===id)x.classList.toggle("active",x.dataset.value===v.decision);
 progress();
});
outer.addEventListener("input",e=>{
 if(!e.target.matches("[data-note]"))return;
 const id=e.target.dataset.note;const v=saved[id]||{decision:""};v.note=e.target.value;
 saved[id]=v;localStorage.setItem(key,JSON.stringify(saved));progress();
});
document.getElementById("export").addEventListener("click",()=>{
 const answers=D.tasks.map(t=>({id:t.id,kind:t.type,dataset:t.dataset,images:t.images,
 decision:(saved[t.id]||{}).decision||"PENDING",note:(saved[t.id]||{}).note||""}));
 const payload={schema:"paper_a_post_quiz_human_reconciliation_v1",
 source_report_sha256:D.report_sha256,source_cohort_sha256:D.cohort_sha256,
 generated_utc:new Date().toISOString(),status:"RECONCILIATION_NOT_SIGNOFF",
 answers,scientific_signoff_granted:false,protected_gt_access_authorized:false};
 const url=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)],{type:"application/json"}));
 const a=document.createElement("a");a.href=url;a.download="PaperA_RECONCILIACAO_"+D.report_sha256.slice(0,12)+".json";
 document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),2000);
});
progress();
})();</script></html>"""
    return template.replace("__DATA__",payload)


def write_outputs(doc:dict, report_hash:str, tasks:list[dict], info:dict, history:dict,
                  *, signoff:Path, source:Path) -> dict:
    out=signoff/("RECONCILIACAO_POS_QUIZ_"+report_hash[:12])
    out.mkdir(parents=True,exist_ok=True)
    summary={"schema":"paper_a_post_quiz_preconfirmatory_audit_v1",
             "source_report_sha256":report_hash,"source_report_name":source.name,
             "source_cohort_sha256":doc["source_sha256"]["cohort_sheet_sha256"],
             "results":info["summary"],
             "historical_matrix":history,
             "provisional_same_scene_components":info["same_pair_components"],
             "tasks":tasks,"scientific_signoff":False,
             "protected_GT_opened":False,
             "cohort_modified":False,"requires_new_freeze_review":True}
    target=out/"AUDITORIA_POS_QUIZ.json"
    content=json.dumps(summary,ensure_ascii=False,indent=2).encode("utf-8")
    if target.exists() and target.read_bytes()!=content:
        raise RuntimeError("Different output audit already exists; do not overwrite reviewer snapshot")
    if not target.exists():
        target.write_bytes(content)
    matrix=out/"MATRIZ_HISTORICA_PENDENTE.json"
    matrix_content=json.dumps(history,ensure_ascii=False,indent=2).encode("utf-8")
    if not matrix.exists():matrix.write_bytes(matrix_content)
    review=out/"REVISAR_PENDENCIAS.html"
    web=visual_html({"report_sha256":report_hash,
                     "cohort_sha256":doc["source_sha256"]["cohort_sheet_sha256"],
                     "tasks":tasks})
    review.write_text(web,encoding="utf-8")
    return {"status":"POST_QUIZ_RECONCILIATION_READY_NOT_APPROVED",
            "reconciliation_html":str(review),"historical_matrix":str(matrix),
            "audit_json":str(target),"tasks":len(tasks),
            "results":info["summary"],"protected_GT_opened":False,
            "scientific_signoff":False}


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report",type=Path,required=True,help="Exported original quiz HTML or JSON")
    parser.add_argument("--signoff",type=Path,default=SIGNOFF)
    parser.add_argument("--candidates",type=Path,default=CANDIDATES)
    parser.add_argument("--evidence-zip",type=Path,default=WORK/"PaperA_PRE_FREEZE_REVIEW_ONLY.zip")
    args=parser.parse_args()
    doc,sha=load_quiz_report(args.report)
    verified=verify_sources(doc,signoff=args.signoff,candidates=args.candidates)
    tasks,details=reconcile_tasks(doc)
    hist=historical_matrix(verified,zip_path=args.evidence_zip)
    result=write_outputs(doc,sha,tasks,details,hist,signoff=args.signoff,source=args.report)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
