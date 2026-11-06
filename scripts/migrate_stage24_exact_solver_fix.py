"""One-time exact-solver fix migration. Only accepts the reviewed exact max-flow implementation."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def digest(data):return hashlib.sha256(data).hexdigest()
def main():
 out=ROOT/'results/local_dev/stage24_paper_a_recertification';path=out/'campaign_source_fingerprint.json'
 manifest=json.loads(path.read_text(encoding='utf-8'));name='src/stage24_integrity.py'
 original=subprocess.check_output(['git','show','e32f00d:'+name],cwd=ROOT).replace(b'\r\n',b'\n')
 current=(ROOT/name).read_bytes();normalized=current.replace(b'\r\n',b'\n')
 start=original.index(b'        if not certified:\n            # Greedy ordering');end=original.index(b'        if certified:\n',start)
 assert digest(normalized)=='0306bc07c519198dd42a69c1e378d04b20beb25b42966a30807079d75bcaa6de','Unreviewed code change'
 oldhash=manifest['source_sha256'][name]
 if oldhash==digest(current):
  print('EXACT_SOLVER_MIGRATION_ALREADY_APPLIED');return
 assert oldhash in {digest(original),digest(original.replace(b'\n',b'\r\n'))},'Unknown prior matcher'
 for source,h in manifest['source_sha256'].items():
  if source!=name:assert digest((ROOT/source).read_bytes())==h,'Other source changed: '+source
 files=list((out/'folds').rglob('*.json'))
 for f in files:
  assert f.name in ('pair_screen.json','geometry_audit.json') or f.parent.name=='individual_descriptor_parts','Unsupported group checkpoint'
 inventory={str(f.relative_to(out)):digest(f.read_bytes()) for f in files}
 backup=out/'campaign_source_fingerprint.before_exact_solver_fix.json'
 if not backup.exists():backup.write_bytes(path.read_bytes())
 report={'old_matcher_sha256':oldhash,'new_matcher_sha256':digest(current),'preserved_checkpoints':inventory,'justification':'Restricted solver removed; full graph uses unit-capacity Dinic max flow, mathematically equivalent to maximum bipartite cardinality; memberships, NMS, thresholds, data, folds unchanged. Independent graph oracle and native regression validated.'}
 (out/'exact_solver_migration.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 manifest['source_sha256'][name]=digest(current)
 tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(manifest,indent=2,sort_keys=True),encoding='utf-8');tmp.replace(path)
 assert inventory=={str(f.relative_to(out)):digest(f.read_bytes()) for f in files}
 print('EXACT_SOLVER_MIGRATED_PRESERVING',len(files),'CHECKPOINTS')
if __name__=='__main__':main()
