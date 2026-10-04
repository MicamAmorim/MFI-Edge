from __future__ import annotations
import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from skimage import morphology, filters, graph

EPS=1e-12


def endpoints(edge):
    sk=morphology.thin(np.asarray(edge,bool))
    n=ndi.convolve(sk.astype(np.uint8),np.ones((3,3),np.uint8),mode='constant',cval=0)-sk
    return np.argwhere(sk & (n==1)), sk


def hysteresis_from_threshold(score, high, low_ratio=0.50):
    high=float(high); high_eff=np.nextafter(high,-np.inf); return filters.apply_hysteresis_threshold(np.asarray(score,float),high*low_ratio,high_eff)


def morphological_link(edge, radius=1):
    x=np.asarray(edge,bool)
    y=morphology.closing(x,morphology.disk(int(radius)))
    return morphology.thin(y)


def _angle_diff_pi(a,b):
    d=np.abs((a-b+np.pi/2)%np.pi-np.pi/2)
    return d


def geodesic_link(edge, detector_score, mfi_confidence, theta_normal,
                  max_gap=7.0, corridor=4, alpha=0.40, beta=0.50, gamma=0.10,
                  endpoint_angle_deg=55.0, max_mean_cost=0.58, max_stretch=1.8,
                  max_links=100):
    """Connect short gaps by minimum-cost paths guided by detector+MFI evidence.

    The path cost favours high detector response, high MFI confidence and tangent
    orientation consistent with the endpoint-to-endpoint direction. Candidate endpoint
    pairs must be spatially close and directionally compatible.
    """
    pts,sk=endpoints(edge)
    if len(pts)<2: return sk
    ds=np.asarray(detector_score,float); mc=np.asarray(mfi_confidence,float)
    # normalize detector score robustly
    q=np.quantile(ds[np.isfinite(ds)],0.995) if np.isfinite(ds).any() else 1.0
    dsn=np.clip(ds/max(q,EPS),0,1)
    th=np.asarray(theta_normal,float)
    candidates=[]
    tree=cKDTree(pts.astype(float))
    for i,j in tree.query_pairs(r=float(max_gap), output_type='set'):
        y1,x1=pts[i]; y2,x2=pts[j]
        dist=float(np.hypot(y2-y1,x2-x1))
        if dist<1.5: continue
        phi=np.arctan2(y2-y1,x2-x1)
        # gradient normal + pi/2 = local edge tangent
        t1=th[y1,x1]+np.pi/2; t2=th[y2,x2]+np.pi/2
        d1=float(_angle_diff_pi(t1,phi)); d2=float(_angle_diff_pi(t2,phi))
        if max(d1,d2)>np.deg2rad(endpoint_angle_deg): continue
        candidates.append((dist,i,j,phi))
    candidates.sort(key=lambda z:z[0])
    used=set(); accepted=0
    out=sk.copy(); h,w=out.shape
    for dist,i,j,phi in candidates:
        if accepted>=max_links: break
        if i in used or j in used: continue
        y1,x1=pts[i]; y2,x2=pts[j]
        pad=int(corridor+2)
        ya=max(0,min(y1,y2)-pad); yb=min(h,max(y1,y2)+pad+1)
        xa=max(0,min(x1,x2)-pad); xb=min(w,max(x1,x2)+pad+1)
        loc_d=dsn[ya:yb,xa:xb]; loc_m=mc[ya:yb,xa:xb]; loc_t=th[ya:yb,xa:xb]+np.pi/2
        orient=_angle_diff_pi(loc_t,phi)/(np.pi/2)
        cost=alpha*(1-loc_d)+beta*(1-loc_m)+gamma*orient
        # discourage existing-edge detours only slightly; endpoints need finite cost
        cost=np.clip(cost,1e-3,2.0)
        start=(int(y1-ya),int(x1-xa)); end=(int(y2-ya),int(x2-xa))
        try:
            path,total=graph.route_through_array(cost,start,end,fully_connected=True,geometric=True)
        except Exception:
            continue
        plen=max(len(path),1); mean=float(total/plen)
        if mean>max_mean_cost or plen>max_stretch*dist+3: continue
        yy=np.array([p[0]+ya for p in path]); xx=np.array([p[1]+xa for p in path])
        out[yy,xx]=True
        used.add(i); used.add(j); accepted+=1
    return morphology.thin(out)


def postprocess_binary(score, threshold, method='none', mfi_confidence=None,
                       theta_normal=None, **kwargs):
    method=method.lower()
    if method=='none': return np.asarray(score)>=threshold
    if method=='hysteresis':
        return morphology.thin(hysteresis_from_threshold(score,threshold,kwargs.get('low_ratio',0.5)))
    if method=='closing':
        return morphological_link(np.asarray(score)>=threshold,kwargs.get('radius',1))
    if method in ('geodesic','geo'):
        base=np.asarray(score)>=threshold
        return geodesic_link(base,score,mfi_confidence,theta_normal,**{k:v for k,v in kwargs.items() if k not in ('low_ratio','radius')})
    if method in ('hyst_geo','hysteresis_geodesic'):
        base=hysteresis_from_threshold(score,threshold,kwargs.get('low_ratio',0.5))
        return geodesic_link(base,score,mfi_confidence,theta_normal,**{k:v for k,v in kwargs.items() if k not in ('low_ratio','radius')})
    raise ValueError(method)


def continuity_metrics(pred,gt,tol=2):
    """Simple continuity diagnostics complementary to PR/F metrics."""
    p=morphology.thin(np.asarray(pred,bool)); g=np.asarray(gt,bool)
    lab,n=ndi.label(p,structure=np.ones((3,3),int))
    if tol>0:
        gd=ndi.binary_dilation(g,iterations=tol)
    else: gd=g
    comps=[]
    for k in range(1,n+1):
        c=lab==k
        if np.logical_and(c,gd).any(): comps.append(c)
    # coverage of GT by each predicted component; largest component indicates continuity
    best=0.0
    for c in comps:
        cd=ndi.binary_dilation(c,iterations=tol) if tol>0 else c
        cov=np.logical_and(g,cd).sum()/max(g.sum(),1)
        best=max(best,float(cov))
    eps,_=endpoints(p)
    return {
        'edge_components_on_gt':int(len(comps)),
        'largest_component_gt_coverage':float(best),
        'endpoint_count':int(len(eps)),
    }
