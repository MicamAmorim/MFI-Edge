"""Separate prospective successor gate. Does not activate or rewrite A219.

No protected GT or outcome I/O. An external independently authored review
must approve the exact preview, cohort, recipe, code and adjudication bytes.
This module cannot create its own reviewer decision or waive pending items.
"""
from __future__ import annotations
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import csv,json,hashlib,subprocess,sys,copy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from paper_a_freeze_guard import validate_fitted_recipe, REQUIRED_APPROVALS
P1_SHA='628d1e345b6d1117c3cbfbc6ecaf75d4cac8db6a7796d328e2ea911ce9891a9c'
PRIMARY_DOMAINS={'MultiCue','NYUDv2','VSB100'}
DOMAINS=PRIMARY_DOMAINS|{'BIPED'}
def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):h.update(block)
    return h.hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def source_paths():
    return sorted({p.relative_to(ROOT).as_posix() for base in ('src','scripts') for p in (ROOT/base).rglob('*.py')}|{p.name for p in ROOT.glob('*.py')})
def _assert(condition,message):
    if not condition:raise PermissionError(message)
def validate_review(folder:Path):
    """Validate reviewable bytes. Does not imply a freeze already exists."""
    folder=Path(folder);review=read(folder/'INDEPENDENT_REVIEW.json')
    _assert(review.get('decision')=='APPROVE_PROSPECTIVE_FREEZE','Independent approval absent')
    _assert(review.get('independently_authored') is True,'Independent authorship not attested')
    who=review.get('reviewer_identity','').strip()
    _assert(bool(who) and who not in ('Codex primary preparer','Codex AI','PENDING'),'Accountable independent reviewer required')
    _assert(all(review.get('approvals',{}).get(k) is True for k in REQUIRED_APPROVALS),'Scientific review fields are pending')
    _assert(review.get('executor_and_analysis_reviewed') is True,'Successor code review pending')
    dt=datetime.fromisoformat(review['reviewed_utc'].replace('Z','+00:00'))
    _assert(dt.tzinfo is not None and dt<=datetime.now(timezone.utc),'Invalid independent review time')
    files=review.get('reviewed_files',{})
    required={'protocol.json','cohort.csv','recipe.json','source_pins.json','scene_adjudication.json','power.json','row_review.csv','environment.json'}
    _assert(set(files)==required,'Review must bind every required artifact')
    for name in required:
        p=folder/name;_assert(p.is_file() and not p.is_symlink() and digest(p)==files[name],'Reviewed input changed: '+name)
    protocol=read(folder/'protocol.json');recipe=read(folder/'recipe.json')
    _assert(protocol.get('execution_output_root')==r'F:\MFI-Edge-Data\Paper_A_confirmation_successor','Scientific cache root differs from reviewed F: destination')
    _assert(protocol.get('status')=='frozen' and protocol.get('freeze_commit') is None,'Expected exact prospective frozen preview')
    _assert(protocol.get('confirmatory_outcomes_opened') is False,'Prior confirmatory access disclosed or uncertain')
    _assert(digest(folder/'recipe.json')==P1_SHA,'P1 recipe changed')
    # Preserve the original fitted artifact byte for byte. Its seven overlap
    # attestations were deliberately null. Only this separately reviewed
    # declaration can supply those attestations in an in-memory validation
    # copy; no fitted values, original proof hashes or files are rewritten.
    _assert(review.get('no_development_confirmation_overlap') is True,'Independent training/cohort overlap attestation pending')
    attested=copy.deepcopy(recipe)
    for h in attested['hypotheses']:
        proofs=[h['membership']['fit_provenance'],h['candidate']['threshold_fit_provenance'],h['control']['threshold_fit_provenance']]
        if h['id']=='H2':proofs.append(h['candidate']['capacity_fit_provenance'])
        for proof in proofs:proof['no_confirmatory_overlap_attested']=True
    _assert(not validate_fitted_recipe(attested,protocol,ROOT),'Historical fitting lineage invalid')
    pins=read(folder/'source_pins.json')
    _assert(set(pins)==set(source_paths()),'Runtime dependency closure incomplete')
    for relative,value in pins.items():
        _assert(digest(ROOT/relative)==value,'Runtime source changed: '+relative)
    with (folder/'cohort.csv').open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
    counts=dict(Counter(r['dataset'] for r in rows));spec=protocol['cohort']
    _assert(set(counts)==DOMAINS and counts==spec['counts'] and len(rows)==spec['total_evaluation_images'],'Declared full evaluation counts differ')
    primary=[r for r in rows if r.get('analysis_role')=='primary'];secondary=[r for r in rows if r.get('analysis_role')=='secondary_exploratory']
    primary_counts=dict(Counter(r['dataset'] for r in primary))
    _assert(len(primary)+len(secondary)==len(rows) and set(primary_counts)==PRIMARY_DOMAINS and all(r['dataset']=='BIPED' for r in secondary),'Invalid prospective primary/secondary partition')
    _assert(dict(Counter(r['dataset'] for r in secondary))==spec['secondary_counts'] and 0<len(secondary)<60,'Secondary BIPED count inconsistent with below-min60 design')
    _assert(primary_counts==spec['primary_counts'] and len(primary)==spec['target_n_independent_images'] and set(spec['dataset_names'])==PRIMARY_DOMAINS,'Primary target differs from frozen partition')
    _assert(spec['required_domains']==3 and spec['min_n_per_domain']==60 and min(primary_counts.values())>=60,'Original min60 must hold in every primary domain')
    _assert(len({(r['dataset'],r['image_id']) for r in rows})==len(rows) and len({r['scene_group'] for r in rows})==len(rows),'Repeated image or scene')
    with (folder/'row_review.csv').open(newline='',encoding='utf-8') as f:reviews=list(csv.DictReader(f))
    by={(r['dataset'],r['image_id']):r for r in reviews}
    _assert(len(by)==len(rows)==len(reviews),'Independent row review incomplete')
    for r in rows:
        q=by.get((r['dataset'],r['image_id']),{})
        _assert(q.get('image_sha256')==r['image_sha256'] and q.get('scene_group')==r['scene_group'],'Row reviewer identity/hash mismatch')
        _assert(q.get('scene_decision')=='PASS' and q.get('exposure_decision')=='PASS' and bool(q.get('evidence','').strip()),'Scene/exposure certification pending')
        if r['dataset']=='VSB100':
            _assert(not any(v in r['image_id'] for v in ('_alec_baldwin_','_up_dug_','_up_trailer_')),'Reserved or nonphotographic video included')
    scene=read(folder/'scene_adjudication.json')
    _assert(scene.get('all_flags_adjudicated') is True and scene.get('confirmatory_GT_or_outcomes_opened') is False,'Scene audit incomplete')
    power=read(folder/'power.json')
    eligible=[x for x in power['reports'] if x['domain_counts']==primary_counts]
    _assert(len(eligible)==1,'Exact final design lacks prospective power simulation')
    effect=[x for x in eligible[0]['results'] if x['scenario']=='homogeneous_020']
    _assert(len(effect)==1 and effect[0]['joint_rejection_rate']>=.8,'Prospective joint power target .80 at rho .20 not met')
    inference=protocol['inference']
    _assert(inference['permutations']==100000 and inference['permutation_seed']==20261115 and inference['alpha_familywise']==.05 and inference['bootstrap_replicates']==2000,'Inference constants changed')
    return protocol,recipe,rows,review,pins
def authorize(folder:Path):
    """No protected data may be accessed before this succeeds completely."""
    protocol,recipe,rows,review,pins=validate_review(folder);receipt=read(folder/'FREEZE_RECEIPT.json');commit=receipt.get('freeze_commit','')
    _assert(len(commit)==40 and all(c in '0123456789abcdef' for c in commit),'Missing actual freeze commit')
    _assert(subprocess.run(['git','merge-base','--is-ancestor',commit,'HEAD'],cwd=ROOT,capture_output=True).returncode==0,'Freeze commit is not an ancestor')
    _assert(receipt.get('review_sha256')==digest(folder/'INDEPENDENT_REVIEW.json'),'Review changed after freeze')
    for p in [folder/name for name in review['reviewed_files']]+[folder/'INDEPENDENT_REVIEW.json']+[ROOT/rel for rel in pins]:
        rel=p.resolve().relative_to(ROOT.resolve()).as_posix();blob=subprocess.run(['git','show',commit+':'+rel],cwd=ROOT,capture_output=True)
        _assert(blob.returncode==0 and blob.stdout.replace(b'\r\n',b'\n')==p.read_bytes().replace(b'\r\n',b'\n'),'Freeze commit does not contain reviewed bytes: '+rel)
    return protocol,recipe,rows,review,receipt
