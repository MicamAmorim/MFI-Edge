
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

def save_heatmap(a,path,title,cmap="inferno",vmin=None,vmax=None):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    fig=plt.figure(figsize=(8,5))
    plt.imshow(a,cmap=cmap,vmin=vmin,vmax=vmax)
    plt.title(title); plt.axis("off"); plt.colorbar(shrink=.75)
    plt.tight_layout(); fig.savefig(path,dpi=150,bbox_inches="tight"); plt.close(fig)

def save_panel(img, scale_results, final_bits, best_scale, gt_prob, outpath, title=""):
    outpath=Path(outpath); outpath.parent.mkdir(parents=True,exist_ok=True)
    n=2+len(scale_results)
    fig,axs=plt.subplots(2,n,figsize=(4*n,8))
    axs[0,0].imshow(img,cmap="gray"); axs[0,0].set_title("Original")
    axs[1,0].imshow(gt_prob,cmap="gray"); axs[1,0].set_title("Ground truth (mean)")
    for i,r in enumerate(scale_results):
        axs[0,i+1].imshow(r.bits,cmap="inferno")
        axs[0,i+1].set_title(f"Surprisal {r.window}x{r.window}")
        axs[1,i+1].imshow(r.active,cmap="gray")
        axs[1,i+1].set_title(f"Refine mask {r.window}")
    axs[0,-1].imshow(final_bits,cmap="inferno"); axs[0,-1].set_title("Final max bits")
    axs[1,-1].imshow(best_scale,cmap="viridis"); axs[1,-1].set_title("Best scale")
    for ax in axs.flat: ax.axis("off")
    fig.suptitle(title)
    plt.tight_layout(); fig.savefig(outpath,dpi=140,bbox_inches="tight"); plt.close(fig)
