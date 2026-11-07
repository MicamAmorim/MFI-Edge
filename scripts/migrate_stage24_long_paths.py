"""Migrate only signatures for the reviewed Windows long-path I/O correction."""
import hashlib,json,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.stage24_recertification_cv import native_path,write_json
from src.stage24_recertification_ops import AGGREGATORS,THINNING,SUPPRESSORS,CALIBRATION_MODES
def sha(value):return hashlib.sha256(value).hexdigest()
def signature(hashes,cfg):
 return sha(json.dumps({'source_sha256':hashes,'cfg':cfg,'aggregators':AGGREGATORS,'thinning':THINNING,'suppressors':SUPPRESSORS,'calibrations':CALIBRATION_MODES,'protocol':'native_GT_one_to_one_v1'},sort_keys=True,default=str).encode())
def main():
 out=ROOT/'results/local_dev/stage24_paper_a_recertification';mp=out/'campaign_source_fingerprint.json'
 manifest=json.loads(mp.read_text(encoding='utf-8'));name='src/stage24_recertification_cv.py'
 current=(ROOT/name).read_bytes()
 assert sha(current.replace(b'\r\n',b'\n'))=='56bfa0f2ce5618b9c1f1911ce1e919ad7f539a88a2aa0652555dcab57f2bc0cf','Unreviewed I/O source'
 if manifest['source_sha256'][name]==sha(current):
  print('LONG_PATH_MIGRATION_ALREADY_APPLIED');return
 original=subprocess.check_output(['git','show','7debee6:'+name],cwd=ROOT).replace(b'\r\n',b'\n')
 assert manifest['source_sha256'][name] in {sha(original),sha(original.replace(b'\n',b'\r\n'))},'Unknown prior CV source'
 for source,h in manifest['source_sha256'].items():
  if source!=name:assert sha((ROOT/source).read_bytes())==h,'Unreviewed source change: '+source
 options=manifest['configuration'];cfg={'seed':options['seed'],'threshold_count':options['thresholds'],'inner_threshold_count':options['inner_thresholds'],'inner_top':options['inner_top']}
 names=('stage24_recertification_cv.py','stage24_recertification_ops.py','stage24_integrity.py','stage24_residual.py')
 old={n:manifest['source_sha256']['src/'+n] for n in names};new=dict(old);new[Path(name).name]=sha(current)
 prior,future=signature(old,cfg),signature(new,cfg)
 updates=[];total=0
 for f in native_path(out/'folds').rglob('*.json'):
  raw=f.read_bytes();obj=json.loads(raw);changed=False;total+=1
  if isinstance(obj,dict):
   if 'config_sha256' in obj:
    assert obj['config_sha256'] in (prior,future),'Unknown group signature: '+str(f)
    if obj['config_sha256']==prior:obj['config_sha256']=future;changed=True
   if isinstance(obj.get('spec'),dict) and 'signature' in obj['spec']:
    assert obj['spec']['signature'] in (prior,future),'Unknown part signature: '+str(f)
    if obj['spec']['signature']==prior:obj['spec']['signature']=future;changed=True
  if changed:updates.append((f,raw,obj))
 backup=out/'checkpoints_before_long_path_fix.zip'
 if not backup.exists():
  with zipfile.ZipFile(backup,'w',compression=zipfile.ZIP_DEFLATED) as z:
   z.writestr(mp.name,mp.read_bytes())
   for f,raw,obj in updates:z.writestr(f.relative_to(native_path(out)).as_posix(),raw)
 with zipfile.ZipFile(backup) as z:assert z.testzip() is None,'Invalid backup'
 for f,raw,obj in updates:write_json(f,obj)
 report={'total_checkpoint_files':total,'signature_updates':len(updates),'old_signature':prior,'new_signature':future,'backup':backup.name,'scientific_fields_changed':False,'reason':'Reviewed path-only I/O support. Models, fitting, matcher, thresholds and folds unchanged.'}
 write_json(out/'long_path_migration.json',report)
 manifest['source_sha256'][name]=sha(current);write_json(mp,manifest)
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
