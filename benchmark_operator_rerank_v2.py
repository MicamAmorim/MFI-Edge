from pathlib import Path
import time
import numpy as np,pandas as pd
from skimage.io import imread
from benchmark_synthetic import operator_specs
from src.conditioning import apply_conditioning
from src.pipeline import precompute_multiscale_features,multiscale_from_precomputed
from src.hybrid import percentile_confidence,mfi_roi,hard_gate
from src.classical_detectors import detector_score
from src.postprocess import gradient_orientation,non_maximum_suppression
from src.evaluation import benchmark_metrics
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'datasets'/'sintetics'/'benchmark_v2'/'validation'
OUT=ROOT/'benchmark_outputs'/'stage4'/'operator_rerank_v2.csv'
SCALES=(25,13,7,5,3)

def main():
 mf=pd.read_csv(DATA/'manifest.csv'); cache=[]
 t=time.perf_counter()
 for r in mf.itertuples(index=False):
  img=imread(ROOT/r.image); gt=imread(ROOT/r.ground_truth)>0; pre=apply_conditioning(img,'median',size=3)
  feats,_=precompute_multiscale_features(pre,SCALES,feature_mode='oriented')
  sch=non_maximum_suppression(detector_score(pre,'scharr',1),gradient_orientation(pre,1))
  cache.append((pre.shape[:2],gt,feats,sch))
 print('cache',time.perf_counter()-t,flush=True)
 rows=[]; specs=operator_specs()
 # de-duplicate by name
 uniq={s['name']:s for s in specs}; specs=list(uniq.values()); print('ops',len(specs),flush=True)
 for ix,spec in enumerate(specs):
  if ix%20==0: print(ix,spec['name'],flush=True)
  raw=[]
  for shape,gt,feats,sch in cache:
   kw={k:v for k,v in spec.items() if k in ('family','F','F1','F2')}
   _,mfi,_=multiscale_from_precomputed(feats,shape,q=.1,refine_quantile=.82,heterogeneity_quantile=.82,dilation_radius=3,**kw)
   raw.append((percentile_confidence(mfi),sch,gt))
  for q in (.60,.65,.70):
   scores=[];gts=[]
   for conf,sch,gt in raw:
    roi,_=mfi_roi(conf,q,0,True); scores.append(hard_gate(sch,roi)); gts.append(gt)
   m=benchmark_metrics(scores,gts,tol=2,n_thresholds=25)
   rows.append({'operator':spec['name'],'family':spec['family'],'q_measure':.1,'roi_q':q,
                **{k:v for k,v in m.items() if k!='curve'}})
 df=pd.DataFrame(rows).sort_values(['ODS','AP','OIS'],ascending=False); df.to_csv(OUT,index=False)
 print(df.head(20)[['operator','roi_q','ODS','OIS','AP','R50','ROC_AUC']].to_string(index=False),flush=True)
 print('elapsed',time.perf_counter()-t,flush=True)
if __name__=='__main__': main()
