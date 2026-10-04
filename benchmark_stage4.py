from __future__ import annotations
from pathlib import Path
import json, time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from skimage.io import imread

from src.pipeline import precompute_multiscale_features, multiscale_from_precomputed
from src.classical_detectors import detector_score
from src.postprocess import gradient_orientation, non_maximum_suppression
from src.hybrid import percentile_confidence, mfi_roi, hard_gate
from src.conditioning import apply_conditioning, condition_roi
from src.linking import postprocess_binary, continuity_metrics
from src.evaluation import benchmark_metrics, tolerant_prf, counts_to_prf, tolerant_counts, average_precision_from_pr

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'datasets'/'sintetics'/'benchmark_v2'
OUT=ROOT/'benchmark_outputs'/'stage4'
SCALES=(25,13,7,5,3)

PRECONDS={
    'none':('none',{}),
    'gaussian06':('gaussian',{'sigma':0.6}),
    'box3':('box',{'size':3}),
    'median3':('median',{'size':3}),
}
COND={
    'none':('none',{}),
    'gaussian1':('gaussian',{'sigma':1.0}),
    'box3':('box',{'size':3}),
    'median3':('median',{'size':3}),
    'bilateral':('bilateral',{'sigma_color':0.08,'sigma_spatial':2.0}),
    'meanshift':('meanshift',{'sp':5,'sr':18,'max_level':1}),
    'anisotropic':('anisotropic',{'niter':10,'kappa':0.10,'gamma':0.15}),
    'gravity_s3':('gravity',{'G':0.05,'omega_c':20,'iterations':30,'step':0.20,'halo':8}),
    'gravity_s4':('gravity',{'G':0.05,'omega_c':70,'iterations':50,'step':0.20,'halo':8}),
}
ROI_QS=(0.60,0.65,0.70,0.75,0.80,0.85)


def load_split(split):
    mf=pd.read_csv(DATA/split/'manifest.csv')
    items=[]
    for r in mf.itertuples(index=False):
        img=imread(ROOT/r.image)
        gt=imread(ROOT/r.ground_truth)>0
        items.append((r.id,img,gt,r))
    return items


def compute_mfi(img):
    pre,_=precompute_multiscale_features(img,SCALES,feature_mode='oriented')
    _,score,_=multiscale_from_precomputed(pre,np.asarray(img).shape[:2],family='CF1F2',F1='CL',F2='CL',q=.1,
                                           refine_quantile=.82,heterogeneity_quantile=.82,dilation_radius=3)
    return score


def eval_scores(scores,gts,nth=41):
    m=benchmark_metrics(scores,gts,tol=2,n_thresholds=nth)
    return {k:v for k,v in m.items() if k!='curve'}


def make_base_cache(items,precond_name):
    method,params=PRECONDS[precond_name]
    cache={}; times=[]
    for sid,img,gt,row in items:
        t0=time.perf_counter(); pim=apply_conditioning(img,method,**params); tcond=time.perf_counter()-t0
        t0=time.perf_counter(); mfi=compute_mfi(pim); tmfi=time.perf_counter()-t0
        conf=percentile_confidence(mfi)
        cache[sid]={'img':img,'pre':pim,'gt':gt,'mfi':mfi,'conf':conf,'row':row,'t_pre':tcond,'t_mfi':tmfi}
        times.append((tcond,tmfi))
    return cache,np.array(times)


def score_from_image(img,roi):
    raw=detector_score(img,'scharr',1.0)
    ori=gradient_orientation(img,1.0)
    nms=non_maximum_suppression(raw,ori)
    return hard_gate(nms,roi),ori


def stage_precondition(items):
    gts=[gt for _,_,gt,_ in items]
    rows=[]; caches={}
    for pname in PRECONDS:
        print('PRECONDITION',pname,flush=True)
        cache,times=make_base_cache(items,pname); caches[pname]=cache
        for q in ROI_QS:
            scores=[]
            for sid,_,_,_ in items:
                d=cache[sid]; roi,_=mfi_roi(d['conf'],q,0,already_confidence=True)
                s,_=score_from_image(d['pre'],roi); scores.append(s)
            met=eval_scores(scores,gts)
            rows.append({'precondition':pname,'roi_q':q,'mean_pre_s':times[:,0].mean(),'mean_mfi_s':times[:,1].mean(),**met})
    df=pd.DataFrame(rows).sort_values(['ODS','AP','OIS'],ascending=False)
    df.to_csv(OUT/'preconditioning_validation.csv',index=False)
    best=df.iloc[0]
    return df,caches[str(best.precondition)],str(best.precondition),float(best.roi_q)


def stage_conditioning(items,cache,base_precond,base_q):
    gts=[gt for _,_,gt,_ in items]
    rows=[]; score_cache={}
    qset=sorted(set([base_q,0.65,0.70,0.75,0.80]))
    for cname,(method,params) in COND.items():
        print('ROI CONDITION',cname,flush=True)
        for q in qset:
            scores=[]; times=[]; fracs=[]; oris=[]
            for sid,_,_,_ in items:
                d=cache[sid]; roi,_=mfi_roi(d['conf'],q,0,already_confidence=True)
                if method=='none':
                    cim=d['pre']; frac=float(roi.mean()); dt=0.0
                else:
                    cim,frac,dt=condition_roi(d['pre'],roi,method,params,tile=16,blend_radius=2)
                s,ori=score_from_image(cim,roi)
                scores.append(s); oris.append(ori); times.append(dt); fracs.append(frac)
            met=eval_scores(scores,gts)
            row={'precondition':base_precond,'conditioning':cname,'roi_q':q,'mean_condition_s':np.mean(times),
                 'mean_processed_fraction':np.mean(fracs),**met}
            rows.append(row); score_cache[(cname,q)]={'scores':scores,'oris':oris}
    df=pd.DataFrame(rows).sort_values(['ODS','AP','OIS'],ascending=False)
    df.to_csv(OUT/'conditioning_validation.csv',index=False)
    best=df.iloc[0]
    return df,score_cache,str(best.conditioning),float(best.roi_q)


def full_vs_roi_runtime(items,cache,cname,q):
    method,params=COND[cname]
    rows=[]
    for sid,_,_,_ in items:
        d=cache[sid]; roi,_=mfi_roi(d['conf'],q,0,already_confidence=True)
        t0=time.perf_counter(); full=apply_conditioning(d['pre'],method,**params); tf=time.perf_counter()-t0
        loc,frac,tr=condition_roi(d['pre'],roi,method,params,tile=16,blend_radius=2)
        rows.append({'id':sid,'conditioning':cname,'full_s':tf,'roi_s':tr,'speedup_condition_stage':tf/max(tr,1e-9),
                     'roi_fraction':float(roi.mean()),'processed_fraction':frac,
                     'mae_inside_roi':float(np.mean(np.abs(full[roi]-loc[roi]))) if roi.any() else 0.0})
    df=pd.DataFrame(rows); df.to_csv(OUT/'roi_runtime_validation.csv',index=False); return df


def binary_curve(scores,gts,confs,oris,method,kwargs,nth=15):
    vals=np.concatenate([s[np.isfinite(s)].ravel() for s in scores])
    thresholds=np.unique(np.quantile(vals,np.linspace(.70,.995,nth)))
    prs=[]; per_by_t=[]
    for t in thresholds:
        mp=npred=mg=ngt=0; per=[]
        for s,g,c,o in zip(scores,gts,confs,oris):
            p=postprocess_binary(s,float(t),method,mfi_confidence=c,theta_normal=o,**kwargs)
            cnt=tolerant_counts(p,g,2); mp+=cnt[0]; npred+=cnt[1]; mg+=cnt[2]; ngt+=cnt[3]
            per.append(tolerant_prf(p,g,2)[2])
        P,R,F=counts_to_prf(mp,npred,mg,ngt)
        prs.append((t,P,R,F)); per_by_t.append(per)
    arr=np.array(prs,float); bi=int(np.argmax(arr[:,3]))
    ois=float(np.mean(np.max(np.array(per_by_t),axis=0)))
    ap=average_precision_from_pr(arr[:,1],arr[:,2])
    ok=arr[:,1]>=.5; r50=float(np.max(arr[ok,2])) if np.any(ok) else 0.0
    return {'ODS_threshold':float(arr[bi,0]),'ODS_precision':float(arr[bi,1]),'ODS_recall':float(arr[bi,2]),'ODS':float(arr[bi,3]),
            'OIS':ois,'AP':ap,'R50':r50,'curve':arr}


def stage_linking(items,cache,scores,oris):
    gts=[gt for _,_,gt,_ in items]; confs=[cache[sid]['conf'] for sid,_,_,_ in items]
    configs=[
        ('none',{}),
        ('hysteresis',{'low_ratio':.50}),('hysteresis',{'low_ratio':.70}),
        ('closing',{'radius':1}),('closing',{'radius':2}),
        ('geodesic',{'max_gap':5,'max_mean_cost':.55}),
        ('geodesic',{'max_gap':8,'max_mean_cost':.60}),
        ('hyst_geo',{'low_ratio':.60,'max_gap':5,'max_mean_cost':.55}),
        ('hyst_geo',{'low_ratio':.60,'max_gap':8,'max_mean_cost':.60}),
    ]
    rows=[]
    for name,kw in configs:
        print('LINK',name,kw,flush=True)
        met=binary_curve(scores,gts,confs,oris,name,kw,nth=15)
        row={'linking':name,'params':json.dumps(kw,sort_keys=True),**{k:v for k,v in met.items() if k!='curve'}}
        cont=[]
        for s,g,c,o in zip(scores,gts,confs,oris):
            pred=postprocess_binary(s,met['ODS_threshold'],name,mfi_confidence=c,theta_normal=o,**kw)
            cont.append(continuity_metrics(pred,g,2))
        row['mean_components_on_gt']=float(np.mean([x['edge_components_on_gt'] for x in cont]))
        row['mean_largest_component_gt_coverage']=float(np.mean([x['largest_component_gt_coverage'] for x in cont]))
        row['mean_endpoint_count']=float(np.mean([x['endpoint_count'] for x in cont]))
        rows.append(row)
    df=pd.DataFrame(rows).sort_values(['ODS','AP','mean_largest_component_gt_coverage'],ascending=[False,False,False])
    df.to_csv(OUT/'linking_validation.csv',index=False)
    return df


def run_test(items,precond_name,cname,q,link_row):
    print('FINAL TEST',precond_name,cname,q,link_row.linking,flush=True)
    pre_m,pre_p=PRECONDS[precond_name]; cond_m,cond_p=COND[cname]
    scores=[]; gts=[]; confs=[]; oris=[]; runt=[]
    for sid,img,gt,row in items:
        t0=time.perf_counter(); pre=apply_conditioning(img,pre_m,**pre_p); tpre=time.perf_counter()-t0
        t0=time.perf_counter(); mfi=compute_mfi(pre); tmfi=time.perf_counter()-t0
        conf=percentile_confidence(mfi); roi,_=mfi_roi(conf,q,0,already_confidence=True)
        if cond_m=='none': cim=pre; frac=float(roi.mean()); tc=0.0
        else: cim,frac,tc=condition_roi(pre,roi,cond_m,cond_p,tile=16,blend_radius=2)
        t0=time.perf_counter(); s,ori=score_from_image(cim,roi); tloc=time.perf_counter()-t0
        scores.append(s); gts.append(gt); confs.append(conf); oris.append(ori)
        runt.append({'id':sid,'family':row.family,'pre_s':tpre,'mfi_s':tmfi,'cond_s':tc,'localize_s':tloc,
                     'total_s':tpre+tmfi+tc+tloc,'roi_fraction':float(roi.mean()),'processed_fraction':frac})
    cont=eval_scores(scores,gts,61)
    kw=json.loads(link_row.params); val_thr=float(link_row.ODS_threshold); lname=str(link_row.linking)
    mp=npred=mg=ngt=0; per_rows=[]
    for (sid,img,gt,row),s,c,o in zip(items,scores,confs,oris):
        pred=postprocess_binary(s,val_thr,lname,mfi_confidence=c,theta_normal=o,**kw)
        cnt=tolerant_counts(pred,gt,2); mp+=cnt[0]; npred+=cnt[1]; mg+=cnt[2]; ngt+=cnt[3]
        p,r,f=tolerant_prf(pred,gt,2); cm=continuity_metrics(pred,gt,2)
        per_rows.append({'id':sid,'family':row.family,'precision':p,'recall':r,'F1':f,**cm})
    P,R,F=counts_to_prf(mp,npred,mg,ngt)
    per=pd.DataFrame(per_rows); per.to_csv(OUT/'test_per_image.csv',index=False)
    rtdf=pd.DataFrame(runt); rtdf.to_csv(OUT/'test_runtime.csv',index=False)
    fam=per.groupby('family')[['precision','recall','F1','largest_component_gt_coverage','edge_components_on_gt','endpoint_count']].mean().sort_values('F1',ascending=False)
    fam.to_csv(OUT/'test_by_condition_family.csv')
    summary={'validation_threshold':val_thr,'fixed_test_precision':P,'fixed_test_recall':R,'fixed_test_F1':F,
             'continuous_test_ODS_no_link':cont['ODS'],'continuous_test_OIS_no_link':cont['OIS'],'continuous_test_AP_no_link':cont['AP'],
             'continuous_test_R50_no_link':cont['R50'],'continuous_test_ROC_AUC_no_link':cont['ROC_AUC'],
             'mean_largest_component_gt_coverage':float(per.largest_component_gt_coverage.mean()),
             'mean_edge_components_on_gt':float(per.edge_components_on_gt.mean()),'mean_endpoint_count':float(per.endpoint_count.mean()),
             'mean_total_runtime_s':float(rtdf.total_s.mean()),'mean_roi_fraction':float(rtdf.roi_fraction.mean()),
             'mean_processed_fraction':float(rtdf.processed_fraction.mean())}
    return summary,per,fam


def baselines_test(items):
    methods={}
    for name in ('scharr','sobel','prewitt'):
        ss=[]; gg=[]
        for _,img,gt,_ in items:
            raw=detector_score(img,name,1.0); ori=gradient_orientation(img,1.0); ss.append(non_maximum_suppression(raw,ori)); gg.append(gt)
        methods[name.upper()]=eval_scores(ss,gg,61)
    return methods


def plots(cond_df,link_df,fam_df):
    best=cond_df.sort_values(['ODS','AP'],ascending=False).groupby('conditioning',as_index=False).first().sort_values('ODS',ascending=False)
    fig,ax=plt.subplots(figsize=(9,5)); ax.bar(best.conditioning,best.ODS); ax.set_ylabel('Validation ODS'); ax.set_title('MFI-Edge-SCHARR: ROI conditioning'); ax.tick_params(axis='x',rotation=35); fig.tight_layout(); fig.savefig(OUT/'conditioning_ods.png',dpi=180); plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,5)); ax.scatter(link_df.mean_largest_component_gt_coverage,link_df.ODS)
    for _,r in link_df.iterrows(): ax.annotate(r.linking,(r.mean_largest_component_gt_coverage,r.ODS),fontsize=8)
    ax.set_xlabel('Largest-component GT coverage'); ax.set_ylabel('ODS'); ax.set_title('Linking: accuracy vs continuity'); ax.grid(alpha=.2); fig.tight_layout(); fig.savefig(OUT/'linking_tradeoff.png',dpi=180); plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,5)); ax.bar(fam_df.index,fam_df.F1); ax.set_ylabel('Fixed-threshold F1'); ax.set_title('Held-out robustness by degradation family'); ax.tick_params(axis='x',rotation=35); fig.tight_layout(); fig.savefig(OUT/'test_family_f1.png',dpi=180); plt.close(fig)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    val=load_split('validation'); test=load_split('test')
    t0=time.perf_counter()
    pre_df,cache,pre_name,pre_q=stage_precondition(val)
    print('BEST PRE',pre_name,pre_q,flush=True)
    cond_df,score_cache,cname,q=stage_conditioning(val,cache,pre_name,pre_q)
    print('BEST COND',cname,q,flush=True)
    runtime_df=full_vs_roi_runtime(val,cache,cname,q) if cname!='none' else pd.DataFrame()
    best_scores=score_cache[(cname,q)]['scores']; best_oris=score_cache[(cname,q)]['oris']
    link_df=stage_linking(val,cache,best_scores,best_oris)
    link_best=link_df.iloc[0]
    summary,per,fam=run_test(test,pre_name,cname,q,link_best)
    bases=baselines_test(test)
    plots(cond_df,link_df,fam)
    report={'selected':{'precondition':pre_name,'conditioning':cname,'roi_q':q,'linking':link_best.linking,
                        'link_params':json.loads(link_best.params),'validation_link_threshold':float(link_best.ODS_threshold)},
            'validation_best_preconditioning':pre_df.head(10).to_dict('records'),
            'validation_best_conditioning':cond_df.head(10).to_dict('records'),
            'validation_linking':link_df.to_dict('records'),
            'held_out_test':summary,'classical_baselines_continuous_test':bases,
            'roi_runtime_validation':None if runtime_df.empty else {'mean_full_s':float(runtime_df.full_s.mean()),'mean_roi_s':float(runtime_df.roi_s.mean()),
                'median_speedup':float(runtime_df.speedup_condition_stage.median()),'mean_processed_fraction':float(runtime_df.processed_fraction.mean()),
                'mean_mae_inside_roi_vs_full':float(runtime_df.mae_inside_roi.mean())},
            'elapsed_s':time.perf_counter()-t0}
    (OUT/'summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__': main()
