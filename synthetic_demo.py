
from pathlib import Path
import numpy as np, pandas as pd
from skimage.draw import line, disk, rectangle_perimeter
from skimage.util import random_noise
from src.pipeline import multiscale_detect
from src.evaluation import best_f1
from src.viz import save_panel
from src.operators import FUNCTIONS

def make_case(kind, n=160, seed=0):
    rng=np.random.default_rng(seed)
    img=np.zeros((n,n),float)+0.18
    gt=np.zeros((n,n),bool)
    if kind=="vertical":
        x=n//2; img[:,x:]=0.82; gt[:,x]=1
    elif kind=="diagonal":
        rr,cc=line(15,10,n-20,n-10); gt[rr,cc]=1
        Y,X=np.mgrid[:n,:n]; img[(Y-X)>0]=0.78
    elif kind=="circle":
        rr,cc=disk((n//2,n//2),n//4,shape=img.shape); img[rr,cc]=0.8
        from scipy import ndimage as ndi
        gt=np.logical_xor(ndi.binary_dilation(img>.5),ndi.binary_erosion(img>.5))
    elif kind=="box":
        r0=n//4; c0=n//4; r1=3*n//4; c1=3*n//4
        img[r0:r1,c0:c1]=0.8
        rr,cc=rectangle_perimeter((r0,c0),(r1-1,c1-1),shape=img.shape); gt[rr,cc]=1
    elif kind=="two_scale":
        img[:,n//3:]=0.65; gt[:,n//3]=1
        img[n//2-10:n//2+10,2*n//3:]=0.92
        gt[n//2-10:n//2+10,2*n//3]=1
    else:
        raise ValueError(kind)
    img=random_noise(img,mode="gaussian",var=0.003,rng=np.random.default_rng(seed))
    return np.clip(img,0,1),gt

def main():
    out=Path("outputs_synthetic"); out.mkdir(exist_ok=True)
    cases=["vertical","diagonal","circle","box","two_scale"]
    specs=[
      ("CF_TP",dict(family="CF",F="TP")),
      ("CF_FGL",dict(family="CF",F="FGL")),
      ("CF1F2_TP_TL",dict(family="CF1F2",F1="TP",F2="TL")),
      ("CF1F2_FGL_TM",dict(family="CF1F2",F1="FGL",F2="TM")),
    ]
    rows=[]
    for name,kw in specs:
        for i,case in enumerate(cases):
            img,gt=make_case(case,seed=i)
            sr,bits,bscale,_=multiscale_detect(img,scales=(33,17,9),q=.1,**kw)
            met=best_f1(bits,gt,tol=2)
            save_panel(img,sr,bits,bscale,gt.astype(float),out/f"{name}_{case}.png",
                       title=f"{name} | {case} | F1={met['F1']:.3f}")
            rows.append({"operator":name,"case":case,**met})
    df=pd.DataFrame(rows)
    df.to_csv(out/"metrics.csv",index=False)
    df.groupby("operator")[["F1","precision","recall"]].mean().sort_values("F1",ascending=False).to_csv(out/"summary.csv")
    print(df.groupby("operator")[["F1","precision","recall"]].mean().sort_values("F1",ascending=False))

if __name__=="__main__":
    main()
