#!/usr/bin/env python3
"""Paper A N219: restricted original-only visual audit over a localhost/Tailscale Serve proxy.

No GT/H5/map/F1/outcome access. DRAFT reviewer notes are never scientific PASS.
Zero runtime dependencies beyond Pillow (used for authorized RGB thumbnails).
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
import re
import secrets
import sys
import threading
import time
from urllib.parse import parse_qs, unquote, urlsplit
import zipfile

try:
    from PIL import Image, ImageOps, ImageFile
    Image.MAX_IMAGE_PIXELS = 60_000_000
    ImageFile.LOAD_TRUNCATED_IMAGES = False
    PIL_OK = True
except ImportError:
    PIL_OK = False

DEFAULT_DATA = Path(r'F:\MFI-Edge-Data\MultiCue')
UI_DIR = Path(__file__).resolve().parent / 'paper_a_mobile_review'
IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
BAD_PARTS = {'gt', 'ground-truth', 'ground_truth', 'groundtruth', 'edge_maps', 'annotations',
             'prediction', 'predictions', 'results', 'maps', 'scores', 'f1', 'labels',
             'masks', 'mask', 'h5', 'hdf5', '.git', 'test_gt'}
FIELDS = ('dataset','image_id','relative_path','image_sha256','independence_review',
          'prior_exposure_review','scene_group','notes')
TOPICS = ('scenes','conflicts','exposure','p1','gt','statistics','protocol','final')
CHOICES = ('PENDING','PRELIMINARY_APPROVE','NEEDS_EVIDENCE','REJECT')
SCENE = ('PENDING','APPEARS_INDEPENDENT','POSSIBLE_DUPLICATE','CONFIRMED_DUPLICATE')
EXPOSURE = ('PENDING','NO_EVIDENCE_IDENTIFIED','POSSIBLE_PRIOR_USE','DOCUMENTED_PRIOR_USE')


def utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    name = path.with_name('.' + path.name + '.' + secrets.token_hex(8) + '.tmp')
    try:
        with name.open('xb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        try: name.unlink(missing_ok=True)
        except OSError: pass


def load_csv(path:Path, maxsize=15_000_000) -> list[dict]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size>maxsize:
        raise ValueError('CSV ausente ou nao seguro: '+str(path))
    with path.open('r',encoding='utf-8-sig',newline='') as stream:
        return list(csv.DictReader(stream))


def load_json(path:Path, maxsize=8_000_000) -> dict:
    if not path.is_file() or path.is_symlink() or path.stat().st_size>maxsize:
        raise ValueError('JSON ausente ou nao seguro: '+str(path))
    with path.open('r',encoding='utf-8-sig') as stream:
        doc=json.load(stream)
    if not isinstance(doc,dict):raise ValueError('Formato JSON invalido: '+str(path))
    return doc


def within(path:Path, root:Path) -> bool:
    try:
        return path.resolve(strict=True).is_relative_to(root.resolve(strict=True))
    except (ValueError,OSError):
        return False


def safe_original(base:Path, name:str) -> Path|None:
    # Do not accept paths, symlinks or filename fragments from the browser.
    if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,160}', name):return None
    if '/' in name or '\\' in name or name.startswith('.') or Path(name).suffix.lower() not in IMAGE_EXT:return None
    p=base/name
    if p.is_symlink() or not p.is_file() or not within(p,base):return None
    if p.stat().st_size > 45_000_000:return None
    return p


def csv_from_text(path:Path) -> list[dict]:
    if not path.is_file():return []
    try:return load_csv(path)
    except (ValueError,UnicodeDecodeError,OSError):return []


class ReviewData:
    def __init__(self, repo:Path, data:Path, state_dir:Path|None=None):
        self.repo=repo.resolve()
        self.data=data
        self.work=data/'paper_a_completion'
        self.signoff=self.work/'scientific_signoff'
        self.state_dir=state_dir or (self.signoff/'MOBILE_A219_RASCUNHO')
        self.path_roster=self.signoff/'COORTE_A_N219_PARA_REVISAO_NAO_FROZEN.csv'
        self.path_sheet=self.signoff/'CANDIDATE_A_N219_SCIENCE_REVIEW_NOT_ACTIVE'/'REVIEW_A_N219_ALL_PENDING.csv'
        self.path_cfg=self.repo/'docs/paper_a_confirmation/COORTE_A_N219_PROPOSTA_NAO_CONGELADA.json'
        self.path_preview=self.signoff/'FROZEN_PROTOCOL_BYTES_TO_REVIEW_NOT_ACTIVE.json'
        self.path_power=self.signoff/'PODER_A_N219_SENSIBILIDADE_NAO_APROVADA.json'
        self.path_active=self.repo/'docs/paper_a_confirmation/protocol.json'
        self.path_p1=self.repo/'docs/paper_a_confirmation/P1_DEVELOPMENT_RECIPE_UNATTESTED.json'
        self.path_stage=self.repo/'results/automation/stage13c_biped_preflight/summary.json'
        self.path_old=self.signoff/'REVIEW_220_IMAGES_PENDING.csv'
        self.path_readiness=self.signoff/'COORTE_A_N219_READINESS_NOT_APPROVED.json'
        self.bases={
            'BIPED':self.repo/'datasets/BIPEDv2/edges/imgs/train/rgbr/real',
            'MultiCue':self.data/'source_frames_only',
        }
        self.optional={
            'biped_test':self.repo/'datasets/BIPEDv2/edges/imgs/test/rgbr',
            'biped_train':self.bases['BIPED'],
            'multicue_pool':self.bases['MultiCue'],
        }
        self._lock=threading.RLock()
        self.visual={}
        self.hashes={}
        self.refs={}
        self.p1parts=[]
        self.provenance=[]
        self.items=[]
        self.images={}
        self.source_sets={}
        self.matched_id={}
        self.stage={}
        self.power={}
        self.status={}
        self.decisions={}
        self._load()

    def _load(self):
        cfg=load_json(self.path_cfg)
        roster=load_csv(self.path_roster)
        review=load_csv(self.path_sheet)
        preview=load_json(self.path_preview)
        power=load_json(self.path_power)
        active=load_json(self.path_active)
        readiness=load_json(self.path_readiness)
        if not PIL_OK:
            raise RuntimeError('Pillow não está instalado na .venv. Instale com python -m pip install Pillow')
        if cfg.get('status')!='PROPOSAL_NOT_FROZEN_NOT_APPROVED' or cfg.get('counts')!={'BIPED':125,'MultiCue':94,'N':219}:
            raise ValueError('Proposta A219 foi alterada ou esta ativa. Recusando abrir painel.')
        if (len(roster)!=219 or len(review)!=219 or
            Counter(r.get('dataset') for r in roster)!={'BIPED':125,'MultiCue':94}):
            raise ValueError('Rosters A219 nao possuem exatamente 219 linhas.')
        if active.get('status')!='draft_not_frozen' or active.get('confirmatory_outcomes_opened') is not False:
            raise ValueError('Protocolo ativo nao esta em draft nao-confirmatorio.')
        if preview.get('cohort',{}).get('target_n_independent_images')!=219 or preview.get('freeze_commit') is not None:
            raise ValueError('Previa de freeze nao corresponde a A219.')
        if power.get('GT_opened') is not False or power.get('H1_H2_executed') is not False:
            raise ValueError('Relatorio de poder reporta acesso confirmatorio; interromper.')
        if (self.work/'freeze_approval.json').exists() or (self.signoff/'FINAL_INDEPENDENT_REVIEW.json').exists():
            raise ValueError('Assinatura ou freeze ja presente; painel de pre-freeze nao deve alterar o estado.')
        if cfg.get('source_cohort_sha256') != sha_file(self.path_old):
            raise ValueError('A revisão inicial de 220 originais foi alterada após a seleção A219.')
        if (readiness.get('status')!='A_N219_ORIGINAL_SHA_VERIFIED_SCIENCE_GATES_OPEN' or
            readiness.get('counts')!=cfg.get('counts') or
            readiness.get('review_roster_sha256')!=sha_file(self.path_roster) or
            readiness.get('scientific_signoff') is not False or
            readiness.get('GT_accessed') is not False):
            raise ValueError('Readiness A219 incompatível; o painel exige a auditoria original sem aprovação.')
        self.cfg=cfg
        self.power=power
        self.stage=load_json(self.path_stage) if self.path_stage.is_file() else {'status':'INDISPONIVEL'}
        self.hashes={
            'roster':sha_file(self.path_roster),
            'review':sha_file(self.path_sheet),
            'preview':sha_file(self.path_preview),
            'power':sha_file(self.path_power),
            'candidate':sha_file(self.path_cfg),
            'active':sha_file(self.path_active),
            'readiness':sha_file(self.path_readiness),
        }
        planned=cfg['images']
        sha_lines=sorted(f"{r['dataset']}|{r['image_id']}|{r['image_sha256']}\n" for r in roster)
        if hashlib.sha256(''.join(sha_lines).encode('utf-8')).hexdigest()!=cfg.get('roster_sha256_sorted_dataset_id_source_sha'):
            raise ValueError('Digest dos 219 hashes não corresponde à proposta A219.')
        expected=[(ds,iid) for ds in ('BIPED','MultiCue') for iid in planned[ds].split(',')]
        if [(r['dataset'],r['image_id']) for r in roster]!=expected:
            raise ValueError('Ordem/IDs da proposta sao diferentes do inventario A219.')
        initial={r['image_id'] for r in load_csv(self.path_old) if r['dataset']=='BIPED'}
        if sum(r['dataset']=='BIPED' and r['image_id'] in initial for r in roster)!=83:
            raise ValueError('83 BIPED da selecao inicial nao foram conservadas.')
        resources=UI_DIR
        evidence_candidates=[resources/'evidencias_a219.csv',
            self.signoff/'A219_EVIDENCIAS_219_LINHAS_SEM_PASS.csv',
            self.repo/'docs/paper_a_confirmation/A219_EVIDENCIAS_219_LINHAS_SEM_PASS.csv']
        evidence=next((csv_from_text(p) for p in evidence_candidates if csv_from_text(p)),[])
        evidence_map={(r.get('dataset'),r.get('image_id')):r for r in evidence}
        review_map={(r.get('dataset'),r.get('image_id')):r for r in review}
        for r in roster:
            ds,iid=r['dataset'],r['image_id']
            proof=evidence_map.get((ds,iid),{})
            if proof and proof.get('image_sha256')!=r['image_sha256']:
                proof={}  # do not join stale evidence to a new source SHA
            rv=review_map.get((ds,iid),{})
            if any(rv.get(k)!=r.get(k) for k in ('dataset','image_id','relative_path','image_sha256')):
                raise ValueError('Planilha de revisao difere da coorte A219: '+iid)
            if (rv.get('independence_review')!='pending' or rv.get('prior_exposure_review')!='pending' or
                rv.get('reviewer_independence_decision') not in ('PENDING','') or
                rv.get('reviewer_prior_exposure_decision') not in ('PENDING','')):
                raise PermissionError('Avaliação independente não pode estar pré-aprovada: '+iid)
            p=safe_original(self.bases[ds],r['relative_path'])
            if p is None:raise ValueError('Original RGB faltando/nao permitido: '+ds+'/'+iid)
            key=f'{ds}:{iid}'
            self.images[key]={'path':p,'dataset':ds,'id':iid,'origin':'A219',
                'sha':r['image_sha256']}
            obj={
                'key':key,'dataset':ds,'image_id':iid,
                'sha256':r['image_sha256'],'file':r['relative_path'],
                'new_biped':ds=='BIPED' and iid not in initial,
                'scene_observation':proof.get('quiz_scene_response','SEM_DADO'),
                'exposure_observation':proof.get('quiz_exposure_response','SEM_DADO'),
                'scene_note':proof.get('quiz_scene_evidence',''),
                'group_note':proof.get('quiz_group_decisions',''),
                'historical_note':proof.get('historical_technical_gt_contact_context',''),
                'reviewer_attention':proof.get('reviewer_action_required',rv.get('historical_attention','')),
                'related_pairs':proof.get('reviewed_selected_pair_relations',''),
                'thumbnail':f'/api/thumb/{key}',
                'full':f'/api/full/{key}',
            }
            self.items.append(obj)
            self.matched_id.setdefault(iid,[]).append(key)
        # Check every displayed candidate original against the scientifically
        # selected RGB source SHA. Never touch annotations or predictions.
        for im in self.images.values():
            if im['sha'] is not None and sha_file(im['path'])!=im['sha']:
                raise PermissionError('Imagem original diverge do inventário A219: '+im['id'])
        self.source_sets={'A219':[x['key'] for x in self.items]}
        for name,base in self.optional.items():
            ids=[]
            if base.is_dir():
                for p in sorted(base.iterdir()):
                    if not p.is_file() or p.suffix.lower() not in IMAGE_EXT:continue
                    original=safe_original(base,p.name)
                    if original is None:continue
                    key=f'pool:{name}:{p.stem}'
                    if key not in self.images:
                        self.images[key]={'path':original,'dataset':name,'id':p.stem,
                            'origin':name,'sha':None}
                        self.matched_id.setdefault(p.stem,[]).append(key)
                    ids.append(key)
            self.source_sets[name]=ids
        # UDED development sources if original-only folders are available.
        development=[]
        dataset_root=self.repo/'datasets'
        if dataset_root.is_dir():
            for candidate in sorted(dataset_root.iterdir()):
                if not candidate.is_dir() or 'uded' not in candidate.name.lower():continue
                for sub in ('images','imgs','originals','rgb'):
                    directory=candidate/sub
                    if not directory.is_dir():continue
                    for p in list(sorted(directory.iterdir()))[:1000]:
                        if p.suffix.lower() not in IMAGE_EXT or not p.is_file():continue
                        valid=safe_original(directory,p.name)
                        if valid is None:continue
                        key='pool:uded:'+p.stem
                        if key not in self.images:
                            self.images[key]={'path':valid,'dataset':'UDED','id':p.stem,
                                'origin':'UDED_origem_disponivel','sha':None}
                            development.append(key)
        self.source_sets['uded_originais_disponiveis']=development
        self.p1parts=csv_from_text(resources/'proveniencias_p1.csv')
        if not self.p1parts and self.path_p1.is_file():
            recipe=load_json(self.path_p1)
            for h in recipe.get('hypotheses',[]):
                sources=[('membership',h.get('membership',{}).get('fit_provenance',{})),
                    ('candidate_threshold',h.get('candidate',{}).get('threshold_fit_provenance',{})),
                    ('control_threshold',h.get('control',{}).get('threshold_fit_provenance',{}))]
                if h.get('id')=='H2':sources.append(('capacity',h.get('candidate',{}).get('capacity_fit_provenance',{})))
                for role,s in sources:self.p1parts.append({'hipotese':h.get('id'),'parte_ajustada':role,
                    'training_ids_sha256':s.get('training_ids_sha256'),
                    'fitting_commit':s.get('fitting_commit'),
                    'independencia_registrada':str(s.get('no_confirmatory_overlap_attested'))})
        self.visual=Counter((x['scene_observation'],x['exposure_observation']) for x in self.items)
        self.provenance=self._scan_provenance()
        self._read_state()

    def _scan_provenance(self) -> list[dict]:
        # ONLY text metadata from prespecified historical audit locations;
        # no outcomes, GT masks, H5 or cached descriptors are opened.
        sources=[
            self.repo/'results/paper_a_evidence/stage24/source_provenance.csv',
            self.repo/'results/paper_a_evidence/stage24gl/source_provenance.csv',
            self.repo/'results/paper_a_evidence/stage24_image_groups/provenance.json',
            self.repo/'results/local_dev/paper_a_confirmation_inventory/predata_audit/historical_source_audit.json',
            self.repo/'results/local_dev/paper_a_confirmation_inventory/predata_audit/biped_train_after_visual_dedup_candidates.csv',
            self.repo/'docs/paper_a_confirmation/visual_duplicate_decisions.csv',
            self.path_stage,
        ]
        found=[]
        for p in sources:
            if not p.is_file() or p.is_symlink() or not within(p,self.repo):continue
            if p.stat().st_size>4_000_000:continue
            try:
                raw=p.read_text(encoding='utf-8-sig',errors='replace')
                if len(raw)>4_000_000:continue
                found.append({'path':p.relative_to(self.repo).as_posix(),'sha256':sha_file(p),
                    'text':raw, 'role':'Referencia em metadata/codigo; execucao nao comprovada'})
            except (OSError,UnicodeError):continue
        return found

    def history_for(self,key:str) -> list[dict]:
        item=self.image_for(key)
        if item is None:return []
        iid=item['id']
        results=[]
        marker=re.compile(r'(?<![A-Za-z0-9_])'+re.escape(iid)+r'(?![A-Za-z0-9_])',re.I)
        for src in self.provenance:
            matches=list(marker.finditer(src['text']))
            if not matches:continue
            pos=matches[0].start()
            excerpt=src['text'][max(0,pos-150):min(len(src['text']),pos+250)]
            excerpt=re.sub(r'\s+',' ',excerpt).strip()
            results.append({'path':src['path'],'sha256':src['sha256'],
                'mentions':min(1000,len(matches)),'excerpt':excerpt,
                'meaning':src['role']})
        if item['dataset']=='BIPED':
            results.insert(0,{'path':'results/automation/stage13c_biped_preflight/summary.json',
                'meaning':'Stage13c catalogou 200 pares RGB/GT em BIPED train; nao prova ajuste de modelo, nem isencao de uso previo.',
                'excerpt':'Contexto de split train, sem atestacao individual de fitting'})
        return results[:15]

    def image_for(self,key):
        return self.images.get(key)

    def check_unchanged(self):
        for name,path in [('roster',self.path_roster),('review',self.path_sheet),
                          ('preview',self.path_preview),('power',self.path_power),
                          ('candidate',self.path_cfg),('active',self.path_active),
                          ('readiness',self.path_readiness)]:
            if sha_file(path)!=self.hashes[name]:raise PermissionError('Fonte de pesquisa alterada: '+name)
        if (self.signoff/'FINAL_INDEPENDENT_REVIEW.json').exists() or (self.work/'freeze_approval.json').exists():
            raise PermissionError('Assinatura/freeze ja existente. Escrita de rascunho bloqueada.')

    def _read_state(self):
        src=self.state_dir/'decisions_DRAFT.json'
        if not src.is_file():
            self.decisions={'schema':'paper_a_mobile_a219_draft_v1',
                'status':'DRAFT_NOT_INDEPENDENT_SCIENTIFIC_SIGNOFF',
                'created_utc':utc_now(),
                'source_hashes':self.hashes.copy(),
                'per_image':{},'topics':{},'events':[]}
            return
        doc=load_json(src,8_000_000)
        if doc.get('source_hashes')!=self.hashes or doc.get('schema')!='paper_a_mobile_a219_draft_v1':
            raise ValueError('Rascunho anterior pertence a outro conjunto de hashes; preservar e revisar separadamente')
        self.decisions=doc

    def _write_state(self):
        self.check_unchanged()
        target=self.state_dir/'decisions_DRAFT.json'
        if target.is_symlink():raise PermissionError('Arquivo de rascunho inseguro')
        raw=(json.dumps(self.decisions,indent=2,ensure_ascii=False)+'\n').encode('utf-8')
        if target.exists():
            history=self.state_dir/'historico'
            history.mkdir(parents=True,exist_ok=True)
            old=target.read_bytes()
            snapshot=history/(utc_now().replace(':','-')+'_'+hashlib.sha256(old).hexdigest()[:12]+'.json')
            if not snapshot.exists():snapshot.write_bytes(old)
        atomic(target,raw)

    def save_item(self,payload:dict):
        key=payload.get('key')
        if key not in {r['key'] for r in self.items}:
            raise ValueError('ID de imagem nao pertence a coorte A219')
        scene=payload.get('scene','PENDING')
        exposure=payload.get('exposure','PENDING')
        if scene not in SCENE or exposure not in EXPOSURE:raise ValueError('Decisao desconhecida')
        note=str(payload.get('note','')).strip()[:6000]
        group=str(payload.get('group','')).strip()[:100]
        if group and not re.fullmatch(r'[\w .-]{1,100}',group,re.UNICODE):
            raise ValueError('Identificador de cena invalido')
        if scene!='PENDING' and len(note)<15:
            raise ValueError('Justifique a avaliacao visual (minimo 15 caracteres)')
        if exposure!='PENDING' and len(note)<15:
            raise ValueError('Justifique historico/exposicao (minimo 15 caracteres)')
        with self._lock:
            self.check_unchanged()
            self.decisions['per_image'][key]={'scene':scene,'exposure':exposure,
                'group':group,'note':note,'updated_utc':utc_now(),
                'status':'DRAFT_AUTHOR_ASSESSMENT_ONLY'}
            self.decisions['events'].append({'type':'image','key':key,'utc':utc_now()})
            self.decisions['events']=self.decisions['events'][-3000:]
            self._write_state()
        return self.decisions['per_image'][key]

    def save_topic(self,payload:dict):
        topic=payload.get('topic')
        state=payload.get('decision','PENDING')
        note=str(payload.get('note','')).strip()[:12000]
        if topic not in TOPICS or state not in CHOICES:
            raise ValueError('Item de aprovacao desconhecido')
        if state!='PENDING' and len(note)<40:
            raise ValueError('A aprovacao preliminar requer justificativa auditavel (>=40 caracteres)')
        with self._lock:
            self.check_unchanged()
            self.decisions['topics'][topic]={'decision':state,'note':note,
                'updated_utc':utc_now(),'scientific_signoff':False}
            self.decisions['events'].append({'type':'topic','topic':topic,'utc':utc_now()})
            self.decisions['events']=self.decisions['events'][-3000:]
            self._write_state()
        return self.decisions['topics'][topic]

    def summary(self):
        d=self.decisions
        topic_count=Counter((d.get('topics',{}).get(topic,{}).get('decision') or 'PENDING') for topic in TOPICS)
        scene_count=Counter(x.get('scene','PENDING') for x in d.get('per_image',{}).values())
        return {
            'status':'REVIEW_ONLY_NO_FREEZE',
            'counts':{'BIPED':125,'MultiCue':94,'total':219},
            'visual_review_count':dict(Counter(r['scene_observation'] for r in self.items)),
            'exposure_review_count':dict(Counter(r['exposure_observation'] for r in self.items)),
            'source_hashes':self.hashes,
            'scientific_signoff':False,'GT_opened_by_server':False,
            'H1_H2_executed_by_server':False,
            'saved_image_reviews':len(d.get('per_image',{})),
            'saved_scene_statuses':dict(scene_count),
            'saved_topic_decisions':dict(topic_count),
            'source_sets':[{ 'id':k,'count':len(v), 'description': {
                'A219':'Coorte confirmatoria candidata (originais RGB)',
                'biped_train':'BIPED train RGB completo: PRESENCA NA BASE, nao uso documentado em fitting',
                'biped_test':'BIPED test RGB: universo externo, nao usado como GT aqui',
                'multicue_pool':'MultiCue: quadros RGB disponiveis no PC',
                'uded_originais_disponiveis':'UDED RGB de desenvolvimento se localizados'}[k]}
                for k,v in self.source_sets.items()],
            'evidence_files':{'P1_recipe':self.path_p1.is_file(),
                'Stage13c_summary':self.path_stage.is_file(),
                'signed_decision':False,'P1_parts':len(self.p1parts),
                'available_rgb_sets':list(self.source_sets)},
            'warnings':[
                'Um SHA RGB unico nao estabelece independencia entre cenas.',
                'Mosaicos BIPED train mostram o universo de arquivos; nao provam treinamento ou calibracao.',
                'GT train foi referenciado por Stage13c para verificacao tecnica; precisa de analise de contaminacao.',
                'Dados com pouca evidencia permanecem pendentes; nenhum PASS cientifico e criado.',
                'Para signoff independente, exporte o dossie e obtenha revisao de outra pessoa.'
            ],
        }

    def get_set(self,set_name='A219',q='',page=1,limit=60):
        keys=self.source_sets.get(set_name,[])
        if not keys: return {'items':[],'total':0,'page':page,'pages':0,'set':set_name}
        q=q.casefold()
        filtered=[]
        for k in keys:
            meta=self.images[k]
            if q and q not in (meta['id']+' '+meta['dataset']).casefold():continue
            src_item=next((x for x in self.items if x['key']==k),None)
            entry={'key':k,'image_id':meta['id'],'dataset':meta['dataset'],
                   'thumbnail':'/api/thumb/'+k,'full':'/api/full/'+k,
                   'role':meta['origin'],'is_A219':k in {x['key'] for x in self.items}}
            if src_item:entry.update({'new_biped':src_item['new_biped'],
                'scene_observation':src_item['scene_observation'],
                'exposure_observation':src_item['exposure_observation'],
                'saved':self.decisions['per_image'].get(k)})
            filtered.append(entry)
        page=max(1,int(page));limit=max(1,min(100,int(limit)))
        return {'items':filtered[(page-1)*limit:page*limit],
                'total':len(filtered),'page':page,'pages':(len(filtered)+limit-1)//limit,'set':set_name}

    @lru_cache(maxsize=2000)
    def image_hash(self,key:str) -> tuple[int,str]|None:
        if not PIL_OK:return None
        image=self.image_for(key)
        if not image:return None
        path=image['path']
        try:
            # dHash of displayed ORIGINAL RGB only. Identical scene detection is approximate.
            with Image.open(path) as im:
                rgb=ImageOps.exif_transpose(im).convert('L')
                rgb=rgb.resize((9,8),Image.Resampling.LANCZOS)
                pix=list(rgb.get_flattened_data()) if hasattr(rgb,'get_flattened_data') else list(rgb.getdata())
                bits=0
                for y in range(8):
                    for x in range(8): bits=(bits<<1)|int(pix[y*9+x]>pix[y*9+x+1])
            return bits, sha_file(path) if image['sha'] is not None else ''
        except (OSError,ValueError):return None

    def similarity(self,key:str,scope='all',limit=14):
        selected=self.image_hash(key)
        if selected is None:return []
        other_keys=(list(self.images) if scope=='all' else self.source_sets.get(scope,[]))
        scored=[]
        for other in other_keys[:1500]:
            if other==key:continue
            check=self.image_hash(other)
            if check is None:continue
            distance=(selected[0]^check[0]).bit_count()
            # dHash is not a rigorous repeat/scene detector; never auto approve.
            info=self.images[other]
            scored.append((distance,other,info))
        scored.sort(key=lambda item:item[0])
        return [{'key':key2,'image_id':info['id'],'dataset':info['dataset'],
                 'origin':info['origin'],'distance':dist,
                 'thumbnail':'/api/thumb/'+key2,'full':'/api/full/'+key2,
                 'same_RGB_SHA256':bool(selected[1] and selected[1]==self.image_hash(key2)[1]),
                 'interpretation':'TRIAGEM_VISUAL_NAO_CERTIFICACAO'}
                for dist,key2,info in scored[:min(max(limit,1),30)]]

    def raster(self,key:str,full:bool=False) -> bytes:
        if not PIL_OK:raise RuntimeError('Pillow nao instalado na .venv')
        item=self.image_for(key)
        if not item:raise FileNotFoundError('Imagem fora da allowlist de originais')
        path=item['path']
        if not path.is_file() or path.is_symlink():raise FileNotFoundError('Original indisponivel')
        # Verify candidate originals on every presentation, but no GT or predictions.
        if item['sha'] is not None and sha_file(path)!=item['sha']:
            raise PermissionError('SHA do original alterado: '+key)
        with Image.open(path) as image:
            image=ImageOps.exif_transpose(image)
            image.thumbnail((1700,1300) if full else (360,245),Image.Resampling.LANCZOS)
            if image.mode!='RGB':image=image.convert('RGB')
            stream=io.BytesIO()
            image.save(stream,'JPEG',quality=88 if full else 76,optimize=True)
            return stream.getvalue()

    def export_bundle(self) -> bytes:
        with self._lock:
            self.check_unchanged()
            data=self.decisions.copy()
            rows=[]
            for item in self.items:
                saved=data.get('per_image',{}).get(item['key'],{})
                rows.append({'dataset':item['dataset'],'image_id':item['image_id'],
                    'image_sha256':item['sha256'],'scene_observation':item['scene_observation'],
                    'exposure_observation':item['exposure_observation'],
                    'new_biped':item['new_biped'],
                    'scene_draft':saved.get('scene','PENDING'),
                    'exposure_draft':saved.get('exposure','PENDING'),
                    'scene_group_draft':saved.get('group',''),
                    'reason':saved.get('note',''),
                    'scientific_signoff':'FALSE'})
            md=['# Revisao local Paper A A219 — RASCUNHO NAO CERTIFICADO','',
                'Este arquivo registra interpretacoes do autor/usuario, nao equivale a',
                'revisao cientifica independente, freeze ou acesso autorizado ao GT.','',
                '## Evidencias fixadas (SHA256)', '']
            for name,sha in self.hashes.items():md.append('- '+name+': '+sha)
            md+=['','## Itens pendentes','']
            for k in TOPICS:
                d=data.get('topics',{}).get(k,{})
                md.append('- '+k+': '+d.get('decision','PENDING')+' — '+d.get('note','SEM_JUSTIFICATIVA'))
            md+=['','## Limites','',
                '- Contato tecnico Stage13c com GT train requer rastreabilidade.',
                '- Comparacao dHash/visao RGB nao prova ausencia de fitting previo.',
                '- Nenhum registro do painel atualiza FINAL_INDEPENDENT_REVIEW.json.',
                '- Nenhum GT, F1 ou H1/H2 foi aberto/executado por este painel.']
            out=io.BytesIO()
            with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
                z.writestr('DECISOES_A219_RASCUNHO_NAO_APROVADO.json',
                    json.dumps(data,indent=2,ensure_ascii=False))
                f=io.StringIO(newline='')
                writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n')
                writer.writeheader();writer.writerows(rows)
                z.writestr('PLANILHA_219_AVALIACOES_RASCUNHO.csv',f.getvalue())
                z.writestr('PARECER_RASCUNHO.md','\n'.join(md)+'\n')
                z.writestr('SUMARIO_VERIFICAVEL.json',json.dumps(self.summary(),indent=2,ensure_ascii=False))
            return out.getvalue()


class Auth:
    def __init__(self,pin=None):
        self.pin=pin or f'{secrets.randbelow(10**12):012d}'
        self.sid=secrets.token_urlsafe(32)
        self.csrf=secrets.token_urlsafe(32)
        self.failures=[]
        self.lock=threading.Lock()

    def allowed(self,cookie):
        jar=SimpleCookie()
        try:jar.load(cookie or '')
        except Exception:return False
        value=jar.get('paper_a_a219_sid')
        return value is not None and secrets.compare_digest(value.value,self.sid)

    def login(self,pin):
        with self.lock:
            t=time.monotonic()
            self.failures=[x for x in self.failures if t-x < 600]
            if len(self.failures)>=12:return False
            if not isinstance(pin,str) or not secrets.compare_digest(pin,self.pin):
                self.failures.append(t)
                return False
            self.failures=[]
            return True


class AppHandler(BaseHTTPRequestHandler):
    server: 'AppServer'

    def log_message(self,format,*args):
        # Avoid recording review text / session cookies / URLs in server logs.
        pass

    def _host_ok(self):
        host=self.headers.get('Host','').split(':',1)[0].lower().strip('[]')
        return host in ('127.0.0.1','localhost') or host.endswith('.ts.net')

    def _origin_ok(self):
        origin=self.headers.get('Origin')
        if not origin:return True  # non-browser clients still require session + CSRF
        try:
            u=urlsplit(origin)
            return u.netloc.lower()==self.headers.get('Host','').lower() and u.scheme in ('http','https')
        except ValueError:return False

    def _answer(self,code:int,data:bytes|str,mime='application/json; charset=utf-8',extra=None):
        if isinstance(data,str):data=data.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type',mime)
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',
            "default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self'; "
            "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        for a,b in (extra or {}).items():self.send_header(a,b)
        self.end_headers()
        self.wfile.write(data)

    def _json(self,obj,status=200,extra=None):
        self._answer(status,json.dumps(obj,ensure_ascii=False,separators=(',',':')),
                     extra=extra)

    def _read_body(self):
        try:n=int(self.headers.get('Content-Length','0'))
        except (ValueError,OverflowError):raise ValueError('Tamanho invalido')
        if not 0<n<=30_000:raise ValueError('Payload ausente/grande demais')
        return json.loads(self.rfile.read(n))

    def _authed(self):
        return self.server.auth.allowed(self.headers.get('Cookie'))

    def _session(self):
        return {'authenticated':self._authed(),
                'csrf':self.server.auth.csrf if self._authed() else None}

    def do_GET(self):
        if not self._host_ok():return self._json({'error':'Host nao permitido'},403)
        route=urlsplit(self.path)
        path=route.path
        ui=UI_DIR
        if path in ('/','/index.html','/app.css','/app.js'):
            mapping={'/':'index.html','/index.html':'index.html',
                     '/app.css':'app.css','/app.js':'app.js'}
            name=mapping[path]
            p=ui/name
            mime='text/html; charset=utf-8' if name.endswith('.html') else ('text/css; charset=utf-8' if name.endswith('.css') else 'text/javascript; charset=utf-8')
            if not p.is_file():return self._json({'error':'Frontend ausente'},500)
            return self._answer(200,p.read_bytes(),mime)
        if path=='/api/session':return self._json(self._session())
        if not self._authed():return self._json({'error':'Senha temporaria necessaria'},401)
        data=self.server.data
        q=parse_qs(route.query)
        one=lambda name,default='':(q.get(name) or [default])[0]
        try:
            if path=='/api/summary':return self._json(data.summary())
            if path=='/api/items':
                return self._json(data.get_set(one('set','A219'),one('q'),
                    int(one('page','1')),int(one('limit','60'))))
            if path=='/api/details':
                key=one('key')
                item=next((r for r in data.items if r['key']==key),None)
                if not item:return self._json({'error':'Fora da coorte A219'},404)
                return self._json({'item':item,'history':data.history_for(key),
                    'saved':data.decisions['per_image'].get(key,{})})
            if path=='/api/similar':
                key=one('key')
                if key not in data.images:return self._json({'error':'Imagem invalida'},404)
                return self._json({'items':data.similarity(key,one('scope','all'),14)})
            if path=='/api/topics':
                return self._json({'topics':data.decisions.get('topics',{}),
                    'p1parts':data.p1parts,'stage':data.stage,'power':data.power,
                    'protocol_hash':data.hashes['preview']})
            if path.startswith('/api/thumb/') or path.startswith('/api/full/'):
                full=path.startswith('/api/full/')
                key=unquote(path.split('/',3)[3])
                jpg=data.raster(key,full=full)
                return self._answer(200,jpg,'image/jpeg')
            if path=='/api/export':
                blob=data.export_bundle()
                return self._answer(200,blob,'application/zip',{
                    'Content-Disposition':'attachment; filename="PaperA_A219_REVISAO_MOBILE_RASCUNHO_SEM_PASS.zip"'})
        except (ValueError,PermissionError,RuntimeError,FileNotFoundError) as e:
            return self._json({'error':str(e)},409)
        return self._json({'error':'Rota desconhecida'},404)

    def do_POST(self):
        if not self._host_ok() or not self._origin_ok():
            return self._json({'error':'Host ou origem nao permitidos'},403)
        path=urlsplit(self.path).path
        try:body=self._read_body()
        except (ValueError,json.JSONDecodeError) as e:return self._json({'error':str(e)},400)
        if not isinstance(body,dict):return self._json({'error':'JSON invalido'},400)
        if path=='/api/login':
            if not self.server.auth.login(body.get('pin')):
                return self._json({'error':'Codigo incorreto ou tentativas excessivas'},403)
            host=self.headers.get('Host','').split(':',1)[0].lower()
            secure=host.endswith('.ts.net') or self.headers.get('X-Forwarded-Proto','').lower()=='https'
            cookie=('paper_a_a219_sid='+self.server.auth.sid+'; Path=/; HttpOnly; SameSite=Strict'+
                ('; Secure' if secure else ''))
            return self._json({'authenticated':True,'csrf':self.server.auth.csrf},extra={'Set-Cookie':cookie})
        if not self._authed():return self._json({'error':'Senha temporaria necessaria'},401)
        if not secrets.compare_digest(str(self.headers.get('X-CSRF-Token','')),self.server.auth.csrf):
            return self._json({'error':'CSRF token ausente'},403)
        try:
            if path=='/api/save-item':return self._json({'saved':self.server.data.save_item(body)})
            if path=='/api/save-topic':return self._json({'saved':self.server.data.save_topic(body)})
        except (PermissionError,ValueError,OSError) as e:
            return self._json({'error':str(e)},409)
        return self._json({'error':'Rota desconhecida'},404)


class AppServer(ThreadingHTTPServer):
    daemon_threads=True
    allow_reuse_address=True
    def __init__(self,address,review,auth):
        super().__init__(address,AppHandler)
        self.data=review
        self.auth=auth


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--data',type=Path,default=DEFAULT_DATA)
    p.add_argument('--bind',default='127.0.0.1')
    p.add_argument('--port',type=int,default=18765)
    p.add_argument('--state-dir',type=Path)
    p.add_argument('--check',action='store_true',help='Check only pre-freeze sources; do not listen')
    args=p.parse_args(argv)
    if args.bind!='127.0.0.1':p.error('Somente --bind 127.0.0.1 e permitido; use Tailscale Serve')
    if args.port<1024 or args.port>65535:p.error('Porta invalida')
    review=ReviewData(args.repo,args.data,args.state_dir)
    if args.check:
        print(json.dumps(review.summary(),indent=2,ensure_ascii=False))
        return 0
    auth=Auth()
    with AppServer((args.bind,args.port),review,auth) as server:
        print('\n=== PAPER A A219 — AUDITORIA MOBILE (RASCUNHO) ===',flush=True)
        print('Endereço local: http://127.0.0.1:'+str(args.port),flush=True)
        print('Código temporário de acesso: '+auth.pin,flush=True)
        print('Nunca compartilhe o código ou publique o serviço via Tailscale Funnel.',flush=True)
        print('Sem acesso a GT, H5, F1, mapas ou H1/H2. Ctrl+C encerra o servidor.',flush=True)
        try:server.serve_forever(poll_interval=.4)
        except KeyboardInterrupt:pass
    return 0


if __name__=='__main__':raise SystemExit(main())
