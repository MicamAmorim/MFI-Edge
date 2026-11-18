"""Reviewed prospective three-domain runner. No override, tuning or exclusions.

This successor is separate from the historical rejected A219 design. It can
only run after a signed independent review and byte-verified Git freeze.
Every incomplete/invalid reference aborts; the frozen sample is never replaced.
"""
from __future__ import annotations
from pathlib import Path
import sys,json,csv,hashlib,zipfile,os,importlib.metadata,platform,tarfile,re
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts'))
from paper_a_vsb100_freeze_guard import authorize,digest,read
from execute_paper_a_frozen_cohort import binary_annotation,materialize_gt_once,TAR_SHA
from src.paper_a_prefreeze_map_adapter import predict_original_pregt
from src.paper_a_confirmation_paired_f1 import evaluate_paired_binary
from src.paper_a_vsb100_contract import decode_vsb100_boundaries,evaluate_vsb100_paired_binary
from src.paper_a_nyud_contract import decode_nyud_boundaries,evaluate_nyud_paired_binary
from src.paper_a_three_domain_inference import permutation_test,stratified_bootstrap,holm2,rho,partition_primary_secondary
FOLDER=ROOT/'docs/paper_a_confirmation/successor_vsb100_20261117'
MCDATA=Path(r'F:\MFI-Edge-Data\MultiCue')
VSBDATA=Path(r'F:\MFI-Edge-Data\VSB100_confirmation_not_frozen')
NYDATA=Path(r'F:\MFI-Edge-Data\NYUDv2_confirmation_not_frozen')
ORIGINAL=Path(r'C:\Users\Windows 11\Documents\MFI-Edge')
COLS=('dataset','image_id','scene_group','image_sha256','X1','Y1','X2','Y2')
def environment():
    return {'python':platform.python_version(),'packages':{p:importlib.metadata.version(p) for p in ('numpy','scipy','scikit-image','opencv-python','Pillow')}}
def save_new(path,obj):
    staged=path.with_suffix(path.suffix+'.part')
    with staged.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False)
    os.replace(staged,path)
def array_manifest(arrays):
    return {name:{'shape':list(a.shape),'dtype':a.dtype.str,'sha256_C_order':hashlib.sha256(np.ascontiguousarray(a).tobytes(order='C')).hexdigest()} for name,a in sorted(arrays.items())}
def verify_map_cache(path,expected):
    if not path.is_file() or path.is_symlink() or digest(path)!=expected['NPZ_sha256']:raise ValueError('Map cache payload hash mismatch')
    with np.load(path,allow_pickle=False) as z:actual=array_manifest({name:z[name] for name in z.files})
    if actual!=expected['arrays']:raise ValueError('Map cache array geometry/type/hash mismatch')
def persist_map_cache(path,arrays):
    detail=array_manifest(arrays)
    if path.exists():
        with np.load(path,allow_pickle=False) as z:prior=array_manifest({name:z[name] for name in z.files})
        if prior!=detail:raise ValueError('Orphan map cache differs from deterministic inference; refuse overwrite')
    else:
        tmp=path.with_suffix('.npz.part')
        with tmp.open('xb') as f:np.savez_compressed(f,**arrays)
        os.replace(tmp,path)
    record={'file':path.name,'NPZ_sha256':digest(path),'arrays':detail}
    verify_map_cache(path,record);return record
def original(row):
    base={'BIPED':ORIGINAL/'datasets/BIPEDv2/edges/imgs/train/rgbr/real','MultiCue':MCDATA/'source_frames_only','VSB100':VSBDATA/'RGB_only','NYUDv2':NYDATA/'rgb_only'}[row['dataset']]
    p=Path(row['source_path'])
    if p.is_symlink() or not p.resolve().is_relative_to(base.resolve()) or p.name!=row['relative_path'] or p.stem!=row['image_id'] or digest(p)!=row['image_sha256']:raise ValueError('Frozen original provenance changed')
    with Image.open(p) as im:a=np.array(im.convert('RGB'))
    if a.shape[:2]!=(int(row['native_height']),int(row['native_width'])):raise ValueError('Frozen original geometry changed')
    return a
def mc_names(rows):
    with (MCDATA/'multicue_h5_anchored_sequence_candidates.csv').open(newline='',encoding='utf-8-sig') as f:by={r['sequence_id']:r for r in csv.DictReader(f)}
    result={}
    for r in rows:
        if r['dataset']!='MultiCue':continue
        x=by[r['image_id']]
        if x['capture_prefix']!=r['capture_prefix'] or r['capture_prefix']=='4113':raise ValueError('Historical MultiCue capture or metadata changed')
        names=json.loads(x['edges_png_names'])
        if len(names)!=6 or len(set(names))!=6 or any(n!=f'multicue/ground-truth/images/edges/{r["image_id"]}.{i}.png' for i,n in enumerate(sorted(names),1)):raise ValueError('Invalid six-annotator edge mapping')
        if r['annotation_archive_sha256']!=TAR_SHA or json.loads(r['annotation_member'])!=sorted(names):raise ValueError('Frozen MultiCue GT source mapping changed')
        result[r['image_id']]=sorted(names)
    return result
def materialize_nyud_after_authorization(rows,output):
    archive=NYDATA/'eccv14-data.tgz';requested={r['annotation_member'] for r in rows if r['dataset']=='NYUDv2'};expected={r['annotation_archive_sha256'] for r in rows if r['dataset']=='NYUDv2'}
    if len(expected)!=1 or digest(archive)!=next(iter(expected)):raise ValueError('Frozen NYUD annotation archive changed')
    for r in rows:
        if r['dataset']=='NYUDv2' and (not re.fullmatch(r'img_\d+',r['image_id']) or r['annotation_member']!=f'eccv14-data/benchmarkData/groundTruth/{r["image_id"]}.mat'):raise ValueError('NYUD GT/RGB identity mismatch')
    target=output/'verified_nyud_gt';target.mkdir(exist_ok=True);found={}
    with tarfile.open(archive,'r:*') as tar:
        for name in sorted(requested):
            member=tar.getmember(name)
            if not member.isfile() or not 0<member.size<=20_000_000:raise ValueError('Invalid supplied NYUD annotation member')
            with tar.extractfile(member) as stream:payload=stream.read(20_000_001)
            if len(payload)!=member.size:raise ValueError('Incomplete NYUD annotation payload')
            p=target/Path(name).name;source_hash=hashlib.sha256(payload).hexdigest()
            if p.exists():
                if digest(p)!=source_hash:raise ValueError('Existing NYUD annotation cache differs from source')
            else:
                with p.open('xb') as f:f.write(payload)
            found[name]=p
    return found
def main():
    # First action: validate independent review, exact files and freeze ancestry.
    protocol,recipe,rows,review,receipt=authorize(FOLDER)
    if environment()!=read(FOLDER/'environment.json'):raise PermissionError('Reviewed runtime versions changed')
    output=Path(r'F:\MFI-Edge-Data\Paper_A_confirmation_successor')/receipt['freeze_commit']
    output.mkdir(parents=True,exist_ok=True)
    if (output/'inference.json').exists():raise RuntimeError('Completed evaluation exists; do not overwrite')
    # Archives remain opaque until authorization; hash before first GT decode.
    for split in ('train','test'):
        archive=VSBDATA/f'General_{split}_fullres.zip'
        expected={r['annotation_archive_sha256'] for r in rows if r['dataset']=='VSB100' and r['source_split'].lower()==split}
        if len(expected)!=1 or digest(archive)!=next(iter(expected)):raise ValueError('Frozen VSB100 annotation archive changed')
    if digest(MCDATA/'multicue-dataset.tar.bz2')!=TAR_SHA:raise ValueError('Frozen MultiCue archive changed')
    names=mc_names(rows);gtroot=output/'verified_gt_cache';ground=materialize_gt_once(names,gtroot,digest(FOLDER/'cohort.csv'));nyground=materialize_nyud_after_authorization(rows,output)
    checkpoint=output/'checkpoints';checkpoint.mkdir(exist_ok=True);caches=output/'native_map_caches';caches.mkdir(exist_ok=True);records=[]
    for index,row in enumerate(rows,1):
        im=original(row);native=tuple(im.shape[:2]);domain=row['dataset']
        if domain=='BIPED':
            p=ORIGINAL/'datasets/BIPEDv2/edges/edge_maps/train/rgbr/real'/(row['image_id']+'.png')
            if p.name!=row['annotation_member'] or digest(p)!=row['annotation_file_sha256']:raise ValueError('Frozen secondary BIPED GT bytes changed')
            raw_hash=[digest(p)];annotations=[binary_annotation(p,native,dataset=domain)]
        elif domain=='MultiCue':
            paths=[ground[n] for n in names[row['image_id']]];raw_hash=[digest(p) for p in paths];annotations=[binary_annotation(p,native,dataset=domain) for p in paths]
        elif domain=='NYUDv2':
            p=nyground[row['annotation_member']];payload=p.read_bytes();raw_hash=[digest(p)];annotations=decode_nyud_boundaries(payload,native)
        else:
            prefix=f'General_{row["source_split"].lower()}_fullres/Groundtruth/'
            # Verify video and frame mapping from the exact frozen image identity.
            identity=row['image_id'].removeprefix('VSB100_'+row['source_split']+'_');video,frame=identity.rsplit('_',1)
            if row['annotation_member']!=prefix+video+'/'+frame+'.mat':raise ValueError('GT/RGB identity mismatch')
            with zipfile.ZipFile(VSBDATA/f'General_{row["source_split"].lower()}_fullres.zip') as z:
                info=z.getinfo(row['annotation_member'])
                if not 0<info.file_size<=20_000_000:raise ValueError('Annotation size exceeds reviewed policy')
                payload=z.read(info)
            raw_hash=[hashlib.sha256(payload).hexdigest()];annotations=decode_vsb100_boundaries(payload,native)
        key={'image_sha256':row['image_sha256'],'GT_sha256':raw_hash,'review_sha256':digest(FOLDER/'INDEPENDENT_REVIEW.json'),'source_pins_sha256':digest(FOLDER/'source_pins.json'),'protocol_sha256':digest(FOLDER/'protocol.json'),'recipe_sha256':digest(FOLDER/'recipe.json'),'freeze_commit':receipt['freeze_commit']}
        cp=checkpoint/(domain+'__'+row['image_id']+'.json');sig=cp.with_suffix('.sha256')
        if cp.exists():
            if not sig.is_file() or sig.read_text().strip()!=digest(cp):raise ValueError('Checkpoint hash mismatch')
            record=read(cp)
            if record['inputs']!=key:raise ValueError('Checkpoint input provenance changed')
            verify_map_cache(caches/record['map_cache']['file'],record['map_cache'])
        else:
            pregt=predict_original_pregt(im,recipe);preds=pregt.predictions;vals={};details={}
            arrays={name:np.ascontiguousarray(a) for name,a in pregt.descriptors.items()}
            for tag,pred in preds.items():
                arrays[tag+'_candidate']=np.ascontiguousarray(pred.candidate);arrays[tag+'_control']=np.ascontiguousarray(pred.control)
            cache=persist_map_cache(caches/(domain+'__'+row['image_id']+'.npz'),arrays)
            for j,tag in enumerate(('H1','H2'),1):
                pred=preds[tag]
                if domain=='VSB100':paired=evaluate_vsb100_paired_binary(pred.candidate,pred.control,annotations)
                elif domain=='NYUDv2':paired=evaluate_nyud_paired_binary(pred.candidate,pred.control,annotations)
                else:paired=evaluate_paired_binary(pred.candidate,pred.control,annotations,domain=domain)
                vals['X'+str(j)]=float(pred.feature);vals['Y'+str(j)]=paired.delta_f1;details[tag]={**paired.to_dict(),'status':'GATED_POST_FREEZE_PAIRED_EVALUATION','freeze_commit':receipt['freeze_commit']}
            out={k:row[k] for k in COLS[:4]};out.update(vals)
            record={'inputs':key,'outcome':out,'separate_annotation_F1':details,'map_cache':cache};save_new(cp,record)
            with sig.open('x',encoding='ascii') as f:f.write(digest(cp)+'\n')
        out=record['outcome']
        if set(out)!=set(COLS) or any(out[k]!=row[k] for k in COLS[:4]) or any(not np.isfinite(out[k]) for k in ('X1','Y1','X2','Y2')):raise ValueError('Incomplete/nonfinite/misaligned outcome; abort whole analysis')
        records.append(out);print(f'[FROZEN] {index}/{len(rows)} {domain} {row["image_id"]}',flush=True)
    path=output/'paired_outcomes.csv'
    if not path.exists():
        with path.open('x',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=COLS);w.writeheader();w.writerows(records)
    else:
        with path.open(newline='',encoding='utf-8') as f:prior=list(csv.DictReader(f))
        if prior!=[{k:str(r[k]) for k in COLS} for r in records]:raise ValueError('Existing aggregate outcomes changed')
    primary,secondary=partition_primary_secondary(records,rows)
    analyses=[permutation_test(primary,tag,100000,20261115+j) for j,tag in enumerate(('H1','H2'))];adjusted=holm2(*(a['p_one_sided'] for a in analyses))
    for j,(a,p) in enumerate(zip(analyses,adjusted)):
        a['holm_p_adjusted']=p;a['bootstrap95']=stratified_bootstrap(primary,a['hypothesis'],2000,20261215+j);a['confirmed']=bool(p<.05 and a['statistic_within_domain']*(-1 if j==0 else 1)>0)
    diagnostic={'status':'EXPLORATORY_ONLY_NOT_COUNTED_IN_PRIMARY_TESTS','n':len(secondary),'hypotheses':{}}
    for j,tag in enumerate(('H1','H2'),1):
        try:r=rho([v['X'+str(j)] for v in secondary],[v['Y'+str(j)] for v in secondary])
        except ValueError:r=None
        diagnostic['hypotheses'][tag]={'rho':r,'mean_paired_delta_F1':float(np.mean([v['Y'+str(j)] for v in secondary])),'primary_confirmation_claim':False}
    save_new(output/'inference.json',{'status':'FROZEN_EVALUATION_COMPLETED_NUMERICAL_REVIEW_PENDING','freeze_commit':receipt['freeze_commit'],'independent_review_sha256':digest(FOLDER/'INDEPENDENT_REVIEW.json'),'outcomes_sha256':digest(path),'N_primary':len(primary),'N_secondary_BIPED':len(secondary),'N_total':len(records),'analyses':analyses,'secondary_BIPED':diagnostic,'environment':environment(),'no_confirmatory_tuning':True,'not_official_Berkeley_or_VSB_benchmark':True})
    print('Completed: '+str(output),flush=True)
if __name__=='__main__':main()
