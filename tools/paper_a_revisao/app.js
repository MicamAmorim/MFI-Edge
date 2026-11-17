(()=>{"use strict";
const E=id=>document.getElementById(id);
const D=JSON.parse(E("review-data").textContent);
const key="paperA_quiz_293_v1_"+D.meta.cohort_sheet_sha256.slice(0,16)+"_"+D.meta.candidate_sha256.slice(0,12);
const esc=x=>String(x??"").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
const names={inicio:"Visão geral",grupos:"22 grupos suspeitos",imagens:"293 capturas",p1:"7 proveniências P1",ciencia:"10 questões científicas",relatorio:"Relatório de revisão"};
const groupById={};for(const g of D.groups)for(const id of g.ids)groupById[id]=g.id;
const lookup=Object.fromEntries(D.items.map(r=>[r.dataset+":"+r.id,r]));
const STATE=()=>({meta:{reviewer:"",affiliation:"",role:"",conflicts:""},groups:{},images:{},p1:{},science:{},notes:""});
let S=STATE();
try{
 const old=JSON.parse(localStorage.getItem(key)||"null");
 if(old&&old.meta&&old.groups&&old.images&&old.p1&&old.science)S=old;
 // Legacy "Sustentado por evidências" clicks with no document cited must
 // not be silently promoted to "Sim, conferi a evidência" after UX upgrade.
 const migration=key+":objective_questions_v2";
 if(localStorage.getItem(migration)!=="1"){
  for(const kind of ["p1","science"]){
   for(const answer of Object.values(S[kind]||{})){
    if(answer.decision==="SUPPORTED"&&(answer.evidence||"").trim().length<15){
     answer.decision="";
    }
   }
  }
  localStorage.setItem(key,JSON.stringify(S));
  localStorage.setItem(migration,"1");
 }
}catch(_){}
let groupIndex=0,page=0,search="",filter="all",tab="inicio";const perPage=6;
const selectedImages=D.items.filter(i=>i.in_initial_cohort);
const altImages=D.items.filter(i=>!i.in_initial_cohort);
function persist(){try{localStorage.setItem(key,JSON.stringify(S))}catch(e){E("progress-label").textContent="Exporte JSON: armazenamento indisponível"}updateProgress()}
const getGroup=id=>S.groups[id]||(S.groups[id]={decision:"",representative:"",subgroups:"",evidence:""});
const getImage=x=>S.images[x]||(S.images[x]={scene:"",exposure:"",evidence:""});
const getCheck=(kind,id)=>S[kind][id]||(S[kind][id]={decision:"",evidence:""});
function imageDone(i){
 const a=S.images[i.dataset+":"+i.id]||{};
 if(!a.scene || !a.exposure)return false;
 const pair=Object.values(a.pairReviews||{});
 if(a.scene==="GROUP"&&!pair.includes("SAME")&&(a.evidence||"").trim().length<20)return false;
 if(a.scene==="PASS"&&!pair.includes("DIFFERENT")&&(a.evidence||"").trim().length<25)return false;
 if(a.scene==="EXCLUDE"&&(a.evidence||"").trim().length<15)return false;
 if(a.exposure==="NO_RELEVANT_EXPOSURE"&&(a.evidence||"").trim().length<25)return false;
 if(a.exposure==="EXPOSURE"&&(a.evidence||"").trim().length<15)return false;
 return true;
}
function checkDone(kind,id){const a=S[kind][id]||{};return !!(a.decision&&(a.decision==="UNCERTAIN"||(a.evidence||"").trim().length>=15))}
function stats(){const g=D.groups.filter(groupDone).length,im=D.items.filter(imageDone).length,p=D.p1.filter(x=>checkDone("p1",x.id)).length,s=D.science.filter(x=>checkDone("science",x.id)).length;return{groups:g,images:im,p1:p,science:s,total:g+im+p+s,maximum:D.groups.length+D.items.length+D.p1.length+D.science.length}}
function updateProgress(){const st=stats();E("n-groups").textContent=st.groups+"/22";E("n-images").textContent=st.images+"/293";E("n-p1").textContent=st.p1+"/7";E("n-science").textContent=st.science+"/10";E("progress-label").textContent=st.total+"/"+st.maximum+" itens";E("progress-bar").style.width=(100*st.total/st.maximum).toFixed(1)+"%"}
function go(to){if(!names[to])return;tab=to;document.querySelectorAll(".page").forEach(x=>x.classList.toggle("active",x.id==="page-"+to));document.querySelectorAll(".nav").forEach(x=>x.classList.toggle("active",x.dataset.tab===to));E("section-name").textContent=names[to];if(to==="grupos")renderGroup();if(to==="imagens")renderImages();if(to==="p1")renderChecks("p1");if(to==="ciencia")renderChecks("science");if(to==="relatorio")renderFinal();window.scrollTo(0,0)}
document.querySelectorAll("[data-tab]").forEach(x=>x.addEventListener("click",()=>go(x.dataset.tab)));
document.querySelectorAll("[data-goto]").forEach(x=>x.addEventListener("click",()=>go(x.dataset.goto)));
for(const id of ["reviewer","affiliation","role","conflicts"]){E(id).value=S.meta[id]||"";E(id).addEventListener("input",()=>{S.meta[id]=E(id).value;persist()})}
E("overall-notes").value=S.notes||"";E("overall-notes").addEventListener("input",()=>{S.notes=E("overall-notes").value;persist()});
E("sha-cohort").textContent=D.meta.cohort_sheet_sha256;
E("sha-candidates").textContent=D.meta.candidate_sha256;
function options(items,selected,kind,id){
 return '<div class="choices">'+items.map(([value,label,tone])=>
  '<button type="button" class="choice '+(tone||"")+" "+(selected===value?"chosen":"")+
  '" data-kind="'+esc(kind)+'" data-key="'+esc(id)+'" data-value="'+esc(value)+
  '" aria-pressed="'+String(selected===value)+'">'+esc(label)+"</button>").join("")+"</div>"
}
const groupOptions=[
 ["ONE","Sim, todas mostram o mesmo lugar"],
 ["SUBGROUPS","Apenas algumas mostram o mesmo lugar"],
 ["DISTINCT","Não, mostram lugares diferentes"],
 ["UNCERTAIN","Não consigo decidir","maybe"]
];
const cueOptions=[
 ["BUILDINGS","Os mesmos prédios/fachadas"],
 ["ROADS","As mesmas ruas, placas ou postes"],
 ["NATURE","As mesmas árvores ou paisagem"],
 ["OTHER","Outras estruturas fixas iguais"],
 ["MOVING","Apenas veículos ou pessoas parecidos"],
 ["NONE","Não identifiquei estruturas comuns"]
];
function groupDone(g){
 const v=S.groups[g.id]||{};
 if(!v.decision)return false;
 if(v.decision==="UNCERTAIN")return true;
 const cue=v.cue || (v.evidence?.trim().length>=25?"LEGACY_NOTES":"");
 if(!cue)return false;
 if(v.decision==="ONE")return Boolean(g.ids.includes(v.representative))&&!["MOVING","NONE"].includes(cue);
 if(v.decision==="SUBGROUPS"){
   const checked=(v.sameAsFirst||[]).filter(id=>g.ids.slice(1).includes(id));
   return (checked.length>0 && checked.length<g.ids.length-1) ||
     Boolean(v.subgroups && v.subgroups.trim().length>=8);
 }
 if(v.decision==="DISTINCT")return true;
 return false;
}
function readGroupFields(g,v){
 const keep=E("group-keep"),sub=E("group-subgroups"),notes=E("group-evidence");
 if(keep)v.representative=keep.value;
 if(sub)v.subgroups=sub.value;
 if(notes)v.evidence=notes.value;
}
function renderGroup(){
 const g=D.groups[groupIndex],v=getGroup(g.id);
 E("group-pos").textContent="Grupo "+(groupIndex+1)+" / "+D.groups.length;
 E("group-index").innerHTML=D.groups.map((x,i)=>
  '<button class="'+(i===groupIndex?"active ":"")+(groupDone(x)?"done":"")+
  '" data-group-go="'+i+'">'+String(i+1).padStart(2,"0")+"</button>").join("");
 const imgset=g.ids.map(id=>{const im=lookup["BIPED:"+id];return '<div><img class="thumb" src="'+esc(im.thumbnail)+
 '" alt="Original '+esc(id)+'"><b>'+esc(id)+'</b><a class="smalllink" href="'+esc(im.original_href)+
 '" target="_blank" rel="noopener">Abrir original</a></div>'}).join("");
 const checkboxChoices=g.ids.slice(1).map(id=>'<label class="scene-checkbox"><input type="checkbox" data-group-same="'+esc(id)+
 '" '+((v.sameAsFirst||[]).includes(id)?"checked":"")+'><span>'+esc(id)+'</span></label>').join("");
 const cueHtml=options(cueOptions,v.cue||"","groupcue",g.id);
 E("group-content").innerHTML='<article class="card"><div class="toolbar"><span class="badge flag">'+
  'Alerta de possível repetição, não decisão automática</span><span class="badge '+(groupDone(g)?"selected":"")+
  '">'+(groupDone(g)?"Resposta registrada":"Aguardando resposta")+'</span></div><h2>'+esc(g.ids.join(" · "))+'</h2>'+
  '<div class="split"><div><div class="visual"><img src="'+esc(g.panel)+'" alt="Painel comparativo de originais"></div>'+
  '<div class="previewgrid">'+imgset+'</div></div><div>'+
  '<h3>1. As fotos mostram o mesmo lugar, com os mesmos prédios, rua ou paisagem, mesmo que a câmera tenha mudado de posição?</h3>'+
  '<p class="hint">Exemplo: mesma fachada vista de frente e de lado = mesmo lugar. Carros e pessoas parecidos, sozinhos, não comprovam que a cena é igual.</p>'+
  options(g.ids.length===2?groupOptions.filter(x=>x[0]!=="SUBGROUPS"):groupOptions,v.decision,"group",g.id)+
  '<div class="'+(v.decision==="UNCERTAIN"?"hidden":"")+'"><div class="question">2. Qual detalhe fixo você usou para comparar?</div>'+cueHtml+'</div>'+
  '<label class="'+(v.decision==="ONE"?"":"hidden")+'">3. Qual foto é a melhor representante desse lugar?'+
  '<span class="hint">É apenas uma sugestão para decidir depois; nenhuma foto é excluída agora.</span>'+
  '<select id="group-keep"><option value="">Escolha uma foto</option>'+g.ids.map(id=>'<option value="'+esc(id)+
  '" '+(v.representative===id?"selected":"")+'>'+esc(id)+'</option>').join("")+'</select></label>'+
  '<div class="'+(v.decision==="SUBGROUPS"?"":"hidden")+'"><div class="question">3. Quais fotos abaixo mostram o mesmo lugar que '+esc(g.ids[0])+'?</div>'+
  '<div class="scene-checkboxes">'+checkboxChoices+'</div>'+
  '<label>Se houver mais de dois lugares, explique a divisão (opcional)<input id="group-subgroups" placeholder="'+
  esc(g.ids[0])+' e outra foto formam o lugar A; as demais o lugar B" value="'+esc(v.subgroups||"")+
  '"></label></div>'+
  '<label>Observação adicional (opcional)<textarea id="group-evidence" placeholder="Ex.: mesmos edifícios, árvores e placa; mudou apenas o ângulo da câmera.">'+
  esc(v.evidence||"")+'</textarea></label>'+
  '<p class="hint">Sua resposta é uma triagem visual. Ela não autoriza excluir imagens, nem comprova histórico de uso anterior.</p>'+
  '<button class="btn primary" id="group-save">Salvar resposta e ir ao próximo</button></div></div></article>';
}
E("group-content").addEventListener("click",event=>{
 const g=D.groups[groupIndex],v=getGroup(g.id);
 const b=event.target.closest("[data-kind]");
 if(b && (b.dataset.kind==="group" || b.dataset.kind==="groupcue")){
  readGroupFields(g,v);
  if(b.dataset.kind==="group")v.decision=b.dataset.value;
  else v.cue=b.dataset.value;
  persist();renderGroup();return;
 }
 if(event.target.closest("#group-save")){
  readGroupFields(g,v);persist();
  if(groupDone(g)){groupIndex=(groupIndex+1)%D.groups.length;renderGroup()}
  else alert("Escolha uma resposta. Se indicou o mesmo lugar, identifique o elemento fixo e a foto representante; se escolheu 'algumas', marque as fotos correspondentes.");
 }
});
E("group-content").addEventListener("input",e=>{
 const g=D.groups[groupIndex],v=getGroup(g.id);
 if(e.target.id==="group-evidence")v.evidence=e.target.value;
 if(e.target.id==="group-subgroups")v.subgroups=e.target.value;
 persist();
});
E("group-content").addEventListener("change",e=>{
 const g=D.groups[groupIndex],v=getGroup(g.id);
 if(e.target.id==="group-keep")v.representative=e.target.value;
 if(e.target.matches("[data-group-same]")){
  const selected=new Set(v.sameAsFirst||[]);
  if(e.target.checked)selected.add(e.target.dataset.groupSame);
  else selected.delete(e.target.dataset.groupSame);
  v.sameAsFirst=Array.from(selected);
 }
 persist();
});
E("group-index").addEventListener("click",e=>{const b=e.target.closest("[data-group-go]");if(b){groupIndex=Number(b.dataset.groupGo);renderGroup()}});
E("group-prev").addEventListener("click",()=>{groupIndex=(groupIndex+D.groups.length-1)%D.groups.length;renderGroup()});
E("group-next").addEventListener("click",()=>{groupIndex=(groupIndex+1)%D.groups.length;renderGroup()});
E("group-pending").addEventListener("click",()=>{for(let n=1;n<=D.groups.length;n++){const k=(groupIndex+n)%D.groups.length;if(!groupDone(D.groups[k])){groupIndex=k;renderGroup();return}}alert("Todos os grupos têm uma decisão registrada.")});
function filtered(){return D.items.filter(i=>{const k=i.dataset+":"+i.id;if(search&&!([i.id,i.dataset,i.scene_group,i.warning,groupById[i.id]||""].join(" ").toLowerCase().includes(search)))return false;
 switch(filter){case"pending":return !imageDone(i);case"selected":return i.in_initial_cohort;case"alternate":return !i.in_initial_cohort;case"biped":return i.dataset==="BIPED";case"multicue":return i.dataset==="MultiCue";case"flagged":return Boolean(groupById[i.id]);default:return true}});
}
const sceneOpts=[["GROUP","Sim, encontrei outra foto do mesmo lugar"],["PASS","Não encontrei repetição nas fotos comparadas"],["EXCLUDE","Imagem com problema técnico","negative"],["UNCERTAIN","Ainda não sei / preciso comparar mais","maybe"]];
const histOpts=[["NO_RELEVANT_EXPOSURE","Conferi registros: sem uso relevante"],["EXPOSURE","Achei indício de uso anterior","negative"],["UNCERTAIN","Não consultei os registros / não sei","maybe"]];
const comparisonSelection={};
const pairOptions=[["SAME","Sim, mostram o mesmo lugar"],["DIFFERENT","Não, são lugares diferentes"],["UNSURE","Não consigo decidir","maybe"]];
function comparisonPanel(item){
 const sourceKey=item.dataset+":"+item.id;
 const sameDataset=D.items.filter(x=>x.dataset===item.dataset&&x.id!==item.id);
 const suggestions=(item.visual_references||[]).map(x=>lookup[x.dataset+":"+x.id]).filter(Boolean);
 const selected=comparisonSelection[sourceKey]||suggestions[0]?.id||sameDataset[0]?.id;
 const reference=sameDataset.find(x=>x.id===selected)||sameDataset[0];
 if(!reference)return '<p class="hint">Não há imagem de referência disponível.</p>';
 const guessed=(item.visual_references||[]).find(x=>x.id===reference.id);
 const visualCards=suggestions.slice(0,5).map(x=>
  '<button type="button" class="reference-chip '+(x.id===reference.id?'active ':'')+
  '" data-compare-source="'+esc(sourceKey)+'" data-compare-target="'+esc(x.id)+'">'+
  '<img src="'+esc(x.thumbnail)+'" loading="lazy" alt="Referência '+esc(x.id)+'"><span>'+esc(x.id)+
  '</span></button>').join("");
 const options= sameDataset.map(x=>'<option value="'+esc(x.id)+'" '+(x.id===reference.id?'selected':'')+
  '>'+esc(x.id)+(item.visual_references?.some(n=>n.id===x.id)?' · sugerida':'')+
  '</option>').join("");
 const review=getImage(sourceKey).pairReviews?.[reference.id]||"";
 const pairButtons='<div class="question">Olhando estas DUAS fotos, elas mostram o mesmo lugar?</div><div class="choices">'+
  pairOptions.map(([value,label,tone])=>'<button type="button" class="choice '+(tone||"")+
  ' '+(review===value?"chosen":"")+'" data-pair-source="'+esc(sourceKey)+
  '" data-pair-target="'+esc(reference.id)+'" data-pair-value="'+esc(value)+
  '" aria-pressed="'+String(review===value)+'">'+esc(label)+'</button>').join("")+'</div>';
 return '<div class="comparison-card"><div class="question">Compare com outras capturas antes de responder</div>'+
  '<p class="hint">Referências sugeridas por semelhança visual aproximada (não representam prova). '+
  'A seleção inclui todas as '+sameDataset.length+' outras imagens '+esc(item.dataset)+
  '; a busca não detecta necessariamente mudanças grandes de ângulo.</p>'+
  '<div class="reference-chips">'+visualCards+'</div>'+
  '<label>Escolha qualquer imagem do mesmo conjunto para comparar'+
  '<select class="comparison-select" data-compare-key="'+esc(sourceKey)+'">'+options+'</select></label>'+
  '<div class="comparison-result"><div><img class="comparison-image" src="'+esc(item.thumbnail)+
  '" alt="Imagem principal '+esc(item.id)+'"><strong>'+esc(item.id)+' · atual</strong></div>'+
  '<div><img class="comparison-image" src="'+esc(reference.thumbnail)+'" alt="Referência '+esc(reference.id)+
  '"><strong>'+esc(reference.id)+' · comparação</strong><a class="smalllink" href="'+
  esc(reference.original_href)+'" target="_blank" rel="noopener">Ver original completo</a></div></div>'+
  '<p class="hint">Motivo da sugestão: '+esc(guessed?.reason==='suspected_shared_scene'?
  'par conhecido da triagem geométrica':'semelhança visual aproximada ou escolha manual')+
  '. Estas sugestões são uma triagem: não descartam outras imagens semelhantes.</p>'+pairButtons+
  '<p class="hint">Comparações registradas nesta imagem: '+Object.keys(getImage(sourceKey).pairReviews||{}).length+
  '. Use o seletor acima para conferir outras fotografias.</p></div>';
}
function renderImages(){const list=filtered(),pages=Math.max(1,Math.ceil(list.length/perPage));page=Math.min(page,pages-1);E("images-pos").textContent=(page+1)+" / "+pages+" · "+list.length+" imagens";E("images-prev").disabled=page===0;E("images-next").disabled=page===pages-1;
 E("image-list").innerHTML=list.slice(page*perPage,(page+1)*perPage).map(i=>{const k=i.dataset+":"+i.id,v=getImage(k),flag=groupById[i.id];
 return '<article class="card image-card" data-item="'+esc(k)+'"><div><img class="thumb" loading="lazy" src="'+esc(i.thumbnail)+'" alt="Imagem original '+esc(i.id)+'"><div class="toolbar"><span class="badge '+(i.in_initial_cohort?"selected":"alternate")+'">'+(i.in_initial_cohort?"Selecionada":"Alternativa")+'</span>'+(flag?'<span class="badge flag">'+esc(flag)+'</span>':"")+'</div><div class="hash">SHA256: '+esc(i.sha256.slice(0,22))+'…</div><a class="smalllink" href="'+esc(i.original_href)+'" target="_blank" rel="noopener">Abrir original completo</a></div><div><h3>'+esc(i.dataset+" · "+i.id)+'</h3><p class="hint">'+esc(i.warning.replaceAll("_"," "))+' · Grupo: '+esc(i.scene_group)+'</p>'+comparisonPanel(i)+'<div class="question">Após comparar com outras fotos, você encontrou repetição do mesmo lugar?</div>'+options(sceneOpts,v.scene,"scene",k)+
 '<p class="hint">“Não encontrei” significa apenas que nenhuma repetição apareceu nas comparações registradas; não é garantia de independência absoluta.</p>'+
 '<div class="question">Você consultou logs ou inventários para saber se esta foto foi usada antes no desenvolvimento?</div>'+
 options(histOpts,v.exposure,"exposure",k)+
 '<p class="hint">Se olhou apenas fotos, escolha “Não consultei os registros / não sei”. UDED-14 e Stage23/24 precisam de evidência documental.</p>'+ 
 '<label>Observação ou documento consultado <span class="hint">(opcional se marcou “não sei”; necessário para afirmar ausência de uso anterior ou exclusão)</span><textarea data-image-evidence="'+esc(k)+'" placeholder="Ex.: comparei RGB_001 com RGB_002; mesma fachada. O histórico não foi analisado.">'+esc(v.evidence)+'</textarea></label>'+
 '<p class="hint">'+(imageDone(i)?"Resposta registrada; ainda não é certificação científica":"Se indicar repetição, escolha uma comparação “mesmo lugar”. Se disser que não encontrou, registre ao menos uma comparação “lugares diferentes”.")+'</p></div></article>'}).join("");
}
E("image-list").addEventListener("click",e=>{
 const pair=e.target.closest("[data-pair-source]");
 if(pair){
  const v=getImage(pair.dataset.pairSource);
  if(!v.pairReviews)v.pairReviews={};
  v.pairReviews[pair.dataset.pairTarget]=pair.dataset.pairValue;
  comparisonSelection[pair.dataset.pairSource]=pair.dataset.pairTarget;
  persist();renderImages();return;
 }
 const reference=e.target.closest("[data-compare-source]");
 if(reference){comparisonSelection[reference.dataset.compareSource]=reference.dataset.compareTarget;renderImages();return}
 const b=e.target.closest("[data-kind]");if(!b)return;const v=getImage(b.dataset.key);v[b.dataset.kind]=b.dataset.value;const area=E("image-list").querySelector('textarea[data-image-evidence="'+CSS.escape(b.dataset.key)+'"]');if(area)v.evidence=area.value;persist();renderImages()});
E("image-list").addEventListener("change",e=>{if(e.target.matches("[data-compare-key]")){comparisonSelection[e.target.dataset.compareKey]=e.target.value;renderImages()}});
E("image-list").addEventListener("input",e=>{if(e.target.matches("textarea[data-image-evidence]")){getImage(e.target.dataset.imageEvidence).evidence=e.target.value;persist()}});
E("image-search").addEventListener("input",e=>{search=e.target.value.toLowerCase().trim();page=0;renderImages()});
E("image-filter").addEventListener("change",e=>{filter=e.target.value;page=0;renderImages()});
E("images-prev").addEventListener("click",()=>{page=Math.max(0,page-1);renderImages();window.scrollTo(0,0)});
E("images-next").addEventListener("click",()=>{page++;renderImages();window.scrollTo(0,0)});
const checkOptions=[
 ["SUPPORTED","Sim, conferi a evidência indicada"],
 ["REFUTED","Encontrei um problema","negative"],
 ["UNCERTAIN","Não consegui conferir / não sei","maybe"]
];
const CHECK_EXPLANATIONS={
 "GT_BIPED":{
  known:"Foram observados os valores 0, 254 e 255 em três máscaras do BIPED test, fora da coorte.",
  unknown:"Esses valores, isoladamente, NÃO demonstram que 254 significa borda. A semântica depende da documentação original.",
  question:"Você consultou uma fonte da versão do BIPED que confirme que 254 e 255 significam borda?",
  how:"Se não encontrou documento ou não sabe interpretar, escolha “Não consegui conferir”. Isso é uma resposta útil."},
 "GT_MULTICUE":{
  known:"Doze máscaras MultiCue do grupo excluído 4113 tinham os valores 0 e 65535.",
  unknown:"Não foi demonstrada documentalmente a polaridade para toda a coorte.",
  question:"Você encontrou na documentação do MultiCue que o valor 65535 representa borda?",
  how:"Não basta o número aparecer na imagem. Se não leu uma fonte que explique seu significado, marque “Não consegui conferir”."},
 "GT_MULTIANNOTATOR":{
  known:"Há seis anotações edges relacionadas a cada captura MultiCue no contrato proposto.",
  unknown:"A regra de agregar as seis avaliações deve ser aceita como escolha prévia, sem contá-las como seis fotos independentes.",
  question:"Você conferiu que cada foto MultiCue conta uma vez, combinando suas seis anotações sem multiplicar o tamanho da amostra?",
  how:"Leia a proposta do contrato multi-anotador. Se não teve acesso ao cálculo e às regras, marque que não conseguiu conferir."},
 "STAGE13C":{
  known:"O histórico registra acesso a GT BIPED train para verificações técnicas de dimensão.",
  unknown:"Esse registro sozinho não demonstra que os resultados jamais orientaram escolhas científicas.",
  question:"Você conseguiu conferir nos logs que o uso do GT no Stage13c não foi usado para ajustar os parâmetros do Paper A?",
  how:"Para responder SIM, verifique os relatórios de execução e a sequência histórica. Apenas ver uma foto não responde."},
 "BIPED_UNIVERSE":{
  known:"O inventário contém 198 candidatas BIPED; 125 foram escolhidas inicialmente.",
  unknown:"Algumas dessas fotos mostram a mesma cena. Ter 125 arquivos não equivale a 125 cenas independentes.",
  question:"Após comparar as imagens, você conseguiu identificar 125 cenas BIPED diferentes e elegíveis?",
  how:"Use as seções 02 e 03. Se restarem cenas suspeitas ou fotos não avaliadas, selecione “Não consegui conferir”."},
 "MULTICUE_SCENE":{
  known:"Existem 95 capturas MultiCue propostas; o grupo histórico 4113 foi excluído.",
  unknown:"A ausência de repetição entre as 95 capturas não está certificada apenas pelos nomes dos arquivos.",
  question:"Você conseguiu conferir que nenhuma das 95 capturas MultiCue representa a mesma cena ou uma captura dependente?",
  how:"Use a comparação de imagens e os metadados de sequência. Atenção ao alerta do prefixo 4108."},
 "UDED_LINEAGE":{
  known:"A checagem anterior não encontrou colisão exata de SHA-256 entre os originais comparados.",
  unknown:"Hashes diferentes não descartam fotos do mesmo lugar ou exposição anterior durante desenvolvimento.",
  question:"Você conseguiu excluir sobreposição de cena ou uso anterior entre UDED-14 e as imagens confirmatórias?",
  how:"É necessário examinar a história do desenvolvimento, não apenas os hashes. Se não conferiu, responda “Não consegui conferir”."},
 "SAMPLE_SIZE":{
  known:"O número 220 (125 BIPED + 95 MultiCue) e o poder estimado são provisórios e anteriores à confirmação.",
  unknown:"Uma duplicação de cena pode reduzir o número de observações independentes.",
  question:"Depois da revisão de cenas, o plano mantém um tamanho amostral justificado sem contar duplicatas como independentes?",
  how:"Não aprove o N só porque há 220 arquivos. Registre os agrupamentos e avalie se há alternativas suficientes."},
 "INFERENCE":{
  known:"O plano propõe H1 negativo, H2 positivo, Spearman por domínio, 100 mil permutações e correção de Holm.",
  unknown:"A adequação dessa escolha estatística exige leitura do protocolo e de seus critérios de dados ausentes e empates.",
  question:"Você leu o protocolo e confirmou que as regras de H1/H2 estão fixadas antes de abrir os resultados?",
  how:"Confira direções, correção Holm, unidade por cena, valores ausentes e critérios de exclusão."},
 "GT_EDGE_CASES":{
  known:"O executor v2 foi programado para interromper a análise ao encontrar máscaras com valores ou formatos inesperados.",
  unknown:"A forma de tratar esses casos e seus efeitos no N ainda precisa estar justificada no protocolo.",
  question:"Você encontrou no protocolo a regra a seguir se uma máscara estiver vazia, constante ou inválida?",
  how:"Se há ambiguidade, marque “Encontrei um problema” e descreva-a, ou “Não consegui conferir”."},
};
const P1_DESCRIPTIONS={
 "H1.membership":"Parâmetros que ajustam as duas características usadas na hipótese H1.",
 "H1.candidate_threshold":"Limiar escolhido durante o desenvolvimento para o operador candidato H1.",
 "H1.control_threshold":"Limiar escolhido durante o desenvolvimento para o controle H1.",
 "H2.membership":"Parâmetros que ajustam as três características da hipótese H2.",
 "H2.candidate_threshold":"Limiar escolhido para o operador candidato H2.",
 "H2.control_threshold":"Limiar escolhido para o controle H2.",
 "H2.capacity":"Pesos/capacidade ajustados para o operador Choquet H2."
};
function renderChecks(kind){
 const list=kind==="p1"?D.p1:D.science,id=kind==="p1"?"p1-list":"science-list";
 E(id).innerHTML=list.map((item,n)=>{
  const v=getCheck(kind,item.id);
  const p1=kind==="p1";
  const explain=p1?{
    known:"O pipeline recompôs o hash dos 14 exemplos de desenvolvimento UDED-14 para esta parte do ajuste.",
    unknown:"Isso não prova, sozinho, a ausência de cenas repetidas ou de exposição histórica.",
    question:"Você conseguiu conferir nos registros que este ajuste foi feito apenas com os 14 exemplos de desenvolvimento?",
    how:"Os identificadores de commit e SHA estão abaixo. Se você não os verificou, escolha “Não consegui conferir”."
   }:(CHECK_EXPLANATIONS[item.id]||{
    known:item.description||"",unknown:"Ainda precisa de revisão documental.",
    question:item.question,how:"Marque 'Não consegui conferir' se não dispõe de evidência."
   });
  const technical=p1?
   '<details class="technical"><summary>Ver dados técnicos usados como evidência</summary>'+
   '<p class="hint">'+esc(item.title)+" — "+esc(P1_DESCRIPTIONS[item.id]||"Parte ajustada em desenvolvimento")+'</p>'+
   '<p class="hash">Commit do ajuste: '+esc(item.commit)+'<br>SHA da lista UDED-14: '+esc(item.training_hash)+'</p>'+
   '<p class="hint">Arquivo: P1_LINEAGE_METADATA_CROSSCHECK_NOT_APPROVED.json</p></details>':
   '<details class="technical"><summary>Ver arquivo citado pela proposta</summary>'+
   '<p class="hash">'+esc(item.source||"Referência documental não especificada")+'</p>'+
   '<p class="hint">A referência é um caminho para verificação; não significa que esta tela tenha validado a documentação original.</p></details>';
  return '<article class="card guided-review" data-check="'+esc(kind+":"+item.id)+'">'+
   '<div class="toolbar"><span class="badge">Pergunta '+(n+1)+" / "+list.length+
   '</span><span class="badge '+(checkDone(kind,item.id)?"selected":"")+'">'+
   (checkDone(kind,item.id)?"Resposta registrada":"Ainda não respondida")+'</span></div>'+
   '<h3>'+esc(item.title)+'</h3>'+
   '<div class="evidence-explainer"><p><strong>O que o sistema já verificou ou registrou:</strong> '+esc(explain.known)+'</p>'+
   '<p><strong>O que ainda não podemos afirmar:</strong> '+esc(explain.unknown)+'</p></div>'+
   '<div class="question">'+esc(explain.question)+'</div>'+
   options(checkOptions,v.decision,kind,item.id)+
   '<p class="hint"><strong>Como responder:</strong> '+esc(explain.how)+'</p>'+
   technical+
   '<label>Qual documento você conferiu ou qual problema encontrou? '+
   '<span class="hint">'+(v.decision==="UNCERTAIN"?'Opcional quando não souber':
    'Obrigatório se marcou que conferiu ou encontrou um problema')+'</span>'+
   '<textarea data-check-evidence="'+esc(kind+":"+item.id)+'" placeholder="Ex.: conferi o arquivo X, seção Y; ou não encontrei documentação suficiente.">'+
   esc(v.evidence||"")+'</textarea></label>'+
   '<p class="hint">Uma resposta “Não consegui conferir” registra a pendência; não aprova o freeze.</p>'+
   '</article>';
 }).join("");
}
for(const kind of ["p1","science"]){
 const id=kind==="p1"?"p1-list":"science-list";
 E(id).addEventListener("click",e=>{
  const b=e.target.closest("[data-kind]");if(!b)return;
  const v=getCheck(kind,b.dataset.key);v.decision=b.dataset.value;
  persist();renderChecks(kind);
 });
 E(id).addEventListener("input",e=>{
  if(e.target.matches("[data-check-evidence]")){
   const k=e.target.dataset.checkEvidence.split(":");
   getCheck(k[0],k.slice(1).join(":")).evidence=e.target.value;persist();
  }
 });
}
function payload(){return{schema:"paper_a_human_local_visual_review_293_v1",status:"DRAFT_HUMAN_REVIEW_NOT_SCIENTIFIC_SIGNOFF",generated_utc:new Date().toISOString(),source_sha256:D.meta,reviewer:S.meta,review_notes:S.notes,stats:stats(),group_reviews:D.groups.map(g=>({id:g.id,image_ids:g.ids,...getGroup(g.id),complete:groupDone(g)})),capture_reviews:D.items.map(i=>({dataset:i.dataset,image_id:i.id,original_sha256:i.sha256,in_initial_cohort:i.in_initial_cohort,scene_group:i.scene_group,flagged_group:groupById[i.id]||null,...getImage(i.dataset+":"+i.id),comparisons_summary:Object.entries(getImage(i.dataset+":"+i.id).pairReviews||{}).map(([ref,val])=>ref+": "+val).join("; "),complete:imageDone(i)})),P1_seven_review:D.p1.map(x=>({id:x.id,title:x.title,...getCheck("p1",x.id),complete:checkDone("p1",x.id)})),methodological_review:D.science.map(x=>({id:x.id,title:x.title,...getCheck("science",x.id),complete:checkDone("science",x.id)})),scientific_signoff_granted:false,protected_GT_access_authorized:false}}
function download(text,filename,type){const url=URL.createObjectURL(new Blob([text],{type}));const a=document.createElement("a");a.href=url;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),4000)}
function stamp(){return new Date().toISOString().replace(/[:.]/g,"-").slice(0,19)}
function exportJson(){download(JSON.stringify(payload(),null,2),"PaperA_QUIZ_293_"+stamp()+".json","application/json;charset=utf-8")}
function report(){const p=payload();function table(title,rows,cols){return '<section><h2>'+esc(title)+'</h2><table><thead><tr>'+cols.map(c=>'<th>'+esc(c[0])+'</th>').join("")+'</tr></thead><tbody>'+rows.map(row=>'<tr>'+cols.map(c=>'<td>'+esc(Array.isArray(row[c[1]])?row[c[1]].join(", "):row[c[1]]??"PENDENTE")+'</td>').join("")+'</tr>').join("")+'</tbody></table></section>'}
 const sections=[table("22 grupos",p.group_reviews,[["Grupo","id"],["Imagens","image_ids"],["Decisão","decision"],["Estruturas observadas","cue"],["Mesma cena que a primeira","sameAsFirst"],["Manter","representative"],["Subgrupos","subgroups"],["Observação","evidence"]]),table("293 imagens",p.capture_reviews,[["Dataset","dataset"],["Imagem","image_id"],["Na seleção","in_initial_cohort"],["Comparações par-a-par","comparisons_summary"],["Cena","scene"],["Histórico","exposure"],["Justificativa","evidence"]]),table("7 provas P1",p.P1_seven_review,[["ID","id"],["Decisão","decision"],["Justificativa","evidence"]]),table("10 questões científicas",p.methodological_review,[["Tema","title"],["Decisão","decision"],["Justificativa","evidence"]])];
return '<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Paper A — parecer de revisão</title><style>body{font:14px/1.5 Segoe UI,Arial,sans-serif;max-width:1180px;padding:25px;margin:auto;color:#253649}h1{color:#14667a}h2{margin-top:30px}table{width:100%;border-collapse:collapse;font-size:12px}th,td{border:1px solid #d3e1e8;padding:7px;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:#eef5f7}.warning{border-left:5px solid #cc954d;background:#fff6e7;padding:14px}</style><h1>Paper A · Relatório de revisão pré-freeze</h1><div class="warning"><b>NÃO É APROVAÇÃO CIENTÍFICA INDEPENDENTE NEM AUTORIZAÇÃO DE FREEZE.</b> Decisões humanas declaradas pelo responsável abaixo. Não abre GT/F1 e não confirma H1/H2.</div><p><b>Avaliador:</b> '+esc(p.reviewer.reviewer)+' · <b>Vínculo:</b> '+esc(p.reviewer.affiliation)+' · <b>Papel:</b> '+esc(p.reviewer.role)+'<br><b>Participação prévia:</b> '+esc(p.reviewer.conflicts)+'<br><b>Gerado:</b> '+esc(p.generated_utc)+'<br><b>Completos:</b> '+p.stats.total+' / '+p.stats.maximum+'<br><b>Planilha SHA:</b> '+esc(p.source_sha256.cohort_sheet_sha256)+'</p><p><b>Observações gerais:</b> '+esc(p.review_notes)+'</p>'+sections.join("")+'<script id="report-data" type="application/json">'+JSON.stringify(p).replace(/</g,"\\u003c")+'<\/script></html>'}
function exportCsv(){const items=payload().capture_reviews,keys=["dataset","image_id","original_sha256","in_initial_cohort","flagged_group","comparisons_summary","scene","exposure","evidence","complete"];const q=x=>'"'+String(x??"").replace(/"/g,'""')+'"';download("\uFEFF"+[keys.join(";"),...items.map(row=>keys.map(k=>q(row[k])).join(";"))].join("\r\n"),"PaperA_TRIAGEM_293_"+stamp()+".csv","text/csv;charset=utf-8")}
function renderFinal(){const st=stats(),groupProblems=D.groups.filter(g=>["ONE","SUBGROUPS"].includes((S.groups[g.id]||{}).decision)).length,imageProblems=D.items.filter(i=>["GROUP","EXCLUDE"].includes((S.images[i.dataset+":"+i.id]||{}).scene)||(S.images[i.dataset+":"+i.id]||{}).exposure==="EXPOSURE").length;
 E("final-status").innerHTML='<div class="metrics"><div><b>'+st.total+'/'+st.maximum+'</b><span>Itens respondidos, inclusive “não sei”</span></div><div><b>'+groupProblems+'</b><span>Grupos com possível repetição</span></div><div><b>'+imageProblems+'</b><span>Imagens sinalizadas</span></div><div><b>'+((st.maximum-st.total))+'</b><span>Itens pendentes</span></div></div><div class="progress-warning"><b>Revisão científica ainda não concluída automaticamente.</b><p>'+((st.maximum-st.total)>0?"Existem itens sem decisão completa. O relatório sinalizará as omissões.":"Todos os itens têm respostas; isso não certifica a independência ou autoriza o freeze.")+'</p></div>';
}
E("save-top").addEventListener("click",exportJson);
E("export-json").addEventListener("click",exportJson);
E("generate-report").addEventListener("click",()=>{if(!S.meta.reviewer.trim()&&!confirm("Sem nome do avaliador. Exportar relatório incompleto?"))return;download(report(),"PaperA_RELATORIO_293_"+stamp()+".html","text/html;charset=utf-8")});
E("export-csv").addEventListener("click",exportCsv);
E("import-json").addEventListener("click",()=>E("json-input").click());
E("json-input").addEventListener("change",async e=>{const file=e.target.files[0];if(!file)return;try{const p=JSON.parse(await file.text());if(p.schema!=="paper_a_human_local_visual_review_293_v1"||p.source_sha256.cohort_sheet_sha256!==D.meta.cohort_sheet_sha256||p.source_sha256.candidate_sha256!==D.meta.candidate_sha256||p.capture_reviews.length!==293)throw Error("Arquivo não corresponde ao inventário, coorte ou versão");if(!confirm("Importar e substituir todas as respostas desta aba?"))return;
 S=STATE();S.meta=p.reviewer||S.meta;S.notes=p.review_notes||"";for(const g of p.group_reviews||[])if(D.groups.some(x=>x.id===g.id))S.groups[g.id]={decision:g.decision,representative:g.representative,subgroups:g.subgroups,evidence:g.evidence,cue:g.cue||"",sameAsFirst:Array.isArray(g.sameAsFirst)?g.sameAsFirst:[]};for(const i of p.capture_reviews||[])if(lookup[i.dataset+":"+i.image_id])S.images[i.dataset+":"+i.image_id]={scene:i.scene,exposure:i.exposure,evidence:i.evidence,pairReviews:i.pairReviews&&typeof i.pairReviews==="object"?i.pairReviews:{}};for(const i of p.P1_seven_review||[])if(D.p1.some(x=>x.id===i.id))S.p1[i.id]={decision:i.decision,evidence:i.evidence};for(const i of p.methodological_review||[])if(D.science.some(x=>x.id===i.id))S.science[i.id]={decision:i.decision,evidence:i.evidence};persist();for(const id of ["reviewer","affiliation","role","conflicts"])E(id).value=S.meta[id]||"";E("overall-notes").value=S.notes;go("relatorio");alert("Respostas importadas. Revise os dados antes de exportar.");
 }catch(e){alert("Falha ao importar: "+e.message)}e.target.value=""});
E("reset").addEventListener("click",()=>{if(!confirm("Apagar TODAS as respostas locais? Exporte JSON antes."))return;S=STATE();localStorage.removeItem(key);location.reload()});
updateProgress();renderGroup();
})();