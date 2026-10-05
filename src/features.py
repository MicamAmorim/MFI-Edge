from __future__ import annotations
import math
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

def _directional_descriptors(gs,gx,gy,hxx,hyy,hxy,window,scale_sensitive=False):
    mag=np.hypot(gx,gy)+EPS
    nx=gx/mag; ny=gy/mag
    tx=-ny; ty=nx
    if scale_sensitive:
        # Fractional radii intentionally remain distinct for 3/5/7 windows.
        radii=(max(0.35,window/12.0),max(0.70,window/6.0))
    else:
        # Historical schedule retained for reproducibility.
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

def _gabor_max(g,window,n_orientations,scale_sensitive=False):
    energies=[]
    if scale_sensitive:
        # Historical min/max clipping made 3/5/7 share the same frequency.
        # This schedule preserves a real scale progression while keeping the
        # smallest wavelength numerically stable.
        freq=max(0.035,min(0.42,1.60/float(window)))
    else:
        freq=max(0.04,min(0.25,2.0/window))
    for theta in np.linspace(0,np.pi,n_orientations,endpoint=False):
        real,imag=filters.gabor(g,frequency=freq,theta=float(theta))
        energies.append(np.hypot(real,imag))
    return np.max(np.stack(energies,axis=0),axis=0)

def feature_scale_schedule(window:int, mode:str='oriented'):
    """Expose the effective scale parameters for audits/reproducibility."""
    mode=mode.lower()
    ms=mode in ('oriented_ms','combined_ms','rotinv_ms')
    if ms:
        sigma=max(0.35,float(window)/10.0)
        structure_rho=max(0.50,float(window)/5.0)
        stats_rho=max(0.50,float(window)/4.0)
        radii=(max(0.35,float(window)/12.0),max(0.70,float(window)/6.0))
        gabor_frequency=max(0.035,min(0.42,1.60/float(window)))
        disk_radius=max(1,int(math.ceil(float(window)/2.0)))
    else:
        sigma=max(0.8,float(window)/12.0)
        structure_rho=max(1.0,float(window)/5.0)
        stats_rho=max(1.0,float(window)/4.0)
        radii=(max(1.0,float(window)/12.0),max(1.5,float(window)/6.0))
        gabor_frequency=max(0.04,min(0.25,2.0/float(window)))
        disk_radius=max(1,int(round(float(window)/2.0)))
    return {
        'window':int(window),'mode':mode,'sigma':float(sigma),
        'structure_rho':float(structure_rho),'stats_rho':float(stats_rho),
        'normal_radius_1':float(radii[0]),'normal_radius_2':float(radii[1]),
        'gabor_frequency':float(gabor_frequency),'disk_radius':int(disk_radius),
    }

def extract_features(img, window:int, mode:str='legacy'):
    """Local edge descriptors in [0,1].

    Modes
    -----
    legacy:
        Original eight descriptors used in Stage 1/2.
    rotinv:
        Historical approximately rotation-invariant descriptors.
    oriented:
        Historical eight orientation-aware descriptors. Retained unchanged for
        reproducibility of Stages 3--10. Note that parameter floors/clips make
        several 3/5/7 responses identical.
    combined:
        Historical twelve-descriptor combined mode.
    oriented_ms:
        Stage-11b scale-sensitive orientation-aware mode. It preserves the same
        eight semantic channels as ``oriented`` but uses distinct smoothing,
        directional sampling and Gabor parameters at 25/13/7/5/3.
    rotinv_ms / combined_ms:
        Scale-sensitive counterparts used for controlled future ablations.
    """
    mode=mode.lower()
    ms=mode in ('oriented_ms','combined_ms','rotinv_ms')
    base_mode={'oriented_ms':'oriented','combined_ms':'combined','rotinv_ms':'rotinv'}.get(mode,mode)
    g=gray_float(img)
    sched=feature_scale_schedule(window,mode)
    sigma=float(sched['sigma'])
    gs=filters.gaussian(g,sigma=sigma,preserve_range=True)

    gx=ndi.sobel(gs,axis=1,mode='reflect')
    gy=ndi.sobel(gs,axis=0,mode='reflect')
    grad=np.hypot(gx,gy)
    lap=np.abs(ndi.gaussian_laplace(g,sigma=max(0.35 if ms else 0.8,sigma)))

    hxx=ndi.gaussian_filter(g,sigma=sigma,order=(0,2),mode='reflect')
    hyy=ndi.gaussian_filter(g,sigma=sigma,order=(2,0),mode='reflect')
    hxy=ndi.gaussian_filter(g,sigma=sigma,order=(1,1),mode='reflect')
    tr=(hxx+hyy)/2
    disc=np.sqrt(np.maximum(((hxx-hyy)/2)**2+hxy*hxy,0))
    hess=np.maximum(np.abs(tr+disc),np.abs(tr-disc))

    if base_mode=='legacy':
        sxx=ndi.uniform_filter(gx*gx,size=window,mode='reflect')
        syy=ndi.uniform_filter(gy*gy,size=window,mode='reflect')
        sxy=ndi.uniform_filter(gx*gy,size=window,mode='reflect')
    else:
        rho=float(sched['structure_rho'])
        sxx=ndi.gaussian_filter(gx*gx,sigma=rho,mode='reflect')
        syy=ndi.gaussian_filter(gy*gy,sigma=rho,mode='reflect')
        sxy=ndi.gaussian_filter(gx*gy,sigma=rho,mode='reflect')
    num=np.sqrt((sxx-syy)**2+4*sxy*sxy)
    den=sxx+syy+EPS
    coherence=np.clip(num/den,0,1)

    if base_mode=='legacy':
        mean=ndi.uniform_filter(g,size=window,mode='reflect')
        mean2=ndi.uniform_filter(g*g,size=window,mode='reflect')
        std=np.sqrt(np.maximum(mean2-mean*mean,0))
        local_max=ndi.maximum_filter(g,size=window,mode='reflect')
        local_min=ndi.minimum_filter(g,size=window,mode='reflect')
        local_range=local_max-local_min
        gabor=_gabor_max(g,window,4,scale_sensitive=False)
    else:
        rho=float(sched['stats_rho'])
        mean=ndi.gaussian_filter(g,sigma=rho,mode='reflect')
        mean2=ndi.gaussian_filter(g*g,sigma=rho,mode='reflect')
        std=np.sqrt(np.maximum(mean2-mean*mean,0))
        radius=int(sched['disk_radius'])
        footprint=morphology.disk(radius)
        local_max=ndi.maximum_filter(g,footprint=footprint,mode='reflect')
        local_min=ndi.minimum_filter(g,footprint=footprint,mode='reflect')
        local_range=local_max-local_min
        gabor=_gabor_max(g,window,4,scale_sensitive=ms)

    dog=np.abs(filters.gaussian(g,sigma=sigma,preserve_range=True)
               -filters.gaussian(g,sigma=max(1.6*sigma,sigma+(0.25 if ms else 0.5)),preserve_range=True))

    normal_contrast,normal_minus_tangent,steered_hessian=_directional_descriptors(
        gs,gx,gy,hxx,hyy,hxy,window,scale_sensitive=ms)

    if base_mode=='legacy':
        names=['grad','laplacian','hessian','coherence','local_std','local_range','dog','gabor4']
        arrs=[grad,lap,hess,coherence,std,local_range,dog,gabor]
    elif base_mode=='rotinv':
        names=['grad','laplacian','hessian','coherence_iso','local_std_iso','local_range_disk','dog','gabor4']
        arrs=[grad,lap,hess,coherence,std,local_range,dog,gabor]
    elif base_mode=='oriented':
        names=['grad','laplacian','hessian','coherence_iso','normal_contrast','normal_minus_tangent','steered_hessian','gabor4']
        arrs=[grad,lap,hess,coherence,normal_contrast,normal_minus_tangent,steered_hessian,gabor]
    elif base_mode=='combined':
        names=['grad','laplacian','hessian','coherence_iso','local_std_iso','local_range_disk','dog','gabor4',
               'normal_contrast','normal_minus_tangent','steered_hessian','grad_x_grad_y_composed']
        arrs=[grad,lap,hess,coherence,std,local_range,dog,gabor,
              normal_contrast,normal_minus_tangent,steered_hessian,np.sqrt(gx*gx+gy*gy)]
    else:
        raise ValueError(f'Unknown feature mode: {mode}')

    out=np.stack([robust01(a) for a in arrs],axis=-1)
    return out,names,robust01(std)