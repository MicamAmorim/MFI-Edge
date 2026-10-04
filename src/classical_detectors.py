from __future__ import annotations
import numpy as np
from scipy import ndimage as ndi
from skimage import color, feature, filters

EPS=1e-12

def gray01(img):
    x=np.asarray(img)
    if x.ndim==3:
        x=color.rgb2gray(x[...,:3])
    x=x.astype(float)
    if x.max()>1:
        x/=255.0
    return np.clip(x,0,1)

def robust01(a, lo=1.0, hi=99.0):
    a=np.asarray(a,float)
    finite=np.isfinite(a)
    if not finite.any():
        return np.zeros_like(a)
    p0,p1=np.percentile(a[finite],[lo,hi])
    if p1<=p0+EPS:
        return np.zeros_like(a)
    return np.clip((a-p0)/(p1-p0),0,1)

def detector_score(img, name:str, sigma:float=1.0):
    g=gray01(img)
    n=name.lower()
    if n=="sobel":
        y=filters.sobel(g)
    elif n=="scharr":
        y=filters.scharr(g)
    elif n=="prewitt":
        y=filters.prewitt(g)
    elif n=="roberts":
        y=filters.roberts(g)
    elif n=="laplacian":
        y=np.abs(filters.laplace(g,ksize=3))
    elif n=="log":
        y=np.abs(ndi.gaussian_laplace(g,sigma=sigma,mode="reflect"))
    elif n in ("gaussian_grad","dograd"):
        gx=ndi.gaussian_filter(g,sigma=sigma,order=(0,1),mode="reflect")
        gy=ndi.gaussian_filter(g,sigma=sigma,order=(1,0),mode="reflect")
        y=np.hypot(gx,gy)
    else:
        raise ValueError(name)
    return robust01(y)

def canny_binary(img, sigma=1.0, low=0.1, high=0.2, roi=None):
    return feature.canny(
        gray01(img),
        sigma=float(sigma),
        low_threshold=float(low),
        high_threshold=float(high),
        use_quantiles=True,
        mask=None if roi is None else np.asarray(roi,bool),
    )

def canny_persistence(img, roi=None, sigmas=(0.8,1.2,1.8),
                      pairs=((0.05,0.15),(0.10,0.25),(0.20,0.40))):
    acc=np.zeros(gray01(img).shape,float)
    n=0
    for sigma in sigmas:
        for low,high in pairs:
            acc += canny_binary(img,sigma,low,high,roi).astype(float)
            n += 1
    return acc/max(n,1)
