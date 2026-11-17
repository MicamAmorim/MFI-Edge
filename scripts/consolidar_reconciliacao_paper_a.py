#!/usr/bin/env python3
"""Paper A post-reconciliation audit; NEVER opens GT or changes cohort/freeze.

Read exact original exported quiz (HTML/JSON) plus its 17-decision reconciliation,
verify both SHA identities, derive same-scene graph, identify unresolvable
logical conflicts and create a targeted 2nd-pass local quiz. All scientific
approval fields remain false. No training/descriptors/F1/confirmatory access.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
import hashlib
import itertools
import json
from pathlib import Path

from auditar_paper_a_pos_quiz import load_quiz_report, reconcile_tasks, verify_sources, SIGNOFF

SCHEMA="paper_a_post_quiz_human_reconciliation_v1"
PAIR_TYPES={"PAIR_CONFLICT","IMAGE_PASS_SAME","MULTICUE_SAME"}
GROUP_TYPES={"GROUP_SUBGROUPS","GROUP_CONTRADICTION"}
VALID_PAIR={"SAME","DIFFERENT","UNSURE"}
VALID_GROUP={"ONE","SUBGROUPS","DISTINCT","UNCERTAIN"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_reconciliation(path: Path, report: dict, report_sha: str) -> tuple[dict, str]:
    if not path.is_file() or path.is_symlink() or not 0<path.stat().st_size<500_000:
        raise ValueError("Reconciliation JSON missing/unsafe")
    raw=path.read_bytes()
    r=json.loads(raw.decode("utf-8-sig"))
    if (r.get("schema")!=SCHEMA or
        r.get("source_report_sha256")!=report_sha or
        r.get("source_cohort_sha256")!=report["source_sha256"]["cohort_sheet_sha256"] or
        r.get("scientific_signoff_granted") is not False or
        r.get("protected_gt_access_authorized") is not False or
        r.get("status")!="RECONCILIATION_NOT_SIGNOFF"):
        raise ValueError("The reconciliation does not belong to this exact unsigned report")
    tasks,_=reconcile_tasks(report)
    expected={t["id"]:t for t in tasks}
    if len(expected)!=len(tasks):
        raise ValueError("Duplicate generated reconciliation task IDs")
    answers=r.get("answers")
    if not isinstance(answers,list) or len(answers)!=len(expected):
        raise ValueError("Reconciliation is missing answers or contains extras")
    received=set()
    for answer in answers:
        key=answer.get("id")
        if key in received or key not in expected:
            raise ValueError("Duplicate/unknown reconciliation response: "+str(key))
        received.add(key)
        task=expected[key]
        if (answer.get("kind")!=task["type"] or
            answer.get("dataset")!=task["dataset"] or
            answer.get("images")!=task["images"] or
            answer.get("decision") not in [v for v,_ in task["choices"]]):
            raise ValueError("Invalid or mismatched decision for "+str(key))
    return r,sha(raw)


def pair_key(dataset: str, a: str, b: str) -> tuple[str,str,str]:
    if a==b:raise ValueError("A photograph cannot be compared with itself")
    return (dataset,*sorted((a,b)))


def analyze(report: dict, rec: dict) -> dict:
    imgs={(r["dataset"],r["image_id"]):r for r in report["capture_reviews"]}
    original=defaultdict(dict)
    for row in report["capture_reviews"]:
        for partner,v in (row.get("pairReviews") or {}).items():
            k=pair_key(row["dataset"],row["image_id"],partner)
            if (row["dataset"],partner) not in imgs or v not in VALID_PAIR:
                raise ValueError("Invalid original pair vote")
            original[k][row["image_id"]]=v
    updated=defaultdict(set)
    updated_id=defaultdict(list)
    group_updates={}
    for item in rec["answers"]:
        kind=item["kind"]
        if kind in PAIR_TYPES:
            value=item["decision"]
            if kind=="IMAGE_PASS_SAME":
                value={"GROUP":"SAME","NO_MATCH":"DIFFERENT","UNSURE":"UNSURE"}[value]
            k=pair_key(item["dataset"],*item["images"])
            updated[k].add(value)
            updated_id[k].append(item["id"])
        elif kind in GROUP_TYPES:
            matches=[g for g in report["group_reviews"]
                     if set(g["image_ids"])==set(item["images"])]
            if len(matches)!=1:
                raise ValueError("Revised group identity unknown")
            group_updates[matches[0]["id"]]=item["decision"]
        else:
            raise ValueError("Unexpected reconciliation kind")

    positive=defaultdict(set)
    negative=defaultdict(set)
    unknown=set()
    for key,votes in original.items():
        vals=updated.get(key,set(votes.values()))
        if vals=={"SAME"}:positive[key].add("pair comparison")
        elif vals=={"DIFFERENT"}:negative[key].add("pair comparison")
        elif vals=={"UNSURE"}:unknown.add(key)
        else:raise ValueError("Unreconciled conflicting pair "+str(key))
        if key in updated:
            target=positive if vals=={"SAME"} else negative if vals=={"DIFFERENT"} else None
            if target is not None:target[key].add("later pair reconciliation")

    same_round_conflicts=set()
    overridden_older_votes=[]
    for group in report["group_reviews"]:
        ds="BIPED";ids=group["image_ids"]
        dec=group_updates.get(group["id"],group["decision"])
        latest=group["id"] in group_updates
        if dec not in VALID_GROUP:
            raise ValueError("Invalid group status")
        if dec=="SUBGROUPS":
            # Subgroup membership is not a signed equivalence relation.
            # Unadjudicated individual links remain merely provisional.
            continue
        if dec not in {"ONE","DISTINCT"}:
            continue
        for a,b in itertools.combinations(ids,2):
            key=pair_key(ds,a,b)
            should="SAME" if dec=="ONE" else "DIFFERENT"
            desired=positive if should=="SAME" else negative
            opposite=negative if should=="SAME" else positive
            later_pair=updated.get(key)
            if latest:
                if later_pair and later_pair!={should}:
                    same_round_conflicts.add(key)
                elif not later_pair:
                    if key in opposite:
                        overridden_older_votes.append({
                            "pair":list(key),"group":group["id"],
                            "older_pair_vote_overridden_by_later_group":should})
                    opposite.pop(key,None)
            elif later_pair and later_pair!={should}:
                # An explicit later pair review takes precedence over
                # an earlier group classification of this same pair.
                continue
            desired[key].add(("revised group " if latest else "original group ")+group["id"])

    # Connected components of positive links; negative links within a
    # component are logical contradictions, not eligibility decisions.
    parent={}
    def find(x):
        parent.setdefault(x,x)
        if parent[x]!=x:parent[x]=find(parent[x])
        return parent[x]
    def union(x,y):
        parent[find(x)]=find(y)
    graph=defaultdict(set)
    for ds,a,b in positive:
        x=(ds,a);y=(ds,b)
        union(x,y)
        graph[x].add(y);graph[y].add(x)

    def path_of(x,y):
        prev={x:None};todo=deque([x])
        while todo:
            node=todo.popleft()
            if node==y:break
            for next_node in sorted(graph.get(node,())):
                if next_node not in prev:
                    prev[next_node]=node;todo.append(next_node)
        if y not in prev:return []
        ans=[];now=y
        while now is not None:
            ans.append(now[1]);now=prev[now]
        return list(reversed(ans))

    conflicts=[]
    for key in sorted(set(positive)&set(negative) |
                      {k for k in negative if find((k[0],k[1]))==find((k[0],k[2]))}):
        ds,a,b=key
        note="CONFLICT_IN_SAME_ROUND" if key in same_round_conflicts else (
            "DIRECT_GROUP_PAIR_CONFLICT" if key in positive else
            "TRANSITIVE_GROUP_CONFLICT")
        conflicts.append({
            "id":f"{ds}__{a}__{b}","dataset":ds,"images":[a,b],
            "reason":note,
            "prior_votes":original.get(key,{}),
            "later_pair_decisions":sorted(updated.get(key,())),
            "latest_group_vs_pair_conflict":key in same_round_conflicts,
            "positive_path":path_of((ds,a),(ds,b)),
            "positive_evidence":sorted(positive.get(key,())),
            "negative_evidence":sorted(negative.get(key,())),
            "review_status":"NEEDS_TARGETED_HUMAN_CLARIFICATION",
        })
    # Include any same-round contradiction even if a negative link was
    # later replaced by a different route; never silently discard.
    found={c["id"] for c in conflicts}
    for ds,a,b in sorted(same_round_conflicts):
        id=f"{ds}__{a}__{b}"
        if id not in found:
            conflicts.append({
                "id":id,"dataset":ds,"images":[a,b],
                "reason":"CONFLICT_IN_SAME_ROUND","prior_votes":original.get((ds,a,b),{}),
                "later_pair_decisions":sorted(updated.get((ds,a,b),())),
                "latest_group_vs_pair_conflict":True,
                "positive_path":path_of((ds,a),(ds,b)),
                "positive_evidence":sorted(positive.get((ds,a,b),())),
                "negative_evidence":sorted(negative.get((ds,a,b),())),
                "review_status":"NEEDS_TARGETED_HUMAN_CLARIFICATION"})

    groups=defaultdict(set)
    for row in imgs:
        groups[(row[0],find(row))].add(row)
    sizes={}
    for ds in ("BIPED","MultiCue"):
        all_candidates={k for k in imgs if k[0]==ds}
        selected={k for k in all_candidates if imgs[k]["in_initial_cohort"] is True}
        all_roots={find(k) for k in all_candidates}
        selected_roots={find(k) for k in selected}
        sizes[ds]={
            "original_images":len(all_candidates),
            "initially_selected_images":len(selected),
            "provisional_components_in_all_images":len(all_roots),
            "provisional_components_among_selected":len(selected_roots),
            "initial_selection_duplicate_surplus_if_all_links_true":
                len(selected)-len(selected_roots),
            "only_conditional_not_power_or_confirmatory_sample_size":True,
        }
    return {
        "status":"POST_RECONCILIATION_CONFLICTS_OPEN_NOT_APPROVED",
        "answers_validated":len(rec["answers"]),
        "remaining_conflicts":conflicts,
        "conflict_count":len(conflicts),
        "revised_pair_count":len(updated),
        "historical_votes_overridden_by_later_group_review":overridden_older_votes,
        "provisional_scene_counts":sizes,
        "rules":"Later signed-by-user-in-quiz answers override earlier local choices only as analysis precedence; not scientific signoff.",
        "protected_GT_access":False,
        "cohort_modified":False,
        "scientific_signoff":False,
    }


def review_page(data:dict) -> str:
    safe=json.dumps(data,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")
    shell=r"""<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Paper A · 2ª passagem — apenas conflitos restantes</title>
<style>body{font:14px/1.5 system-ui;margin:0;background:#f1f5f8;color:#183148}
header{background:#143147;color:#fff;padding:23px max(20px,calc((100vw - 1050px)/2))}
header p{color:#c9dae4}main{max-width:1050px;margin:auto;padding:18px}
section{background:white;padding:19px;border:1px solid #cbdbe6;border-radius:13px;margin:15px 0}
h1{font-size:27px}h2{font-size:19px}.images{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
figure{margin:0;padding:8px;background:#f5f8fa}img{width:100%;height:240px;object-fit:contain}
figcaption{font-weight:700;margin-top:7px}.choices{display:flex;flex-wrap:wrap;gap:9px;margin:12px 0}
button{background:#fff;border:1px solid #b7cedc;border-radius:9px;padding:10px 12px;cursor:pointer}
button.chosen{background:#dff4f6;border:2px solid #117e94}.export{background:#127e96;color:white;font-weight:800}
textarea{display:block;width:100%;box-sizing:border-box;min-height:70px;padding:9px;border:1px solid #c0d1dd;border-radius:8px;font:inherit}
aside{padding:13px;background:#fff3df;border-left:4px solid #d5a24e}.small{font-size:12px;color:#596b7a;overflow-wrap:anywhere}
@media(max-width:650px){.images{grid-template-columns:1fr}img{height:180px}}
</style><header><h1>Paper A — segunda passagem visual</h1>
<p>Você já respondeu às 17 pendências. Restam somente os pares que contradizem outros agrupamentos. Sem GT e sem repetir o quiz.</p></header>
<main><aside><strong>Não aprova H1/H2 nem modifica a coorte.</strong>
<p>Se marcar “lugares diferentes” apesar de existir um caminho de fotos classificadas como iguais, precisaremos corrigir uma dessas ligações também. Abaixo mostramos o caminho correspondente.</p></aside>
<p id="counter"></p><div id="items"></div>
<section><button id="save" class="export">Exportar decisão da segunda passagem (JSON)</button></section></main>
<script id="data" type="application/json">__DATA__</script>
<script>(()=>{"use strict";
const D=JSON.parse(document.getElementById("data").textContent);
const key="PaperA_final_visual_reconcile_"+D.source_report_sha256+"_"+D.reconciliation_sha256;
const answers=JSON.parse(localStorage.getItem(key)||"{}");
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const root=document.getElementById("items");
for(const c of D.remaining_conflicts){
const prev=answers[c.id]||{};
const label=c.reason==="CONFLICT_IN_SAME_ROUND"?
 "As duas decisões mais recentes não concordam":
 c.reason==="DIRECT_GROUP_PAIR_CONFLICT"?
 "Um agrupamento contradiz a comparação do par":
 "Estas fotos ficaram conectadas por outras fotos marcadas iguais";
const div=document.createElement("section");
div.innerHTML='<small>'+esc(c.dataset)+' — '+esc(label)+'</small><h2>'+esc(c.images.join(" × "))+
 '</h2><div class="images">'+c.images.map(id=>'<figure><img loading="lazy" src="../QUIZ_VISUAL_LOCAL_293/assets/images/'+
 esc(c.dataset)+'_'+esc(id)+'.jpg"><figcaption>'+esc(id)+'</figcaption></figure>').join("")+
 '</div><p class="small"><b>Caminho de correspondências:</b> '+esc(c.positive_path.join(" → "))+
 '</p><p><b>Olhando essas duas imagens, elas mostram o mesmo lugar?</b></p><div class="choices">'+
 [["SAME","Sim, mesmo lugar"],["DIFFERENT","Não, lugares distintos"],
 ["UNSURE","Não consigo decidir"]].map(([v,label])=>'<button data-id="'+
 esc(c.id)+'" data-value="'+v+'" class="'+(prev.decision===v?'chosen':'')+'">'+esc(label)+'</button>').join("")+
 '</div><label>Observação (opcional; se forem diferentes, indique qual ligação do caminho parece errada)<textarea data-note="'+
 esc(c.id)+'" placeholder="Ex.: RGB_001 e RGB_002 são distintos; a ligação anterior entre ... foi um engano.">'+
 esc(prev.note||"")+'</textarea></label>';
root.append(div);
}
function count(){document.getElementById("counter").textContent=
 Object.values(answers).filter(x=>x&&x.decision).length+" / "+D.remaining_conflicts.length+
 " respostas registradas";}count();
root.addEventListener("click",e=>{
const b=e.target.closest("[data-id]");if(!b)return;
answers[b.dataset.id]??={};answers[b.dataset.id].decision=b.dataset.value;
localStorage.setItem(key,JSON.stringify(answers));
root.querySelectorAll("button[data-id]").forEach(x=>{
if(x.dataset.id===b.dataset.id)x.classList.toggle("chosen",x.dataset.value===b.dataset.value)});
count();
});
root.addEventListener("input",e=>{const t=e.target.closest("[data-note]");if(!t)return;
answers[t.dataset.note]??={};answers[t.dataset.note].note=t.value;
localStorage.setItem(key,JSON.stringify(answers));});
document.getElementById("save").addEventListener("click",()=>{
const data={schema:"paper_a_second_pass_scene_decisions_v1",
 source_report_sha256:D.source_report_sha256,reconciliation_sha256:D.reconciliation_sha256,
 source_cohort_sha256:D.source_cohort_sha256,
 generated_utc:new Date().toISOString(),status:"DRAFT_NOT_SCIENTIFIC_APPROVAL",
 answers:D.remaining_conflicts.map(c=>({id:c.id,images:c.images,dataset:c.dataset,
 decision:answers[c.id]?.decision||"PENDING",note:answers[c.id]?.note||""})),
 scientific_signoff:false,protected_gt_access:false,cohort_changed:false};
const blob=new Blob([JSON.stringify(data,null,2)],{type:"application/json"});
const u=URL.createObjectURL(blob);const a=document.createElement("a");a.href=u;
a.download="PaperA_SEGUNDA_PASSAGEM_"+D.reconciliation_sha256.slice(0,12)+".json";
document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),2500);
});})();</script></html>"""
    return shell.replace("__DATA__",safe)


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--report",type=Path,required=True)
    p.add_argument("--reconciliation",type=Path,required=True)
    p.add_argument("--out",type=Path,default=None)
    p.add_argument("--no-metadata-verification",action="store_true",
                   help="For synthetic tests ONLY; do not use in scientific run")
    args=p.parse_args()
    original,original_sha=load_quiz_report(args.report)
    revised,revision_sha=load_reconciliation(args.reconciliation,original,original_sha)
    if args.no_metadata_verification:
        raise PermissionError("Metadata verification cannot be bypassed for a scientific run")
    verify_sources(original)
    result=analyze(original,revised)
    output=args.out or SIGNOFF/("SEGUNDA_PASSAGEM_"+revision_sha[:12])
    output.mkdir(parents=True,exist_ok=True)
    result.update({"source_report_sha256":original_sha,
                   "reconciliation_sha256":revision_sha,
                   "source_cohort_sha256":original["source_sha256"]["cohort_sheet_sha256"]})
    target=output/"AUDITORIA_POS_RECONCILIACAO.json"
    raw=json.dumps(result,ensure_ascii=False,indent=2).encode("utf-8")
    if target.exists() and target.read_bytes()!=raw:
        raise RuntimeError("Output mismatch; do not overwrite previous scientific audit")
    target.write_bytes(raw)
    page=output/"REVISAR_CONFLITOS_RESTANTES.html"
    page.write_text(review_page(result),encoding="utf-8")
    print(json.dumps({"status":result["status"],
       "answers_validated":result["answers_validated"],
       "conflicts":result["conflict_count"],
       "provisional_scene_counts":result["provisional_scene_counts"],
       "audit":str(target),"review":str(page),
       "freeze":False,"protected_GT_access":False},ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
