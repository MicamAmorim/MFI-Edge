"""Post-hoc, GT-free image clustering and retrospective model modes from Stage24.
No detector fitting, threshold search, GT loading, or changes to campaign data.
"""
from pathlib import Path
import argparse,csv,json,hashlib,collections,itertools
import numpy as np
from scipy.cluster.hierarchy import linkage,fcluster
from scipy.spatial.distance import pdist,squareform
from skimage.morphology import thin

def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
 with Path(p).open(encoding='utf-8') as f:return list(csv.DictReader(f))
def save(p,rows):
 with Path(p).open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def features(a):
 gy,gx=np.gradient(a.astype(float));energy=np.hypot(gx,gy)
 xx=float(np.mean(gx*gx));yy=float(np.mean(gy*gy));xy=float(np.mean(gx*gy))
 coherence=np.hypot(xx-yy,2*xy)/(xx+yy+1e-15)
 return [float(a.mean()),float(a.std()),float(np.quantile(a,.9)),float(np.mean(a>.5)),float(energy.mean()),float(coherence)]
def embed(x):
 sd=x.std(axis=0);z=(x-x.mean(axis=0))/np.where(sd>1e-12,sd,1.)
 u,s,v=np.linalg.svd(z,full_matrices=False)
 return z,u[:,:3]*s[:3],s*s/max(float(np.sum(s*s)),1e-15)
def clusters(x,k):
 raw=fcluster(linkage(x,method='ward'),k,criterion='maxclust')
 order=sorted(set(raw),key=lambda a:np.flatnonzero(raw==a)[0])
 return np.array([order.index(c)+1 for c in raw])
def ari(a,b):
 n=len(a);pairs=lambda v:v*(v-1)/2
 table=collections.Counter(zip(a,b));obs=sum(pairs(v) for v in table.values())
 aa=sum(pairs(v) for v in collections.Counter(a).values());bb=sum(pairs(v) for v in collections.Counter(b).values())
 exp=aa*bb/pairs(n);den=(aa+bb)/2-exp
 return float((obs-exp)/den) if den else 1.
def silhouette(x,labels):
 d=squareform(pdist(x));vals=[]
 for i,c in enumerate(labels):
  same=np.flatnonzero(labels==c);same=same[same!=i]
  if not len(same):vals.append(0.);continue
  a=float(d[i,same].mean());b=min(float(d[i,labels==other].mean()) for other in set(labels) if other!=c)
  vals.append((b-a)/max(a,b,1e-15))
 return float(np.mean(vals))
def common_models(rows,expected):
 by=collections.defaultdict(dict)
 for r in rows:
  key=(r['image_id'],r['fold']);model=r['model']
  if key in by[model]:raise ValueError('Duplicate model/image/fold: '+model)
  by[model][key]=r
 return {m:v for m,v in by.items() if set(v)==set(expected)}
def canonical(model):
 group,agg=model.split('::')
 agg={'owa_median':'median','owa_optimistic':'maximum','owa_pessimistic':'minimum','owa_centered':'equal_mean'}.get(agg,agg)
 if agg=='median' and len(group.split('|'))==2:agg='equal_mean'
 return group+'::'+agg

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--research-root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
 root=args.research_root.resolve();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
 base=root/'results/local_dev/stage24_paper_a_recertification'
 provenance=read(base/'descriptor_provenance.csv');ids=sorted({r['image_id'] for r in provenance});descs=sorted({r['descriptor_id'] for r in provenance})
 assert len(ids)==14 and len(descs)==13
 source_images={r['image_id']:r['source_sha256'] for r in json.loads((base/'native_dataset_manifest.json').read_text())['records'] if not r['excluded']}
 wanted={(r['image_id'],r['descriptor_id']):r['sha256'] for r in provenance};found={};hashes={}
 # Read only the registered UDED descriptor caches. No GTs or metrics are used here.
 for d in descs:
  for side in sorted((root/'cache/local_dev/stage24/descriptors'/d).glob('*.json')):
   meta=json.loads(side.read_text());ident=meta.get('identity',{});key=(ident.get('image_id'),d)
   if ident.get('dataset')!='UDED' or key not in wanted:continue
   path=side.with_suffix('.npy')
   if digest(path)!=wanted[key]:continue
   assert ident['gt_used'] is False and ident['source_sha256']==source_images[key[0]]
   a=np.load(path,allow_pickle=False);assert a.ndim==2 and a.dtype==np.float32 and np.isfinite(a).all()
   found[key]=features(a);hashes[str(path.relative_to(root))]=wanted[key]
 assert set(found)==set(wanted),f'Missing or invalid float maps: {set(wanted)-set(found)}'
 names=[d+'::'+v for d in descs for v in ['mean','std','q90','fraction_gt_0.5','gradient','orientation_coherence']]
 x=np.array([sum([found[(im,d)] for d in descs],[]) for im in ids]);z,coords,explained=embed(x)
 save(out/'image_features.csv',[dict(image_id=im,**dict(zip(names,x[i]))) for i,im in enumerate(ids)])
 lab={k:clusters(coords,k) for k in [2,3,4]}
 save(out/'clusters.csv',[{'image_id':im,'cluster_k2':int(lab[2][i]),'cluster_k3':int(lab[3][i]),'cluster_k4':int(lab[4][i]),**{f'PC{j+1}':float(coords[i,j]) for j in range(3)}} for i,im in enumerate(ids)])
 ablations=[]
 for j,d in enumerate(descs):
  keep=[a for a in range(x.shape[1]) if a//6!=j];_,c,_=embed(x[:,keep]);ablations.append({'omitted_descriptor':d,'ARI_k3':ari(lab[3],clusters(c,3))})
 save(out/'cluster_stability.csv',ablations)
 # Only now read evaluation outcomes. Same candidate coverage for all images/repeats.
 singles=read(base/'individual_descriptors_corrected_per_image.csv');landscape=read(base/'aggregator_landscape_per_image.csv')
 rows=[]
 for r in singles:
  if r['thinning']=='nms_image':rows.append({'model':r['descriptor_id']+'::single','image_id':r['image_id'],'fold':r['fold'],'F1':float(r['F1'])})
 for r in landscape:
  if r['thinning']=='nms_image' and r['suppressor']=='identity' and r['calibration_mode']=='legacy_sigmoid':
   rows.append({'model':r['group']+'::'+r['aggregator'],'image_id':r['image_id'],'fold':r['fold_id'],'F1':float(r['F1'])})
 expected={(r['image_id'],r['fold']) for r in rows if r['model'].endswith('::single')};assert len(expected)==70
 common=common_models(rows,expected);assert len(common)>=13
 model_names=sorted(common);values=np.array([[np.mean([r['F1'] for (image,fold),r in common[m].items() if image==im]) for m in model_names] for im in ids])
 save(out/'common_candidate_scores.csv',[{'image_id':im,'model':m,'mean_heldout_F1':float(values[i,j]),'repetitions':5} for i,im in enumerate(ids) for j,m in enumerate(model_names)])
 save(out/'candidate_coverage.csv',[{'model':m,'image_fold_records':sum(r['model']==m for r in rows),'included_common_universe':m in common} for m in sorted({r['model'] for r in rows})])
 winners=[];ties=[]
 for i,im in enumerate(ids):
  maximum=float(values[i].max());js=np.flatnonzero(np.abs(values[i]-maximum)<=1e-10);ties.append(sorted({canonical(model_names[j]) for j in js}))
  single=max(values[i,j] for j,m in enumerate(model_names) if m.endswith('::single'))
  winners.append({'image_id':im,'cluster_k3':int(lab[3][i]),'winners':' ; '.join(ties[-1]),'n_ties':len(ties[-1]),'oracle_F1':maximum,'best_single_F1':float(single),'oracle_gain_over_best_single':maximum-float(single)})
 save(out/'image_winners.csv',winners)
 modes=[];profiles=[]
 for k in [2,3,4]:
  for c in sorted(set(lab[k])):
   idx=np.flatnonzero(lab[k]==c);votes=collections.defaultdict(float)
   for i in idx:
    for m in ties[i]:votes[m]+=1/len(ties[i])
   best=max(votes.values());modal=sorted(m for m,v in votes.items() if abs(v-best)<1e-10)
   modes.append({'k':k,'cluster':int(c),'n_images':len(idx),'image_ids':' ; '.join(ids[i] for i in idx),'modal_models':' ; '.join(modal),'modal_fractional_votes':best,'modal_share':best/len(idx),'n_tied_modes':len(modal)})
   if k==3:
    # Descriptor mean-response z scores describe clusters, not semantic ground truth.
    for j,d in enumerate(descs):profiles.append({'cluster':int(c),'descriptor':d,'mean_response_z':float(z[idx,j*6].mean())})
 save(out/'cluster_modes.csv',modes);save(out/'cluster_descriptor_profiles.csv',profiles)
 # Morphological audit of final-model maps; diagnostic only (fitted on all UDED).
 frozen=json.loads((base/'frozen_models.json').read_text())['models'];audit=[]
 for r in read(base/'uded_float_prediction_manifest.csv'):
  if r['variant'] not in ['winner','identity','best_single']:continue
  path=root/r['relative_path'];assert digest(path)==r['score_sha256'];a=np.load(path,allow_pickle=False)
  model=frozen[r['variant']];assert model['thinning']=='nms_image'
  b=a>=model['threshold'];bt=thin(b);n=int(b.sum());nt=int(bt.sum());blocks=int(np.sum(b[:-1,:-1]&b[1:,:-1]&b[:-1,1:]&b[1:,1:]))
  audit.append({'image_id':r['image_id'],'variant':r['variant'],'NMS_threshold_pixels':n,'after_extra_morphological_thin':nt,'removed_fraction':(n-nt)/max(n,1),'full_2x2_blocks':blocks})
 save(out/'boundary_thickness_audit.csv',audit)
 official=json.loads((base/'official_bsds_summary.json').read_text());assert len(official['methods'])==8 and all(m['thinpb'] for m in official['methods'].values())
 chosen=read(base/'inner_selected_heldout.csv');assert len(chosen)==15 and all(r['thinning']=='nms_image' for r in chosen)
 result={'status':'complete_exploratory','n_images':14,'descriptor_maps':len(found),'n_features':x.shape[1],'PCA_components':3,'PCA_explained_fraction':float(explained[:3].sum()),'primary_k':3,'silhouettes':{str(k):silhouette(coords,lab[k]) for k in lab},'leave_one_descriptor_out_ARI_range':[min(r['ARI_k3'] for r in ablations),max(r['ARI_k3'] for r in ablations)],'common_candidate_count':len(common),'canonical_candidate_count':len({canonical(m) for m in common}),'mathematical_aliases_collapsed_for_modes':True,'all_candidate_count':len({r['model'] for r in rows}),'modes':modes,'boundary_audit':{'BSDS_all_eight_thinpb':True,'UDED_all_15_selected_NMS':True,'extra_thinning_mean_removed':{v:float(np.mean([r['removed_fraction'] for r in audit if r['variant']==v])) for v in ['winner','identity','best_single']},'warning':'NMS is not morphological skeletonization; diagnostic maps are final refits, not held-out predictions.'},'limits':['Descriptive transductive clustering of 14 images; no independent test.','Cluster construction does not load GT or performance; all images inform scaling/PCA.','Model winners and modes use held-out outcomes retrospectively: oracle, not deployable selection.','Only common complete-coverage candidates, nms_image, identity suppression and legacy calibration.','No inference that image features cause model performance; no confirmatory p-values.']}
 write(out/'summary.json',result)
 paths=['descriptor_provenance.csv','native_dataset_manifest.json','individual_descriptors_corrected_per_image.csv','aggregator_landscape_per_image.csv','frozen_models.json','uded_float_prediction_manifest.csv','official_bsds_summary.json','inner_selected_heldout.csv']
 write(out/'provenance.json',{'code_sha256':digest(__file__),'scientific_sources':{str((base/n).relative_to(root)):digest(base/n) for n in paths},'descriptor_cache_sha256':hashes,'clustering_uses_GT':False,'clustering_uses_performance':False,'selection_is_posthoc':True})
 print(json.dumps(result,ensure_ascii=True,indent=2))
if __name__=='__main__':main()
