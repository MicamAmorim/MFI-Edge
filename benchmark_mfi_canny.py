from __future__ import annotations
from pathlib import Path
import itertools, numpy as np, pandas as pd
from scipy import ndimage as ndi
from skimage.io import imread
from src.pipeline import precompute_multiscale_features, multiscale_from_precomputed
from src.classical_detectors import canny_binary
from src.hybrid import percentile_confidence, mfi_roi
from src.evaluation import tolerant_counts, counts_to_prf, average_precision_from_pr

ROOT=Path(__file__).resolve().parent
DATA=ROOT/"datasets"/"sintetics"/"test"
OUT=ROOT/"benchmark_outputs"/"mfi_canny_tuned"
SCALES=(33,25,17,11,7,5,3)

def aggregate(preds,gts,tol=2):
    mp=npred=mg=ngt=0; per=[]
    for p,g in zip(preds,gts):
        c=tolerant_counts(p,g,tol)
        mp+=c[0]; npred+=c[1]; mg+=c[2]; ngt+=c[3]
        per.append(counts_to_prf(*c))
    P,R,F=counts_to_prf(mp,npred,mg,ngt)
    return P,R,F,per

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    mf=pd.read_csv(DATA/"manifest.csv")
    items=[(r.case,imread(ROOT/r.image),imread(ROOT/r.ground_truth)>0)
           for r in mf.itertuples(index=False)]
    cases=[c for c,_,_ in items]; imgs={c:i for c,i,g in items}; gts={c:g for c,i,g in items}
    conf={}
    for c,img,gt in items:
        pre,_=precompute_multiscale_features(img,SCALES)
        _,s,_=multiscale_from_precomputed(pre,img.shape[:2],family="CF1F2",F1="CL",F2="CL",q=.1,
                                           refine_quantile=.82,heterogeneity_quantile=.82,dilation_radius=3)
        conf[c]=percentile_confidence(s)

    qs=[0.60,0.70,0.80]; dilations=[0,1,2]
    sigmas=[0.8,1.2,1.6]
    pairs=[(0.05,0.15),(0.05,0.25),(0.10,0.20),(0.10,0.30),(0.15,0.30),(0.20,0.40)]
    rows=[]
    for use_mfi in (False,True):
        qvals=qs if use_mfi else [np.nan]
        dvals=dilations if use_mfi else [0]
        for q,dil,sigma in itertools.product(qvals,dvals,sigmas):
            points=[]; image_fs={c:[] for c in cases}
            rois={c:mfi_roi(conf[c],q,dil,already_confidence=True)[0] for c in cases} if use_mfi else {}
            for low,high in pairs:
                preds=[canny_binary(imgs[c],sigma,low,high,rois[c] if use_mfi else None) for c in cases]
                P,R,F,per=aggregate(preds,[gts[c] for c in cases],2)
                points.append((low,high,P,R,F))
                for c,m in zip(cases,per):
                    image_fs[c].append(m[2])
            a=np.asarray(points,float); bi=int(np.argmax(a[:,4]))
            low,high,P,R,ods=a[bi]
            ois=float(np.mean([max(image_fs[c]) for c in cases]))
            ap=average_precision_from_pr(a[:,2],a[:,3])
            ok=a[:,2]>=0.5; r50=float(np.max(a[ok,3])) if np.any(ok) else 0.0
            rows.append({"method":"MFI-Edge-CANNY" if use_mfi else "CANNY",
                         "roi_q":q,"roi_dilation":dil,"sigma":sigma,
                         "best_low":low,"best_high":high,
                         "ODS":ods,"ODS_precision":P,"ODS_recall":R,
                         "OIS":ois,"AP":ap,"R50":r50})
    pd.DataFrame(rows).sort_values(["ODS","AP","OIS"],ascending=False).to_csv(OUT/"ranking.csv",index=False)

if __name__=="__main__":
    main()
