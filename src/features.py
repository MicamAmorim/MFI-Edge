from __future__ import annotations
import numpy as np
from scipy import ndimage as ndi
from skimage import color, filters, morphology

EPS=1e-12

def robust01(a, lo=1.0, hi=99.0):
    a=np.asarray(a,dtype=float)
    finite=np.isfinite(a)
    if not finite.any(): return np.zeros_like(a)
    p0,p1=np.percentile(a[finite],[lo,hi])
    if p1<=p0+EPS: return np.zeros_like(a)
    return np.clip((a-p0)/(p1-p0),0,1)

def gray_float(img):
    img=np.asarray(img)
    if img.ndim==3:
        img=color.rgb2gray(img[...,:3])
    img=img.astype(float)
    if img.max()>1.0: img/=255.0
    return np.clip(img,0,1)

def _sample_along(g, nx, ny, radius):
    yy,xx=np.mgrid[:g.shape[0],:g.shape[1]]
    plus=ndi.map_coordinates(g,[yy+radius*ny,xx+radius*nx],order=1,mode='reflect')
    minus=ndi.map_coordinates(g,[yy-radius*ny,xx-radius*nx],order=1,mode='reflect')
    return plus,minus

def _directional_descriptors(gs,gx,gy,hxx,hyy,hxy,window):
    mag=np.hypot(gx,gy)+EPS
    nx=gx/mag; ny=gy/mag
    tx=-ny; ty=nx
    radii=(max(1.0,window/12.0),max(1.5,window/6.0))
    nc=[]; tc=[]
    for r in radii:
        p,m=_sample_along(gs,nx,ny,r); nc.append(np.abs(p-m))
        p,m=_sample_along(gs,tx,ty,r); tc.append(np.abs(p-m))
    normal_contrast=np.mean(nc,axis=0)
    tangent_contrast=np.mean(tc,axis=0)
    normal_minus_tangent=np.maximum(normal_contrast-tangent_contrast,0.0)
    steered_hessian=np.abs(nx*nx*hxx+2*nx*ny*hxy+ny*ny*hyy)
    return normal_contrast,normal_minus_tangent,steered_hessian

def _gabor_max(g,window,n_orientations):
    energies=[]
    freq=max(0.04,min(0.25,2.0/window))
    for theta in np.linspace(0,np.pi,n_orientations,endpoint=False):
        real,imag=filters.gabor(g,frequency=freq,theta=float(theta))
        energies.append(np.hypot(real,imag))
    return np.max(np.stack(energies,axis=0),axis=0)

def extract_features(img, window:int, mode:str='legacy'):
    """Local edge descriptors in [0,1].

    Modes
    -----
    legacy:
        Original eight descriptors used in Stage 1/2.
    rotinv:
        Same dimensionality, but square local statistics are replaced by
        approximately rotation-invariant Gaussian/disk statistics and the
        Gabor bank is kept at 4 orientations in the current fast benchmark; isotropic statistics remove the main square-window bias.
    oriented:
        Eight descriptors with explicit normal/tangential composition derived
        from the local gradient direction, plus the same 4-orientation Gabor bank used by the legacy baseline.
    combined:
        Twelve descriptors combining rotinv and explicit directional cues.
    """
    mode=mode.lower()
    g=gray_float(img)
    sigma=max(0.8,window/12.0)
    gs=filters.gaussian(g,sigma=sigma,preserve_range=True)

    gx=ndi.sobel(gs,axis=1,mode='reflect')
    gy=ndi.sobel(gs,axis=0,mode='reflect')
    grad=np.hypot(gx,gy)
    lap=np.abs(ndi.gaussian_laplace(g,sigma=max(0.8,sigma)))

    hxx=ndi.gaussian_filter(g,sigma=sigma,order=(0,2),mode='reflect')
    hyy=ndi.gaussian_filter(g,sigma=sigma,order=(2,0),mode='reflect')
    hxy=ndi.gaussian_filter(g,sigma=sigma,order=(1,1),mode='reflect')
    tr=(hxx+hyy)/2
    disc=np.sqrt(np.maximum(((hxx-hyy)/2)**2+hxy*hxy,0))
    hess=np.maximum(np.abs(tr+disc),np.abs(tr-disc))

    if mode=='legacy':
        sxx=ndi.uniform_filter(gx*gx,size=window,mode='reflect')
        syy=ndi.uniform_filter(gy*gy,size=window,mode='reflect')
        sxy=ndi.uniform_filter(gx*gy,size=window,mode='reflect')
    else:
        # Isotropic Gaussian integration window avoids square-window angular bias.
        rho=max(1.0,window/5.0)
        sxx=ndi.gaussian_filter(gx*gx,sigma=rho,mode='reflect')
        syy=ndi.gaussian_filter(gy*gy,sigma=rho,mode='reflect')
        sxy=ndi.gaussian_filter(gx*gy,sigma=rho,mode='reflect')
    num=np.sqrt((sxx-syy)**2+4*sxy*sxy)
    den=sxx+syy+EPS
    coherence=np.clip(num/den,0,1)

    if mode=='legacy':
        mean=ndi.uniform_filter(g,size=window,mode='reflect')
        mean2=ndi.uniform_filter(g*g,size=window,mode='reflect')
        std=np.sqrt(np.maximum(mean2-mean*mean,0))
        local_max=ndi.maximum_filter(g,size=window,mode='reflect')
        local_min=ndi.minimum_filter(g,size=window,mode='reflect')
        local_range=local_max-local_min
        gabor=_gabor_max(g,window,4)
    else:
        rho=max(1.0,window/4.0)
        mean=ndi.gaussian_filter(g,sigma=rho,mode='reflect')
        mean2=ndi.gaussian_filter(g*g,sigma=rho,mode='reflect')
        std=np.sqrt(np.maximum(mean2-mean*mean,0))
        radius=max(1,int(round(window/2)))
        footprint=morphology.disk(radius)
        local_max=ndi.maximum_filter(g,footprint=footprint,mode='reflect')
        local_min=ndi.minimum_filter(g,footprint=footprint,mode='reflect')
        local_range=local_max-local_min
        gabor=_gabor_max(g,window,4)

    dog=np.abs(filters.gaussian(g,sigma=sigma,preserve_range=True)
               -filters.gaussian(g,sigma=max(1.6*sigma,sigma+0.5),preserve_range=True))

    normal_contrast,normal_minus_tangent,steered_hessian=_directional_descriptors(
        gs,gx,gy,hxx,hyy,hxy,window)

    if mode=='legacy':
        names=['grad','laplacian','hessian','coherence','local_std','local_range','dog','gabor4']
        arrs=[grad,lap,hess,coherence,std,local_range,dog,gabor]
    elif mode=='rotinv':
        names=['grad','laplacian','hessian','coherence_iso','local_std_iso','local_range_disk','dog','gabor4']
        arrs=[grad,lap,hess,coherence,std,local_range,dog,gabor]
    elif mode=='oriented':
        names=['grad','laplacian','hessian','coherence_iso','normal_contrast','normal_minus_tangent','steered_hessian','gabor4']
        arrs=[grad,lap,hess,coherence,normal_contrast,normal_minus_tangent,steered_hessian,gabor]
    elif mode=='combined':
        names=['grad','laplacian','hessian','coherence_iso','local_std_iso','local_range_disk','dog','gabor4',
               'normal_contrast','normal_minus_tangent','steered_hessian','grad_x_grad_y_composed']
        # The final channel intentionally records the explicit gx/gy Euclidean composition.
        arrs=[grad,lap,hess,coherence,std,local_range,dog,gabor,
              normal_contrast,normal_minus_tangent,steered_hessian,np.sqrt(gx*gx+gy*gy)]
    else:
        raise ValueError(f'Unknown feature mode: {mode}')

    out=np.stack([robust01(a) for a in arrs],axis=-1)
    return out,names,robust01(std)
