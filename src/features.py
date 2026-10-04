
from __future__ import annotations
import numpy as np
from scipy import ndimage as ndi
from skimage import color, filters, feature

def robust01(a, lo=1.0, hi=99.0):
    a=np.asarray(a,dtype=float)
    finite=np.isfinite(a)
    if not finite.any(): return np.zeros_like(a)
    p0,p1=np.percentile(a[finite],[lo,hi])
    if p1<=p0+1e-12: return np.zeros_like(a)
    return np.clip((a-p0)/(p1-p0),0,1)

def gray_float(img):
    img=np.asarray(img)
    if img.ndim==3:
        img=color.rgb2gray(img[...,:3])
    img=img.astype(float)
    if img.max()>1.0: img/=255.0
    return np.clip(img,0,1)

def extract_features(img, window:int):
    """Eight complementary local edge descriptors in [0,1]."""
    g=gray_float(img)
    sigma=max(0.8, window/12.0)
    gs=filters.gaussian(g,sigma=sigma,preserve_range=True)

    gx=ndi.sobel(gs,axis=1,mode="reflect")
    gy=ndi.sobel(gs,axis=0,mode="reflect")
    grad=np.hypot(gx,gy)

    lap=np.abs(ndi.gaussian_laplace(g,sigma=max(0.8,sigma)))

    hxx=ndi.gaussian_filter(g,sigma=sigma,order=(0,2),mode="reflect")
    hyy=ndi.gaussian_filter(g,sigma=sigma,order=(2,0),mode="reflect")
    hxy=ndi.gaussian_filter(g,sigma=sigma,order=(1,1),mode="reflect")
    tr=(hxx+hyy)/2
    disc=np.sqrt(np.maximum(((hxx-hyy)/2)**2+hxy*hxy,0))
    l1=np.abs(tr+disc); l2=np.abs(tr-disc)
    hess=np.maximum(l1,l2)

    sxx=ndi.uniform_filter(gx*gx,size=window,mode="reflect")
    syy=ndi.uniform_filter(gy*gy,size=window,mode="reflect")
    sxy=ndi.uniform_filter(gx*gy,size=window,mode="reflect")
    num=np.sqrt((sxx-syy)**2+4*sxy*sxy)
    den=sxx+syy+1e-12
    coherence=np.clip(num/den,0,1)

    mean=ndi.uniform_filter(g,size=window,mode="reflect")
    mean2=ndi.uniform_filter(g*g,size=window,mode="reflect")
    std=np.sqrt(np.maximum(mean2-mean*mean,0))

    local_max=ndi.maximum_filter(g,size=window,mode="reflect")
    local_min=ndi.minimum_filter(g,size=window,mode="reflect")
    local_range=local_max-local_min

    dog=np.abs(filters.gaussian(g,sigma=sigma,preserve_range=True)
               - filters.gaussian(g,sigma=max(1.6*sigma,sigma+0.5),preserve_range=True))

    energies=[]
    freq=max(0.04,min(0.25,2.0/window))
    for theta in (0,np.pi/4,np.pi/2,3*np.pi/4):
        real,imag=filters.gabor(g,frequency=freq,theta=theta)
        energies.append(np.hypot(real,imag))
    gabor=np.max(np.stack(energies,axis=0),axis=0)

    names=["grad","laplacian","hessian","coherence","local_std","local_range","dog","gabor"]
    arrs=[grad,lap,hess,coherence,std,local_range,dog,gabor]
    out=np.stack([robust01(a) for a in arrs],axis=-1)
    return out, names, robust01(std)
