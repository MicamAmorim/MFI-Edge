from __future__ import annotations
from pathlib import Path
import itertools, json
import numpy as np, pandas as pd
from skimage.io import imread

from src.pipeline import precompute_multiscale_features, multiscale_from_precomputed
from src.postprocess import gradient_orientation, non_maximum_suppression
from src.classical_detectors import detector_score, canny_persistence
from src.hybrid import percentile_confidence, mfi_roi, hard_gate, soft_gate
from src.evaluation import benchmark_metrics

ROOT=Path(__file__).resolve().parent
DATA=ROOT/"datasets"/"sintetics"/"test"
OUT=ROOT/"benchmark_outputs"/"mfi_classic"
SCALES=(33,25,17,11,7,5,3)

def load_dataset():
    mf=pd.read_csv(DATA/"manifest.csv")
    return [(r.case,imread(ROOT/r.image),imread(ROOT/r.ground_truth)>0)
            for r in mf.itertuples(index=False)]

def metrics(scores,gts):
    m=benchmark_metrics(scores,gts,tol=2,n_thresholds=25)
    return {k:v for k,v in m.items() if k!="curve"}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    items=load_dataset()
    cases=[c for c,_,_ in items]
    images={c:i for c,i,g in items}; gts={c:g for c,i,g in items}
    gtlist=[gts[c] for c in cases]

    # Stage-1 winner is used as the proposal/attention backbone.
    mfi={}; conf={}; ori={}
    for c,img,gt in items:
        pre,_=precompute_multiscale_features(img,SCALES)
        _,score,_=multiscale_from_precomputed(
            pre,img.shape[:2],family="CF1F2",F1="CL",F2="CL",q=.1,
            refine_quantile=.82,heterogeneity_quantile=.82,dilation_radius=3)
        mfi[c]=score
        conf[c]=percentile_confidence(score)
        ori[c]=gradient_orientation(img,1.0)

    detectors=["sobel","scharr","prewitt","roberts","laplacian","log","gaussian_grad"]
    sigma_by={"log":[0.8,1.0,1.4,2.0],"gaussian_grad":[0.8,1.0,1.4,2.0]}
    cache={(d,s,c):detector_score(images[c],d,s)
           for d in detectors for s in sigma_by.get(d,[1.0]) for c in cases}
    canny_base={c:canny_persistence(images[c]) for c in cases}

    rows=[]
    # Classical baselines.
    for d in detectors:
        for s in sigma_by.get(d,[1.0]):
            raw=[cache[(d,s,c)] for c in cases]
            for post in ("raw","nms"):
                ss=raw if post=="raw" else [non_maximum_suppression(x,ori[c]) for x,c in zip(raw,cases)]
                rows.append({"method":d.upper(),"mfi_roi":False,"roi_q":np.nan,"roi_dilation":0,
                             "gate":"none","post":post,"sigma":s,**metrics(ss,gtlist)})
    rows.append({"method":"CANNY","mfi_roi":False,"roi_q":np.nan,"roi_dilation":0,
                 "gate":"none","post":"persistence","sigma":np.nan,
                 **metrics([canny_base[c] for c in cases],gtlist)})

    # MFI-only reference.
    for post in ("raw","nms"):
        ss=[mfi[c] for c in cases] if post=="raw" else [non_maximum_suppression(mfi[c],ori[c]) for c in cases]
        rows.append({"method":"MFI","mfi_roi":True,"roi_q":np.nan,"roi_dilation":0,
                     "gate":"none","post":post,"sigma":np.nan,**metrics(ss,gtlist)})

    roi_qs=[0.50,0.60,0.70,0.80,0.85,0.90,0.95]
    dilations=[0,1,2,3,5]
    for q,dil,gate in itertools.product(roi_qs,dilations,("hard","soft")):
        rois={c:mfi_roi(conf[c],q,dil,already_confidence=True)[0] for c in cases}
        for d in detectors:
            for s in sigma_by.get(d,[1.0]):
                scores=[]
                for c in cases:
                    x=cache[(d,s,c)]
                    x=hard_gate(x,rois[c]) if gate=="hard" else soft_gate(x,rois[c],conf[c])
                    scores.append(non_maximum_suppression(x,ori[c]))
                rows.append({"method":f"MFI-Edge-{d.upper()}","mfi_roi":True,"roi_q":q,
                             "roi_dilation":dil,"gate":gate,"post":"nms","sigma":s,
                             **metrics(scores,gtlist)})
        cs=[hard_gate(canny_base[c],rois[c]) if gate=="hard"
            else soft_gate(canny_base[c],rois[c],conf[c]) for c in cases]
        rows.append({"method":"MFI-Edge-CANNY","mfi_roi":True,"roi_q":q,"roi_dilation":dil,
                     "gate":gate,"post":"persistence","sigma":np.nan,**metrics(cs,gtlist)})

    df=pd.DataFrame(rows)
    ranked=df.sort_values(["ODS","AP","OIS"],ascending=False).reset_index(drop=True)
    ranked.to_csv(OUT/"ranking.csv",index=False)
    ranked.head(100).to_csv(OUT/"top100.csv",index=False)
    ranked.groupby("method",as_index=False).first().sort_values(["ODS","AP"],ascending=False).to_csv(
        OUT/"best_per_method.csv",index=False)
    (OUT/"config.json").write_text(json.dumps({
        "backbone":"CF1F2(CL,CL)","backbone_q":0.1,"scales":list(SCALES),
        "roi_qs":roi_qs,"dilations":dilations,"gates":["hard","soft"],
        "tolerance_px":2,"thresholds":25},indent=2),encoding="utf-8")

if __name__=="__main__":
    main()
