
from __future__ import annotations
from pathlib import Path
import requests, numpy as np
from scipy.io import loadmat
from skimage.io import imread

BASE="https://raw.githubusercontent.com/BIDS/BSDS500/master/BSDS500/data"
DEFAULT_IDS=["101085","101087","102061","103070","105025","106024","108005","108070","108082","109053"]

def download_bsds_subset(root, split="val", ids=None):
    root=Path(root)
    ids=ids or DEFAULT_IDS
    (root/"images"/split).mkdir(parents=True,exist_ok=True)
    (root/"groundTruth"/split).mkdir(parents=True,exist_ok=True)
    for iid in ids:
        for kind,ext in [("images","jpg"),("groundTruth","mat")]:
            dest=root/kind/split/f"{iid}.{ext}"
            if dest.exists(): continue
            url=f"{BASE}/{kind}/{split}/{iid}.{ext}"
            r=requests.get(url,timeout=60)
            r.raise_for_status()
            dest.write_bytes(r.content)
    return ids

def load_image(root, iid, split="val"):
    return imread(Path(root)/"images"/split/f"{iid}.jpg")

def _extract_boundaries(gt):
    arr=gt["groundTruth"][0]
    outs=[]
    for g in arr:
        try:
            b=np.asarray(g[0][0][1],dtype=float)
            if b.ndim==2: outs.append(b)
        except Exception:
            pass
    if outs: return outs
    def rec(obj):
        found=[]
        if isinstance(obj,np.ndarray):
            if obj.ndim==2 and obj.shape[0]>20 and obj.shape[1]>20 and np.issubdtype(obj.dtype,np.number):
                u=np.unique(obj)
                if u.size<=4 and np.all((u>=0)&(u<=1)): found.append(obj.astype(float))
            if obj.dtype==object:
                for z in obj.flat: found.extend(rec(z))
        elif hasattr(obj,"_fieldnames"):
            for f in obj._fieldnames: found.extend(rec(getattr(obj,f)))
        return found
    return rec(gt["groundTruth"])

def load_gt(root, iid, split="val", consensus=0.5):
    gt=loadmat(Path(root)/"groundTruth"/split/f"{iid}.mat")
    b=_extract_boundaries(gt)
    if not b: raise RuntimeError(f"Could not parse BSDS ground truth for {iid}")
    prob=np.mean(np.stack(b,axis=0),axis=0)
    return prob, prob>=consensus
