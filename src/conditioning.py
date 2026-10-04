from __future__ import annotations
import time
import numpy as np
from scipy import ndimage as ndi
from skimage import color, filters, restoration, morphology

try:
    import cv2
except Exception:
    cv2 = None

EPS = 1e-9


def gray01(img):
    x=np.asarray(img)
    if x.ndim==3:
        x=color.rgb2gray(x[...,:3])
    x=x.astype(float)
    if x.max()>1.0: x/=255.0
    return np.clip(x,0,1)


def anisotropic_diffusion(img, niter=10, kappa=0.10, gamma=0.15):
    """Perona-Malik diffusion (exponential conduction), grayscale [0,1]."""
    x=gray01(img).copy()
    for _ in range(int(niter)):
        n=np.roll(x,-1,0)-x; s=np.roll(x,1,0)-x
        e=np.roll(x,-1,1)-x; w=np.roll(x,1,1)-x
        cn=np.exp(-(n/kappa)**2); cs=np.exp(-(s/kappa)**2)
        ce=np.exp(-(e/kappa)**2); cw=np.exp(-(w/kappa)**2)
        x += gamma*(cn*n+cs*s+ce*e+cw*w)
        x=np.clip(x,0,1)
    return x


def gravitational_smoothing(img, G=0.05, omega_c=20.0, iterations=30,
                            interaction_radius_frac=0.02, step=0.20):
    """Stable grayscale adaptation of Gravitational Smoothing (GS).

    Pixels are particles in spatial-tonal space. We use the published inverse-square
    gravitational force direction, mass=1, fixed spatial positions, and update only
    the tonal coordinate. omega_c controls tonal-vs-spatial distance. The force is
    averaged over a local spatial interaction neighbourhood and integrated with a
    bounded Euler step for numerical stability.

    This preserves the mechanism of Marco-Detchart et al. while adapting the 5-D RGB
    formulation to 3-D (x,y,intensity) grayscale synthetic experiments.
    """
    x=gray01(img).copy()
    h,w=x.shape
    diag=float(np.hypot(h,w))
    rad=max(1,int(np.ceil(interaction_radius_frac*diag)))
    offsets=[]
    for dy in range(-rad,rad+1):
        for dx in range(-rad,rad+1):
            if dx==0 and dy==0: continue
            if dx*dx+dy*dy<=rad*rad:
                offsets.append((dy,dx,float(np.hypot(dx,dy))/max(rad,1)))
    for _ in range(int(iterations)):
        force=np.zeros_like(x)
        weight=np.zeros_like(x)
        for dy,dx,ds in offsets:
            y=np.roll(np.roll(x,dy,axis=0),dx,axis=1)
            di=y-x
            # spatial-tonal distance; omega_c discourages attraction across strong edges
            r2=ds*ds + (omega_c*di)**2 + 1e-4
            # tonal component of G * r / ||r||^3, adapted back to intensity coordinate
            f=G*di/np.power(r2,1.5)
            valid=np.ones_like(x)
            if dy>0: valid[:dy,:]=0
            elif dy<0: valid[dy:,:]=0
            if dx>0: valid[:,:dx]=0
            elif dx<0: valid[:,dx:]=0
            force += f*valid
            weight += valid
        delta=force/np.maximum(weight,1.0)
        # robustly bound one update so rare near-coincident particles cannot explode
        lim=np.quantile(np.abs(delta),0.995) if np.any(delta) else 0.0
        if lim>0: delta=np.clip(delta,-lim,lim)
        x=np.clip(x + step*delta,0,1)
    return x


def apply_conditioning(img, method='none', **params):
    x=gray01(img)
    m=method.lower()
    if m=='none': return x.copy()
    if m=='gaussian':
        return filters.gaussian(x,sigma=float(params.get('sigma',1.0)),preserve_range=True)
    if m=='box':
        k=int(params.get('size',3)); return ndi.uniform_filter(x,size=k,mode='reflect')
    if m=='median':
        k=int(params.get('size',3)); return ndi.median_filter(x,size=k,mode='reflect')
    if m=='bilateral':
        return restoration.denoise_bilateral(x,
            sigma_color=float(params.get('sigma_color',0.08)),
            sigma_spatial=float(params.get('sigma_spatial',2.0)),
            channel_axis=None)
    if m=='meanshift':
        if cv2 is None:
            raise RuntimeError('OpenCV required for mean shift conditioning')
        u8=np.round(np.clip(x,0,1)*255).astype(np.uint8)
        rgb=cv2.cvtColor(u8,cv2.COLOR_GRAY2BGR)
        out=cv2.pyrMeanShiftFiltering(rgb,
            sp=float(params.get('sp',5)), sr=float(params.get('sr',18)),
            maxLevel=int(params.get('max_level',1)))
        return cv2.cvtColor(out,cv2.COLOR_BGR2GRAY).astype(float)/255.0
    if m=='anisotropic':
        return anisotropic_diffusion(x,niter=params.get('niter',10),
                                     kappa=params.get('kappa',0.10),
                                     gamma=params.get('gamma',0.15))
    if m in ('gravity','gravitational'):
        return gravitational_smoothing(x,
            G=float(params.get('G',0.05)), omega_c=float(params.get('omega_c',20)),
            iterations=int(params.get('iterations',30)),
            interaction_radius_frac=float(params.get('interaction_radius_frac',0.02)),
            step=float(params.get('step',0.20)))
    raise ValueError(method)


def conditioning_support(method, params=None):
    params=params or {}; m=method.lower()
    if m=='none': return 1
    if m=='gaussian': return max(2,int(np.ceil(3*float(params.get('sigma',1.0)))))
    if m in ('box','median'): return max(1,int(params.get('size',3))//2+1)
    if m=='bilateral': return max(3,int(np.ceil(3*float(params.get('sigma_spatial',2.0)))))
    if m=='meanshift': return max(4,int(np.ceil(float(params.get('sp',5)))))
    if m=='anisotropic': return max(4,min(12,int(params.get('niter',10))))
    if m in ('gravity','gravitational'): return max(4,int(params.get('halo',8)))
    return 4


def condition_roi(img, roi, method='none', params=None, tile=32, blend_radius=2):
    """Condition only tiles intersecting an MFI ROI, with halo support.

    Returns conditioned image and fraction of pixels for which filter computation was
    requested (including halo). This is a computational strategy; the output outside
    the processing mask is the original image.
    """
    params=params or {}
    x=gray01(img)
    roi=np.asarray(roi,bool)
    if method.lower()=='none': return x.copy(), float(roi.mean()), 0.0
    support=conditioning_support(method,params)
    h,w=x.shape
    proc=np.zeros_like(roi)
    out=x.copy()
    t0=time.perf_counter()
    # Tile only where ROI exists. Halo gives local filters the needed neighbourhood.
    for y0 in range(0,h,tile):
        y1=min(h,y0+tile)
        for x0 in range(0,w,tile):
            x1=min(w,x0+tile)
            core_roi=roi[y0:y1,x0:x1]
            if not core_roi.any(): continue
            ya=max(0,y0-support); yb=min(h,y1+support)
            xa=max(0,x0-support); xb=min(w,x1+support)
            crop=x[ya:yb,xa:xb]
            fc=apply_conditioning(crop,method,**params)
            cy0=y0-ya; cy1=cy0+(y1-y0); cx0=x0-xa; cx1=cx0+(x1-x0)
            core=fc[cy0:cy1,cx0:cx1]
            mask=core_roi
            out[y0:y1,x0:x1][mask]=core[mask]
            proc[ya:yb,xa:xb]=True
    # Small feathering around ROI avoids a hard seam before derivative localization.
    if blend_radius>0 and roi.any():
        dist=ndi.distance_transform_edt(~roi)
        alpha=np.clip(1.0-dist/max(float(blend_radius),1.0),0,1)
        out=alpha*out+(1-alpha)*x
    dt=time.perf_counter()-t0
    return np.clip(out,0,1), float(proc.mean()), dt
