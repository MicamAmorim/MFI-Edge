from __future__ import annotations

from pathlib import Path
import argparse
import gc
import json
import math

import numpy as np
import pandas as pd

from benchmark_uded import (
    DEFAULT_UDED, MODEL_DIR, context_for, load_uded, prepare,
    _variable_tol_curve,
)
from benchmark_uded_quick import resize_items
from benchmark_uded_fusion import TARGET_MEASURES, fusion_specs, fuse, compute_conf, gt_conf_stats
from src.evaluation import tolerant_counts, counts_to_prf
from src.fuzzy_measures import measure_registry


DEFAULT_OUT = Path(__file__).resolve().parent / 'benchmark_outputs' / 'uded_fusion_fixed_v2'


def fixed_eval(scores, gts, threshold, frac_diag=0.0075):
    counts=[]; f1s=[]
    mp=npred=mg=ngt=0
    for s,g in zip(scores,gts):
        tol=max(1,int(round(float(frac_diag)*math.hypot(*g.shape))))
        cnt=tolerant_counts(np.asarray(s)>=float(threshold),g,tol)
        counts.append(tuple(int(x) for x in cnt))
        mp+=cnt[0]; npred+=cnt[1]; mg+=cnt[2]; ngt+=cnt[3]
        f1s.append(float(counts_to_prf(*cnt)[2]))
    p,r,f=counts_to_prf(mp,npred,mg,ngt)
    return {'precision':float(p),'recall':float(r),'F1':float(f),
            'mean_image_F1':float(np.mean(f1s))},counts


def selection_metric(scores,gts,n_thresholds=21):
    m=_variable_tol_curve(scores,gts,beta=1.0,n_thresholds=n_thresholds,frac_diag=0.0075)
    return {k:v for k,v in m.items() if k!='curve'}


def bootstrap_delta(base_counts,cand_counts,n_boot=5000,seed=20261004):
    rng=np.random.default_rng(seed)
    n=len(base_counts)
    deltas=np.empty(int(n_boot),float)
    for b in range(int(n_boot)):
        ids=rng.integers(0,n,size=n)
        bc=np.sum(np.asarray([base_counts[i] for i in ids],dtype=np.int64),axis=0)
        cc=np.sum(np.asarray([cand_counts[i] for i in ids],dtype=np.int64),axis=0)
        fb=counts_to_prf(*bc)[2]; fc=counts_to_prf(*cc)[2]
        deltas[b]=float(fc-fb)
    lo,hi=np.quantile(deltas,[0.025,0.975])
    return {'delta_F1_boot_mean':float(np.mean(deltas)),
            'delta_F1_ci95_low':float(lo),'delta_F1_ci95_high':float(hi),
            'p_delta_gt_0':float(np.mean(deltas>0)),'n_boot':int(n_boot)}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--uded-root',default=str(DEFAULT_UDED))
    ap.add_argument('--model-dir',default=str(MODEL_DIR))
    ap.add_argument('--out',default=str(DEFAULT_OUT))
    ap.add_argument('--max-side',type=int,default=256)
    ap.add_argument('--thresholds',type=int,default=21)
    ap.add_argument('--bootstrap',type=int,default=5000)
    args=ap.parse_args()

    root=Path(args.uded_root); model_dir=Path(args.model_dir); out=Path(args.out)
    out.mkdir(parents=True,exist_ok=True)
    learned=json.loads((model_dir/'learned_measures.json').read_text(encoding='utf-8'))
    context_model=json.loads((model_dir/'context_router.json').read_text(encoding='utf-8'))
    validation=pd.read_csv(model_dir/'validation_best_per_measure.csv')
    roi_by_measure=dict(zip(validation.measure.astype(str),validation.roi_q.astype(float)))

    raw=resize_items(load_uded(root),args.max_side)
    items,names=prepare(raw)
    select_items=items[0::2]; test_items=items[1::2]
    sel_gts=[d['gt'] for d in select_items]; test_gts=[d['gt'] for d in test_items]

    pd.DataFrame([{'id':d['id'],'split':'selection' if i%2==0 else 'heldout'}
                  for i,d in enumerate(items)]).to_csv(out/'uded_natural_split.csv',index=False)

    # Baseline threshold is selected on the natural selection half and then frozen.
    base_sel_scores=[d['scharr'] for d in select_items]
    base_test_scores=[d['scharr'] for d in test_items]
    base_sel=selection_metric(base_sel_scores,sel_gts,args.thresholds)
    base_fixed,base_counts=fixed_eval(base_test_scores,test_gts,base_sel['threshold'])
    print('BASELINE selection',base_sel,flush=True)
    print('BASELINE fixed-heldout',base_fixed,flush=True)

    specs={s['name']:s for s in measure_registry(len(names),learned=learned)
           if s.get('routing')!='oracle'}
    sel_rows=[]; fixed_rows=[]; count_cache={}

    for mi,name in enumerate(TARGET_MEASURES,start=1):
        if name not in specs:
            print('SKIP missing',name,flush=True); continue
        spec=specs[name]; rq=float(roi_by_measure.get(name,0.50))
        print(f'FIXED FUSION [{mi}/{len(TARGET_MEASURES)}] {name} ROI={rq:.2f}',flush=True)
        confs=compute_conf(spec,items,context_model)
        conf_sel=confs[0::2]; conf_test=confs[1::2]
        gtconf_sel=gt_conf_stats(conf_sel,select_items); gtconf_test=gt_conf_stats(conf_test,test_items)

        for strategy,params in fusion_specs(rq):
            key=(name,strategy,json.dumps(params,sort_keys=True))
            sv=[fuse(d['scharr'],c,strategy,params) for d,c in zip(select_items,conf_sel)]
            st=[fuse(d['scharr'],c,strategy,params) for d,c in zip(test_items,conf_test)]
            ms=selection_metric(sv,sel_gts,args.thresholds)
            mf,cnts=fixed_eval(st,test_gts,ms['threshold'])
            sel_rows.append({'measure':name,'strategy':strategy,'params':key[2],
                             'synthetic_roi_q':rq,'gt_conf_mean':gtconf_sel,**ms})
            fixed_rows.append({'measure':name,'strategy':strategy,'params':key[2],
                               'synthetic_roi_q':rq,'selection_threshold':float(ms['threshold']),
                               'gt_conf_mean':gtconf_test,**mf})
            count_cache[key]=cnts
            del sv,st,cnts
        del confs,conf_sel,conf_test
        gc.collect()

    sel=pd.DataFrame(sel_rows).sort_values(['ODS','AP','OIS'],ascending=False).reset_index(drop=True)
    fixed=pd.DataFrame(fixed_rows)
    sel.to_csv(out/'selection_all.csv',index=False); fixed.to_csv(out/'heldout_fixed_all.csv',index=False)

    selected=sel.head(20).copy()
    joined=selected[['measure','strategy','params','synthetic_roi_q','threshold','ODS','OIS','AP','R50']].merge(
        fixed,on=['measure','strategy','params','synthetic_roi_q'],suffixes=('_selection','_heldout'))
    joined['delta_F1_vs_baseline']=joined['F1']-base_fixed['F1']
    joined.to_csv(out/'selected_top20_fixed_heldout.csv',index=False)

    # Paired bootstrap for the five strongest MFI configurations selected without held-out labels.
    boot=[]
    for _,r in sel.head(5).iterrows():
        key=(str(r.measure),str(r.strategy),str(r.params))
        b=bootstrap_delta(base_counts,count_cache[key],args.bootstrap)
        frow=fixed[(fixed.measure==r.measure)&(fixed.strategy==r.strategy)&(fixed.params==r.params)].iloc[0]
        boot.append({'measure':r.measure,'strategy':r.strategy,'params':r.params,
                     'selection_ODS':float(r.ODS),'fixed_heldout_F1':float(frow.F1),
                     'baseline_fixed_heldout_F1':float(base_fixed['F1']),
                     'observed_delta_F1':float(frow.F1-base_fixed['F1']),**b})
    bootdf=pd.DataFrame(boot)
    bootdf.to_csv(out/'paired_bootstrap_top5.csv',index=False)

    summary={
        'dataset':'UDED','n_selection':len(select_items),'n_heldout':len(test_items),'max_side':args.max_side,
        'split':'alternating original UDED order',
        'primary_protocol':'select each score threshold on selection half, freeze it, evaluate held-out once',
        'baseline_selection':base_sel,'baseline_fixed_heldout':base_fixed,
        'best_mfi_selection':sel.iloc[0].to_dict(),
        'best_mfi_selection_fixed_heldout':joined.iloc[0].to_dict(),
        'paired_bootstrap_top5':boot,
        'caveat':'tolerant dilation proxy, not official Berkeley bipartite matching; resized <=256 px',
    }
    (out/'summary.json').write_text(json.dumps(summary,indent=2,default=float),encoding='utf-8')

    print('\nSELECTION TOP 20',flush=True)
    print(sel.head(20)[['measure','strategy','threshold','ODS','OIS','AP','R50']].to_string(index=False),flush=True)
    print('\nFIXED-THRESHOLD HELDOUT FOR SELECTED TOP 20',flush=True)
    print(joined[['measure','strategy','ODS_selection','selection_threshold','precision','recall','F1','delta_F1_vs_baseline']].to_string(index=False),flush=True)
    print('\nPAIRED BOOTSTRAP TOP 5',flush=True)
    print(bootdf.to_string(index=False),flush=True)
    print('UDED_FUSION_FIXED_V2_DONE',flush=True)


if __name__=='__main__':
    main()
