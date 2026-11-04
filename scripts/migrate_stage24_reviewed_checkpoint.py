"""Explicit, one-time audited Stage24 checkpoint migration; never relax fingerprints."""
from pathlib import Path
import hashlib,json,subprocess,shutil,argparse
ROOT=Path(__file__).resolve().parents[1]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def verify_sources(manifest, revision):
    for name, expected in manifest['source_sha256'].items():
        raw=subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)
        lf=raw.replace(b'\r\n',b'\n')
        if revision == '53a4f08' and sha(ROOT/name) == expected and (ROOT/name).read_bytes().replace(b'\r\n',b'\n') == lf:
            continue
        if expected not in {hashlib.sha256(lf).hexdigest(),hashlib.sha256(lf.replace(b'\n',b'\r\n')).hexdigest()}:
            raise RuntimeError('Unreviewed source: '+name)
def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args()
    old=ROOT/'results/local_dev/stage24_paper_a_recertification_before_b25ceb2_20261104'
    new=ROOT/'results/local_dev/stage24_paper_a_recertification'
    a,b=read(old/'campaign_source_fingerprint.json'),read(new/'campaign_source_fingerprint.json')
    verify_sources(a,'565942c');verify_sources(b,'53a4f08')
    assert a['configuration']==b['configuration'],'Configuration drift'
    assert (old/'environment.lock.txt').read_bytes()==(new/'environment.lock.txt').read_bytes(),'Environment drift'
    assert read(old/'native_dataset_manifest.json')==read(new/'native_dataset_manifest.json'),'Dataset drift'
    for name,h in b['source_sha256'].items():
        assert sha(ROOT/name)==h,'Current source drift: '+name
    # Revalidate original image/GT bytes and every descriptor float cache actually
    # used by the current loader. JPEG source photographs are allowed; quantized
    # detector maps are not. GT files are canonical annotations, not score maps.
    import sys
    sys.path.insert(0,str(ROOT))
    from run_stage24_residual_campaign import load_uded_native,descriptor_native
    from src.stage23_descriptors import DESCRIPTOR_IDS
    items,manifest=load_uded_native(Path(b['configuration']['uded_root']))
    assert manifest==read(new/'native_dataset_manifest.json')
    provenance=[]
    for item in items:
        for descriptor in DESCRIPTOR_IDS:
            _,record=descriptor_native(item,descriptor,Path(b['configuration']['cache_root']),allow_legacy=False)
            assert record['source']=='stage24_cache','Unexpected recomputation'
            provenance.append(record)
    relative=Path('folds/r1_f1/individual_descriptor_parts')
    raw='scharr_pre_nms_magnitude__raw.json'
    assert read(old/relative/raw)==read(new/relative/raw),'Native raw regression differs'
    source=old/relative/'scharr_pre_nms_magnitude__nms_image.json'
    target=new/relative/source.name
    data=read(source); spec=data['spec'];rawspec=read(new/relative/raw)['spec']
    assert {k:v for k,v in spec.items() if k!='thinning'}=={k:v for k,v in rawspec.items() if k!='thinning'}
    assert spec['thinning']=='nms_image' and len(data['per_image'])==len(spec['valid_indices'])
    assert {r['image_id'] for r in data['per_image']}=={items[i]['id'] for i in spec['valid_indices']}
    for key in ('tp','fp','fn'):
        assert sum(r[key] for r in data['per_image'])==data['summary'][key]
    for row in data['per_image']:
        assert all(row[k]>=0 for k in ('tp','fp','fn'))
        assert abs(row['F1']-2*row['tp']/(2*row['tp']+row['fp']+row['fn']))<1e-12
    report={'source_revision':'565942c','target_revision':'53a4f08','source_file':str(source),'sha256':sha(source),'validated_float_maps':len(provenance),'provenance':provenance,'basis':'Reviewed exact-cardinality matcher optimizations; unchanged Scharr membership, GT, folds, thresholds and NMS; native raw identity and independent matching oracle tests. Explicit migration of this single checkpoint only.','applied':False}
    if target.exists():
        assert read(target)==data,'Conflicting existing checkpoint'
    elif args.apply:
        target.parent.mkdir(parents=True,exist_ok=True)
        temporary=target.with_suffix('.migration.tmp');shutil.copyfile(source,temporary);temporary.replace(target)
        report['applied']=True
    (new/'checkpoint_migration_53a4f08.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='provenance'},indent=2))
if __name__=='__main__':main()
