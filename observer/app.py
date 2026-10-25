from flask import Flask, jsonify, render_template_string
from pathlib import Path
from datetime import datetime
from collections import deque
import psutil, subprocess, time, os, re, json

ROOT=Path(os.environ.get('MFI_EDGE_ROOT',r'C:\Users\Windows 11\Documents\MFI-Edge'))
PORT=int(os.environ.get('MFI_EDGE_OBSERVER_PORT','8765'))
app=Flask(__name__)
events=deque(maxlen=100); seen={}

HTML='''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MFI-Edge Research Console</title><style>
:root{color-scheme:dark;--bg:#0b0f14;--p:#121a24;--b:#263445;--t:#eef4fb;--m:#8fa2b7;--g:#4bd18b;--y:#f4c95d;--r:#ff6b6b;--a:#64a8ff}*{box-sizing:border-box}body{margin:0;background:#0b0f14;color:var(--t);font-family:Inter,system-ui,Segoe UI,Arial,sans-serif}.w{max-width:1500px;margin:auto;padding:20px}.head{display:flex;justify-content:space-between;gap:15px;align-items:center;flex-wrap:wrap;margin-bottom:16px}h1{margin:0;font-size:26px}.sub{color:var(--m);font-size:13px}.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:12px}.c{background:linear-gradient(180deg,#121a24,#0d141d);border:1px solid var(--b);border-radius:14px;padding:14px;overflow:hidden}.s3{grid-column:span 3}.s5{grid-column:span 5}.s6{grid-column:span 6}.s7{grid-column:span 7}.s12{grid-column:span 12}@media(max-width:1000px){.s3,.s5,.s6,.s7,.s12{grid-column:span 12}}.lab{color:var(--m);font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.08em}.big{font-size:27px;font-weight:800;margin-top:5px}.mid{font-size:17px;font-weight:700;margin-top:6px}.g{color:var(--g)}.r{color:var(--r)}.a{color:var(--a)}.bar{height:12px;background:#182331;border:1px solid var(--b);border-radius:99px;overflow:hidden;margin-top:10px}.fill{height:100%;background:linear-gradient(90deg,#4389ef,#67c0ff);width:0}.k{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:10px}.kv{background:#0a1118;border:1px solid var(--b);border-radius:9px;padding:8px}.v{font-size:19px;font-weight:800;margin-top:3px}table{width:100%;border-collapse:collapse;font-size:12px}th,td{text-align:left;padding:7px;border-bottom:1px solid var(--b)}th{color:var(--m);text-transform:uppercase;font-size:10px}pre,.tree{font:12px/1.5 Consolas,monospace;white-space:pre-wrap;word-break:break-word}pre{background:#080c11;border:1px solid var(--b);border-radius:9px;padding:10px;max-height:280px;overflow:auto}.ev{display:grid;grid-template-columns:75px 80px 1fr;gap:8px;padding:7px 0;border-bottom:1px solid var(--b);font-size:12px}.mut{color:var(--m)}.badge{border:1px solid var(--b);border-radius:99px;padding:6px 10px;font-size:12px}.dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--m);margin-right:6px}.dot.on{background:var(--g)}
</style></head><body><div class="w"><div class="head"><div><h1>MFI-Edge Research Console</h1><div class="sub">Observador externo · sem alterar o MFI</div></div><div class="badge"><span id="dot" class="dot"></span><span id="health">carregando…</span></div></div><div class="grid">
<div class="c s3"><div class="lab">Autopilot</div><div id="auto" class="big">—</div><div id="autod" class="sub">—</div></div>
<div class="c s3"><div class="lab">Etapa inferida</div><div id="stage" class="big a">—</div><div id="exp" class="sub">—</div></div>
<div class="c s3"><div class="lab">Processo ativo</div><div id="proc" class="big">—</div><div id="procd" class="sub">—</div></div>
<div class="c s3"><div class="lab">Última atividade</div><div id="last" class="big">—</div><div id="lastt" class="sub">—</div></div>
<div class="c s7"><div class="lab">Progresso detectado</div><div id="ptitle" class="mid">—</div><div class="bar"><div id="pbar" class="fill"></div></div><div class="k"><div class="kv"><div class="lab">Atual</div><div id="pc" class="v">—</div></div><div class="kv"><div class="lab">Total</div><div id="pt" class="v">—</div></div><div class="kv"><div class="lab">Percentual</div><div id="pp" class="v">—</div></div><div class="kv"><div class="lab">Melhor F1</div><div id="pf" class="v">—</div></div></div></div>
<div class="c s5"><div class="lab">Git</div><div id="branch" class="mid">—</div><div id="head" class="sub">—</div><div id="gitd" class="sub" style="margin-top:10px">—</div></div>
<div class="c s6"><div class="lab">Árvore de processos</div><div id="tree" class="tree">—</div></div>
<div class="c s6"><div class="lab">Processos relevantes</div><table><thead><tr><th>PID</th><th>Processo</th><th>Tempo</th><th>CPU</th><th>RAM</th></tr></thead><tbody id="ptable"></tbody></table></div>
<div class="c s7"><div class="lab">Stream de eventos</div><div id="events"></div></div>
<div class="c s5"><div class="lab">Arquivos recentes</div><table><thead><tr><th>Arquivo</th><th>Hora</th></tr></thead><tbody id="files"></tbody></table></div>
<div class="c s12"><div class="lab">Comando ativo / contexto</div><pre id="cmd">—</pre></div>
</div></div><script>
const esc=s=>String(s??'').replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));async function tick(){try{let d=await (await fetch('/api/status',{cache:'no-store'})).json();dot.className='dot '+(d.active?'on':'');health.textContent=d.active?'observação ativa':'sem processo detectado';auto.textContent=d.autopilot?'RODANDO':'PARADO';auto.className='big '+(d.autopilot?'g':'r');autod.textContent=d.autopilot_detail||'—';stage.textContent=d.stage||'—';exp.textContent=d.experiment||'—';proc.textContent=d.active_process?.name||'—';procd.textContent=d.active_process?`PID ${d.active_process.pid} · ${d.active_process.elapsed}`:'—';last.textContent=d.files[0]?.name||'—';lastt.textContent=d.files[0]?.time||'—';ptitle.textContent=d.progress?.label||'Nenhum progresso estruturado';let pct=d.progress?.percent||0;pbar.style.width=pct+'%';pc.textContent=d.progress?.current??'—';pt.textContent=d.progress?.total??'—';pp.textContent=d.progress?pct.toFixed(1)+'%':'—';pf.textContent=d.progress?.best_f1==null?'—':Number(d.progress.best_f1).toFixed(4);branch.textContent=d.git.branch||'—';head.textContent=d.git.head?`${d.git.head.slice(0,8)} · ${d.git.message}`:'—';gitd.textContent=`${d.git.dirty?'working tree modificado':'working tree limpo'} · ahead ${d.git.ahead??'—'} · behind ${d.git.behind??'—'}`;tree.textContent=d.tree||'—';ptable.innerHTML=d.processes.map(p=>`<tr><td>${p.pid}</td><td>${esc(p.name)}</td><td>${esc(p.elapsed)}</td><td>${p.cpu.toFixed(1)}%</td><td>${p.ram.toFixed(0)} MB</td></tr>`).join('');events.innerHTML=d.events.map(x=>`<div class="ev"><div class="mut">${x.time}</div><div>${x.kind}</div><div>${esc(x.message)}</div></div>`).join('');files.innerHTML=d.files.slice(0,18).map(x=>`<tr><td title="${esc(x.path)}">${esc(x.name)}</td><td>${x.time}</td></tr>`).join('');cmd.textContent=d.active_process?.cmd||'—'}catch(e){health.textContent='erro de leitura'}}tick();setInterval(tick,3000);
</script></body></html>'''

def cmd(args):
    try:
        p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=4);return p.stdout.strip(),p.returncode
    except:return '',1

def dur(sec):
    s=max(0,int(sec));h,r=divmod(s,3600);m,s=divmod(r,60);return f'{h:02d}:{m:02d}:{s:02d}'

def proc_snapshot():
    out=[]
    for p in psutil.process_iter(['pid','ppid','name','cmdline','create_time','memory_info']):
        try:
            n=p.info['name'] or ''; c=' '.join(p.info['cmdline'] or []); low=(n+' '+c).lower()
            if not (('mfi-edge' in low or 'research_controller' in low or 'matlab' in n.lower() or 'codex' in low) and any(k in low for k in ('python','matlab','codex','powershell','pwsh'))): continue
            out.append({'pid':p.info['pid'],'ppid':p.info['ppid'],'name':n,'cmd':c,'elapsed':dur(time.time()-p.info['create_time']),'cpu':p.cpu_percent(None),'ram':(p.info['memory_info'].rss/1048576 if p.info['memory_info'] else 0),'ct':p.info['create_time']})
        except: pass
    return sorted(out,key=lambda x:x['ct'])

def tree(rows):
    by={r['pid']:r for r in rows}; kids={}
    for r in rows:kids.setdefault(r['ppid'],[]).append(r)
    roots=[r for r in rows if r['ppid'] not in by]; lines=[]
    def walk(r,p='',last=True):
        lines.append(p+('└─ ' if last else '├─ ')+f"{r['name']} PID {r['pid']} [{r['elapsed']}]")
        ks=kids.get(r['pid'],[])
        for i,k in enumerate(ks): walk(k,p+('   ' if last else '│  '),i==len(ks)-1)
    for i,r in enumerate(roots):walk(r,'',i==len(roots)-1)
    return '\n'.join(lines)

def infer(rows):
    blob='\n'.join(r['cmd'] for r in rows)
    for p in [ROOT/'automation'/'experiments.json',ROOT/'automation'/'SCIENTIFIC_CONTEXT.md',ROOT/'ROADMAP.md']:
        try:
            if p.exists(): blob+='\n'+p.read_text(encoding='utf-8',errors='ignore')[-10000:]
        except: pass
    exps=re.findall(r'(stage\d+[a-z]?[^\\/\'\"\s]*)',blob,re.I); exp=exps[-1] if exps else None
    m=re.search(r'stage(\d+)([a-z]?)',exp or '',re.I); stage=(f'Stage {m.group(1)}{m.group(2).upper()}' if m else None)
    return stage,exp

def progress():
    ps=[]
    try:
        for p in ROOT.rglob('*.partial.json'):
            try: ps.append((p.stat().st_mtime,p))
            except:pass
    except:pass
    if not ps:return None
    ps.sort(reverse=True); p=ps[0][1]
    try:d=json.loads(p.read_text(encoding='utf-8'))
    except:return None
    rows=d if isinstance(d,list) else ([d] if isinstance(d,dict) else [])
    vals=[r.get('f_measure') for r in rows if isinstance(r,dict) and isinstance(r.get('f_measure'),(int,float))]
    return {'label':p.name.replace('.partial.json',''),'current':len(rows),'total':99,'percent':len(rows)/99*100,'best_f1':max(vals) if vals else None}

def gitstat():
    b,_=cmd(['git','branch','--show-current']); h,_=cmd(['git','rev-parse','HEAD']); m,_=cmd(['git','log','-1','--pretty=%s']); por,_=cmd(['git','status','--porcelain']); a=be=None; o,rc=cmd(['git','rev-list','--left-right','--count','HEAD...@{upstream}'])
    if rc==0 and o:
        try:a,be=map(int,o.split())
        except:pass
    return {'branch':b,'head':h,'message':m,'dirty':bool(por),'ahead':a,'behind':be}

def recent_files():
    arr=[]
    for base in [ROOT/'results',ROOT/'automation',ROOT/'docs']:
        if not base.exists():continue
        for p in base.rglob('*'):
            if p.is_file():
                try:s=p.stat();arr.append((s.st_mtime,p))
                except:pass
    arr.sort(reverse=True,key=lambda x:x[0]);return [{'name':p.name,'path':str(p.relative_to(ROOT)),'time':datetime.fromtimestamp(mt).strftime('%H:%M:%S'),'mtime':mt} for mt,p in arr[:40]]

def track(fs,ps):
    for f in fs[:20]:
        old=seen.get(f['path']); seen[f['path']]=f['mtime']
        if old is not None and f['mtime']>old:events.appendleft({'time':datetime.now().strftime('%H:%M:%S'),'kind':'ARQUIVO','message':'modificado: '+f['path']})
    pids={p['pid'] for p in ps}; known={int(k[4:]) for k in seen if k.startswith('pid:')}
    for p in ps:
        if p['pid'] not in known:seen['pid:'+str(p['pid'])]=time.time();events.appendleft({'time':datetime.now().strftime('%H:%M:%S'),'kind':'PROC','message':f"iniciado: {p['name']} PID {p['pid']}"})
    for pid in known-pids:events.appendleft({'time':datetime.now().strftime('%H:%M:%S'),'kind':'PROC','message':f'encerrado: PID {pid}'});seen.pop('pid:'+str(pid),None)

@app.route('/')
def index():return render_template_string(HTML)
@app.route('/api/status')
def status():
    ps=proc_snapshot(); fs=recent_files(); track(fs,ps); stage,exp=infer(ps); pr=progress(); gs=gitstat(); auto=next((p for p in ps if 'research_controller' in p['cmd'].lower() or 'autopilot' in p['cmd'].lower()),None); active=next((p for p in reversed(ps) if 'matlab' in p['name'].lower()),None) or next((p for p in reversed(ps) if 'python' in p['name'].lower()),None) or (ps[-1] if ps else None)
    return jsonify({'active':active is not None,'autopilot':auto is not None,'autopilot_detail':(f"PID {auto['pid']} · {auto['elapsed']}" if auto else 'controller não detectado'),'stage':stage,'experiment':exp,'active_process':active,'progress':pr,'git':gs,'processes':ps,'tree':tree(ps),'files':fs,'events':list(events)[:80]})

if __name__=='__main__':
    print(f'Local: http://127.0.0.1:{PORT}'); app.run(host='0.0.0.0',port=PORT,debug=False,threaded=True)
