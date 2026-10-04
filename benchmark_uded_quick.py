from __future__ import annotations

from pathlib import Path
import argparse
import gc
import json

import numpy as np
import pandas as pd
from skimage.transform import resize

from benchmark_uded import (
    DEFAULT_UDED, MODEL_DIR, OUT,
    load_uded, prepare, evaluate_measure, evaluate_baseline,
)
from src.fuzzy_measures import measure_registry


def resize_items(items, max_side=256):
    out=[]
    for d in items:
        img=np.asarray(d['img']); gt=np.asarray(d['gt'], bool)
        h,w=gt.shape
        scale=min(1.0, float(max_side)/max(h,w))
        if scale < 1.0:
            nh=max(8,int(round(h*scale))); nw=max(8,int(round(w*scale)))
            shape=(nh,nw,img.shape[2]) if img.ndim==3 else (nh,nw)
            img2=resize(img,shape,order=1,mode='reflect',anti_aliasing=True,preserve_range=True)
            gt2=resize(gt.astype(np.uint8),(nh,nw),order=0,mode='edge',anti_aliasing=False,preserve_range=True)>0.5
        else:
            img2=img; gt2=gt
        out.append({**d,'img':img2,'gt':gt2,'original_shape':[int(h),int(w)],
                    'eval_shape':[int(gt2.shape[0]),int(gt2.shape[1])],'resize_scale':float(scale)})
    return out


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--uded-root',default=str(DEFAULT_UDED))
    ap.add_argument('--model-dir',default=str(MODEL_DIR))
    ap.add_argument('--out',default=str(OUT)+'_256')
    ap.add_argument('--limit',type=int,default=None)
    ap.add_argument('--thresholds',type=int,default=31)
    ap.add_argument('--max-side',type=int,default=256)
    args=ap.parse_args()

    root=Path(args.uded_root); model_dir=Path(args.model_dir); out=Path(args.out)
    out.mkdir(parents=True,exist_ok=True)
    learned=json.loads((model_dir/'learned_measures.json').read_text(encoding='utf-8'))
    context_model=json.loads((model_dir/'context_router.json').read_text(encoding='utf-8'))
    validation=pd.read_csv(model_dir/'validation_best_per_measure.csv')
    roi_by_measure=dict(zip(validation.measure.astype(str),validation.roi_q.astype(float)))

    raw=resize_items(load_uded(root,args.limit),args.max_side)
    pd.DataFrame([{'id':d['id'],'original_shape':str(d['original_shape']),
                   'eval_shape':str(d['eval_shape']),'resize_scale':d['resize_scale']} for d in raw]).to_csv(
                       out/'uded_resize_manifest.csv',index=False)
    items,names=prepare(raw)
    specs=measure_registry(len(names),learned=learned)
    specs=[s for s in specs if s.get('routing')!='oracle']

    rows=[]; per_rows=[]
    for i,spec in enumerate(specs,start=1):
        name=spec['name']; rq=float(roi_by_measure.get(name,0.55))
        print(f'UDED256 MEASURE [{i}/{len(specs)}] {name} ROI={rq:.2f}',flush=True)
        met,scores,curve,per=evaluate_measure(spec,items,context_model,rq,n_thresholds=args.thresholds)
        rows.append({'measure':name,'measure_kind':spec.get('kind',''),
                     'synthetic_selected_roi_q':rq,**met})
        for x in per: per_rows.append({'measure':name,**x})
        del scores, curve, per
        gc.collect()
    ranking=pd.DataFrame(rows).sort_values(['ODS','AP','OIS','F05_ODS'],ascending=False).reset_index(drop=True)
    ranking.to_csv(out/'uded_measure_ranking.csv',index=False)
    pd.DataFrame(per_rows).to_csv(out/'uded_per_image_roi.csv',index=False)

    gts=[d['gt'] for d in items]
    baselines=[
        evaluate_baseline('Scharr+NMS',[d['scharr'] for d in items],gts,args.thresholds),
        evaluate_baseline('Sobel+NMS',[d['sobel'] for d in items],gts,args.thresholds),
        evaluate_baseline('Prewitt+NMS',[d['prewitt'] for d in items],gts,args.thresholds),
        evaluate_baseline('Canny-persistence',[d['canny_persistence'] for d in items],gts,args.thresholds),
    ]
    pd.DataFrame(baselines).sort_values('ODS',ascending=False).to_csv(out/'uded_classical_baselines.csv',index=False)

    summary={'dataset':'UDED','n_images':len(items),'source':'xavysp/UDED',
             'max_side':int(args.max_side),'resize_policy':'downscale only, preserve aspect ratio; GT nearest-neighbor',
             'pipeline':'median3 -> oriented multiscale MFI -> synthetic-selected ROI -> Scharr+NMS',
             'aggregation':'CF1F2(CL,CL)',
             'selection_leakage':'measure fitting and ROI selection use synthetic data only; UDED is evaluation-only',
             'evaluation':'tolerant dilation proxy at 0.75% image diagonal; NOT official Berkeley bipartite matching',
             'top_measure':ranking.iloc[0].to_dict(),'baselines':baselines}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,default=float),encoding='utf-8')

    print('\nUDED256 TOP 20',flush=True)
    print(ranking.head(20)[['measure','measure_kind','synthetic_selected_roi_q','ODS','OIS','AP','F05_ODS','R50','ROC_AUC','roi_gt_coverage']].to_string(index=False),flush=True)
    print('\nUDED256 CLASSICAL BASELINES',flush=True)
    print(pd.DataFrame(baselines).sort_values('ODS',ascending=False).to_string(index=False),flush=True)
    print('MFI_UDED256_BENCHMARK_DONE',flush=True)


if __name__=='__main__':
    main()
