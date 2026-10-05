from __future__ import annotations

"""Fast synthetic smoke test for all second-wave CH-MFI v2 operator families."""

import numpy as np

from src.ch_mfi_v2 import CHMFIv2Config, run_ch_mfi_v2
from src.research_grid_v2 import smoke_grid


def synthetic_image(n=96):
    y,x=np.mgrid[:n,:n]
    img=np.zeros((n,n),float)+0.15
    img[(x>18)&(x<70)&(y>20)&(y<63)]=0.72
    img[((x-68)**2+(y-67)**2)<13**2]=0.95
    img += 0.04*np.sin(x/3.0)*np.cos(y/5.0)
    rng=np.random.default_rng(42)
    img += rng.normal(0,0.015,img.shape)
    return np.clip(img,0,1)


def main():
    img=synthetic_image()
    cfgs=smoke_grid(8)
    failed=[]
    for cfg in cfgs:
        try:
            r=run_ch_mfi_v2(img,cfg)
            assert r.score.shape==img.shape
            assert np.isfinite(r.score).all()
            assert np.isfinite(r.mfi).all()
            assert np.isfinite(r.uncertainty).all()
            print(f"SMOKE_OK {cfg.name} score=[{r.score.min():.4f},{r.score.max():.4f}]",flush=True)
        except Exception as exc:
            failed.append((cfg.name,type(exc).__name__,str(exc)))
            print(f"SMOKE_FAIL {cfg.name}: {type(exc).__name__}: {exc}",flush=True)
    if failed:
        raise SystemExit("CH-MFI-v2 smoke failures: "+repr(failed))
    print("CH_MFI_V2_SMOKE_DONE",flush=True)

if __name__=="__main__": main()
