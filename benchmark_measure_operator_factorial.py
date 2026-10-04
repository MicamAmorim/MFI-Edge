from __future__ import annotations

from pathlib import Path
import argparse
import itertools
import json
import math
import time

import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from skimage.io import imread

from benchmark_synthetic import operator_specs
from src.conditioning import apply_conditioning
from src.classical_detectors import detector_score
from src.evaluation import benchmark_metrics
from src.fuzzy_measures import measure_registry
from src.hybrid import percentile_confidence, mfi_roi, hard_gate
from src.measure_learning import fit_context_centroids, predict_context
from src.pipeline import precompute_multiscale_features, multiscale_from_precomputed
from src.postprocess import gradient_orientation, non_maximum_suppression

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'datasets'/'sintetics'/'benchmark_v2'
MODEL_DIR=ROOT/'benchmark_outputs'/'stage5_measures'
OUT=ROOT/'benchmark_outputs'/'stage5_factorial'
SCALES=(25,13,7,5,3)
ROI_QS=(0.50,0.55,0.60,0.65,0.70,0.75,0.80,0.85)


def coarse_context(family):
    if family in ('gaussian','saltpepper','speckle'): return 'stochastic'
    if family in ('blur','motion'): return 'blur_motion'
    if family in ('texture','compound'): return 'texture_compound'
    return 'structural'


def load_selection():
    mf=pd.read_csv(DATA/'validation'/'manifest.csv').iloc[20:].reset_index(drop=True)
    items=[]; names=None
    for r in mf.itertuples(index=False):
        img=imread(ROOT/r.image); gt=imread(ROOT/r.ground_truth)>0
        pim=apply_conditioning(img,'median',size=3)
        pre,names=precompute_multiscale_features(pim,SCALES,feature_mode='oriented')
        ori=gradient_orientation(pim,1.0)
        sch=non_maximum_suppression(detector_score(pim,'scharr',1.0),ori)
        items.append({'row':r,'gt':gt,'img':pim,'pre':pre,'scharr':sch})
    return items,names


def context_for(spec,d,ctx_model):
    routing=spec.get('routing')
    if routing=='oracle': return {'context_label':coarse_context(d['row'].family)}
    if routing=='estimated': return {'context_label':predict_context(d['img'],ctx_model)}
    return {}


def evaluate(config,items,ctx_model):
    op,measure,rq=config
    scores=[]; gts=[]; cov=[]
    clean={k:v for k,v in measure.items() if k!='name'}
    kwargs={k:v for k,v in op.items() if k in ('family','F','F1','F2')}
    for d in items:
        _,bits,_=multiscale_from_precomputed(
            d['pre'],d['gt'].shape,q=.1,refine_quantile=.82,
            heterogeneity_quantile=.82,dilation_radius=3,
            measure_spec=clean,measure_context=context_for(measure,d,ctx_model),**kwargs)
        conf=percentile_confidence(bits)
        roi,_=mfi_roi(conf,rq,0,already_confidence=True)
        scores.append(hard_gate(d['scharr'],roi)); gts.append(d['gt'])
        gd=ndi.binary_dilation(d['gt'],iterations=1)
        cov.append(np.logical_and(roi,gd).sum()/max(gd.sum(),1))
    m=benchmark_metrics(scores,gts,tol=2,n_thresholds=31)
    return {k:v for k,v in m.items() if k!='curve'}|{'roi_gt_coverage':float(np.mean(cov))}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--chunk-index',type=int,default=0)
    ap.add_argument('--chunk-size',type=int,default=100)
    ap.add_argument('--start',type=int,default=None)
    ap.add_argument('--stop',type=int,default=None)
    args=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    learned=json.loads((MODEL_DIR/'learned_measures.json').read_text())
    ctx_model=json.loads((MODEL_DIR/'context_router.json').read_text())
    names=json.loads((MODEL_DIR/'feature_names.json').read_text())
    measures=measure_registry(len(names),learned)
    ops=operator_specs()
    configs=list(itertools.product(ops,measures,ROI_QS))
    total=len(configs)
    start=args.start if args.start is not None else args.chunk_index*args.chunk_size
    stop=args.stop if args.stop is not None else min(total,start+args.chunk_size)
    print(f'total={total} start={start} stop={stop}',flush=True)
    items,_=load_selection()
    rows=[]; t0=time.perf_counter()
    for idx in range(start,stop):
        op,m,rq=configs[idx]
        met=evaluate((op,m,rq),items,ctx_model)
        rows.append({'global_index':idx,'operator':op['name'],'family':op['family'],
                     'measure':m['name'],'measure_kind':m.get('kind',''),'roi_q':rq,**met})
        if len(rows)%10==0:
            print(idx,op['name'],m['name'],rq,met['ODS'],flush=True)
    df=pd.DataFrame(rows).sort_values(['ODS','AP','OIS'],ascending=False)
    fn=OUT/f'chunk_{start:07d}_{stop:07d}.csv'; df.to_csv(fn,index=False)
    meta={'total_configs':total,'operators':len(ops),'measures':len(measures),'roi_qs':list(ROI_QS),
          'chunk_start':start,'chunk_stop':stop,'elapsed_s':time.perf_counter()-t0}
    (OUT/f'chunk_{start:07d}_{stop:07d}.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    print(df.head(20).to_string(index=False))

if __name__=='__main__': main()
