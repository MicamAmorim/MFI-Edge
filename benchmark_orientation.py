from __future__ import annotations
from pathlib import Path
import itertools, json, time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from skimage.segmentation import find_boundaries
from skimage.util import random_noise

from src.pipeline import precompute_multiscale_features, multiscale_from_precomputed
from src.classical_detectors import detector_score
from src.postprocess import gradient_orientation, non_maximum_suppression
from src.hybrid import percentile_confidence, mfi_roi, hard_gate, soft_gate
from src.evaluation import benchmark_metrics, tolerant_prf

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'benchmark_outputs'/'orientation'
ANGLES=np.arange(0,180,5,dtype=float)
N=96
SCALES=(25,13,7,5,3)
FEATURE_MODES=('legacy','rotinv','oriented','combined')
ROI_QS=(0.50,0.60,0.70,0.80,0.85,0.90)
DILATIONS=(0,1,2)
GATES=('hard','soft')


def make_oriented_step(angle_deg,n=N,seed=123,low=.18,high=.82,noise_var=.003):
    # angle is the edge TANGENT direction in degrees.
    th=np.deg2rad(angle_deg)
    yy,xx=np.mgrid[:n,:n]
    cx=cy=(n-1)/2.0
    # signed perpendicular distance to a line through the image centre
    d=-np.sin(th)*(xx-cx)+np.cos(th)*(yy-cy)
    region=d>0
    img=np.where(region,high,low).astype(float)
    # exact boundary of the same binary region used to generate the step
    gt=find_boundaries(region,mode='inner',connectivity=2)
    img=random_noise(img,mode='gaussian',var=noise_var,rng=np.random.default_rng(seed))
    return np.clip(img,0,1),gt


def eval_scores(scores,gts,nth=61):
    m=benchmark_metrics(scores,gts,tol=2,n_thresholds=nth)
    return {k:v for k,v in m.items() if k!='curve'}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    t0=time.time()
    data={}
    for a in ANGLES:
        img,gt=make_oriented_step(a)
        ori=gradient_orientation(img,1.0)
        sch=detector_score(img,'scharr',1.0)
        sch_nms=non_maximum_suppression(sch,ori)
        data[a]={'img':img,'gt':gt,'ori':ori,'scharr':sch_nms}
    gts=[data[a]['gt'] for a in ANGLES]
    baseline=eval_scores([data[a]['scharr'] for a in ANGLES],gts)
    rows=[{'method':'SCHARR','feature_mode':'none','roi_q':np.nan,'roi_dilation':0,'gate':'none',**baseline}]

    # Compute MFI maps once for each angle/feature representation.
    for mode in FEATURE_MODES:
        print('feature mode',mode,'elapsed',time.time()-t0,flush=True)
        for a in ANGLES:
            pre,_=precompute_multiscale_features(data[a]['img'],SCALES,feature_mode=mode)
            _,score,_=multiscale_from_precomputed(
                pre,data[a]['img'].shape[:2],family='CF1F2',F1='CL',F2='CL',q=.1,
                refine_quantile=.82,heterogeneity_quantile=.82,dilation_radius=3)
            data[a][f'mfi_{mode}']=score
            data[a][f'conf_{mode}']=percentile_confidence(score)

        mfi_only=eval_scores([data[a][f'mfi_{mode}'] for a in ANGLES],gts)
        rows.append({'method':'MFI','feature_mode':mode,'roi_q':np.nan,'roi_dilation':0,'gate':'none',**mfi_only})

        for q,dil,gate in itertools.product(ROI_QS,DILATIONS,GATES):
            scores=[]
            for a in ANGLES:
                roi,_=mfi_roi(data[a][f'conf_{mode}'],q,dil,already_confidence=True)
                # Localization first, gating second: avoids creating artificial ROI-boundary maxima.
                base=data[a]['scharr']
                s=hard_gate(base,roi) if gate=='hard' else soft_gate(base,roi,data[a][f'conf_{mode}'])
                scores.append(s)
            met=eval_scores(scores,gts)
            rows.append({'method':'MFI-Edge-SCHARR','feature_mode':mode,'roi_q':q,
                         'roi_dilation':dil,'gate':gate,**met})

    df=pd.DataFrame(rows).sort_values(['ODS','AP','OIS'],ascending=False).reset_index(drop=True)
    df.to_csv(OUT/'ranking.csv',index=False)
    best=df[df.method=='MFI-Edge-SCHARR'].groupby('feature_mode',as_index=False).first()
    best=best.sort_values(['ODS','AP','OIS'],ascending=False)
    best.to_csv(OUT/'best_by_feature_mode.csv',index=False)

    # Angle-by-angle diagnostics using the global ODS threshold of each best configuration.
    angle_rows=[]
    for rr in best.itertuples(index=False):
        mode=rr.feature_mode; q=float(rr.roi_q); dil=int(rr.roi_dilation); gate=rr.gate; thr=float(rr.ODS_threshold)
        for a in ANGLES:
            roi,_=mfi_roi(data[a][f'conf_{mode}'],q,dil,already_confidence=True)
            base=data[a]['scharr']
            s=hard_gate(base,roi) if gate=='hard' else soft_gate(base,roi,data[a][f'conf_{mode}'])
            pred=s>=thr
            p,r,f=tolerant_prf(pred,data[a]['gt'],tol=2)
            coverage=float(np.logical_and(roi,data[a]['gt']).sum()/max(data[a]['gt'].sum(),1))
            angle_rows.append({'feature_mode':mode,'angle_deg':a,'roi_q':q,'roi_dilation':dil,'gate':gate,
                               'precision':p,'recall':r,'F1':f,'roi_gt_coverage':coverage})
    adf=pd.DataFrame(angle_rows)
    adf.to_csv(OUT/'per_angle.csv',index=False)
    stability=adf.groupby('feature_mode').agg(
        mean_F1=('F1','mean'),min_F1=('F1','min'),max_F1=('F1','max'),std_F1=('F1','std'),
        mean_ROI_GT_coverage=('roi_gt_coverage','mean'),min_ROI_GT_coverage=('roi_gt_coverage','min'))
    stability['range_F1']=stability.max_F1-stability.min_F1
    stability=stability.sort_values(['mean_F1','min_F1'],ascending=False)
    stability.to_csv(OUT/'orientation_stability.csv')

    # Scharr baseline angle curve at its global ODS threshold.
    base_thr=float(baseline['ODS_threshold'])
    b=[]
    for a in ANGLES:
        p,r,f=tolerant_prf(data[a]['scharr']>=base_thr,data[a]['gt'],tol=2)
        b.append({'angle_deg':a,'precision':p,'recall':r,'F1':f})
    pd.DataFrame(b).to_csv(OUT/'scharr_per_angle.csv',index=False)

    # Plot F1 by orientation.
    fig,ax=plt.subplots(figsize=(11,5.5))
    bdf=pd.DataFrame(b)
    ax.plot(bdf.angle_deg,bdf.F1,marker='o',ms=3,label='Scharr')
    for mode in stability.index:
        x=adf[adf.feature_mode==mode]
        ax.plot(x.angle_deg,x.F1,marker='o',ms=3,label=f'MFI-Scharr {mode}')
    ax.set_xlabel('Edge tangent angle (degrees)'); ax.set_ylabel('F1 @ global ODS threshold')
    ax.set_ylim(0,1.03); ax.set_xticks(np.arange(0,180,15)); ax.grid(alpha=.2); ax.legend(ncol=2)
    fig.tight_layout(); fig.savefig(OUT/'f1_by_angle.png',dpi=180,bbox_inches='tight'); plt.close(fig)

    # Plot MFI ROI coverage by orientation.
    fig,ax=plt.subplots(figsize=(11,5.5))
    for mode in stability.index:
        x=adf[adf.feature_mode==mode]
        ax.plot(x.angle_deg,x.roi_gt_coverage,marker='o',ms=3,label=mode)
    ax.set_xlabel('Edge tangent angle (degrees)'); ax.set_ylabel('Fraction of GT edge inside MFI ROI')
    ax.set_ylim(0,1.03); ax.set_xticks(np.arange(0,180,15)); ax.grid(alpha=.2); ax.legend(ncol=2)
    fig.tight_layout(); fig.savefig(OUT/'roi_coverage_by_angle.png',dpi=180,bbox_inches='tight'); plt.close(fig)

    meta={'angles_deg':ANGLES.tolist(),'n':N,'scales':list(SCALES),'seed':123,'noise_var':.003,
          'feature_modes':list(FEATURE_MODES),'roi_qs':list(ROI_QS),'dilations':list(DILATIONS),'gates':list(GATES),
          'backbone':'CF1F2(CL,CL), q=0.1','note':'Same noise realization at all angles to isolate orientation sensitivity.'}
    (OUT/'config.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    print('\nBASELINE SCHARR',baseline)
    print('\nBEST BY FEATURE MODE')
    print(best[['feature_mode','roi_q','roi_dilation','gate','ODS','OIS','AP','R50','ROC_AUC']].to_string(index=False))
    print('\nSTABILITY')
    print(stability.to_string())
    print('\nelapsed',time.time()-t0)

if __name__=='__main__': main()
