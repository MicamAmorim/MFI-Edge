from __future__ import annotations
from pathlib import Path
import json
import numpy as np
import pandas as pd
from scipy import ndimage as ndi
from skimage.draw import disk, ellipse, polygon
from skimage.segmentation import find_boundaries
from skimage.util import random_noise
from skimage.io import imsave

ROOT=Path(__file__).resolve().parent
BASE=ROOT/'datasets'/'sintetics'/'benchmark_v2'


def _region(primitive,n,rng,angle=None):
    yy,xx=np.mgrid[:n,:n]; c=(n-1)/2.0
    if angle is None: angle=float(rng.uniform(0,180))
    th=np.deg2rad(angle)
    d=-np.sin(th)*(xx-c)+np.cos(th)*(yy-c)
    if primitive=='line':
        m=d>0
    elif primitive=='stripe':
        m=np.abs(d)<rng.uniform(7,14)
    elif primitive=='circle':
        m=np.zeros((n,n),bool); rr,cc=disk((c+rng.uniform(-6,6),c+rng.uniform(-6,6)),rng.uniform(16,28),shape=m.shape); m[rr,cc]=1
    elif primitive=='ellipse':
        m=np.zeros((n,n),bool); rr,cc=ellipse(c,c,rng.uniform(12,22),rng.uniform(22,34),rotation=th,shape=m.shape); m[rr,cc]=1
    elif primitive=='rectangle':
        # rotated rectangle through analytic coordinates
        X=np.cos(th)*(xx-c)+np.sin(th)*(yy-c); Y=-np.sin(th)*(xx-c)+np.cos(th)*(yy-c)
        m=(np.abs(X)<rng.uniform(16,30))&(np.abs(Y)<rng.uniform(12,24))
    elif primitive=='triangle':
        r=rng.uniform(22,32); pts=np.array([[c-r,c-r*.6],[c+r,c-r*.5],[c,c+r]])
        # rotate points
        P=pts-np.array([c,c]); R=np.array([[np.cos(th),-np.sin(th)],[np.sin(th),np.cos(th)]]); P=P@R.T+np.array([c,c])
        m=np.zeros((n,n),bool); rr,cc=polygon(P[:,0],P[:,1],shape=m.shape); m[rr,cc]=1
    elif primitive=='sine':
        boundary=c + rng.uniform(8,15)*np.sin(2*np.pi*xx/rng.uniform(35,60)+rng.uniform(0,2*np.pi))
        m=yy>boundary
    elif primitive=='multi':
        m=np.zeros((n,n),bool)
        rr,cc=disk((c-18,c-18),rng.uniform(10,17),shape=m.shape); m[rr,cc]=1
        X=np.cos(th)*(xx-(c+16))+np.sin(th)*(yy-(c+14)); Y=-np.sin(th)*(xx-(c+16))+np.cos(th)*(yy-(c+14))
        m|=(np.abs(X)<rng.uniform(11,18))&(np.abs(Y)<rng.uniform(8,15))
    elif primitive=='tjunction':
        X=np.cos(th)*(xx-c)+np.sin(th)*(yy-c); Y=-np.sin(th)*(xx-c)+np.cos(th)*(yy-c)
        m=(X>0) | ((Y>0)&(np.abs(X)<rng.uniform(5,9)))
    else: raise ValueError(primitive)
    return m,angle,d


def _motion_kernel(length,angle):
    k=max(3,int(length)); k += 1-k%2
    ker=np.zeros((k,k),float); c=(k-1)/2; th=np.deg2rad(angle)
    for t in np.linspace(-c,c,4*k):
        y=int(round(c+t*np.sin(th))); x=int(round(c+t*np.cos(th)))
        if 0<=x<k and 0<=y<k: ker[y,x]=1
    ker/=max(ker.sum(),1)
    return ker


def make_sample(cfg):
    n=int(cfg.get('n',96)); seed=int(cfg['seed']); rng=np.random.default_rng(seed)
    m,angle,d=_region(cfg['primitive'],n,rng,cfg.get('angle'))
    contrast=float(cfg.get('contrast',0.5)); mid=0.5
    lo=mid-contrast/2; hi=mid+contrast/2
    img=np.where(m,hi,lo).astype(float)
    # weak/missing segment while GT remains continuous, for linking tests
    gap=int(cfg.get('gap_length',0))
    if gap>0:
        gt0=find_boundaries(m,mode='inner',connectivity=2)
        pts=np.argwhere(gt0)
        if len(pts):
            center=pts[int(cfg.get('gap_pos',0.52)*(len(pts)-1))]
            rr,cc=np.mgrid[:n,:n]
            patch=(rr-center[0])**2+(cc-center[1])**2 <= (gap/2+2)**2
            img[patch]=mid + (img[patch]-mid)*float(cfg.get('gap_contrast_factor',0.06))
    illum=float(cfg.get('illumination',0.0))
    if illum:
        x=np.linspace(-.5,.5,n)[None,:]
        img += illum*x
    tex=float(cfg.get('texture',0.0))
    if tex:
        yy,xx=np.mgrid[:n,:n]
        img += tex*np.sin(2*np.pi*(xx*np.cos(.7)+yy*np.sin(.7))/rng.uniform(7,15)+rng.uniform(0,6.28))
    blur=float(cfg.get('blur',0.0))
    if blur>0: img=ndi.gaussian_filter(img,blur,mode='reflect')
    motion=int(cfg.get('motion',0))
    if motion>0: img=ndi.convolve(img,_motion_kernel(motion,float(cfg.get('motion_angle',35))),mode='reflect')
    img=np.clip(img,0,1)
    nt=cfg.get('noise','none'); nl=float(cfg.get('noise_level',0.0))
    if nt=='gaussian' and nl>0: img=random_noise(img,mode='gaussian',var=nl,rng=rng)
    elif nt=='s&p' and nl>0: img=random_noise(img,mode='s&p',amount=nl,rng=rng)
    elif nt=='speckle' and nl>0: img=random_noise(img,mode='speckle',var=nl,rng=rng)
    elif nt=='poisson': img=random_noise(img,mode='poisson',rng=rng)
    gt=find_boundaries(m,mode='inner',connectivity=2)
    return np.asarray(img,float),gt


def build_split(split,n_samples,seed0):
    rng=np.random.default_rng(seed0)
    primitives=['line','stripe','circle','ellipse','rectangle','triangle','sine','multi','tjunction']
    families=['clean','gaussian','saltpepper','speckle','blur','motion','illumination','texture','gap','compound']
    rows=[]; idir=BASE/split/'images'; gdir=BASE/split/'ground_truth'; idir.mkdir(parents=True,exist_ok=True); gdir.mkdir(parents=True,exist_ok=True)
    for i in range(n_samples):
        fam=families[i%len(families)]; p=primitives[(i*5 + i//len(families))%len(primitives)]
        cfg={'n':96,'seed':seed0+i,'primitive':p,'angle':float(rng.uniform(0,180)),'contrast':float(rng.choice([.30,.40,.55,.70])),
             'noise':'none','noise_level':0.0,'blur':0.0,'motion':0,'illumination':0.0,'texture':0.0,'gap_length':0,'family':fam}
        sev=float(rng.choice([0.35,0.65,1.0]))
        if fam=='gaussian': cfg.update(noise='gaussian',noise_level=0.004+0.016*sev)
        elif fam=='saltpepper': cfg.update(noise='s&p',noise_level=0.006+0.035*sev)
        elif fam=='speckle': cfg.update(noise='speckle',noise_level=0.008+0.04*sev)
        elif fam=='blur': cfg['blur']=0.5+1.5*sev
        elif fam=='motion': cfg.update(motion=int(round(3+6*sev)),motion_angle=float(rng.uniform(0,180)))
        elif fam=='illumination': cfg['illumination']=0.10+0.25*sev
        elif fam=='texture': cfg['texture']=0.025+0.075*sev
        elif fam=='gap': cfg.update(gap_length=int(round(3+9*sev)),gap_contrast_factor=0.03)
        elif fam=='compound': cfg.update(noise='gaussian',noise_level=0.005+0.01*sev,blur=0.5+0.8*sev,texture=0.02+0.04*sev,illumination=0.08*sev)
        img,gt=make_sample(cfg)
        sid=f'{split}_{i:04d}_{p}_{fam}'
        ip=idir/f'{sid}.png'; gp=gdir/f'{sid}_gt.png'
        imsave(ip,np.round(img*255).astype(np.uint8),check_contrast=False); imsave(gp,(gt*255).astype(np.uint8),check_contrast=False)
        rows.append({**cfg,'id':sid,'split':split,'severity':sev,'image':str(ip.relative_to(ROOT)),'ground_truth':str(gp.relative_to(ROOT))})
    pd.DataFrame(rows).to_csv(BASE/split/'manifest.csv',index=False)
    return rows


def main():
    BASE.mkdir(parents=True,exist_ok=True)
    build_split('validation',40,41000)
    build_split('test',60,51000)
    meta={'description':'MFI-Edge synthetic benchmark v2','validation':40,'test':60,'size':[96,96],
          'primitives':['line','stripe','circle','ellipse','rectangle','triangle','sine','multi','tjunction'],
          'conditions':['clean','gaussian','saltpepper','speckle','blur','motion','illumination','texture','gap','compound'],
          'note':'GT is generated from the clean binary region before degradations. Gap cases deliberately weaken a segment while preserving continuous GT.'}
    (BASE/'README.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    print(BASE)

if __name__=='__main__': main()
