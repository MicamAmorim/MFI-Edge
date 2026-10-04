from __future__ import annotations

from pathlib import Path
import argparse
import gc
import json

import numpy as np
import pandas as pd

from benchmark_uded import (
    DEFAULT_UDED, MODEL_DIR, context_for, load_uded, prepare,
    _variable_tol_curve,
)
from benchmark_uded_quick import resize_items
from src.fuzzy_measures import measure_registry
from src.hybrid import percentile_confidence
from src.pipeline import multiscale_from_precomputed


DEFAULT_OUT = Path(__file__).resolve().parent / 'benchmark_outputs' / 'uded_fusion_v1'
SCALES = (25,13,7,5,3)

# Targeted follow-up after the all-measure UDED screen. This includes the strongest
# UDED hard-gate variants plus synthetic-development winners/controls.
TARGET_MEASURES = (
    'scale_additive_learned',
    'scale_2additive_learned',
    'sugeno_learned_sum0.60',
    'context_additive_estimated',
    'additive_learned',
    'power_q1.5',
    'power_q0.2',
    'sugeno_learned_sum1.40',
)


def metric(scores, gts, n_thresholds=21):
    m = _variable_tol_curve(scores, gts, beta=1.0, n_thresholds=n_thresholds,
                            frac_diag=0.0075)
    return {k:v for k,v in m.items() if k != 'curve'}


def fusion_specs(roi_q):
    out=[('hard', {'roi_q':float(roi_q)})]
    for eps,gamma in ((0.10,1.0),(0.25,1.0),(0.50,1.0),(0.25,0.5),(0.25,2.0)):
        out.append((f'soft_e{eps:.2f}_g{gamma:g}', {'eps':eps,'gamma':gamma}))
    for lam in (0.25,0.50,1.00):
        out.append((f'residual_l{lam:.2f}', {'lambda':lam}))
    for alpha in (0.10,0.25,0.50):
        out.append((f'rank_a{alpha:.2f}', {'alpha':alpha}))
    return out


def fuse(scharr, conf, strategy, params):
    s=np.asarray(scharr,float)
    c=np.asarray(conf,float)
    if strategy=='hard':
        return s*(c>=float(params['roi_q']))
    if strategy.startswith('soft_'):
        eps=float(params['eps']); gamma=float(params['gamma'])
        return s*(eps+(1.0-eps)*np.power(c,gamma))
    if strategy.startswith('residual_'):
        lam=float(params['lambda'])
        return s*np.clip(1.0+lam*(c-0.5),0.05,None)
    if strategy.startswith('rank_'):
        alpha=float(params['alpha'])
        sr=percentile_confidence(s)
        return (1.0-alpha)*sr+alpha*c
    raise ValueError(strategy)


def compute_conf(spec, items, context_model):
    clean={k:v for k,v in spec.items() if k!='name'}
    confs=[]
    for d in items:
        _,bits,_=multiscale_from_precomputed(
            d['features'],d['gt'].shape,
            family='CF1F2',F1='CL',F2='CL',q=.1,
            refine_quantile=.82,heterogeneity_quantile=.82,dilation_radius=3,
            measure_spec=clean,measure_context=context_for(spec,d,context_model))
        confs.append(percentile_confidence(bits))
    return confs


def gt_conf_stats(confs, items):
    vals=[]
    for c,d in zip(confs,items):
        g=np.asarray(d['gt'],bool)
        if np.any(g): vals.append(float(np.mean(np.asarray(c)[g])))
    return float(np.mean(vals)) if vals else float('nan')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--uded-root',default=str(DEFAULT_UDED))
    ap.add_argument('--model-dir',default=str(MODEL_DIR))
    ap.add_argument('--out',default=str(DEFAULT_OUT))
    ap.add_argument('--max-side',type=int,default=256)
    ap.add_argument('--thresholds',type=int,default=21)
    args=ap.parse_args()

    uded_root=Path(args.uded_root); model_dir=Path(args.model_dir); out=Path(args.out)
    out.mkdir(parents=True,exist_ok=True)

    learned=json.loads((model_dir/'learned_measures.json').read_text(encoding='utf-8'))
    context_model=json.loads((model_dir/'context_router.json').read_text(encoding='utf-8'))
    validation=pd.read_csv(model_dir/'validation_best_per_measure.csv')
    roi_by_measure=dict(zip(validation.measure.astype(str),validation.roi_q.astype(float)))

    raw=resize_items(load_uded(uded_root),args.max_side)
    items,names=prepare(raw)
    specs={s['name']:s for s in measure_registry(len(names),learned=learned)
           if s.get('routing')!='oracle'}

    # Alternating-index natural-image split: selection and held-out are disjoint.
    select_items=items[0::2]
    test_items=items[1::2]
    pd.DataFrame([
        {'id':d['id'],'split':'selection' if i%2==0 else 'heldout'}
        for i,d in enumerate(items)
    ]).to_csv(out/'uded_natural_split.csv',index=False)

    # Same Scharr baseline, split without any MFI modulation.
    base_sel=metric([d['scharr'] for d in select_items],[d['gt'] for d in select_items],args.thresholds)
    base_test=metric([d['scharr'] for d in test_items],[d['gt'] for d in test_items],args.thresholds)
    print('BASELINE selection',base_sel,flush=True)
    print('BASELINE heldout',base_test,flush=True)

    val_rows=[]; test_rows=[]
    for mi,name in enumerate(TARGET_MEASURES,start=1):
        if name not in specs:
            print('SKIP missing',name,flush=True); continue
        spec=specs[name]; rq=float(roi_by_measure.get(name,0.50))
        print(f'FUSION MEASURE [{mi}/{len(TARGET_MEASURES)}] {name} ROI={rq:.2f}',flush=True)
        confs=compute_conf(spec,items,context_model)
        conf_sel=confs[0::2]; conf_test=confs[1::2]
        gtconf_sel=gt_conf_stats(conf_sel,select_items)
        gtconf_test=gt_conf_stats(conf_test,test_items)

        for strategy,params in fusion_specs(rq):
            sv=[fuse(d['scharr'],c,strategy,params) for d,c in zip(select_items,conf_sel)]
            st=[fuse(d['scharr'],c,strategy,params) for d,c in zip(test_items,conf_test)]
            mv=metric(sv,[d['gt'] for d in select_items],args.thresholds)
            mt=metric(st,[d['gt'] for d in test_items],args.thresholds)
            val_rows.append({'measure':name,'strategy':strategy,'params':json.dumps(params,sort_keys=True),
                             'synthetic_roi_q':rq,'gt_conf_mean':gtconf_sel,**mv})
            test_rows.append({'measure':name,'strategy':strategy,'params':json.dumps(params,sort_keys=True),
                              'synthetic_roi_q':rq,'gt_conf_mean':gtconf_test,**mt})
            del sv,st
        del confs,conf_sel,conf_test
        gc.collect()

    val=pd.DataFrame(val_rows).sort_values(['ODS','AP','OIS'],ascending=False).reset_index(drop=True)
    test=pd.DataFrame(test_rows)
    val.to_csv(out/'selection_all.csv',index=False)
    test.to_csv(out/'heldout_all.csv',index=False)

    # Select configurations using ONLY the natural selection half, then report held-out.
    selected=val.head(20).copy()
    joined=selected[['measure','strategy','params','synthetic_roi_q','ODS','OIS','AP']].merge(
        test,on=['measure','strategy','params','synthetic_roi_q'],suffixes=('_selection','_heldout'))
    joined=joined.sort_values(['ODS_heldout','AP_heldout','OIS_heldout'],ascending=False).reset_index(drop=True)
    joined.to_csv(out/'selected_top20_heldout.csv',index=False)

    best_per_measure=(val.sort_values(['ODS','AP','OIS'],ascending=False)
                        .groupby('measure',as_index=False).first()
                        .sort_values(['ODS','AP'],ascending=False))
    best_per_measure.to_csv(out/'selection_best_per_measure.csv',index=False)

    summary={
        'dataset':'UDED','max_side':args.max_side,'n_selection':len(select_items),'n_heldout':len(test_items),
        'split':'alternating original UDED order; even 0-based indices selection, odd held-out',
        'selection_rule':'rank measure+fusion combinations on natural selection split only',
        'baseline_selection':base_sel,'baseline_heldout':base_test,
        'best_selection':val.iloc[0].to_dict(),
        'best_selected_heldout_by_heldout_view':joined.iloc[0].to_dict() if len(joined) else None,
        'caveat':'development tolerant dilation metric, not official Berkeley bipartite matcher; held-out columns are reported but not used to form the selected top20 set',
    }
    (out/'summary.json').write_text(json.dumps(summary,indent=2,default=float),encoding='utf-8')

    print('\nSELECTION TOP 20',flush=True)
    print(val.head(20)[['measure','strategy','ODS','OIS','AP','R50','gt_conf_mean']].to_string(index=False),flush=True)
    print('\nSELECTED TOP 20 -> HELDOUT',flush=True)
    print(joined.head(20)[['measure','strategy','ODS_selection','ODS_heldout','OIS_heldout','AP_heldout','R50','gt_conf_mean']].to_string(index=False),flush=True)
    print('UDED_FUSION_V1_DONE',flush=True)


if __name__=='__main__':
    main()
