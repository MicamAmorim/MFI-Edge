from __future__ import annotations

from pathlib import Path
import argparse
import json
import time

import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from skimage.io import imread

from src.conditioning import apply_conditioning
from src.classical_detectors import detector_score
from src.evaluation import benchmark_metrics
from src.fuzzy_measures import measure_registry, shapley_values, interaction_matrix
from src.hybrid import percentile_confidence, mfi_roi, hard_gate
from src.measure_learning import (
    fit_context_centroids,
    learn_2additive,
    learn_additive,
    learn_full_capacity,
    learned_sugeno_from_reliability,
    pool_balanced_samples,
    predict_context,
)
from src.pipeline import precompute_multiscale_features, multiscale_from_precomputed
from src.postprocess import gradient_orientation, non_maximum_suppression

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'datasets'/'sintetics'/'benchmark_v2'
OUT=ROOT/'benchmark_outputs'/'stage5_measures'
SCALES=(25,13,7,5,3)
ROI_QS=(0.55,0.60,0.65,0.70,0.75,0.80)


def coarse_context(family):
    family=str(family)
    if family in ('gaussian','saltpepper','speckle'):
        return 'stochastic'
    if family in ('blur','motion'):
        return 'blur_motion'
    if family in ('texture','compound'):
        return 'texture_compound'
    return 'structural'


def load_split(split):
    mf=pd.read_csv(DATA/split/'manifest.csv')
    items=[]
    for r in mf.itertuples(index=False):
        img=imread(ROOT/r.image)
        gt=imread(ROOT/r.ground_truth)>0
        items.append({'row':r,'img':img,'gt':gt})
    return items


def prepare(items):
    out=[]
    names=None
    for d in items:
        pre_img=apply_conditioning(d['img'],'median',size=3)
        pre,names=precompute_multiscale_features(pre_img,SCALES,feature_mode='oriented')
        ori=gradient_orientation(pre_img,1.0)
        sch=non_maximum_suppression(detector_score(pre_img,'scharr',1.0),ori)
        target=ndi.binary_dilation(d['gt'],iterations=1)
        out.append({**d,'pre_img':pre_img,'features':pre,'scharr':sch,'target':target})
    return out,names


def fit_learned_specs(fit_items,names,full_capacity=True):
    # Pool all scales for global capacities.
    fmap=[]; targ=[]
    for d in fit_items:
        for _,X,_ in d['features']:
            fmap.append(X); targ.append(d['target'])
    X,y=pool_balanced_samples(fmap,targ,max_samples=30000,seed=123)
    learned={}
    learned['additive_learned']=learn_additive(X,y)
    for total in (0.60,0.80,1.00,1.20,1.40):
        learned[f'sugeno_learned_sum{total:.2f}']=learned_sugeno_from_reliability(X,y,total)
    learned['2additive_learned']=learn_2additive(X,y,maxiter=700)
    if full_capacity:
        Xf,yf=pool_balanced_samples(fmap,targ,max_samples=10000,seed=321)
        learned['full_capacity_learned']=learn_full_capacity(Xf,yf,maxiter=280)

    # Scale-specific learned measures.
    scale_add={}; scale_2a={}
    for sidx,w in enumerate(SCALES):
        Xs,ys=pool_balanced_samples([d['features'][sidx][1] for d in fit_items],
                                    [d['target'] for d in fit_items],max_samples=12000,seed=1000+sidx)
        scale_add[str(w)]=learn_additive(Xs,ys)
        scale_2a[str(w)]=learn_2additive(Xs,ys,maxiter=500)
    learned['scale_additive_learned']={'kind':'scale_router','measures':scale_add,
                                       'default':learned['additive_learned']}
    learned['scale_2additive_learned']={'kind':'scale_router','measures':scale_2a,
                                        'default':learned['2additive_learned']}

    # Context-specific banks; routing can be oracle (upper bound) or estimated from the image.
    groups=sorted({coarse_context(d['row'].family) for d in fit_items})
    bank_add={}; bank_2a={}
    for group in groups:
        subset=[d for d in fit_items if coarse_context(d['row'].family)==group]
        fm=[]; yy=[]
        for d in subset:
            for _,Xi,_ in d['features']:
                fm.append(Xi); yy.append(d['target'])
        Xg,yg=pool_balanced_samples(fm,yy,max_samples=14000,seed=abs(hash(group))%(2**31))
        bank_add[group]=learn_additive(Xg,yg)
        bank_2a[group]=learn_2additive(Xg,yg,maxiter=450)
    learned['context_additive_oracle']={'kind':'context_router','measures':bank_add,
                                        'default':learned['additive_learned'],'routing':'oracle'}
    learned['context_2additive_oracle']={'kind':'context_router','measures':bank_2a,
                                         'default':learned['2additive_learned'],'routing':'oracle'}
    learned['context_additive_estimated']={'kind':'context_router','measures':bank_add,
                                           'default':learned['additive_learned'],'routing':'estimated'}
    learned['context_2additive_estimated']={'kind':'context_router','measures':bank_2a,
                                            'default':learned['2additive_learned'],'routing':'estimated'}

    context_model=fit_context_centroids([d['pre_img'] for d in fit_items],
                                        [coarse_context(d['row'].family) for d in fit_items])
    return learned,context_model


def spec_context(spec,d,context_model):
    routing=spec.get('routing')
    if routing=='oracle':
        return {'context_label':coarse_context(d['row'].family)}
    if routing=='estimated':
        return {'context_label':predict_context(d['pre_img'],context_model)}
    return {}


def evaluate_spec(spec,items,context_model,roi_q):
    scores=[]; gts=[]; cover=[]; roi_frac=[]
    t0=time.perf_counter()
    clean={k:v for k,v in spec.items() if k!='name'}
    for d in items:
        ctx=spec_context(spec,d,context_model)
        _,bits,_=multiscale_from_precomputed(
            d['features'],d['gt'].shape,family='CF1F2',F1='CL',F2='CL',q=.1,
            refine_quantile=.82,heterogeneity_quantile=.82,dilation_radius=3,
            measure_spec=clean,measure_context=ctx)
        conf=percentile_confidence(bits)
        roi,_=mfi_roi(conf,roi_q,0,already_confidence=True)
        score=hard_gate(d['scharr'],roi)
        scores.append(score); gts.append(d['gt'])
        gd=ndi.binary_dilation(d['gt'],iterations=1)
        cover.append(float(np.logical_and(roi,gd).sum()/max(gd.sum(),1)))
        roi_frac.append(float(roi.mean()))
    m=benchmark_metrics(scores,gts,tol=2,n_thresholds=41)
    return {**{k:v for k,v in m.items() if k!='curve'},
            'roi_gt_coverage':float(np.mean(cover)),'roi_fraction':float(np.mean(roi_frac)),
            'runtime_s':float(time.perf_counter()-t0)}


def export_interpretability(specs,names):
    rows=[]; pair_rows=[]
    for spec in specs:
        name=spec['name']
        table=spec.get('capacity_table')
        if table is None:
            continue
        mu=np.asarray(table,float)
        n=int(round(np.log2(len(mu))))
        if n!=len(names):
            continue
        sv=np.asarray(spec.get('shapley',shapley_values(mu)),float)
        I=np.asarray(spec.get('interaction',interaction_matrix(mu)),float)
        for i,v in enumerate(sv):
            rows.append({'measure':name,'feature':names[i],'shapley':float(v)})
        for i in range(n):
            for j in range(i+1,n):
                pair_rows.append({'measure':name,'feature_i':names[i],'feature_j':names[j],
                                  'interaction':float(I[i,j])})
    pd.DataFrame(rows).to_csv(OUT/'shapley.csv',index=False)
    pd.DataFrame(pair_rows).to_csv(OUT/'interactions.csv',index=False)


def json_safe(o):
    if isinstance(o,np.ndarray): return o.tolist()
    if isinstance(o,(np.floating,np.integer)): return o.item()
    raise TypeError(type(o).__name__)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--skip-full-capacity',action='store_true')
    ap.add_argument('--max-measures',type=int,default=None)
    args=ap.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    if not (DATA/'validation'/'manifest.csv').exists():
        raise FileNotFoundError('Run synthetic_v2.py first')

    val=load_split('validation'); test=load_split('test')
    # deterministic internal split: first half fits measures; second half selects variants.
    fit_raw,val_raw=val[:20],val[20:]
    fit,names=prepare(fit_raw); select,_=prepare(val_raw); testp,_=prepare(test)
    learned,context_model=fit_learned_specs(fit,names,full_capacity=not args.skip_full_capacity)
    specs=measure_registry(len(names),learned=learned)
    if args.max_measures:
        specs=specs[:args.max_measures]

    # Persist learned capacities before evaluation so experiments are reproducible.
    (OUT/'learned_measures.json').write_text(json.dumps(learned,indent=2,default=json_safe),encoding='utf-8')
    (OUT/'context_router.json').write_text(json.dumps(context_model,indent=2,default=json_safe),encoding='utf-8')
    (OUT/'feature_names.json').write_text(json.dumps(names,indent=2),encoding='utf-8')

    rows=[]
    for i,spec in enumerate(specs):
        print(f'[{i+1}/{len(specs)}] {spec["name"]}',flush=True)
        best=None
        for rq in ROI_QS:
            met=evaluate_spec(spec,select,context_model,rq)
            row={'measure':spec['name'],'measure_kind':spec.get('kind',''), 'roi_q':rq,**met}
            rows.append(row)
            if best is None or (row['ODS'],row['AP'],row['OIS'])>(best['ODS'],best['AP'],best['OIS']):
                best=row
    all_df=pd.DataFrame(rows)
    all_df.to_csv(OUT/'validation_all.csv',index=False)
    best_df=(all_df.sort_values(['ODS','AP','OIS'],ascending=False)
             .groupby('measure',as_index=False).first()
             .sort_values(['ODS','AP','OIS'],ascending=False).reset_index(drop=True))
    best_df.to_csv(OUT/'validation_best_per_measure.csv',index=False)

    # Held-out test: evaluate top-10 variants fixed by internal validation.
    test_rows=[]
    spec_by_name={s['name']:s for s in specs}
    for rank,r in best_df.head(10).iterrows():
        spec=spec_by_name[r.measure]
        met=evaluate_spec(spec,testp,context_model,float(r.roi_q))
        test_rows.append({'selection_rank':rank+1,'measure':r.measure,'measure_kind':r.measure_kind,
                          'roi_q':float(r.roi_q),**met})
    pd.DataFrame(test_rows).sort_values(['ODS','AP','OIS'],ascending=False).to_csv(OUT/'test_top10.csv',index=False)
    export_interpretability(specs,names)

    print('\nVALIDATION TOP 20')
    print(best_df.head(20)[['measure','measure_kind','roi_q','ODS','OIS','AP','R50','ROC_AUC','roi_gt_coverage','roi_fraction']].to_string(index=False))
    print('\nHELD-OUT TOP 10 (preselected on validation)')
    print(pd.DataFrame(test_rows).sort_values(['ODS','AP'],ascending=False)[['measure','roi_q','ODS','OIS','AP','R50','ROC_AUC','roi_gt_coverage']].to_string(index=False))

if __name__=='__main__':
    main()
