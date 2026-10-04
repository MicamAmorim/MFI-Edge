from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from synthetic_demo import make_case
from src.pipeline import multiscale_detect
from src.evaluation import best_f1

OUT = Path('outputs_synthetic_3x3')
OUT.mkdir(exist_ok=True)

cases = ['vertical','diagonal','circle','box','two_scale']
scales = [33,25,17,11,7,5,3]
rows=[]
all_data=[]

for i,case in enumerate(cases):
    img,gt = make_case(case, seed=i)
    sr,bits,bscale,_ = multiscale_detect(
        img,
        scales=scales,
        q=0.1,
        family='CF1F2',
        F1='TP',
        F2='TL',
        refine_quantile=0.82,
        heterogeneity_quantile=0.82,
        dilation_radius=3,
    )
    met = best_f1(bits,gt,tol=2)
    pred = bits >= met['threshold']
    rows.append({'case':case, **met})
    all_data.append((case,img,gt,sr,bits,bscale,pred,met))

cols = 2 + len(scales) + 2
fig, axs = plt.subplots(len(cases), cols, figsize=(2.1*cols, 2.2*len(cases)), squeeze=False)
headers = ['Original','GT'] + [f'{s}x{s}' for s in scales] + ['Final bits','Predição']
for j,h in enumerate(headers):
    axs[0,j].set_title(h, fontsize=10)

for r,(case,img,gt,sr,bits,bscale,pred,met) in enumerate(all_data):
    axs[r,0].imshow(img, cmap='gray', vmin=0, vmax=1)
    axs[r,0].set_ylabel(case, fontsize=10)
    axs[r,1].imshow(gt, cmap='gray')
    for k,res in enumerate(sr):
        axs[r,2+k].imshow(res.bits, cmap='inferno')
    axs[r,2+len(scales)].imshow(bits, cmap='inferno')
    axs[r,3+len(scales)].imshow(pred, cmap='gray')
    axs[r,3+len(scales)].text(0.02, 0.98, f"F1={met['F1']:.3f}", transform=axs[r,3+len(scales)].transAxes,
                              va='top', ha='left', fontsize=8,
                              bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.75, edgecolor='none'))
    for c in range(cols):
        axs[r,c].axis('off')

fig.suptitle('CF1F2(TP, TL) — refinamento multiescala até 3x3', fontsize=16, y=0.995)
plt.tight_layout(rect=[0,0,1,0.98])
main_png = OUT/'synthetic_multiscale_to_3x3.png'
fig.savefig(main_png, dpi=180, bbox_inches='tight')
plt.close(fig)

cols2 = 1 + len(scales)
fig, axs = plt.subplots(len(cases), cols2, figsize=(2.1*cols2, 2.2*len(cases)), squeeze=False)
headers2=['Original']+[f'Máscara {s}x{s}' for s in scales]
for j,h in enumerate(headers2): axs[0,j].set_title(h, fontsize=10)
for r,(case,img,gt,sr,bits,bscale,pred,met) in enumerate(all_data):
    axs[r,0].imshow(img,cmap='gray',vmin=0,vmax=1); axs[r,0].set_ylabel(case,fontsize=10)
    for k,res in enumerate(sr): axs[r,1+k].imshow(res.active,cmap='gray')
    for c in range(cols2): axs[r,c].axis('off')
fig.suptitle('Funil coarse-to-fine — regiões preservadas para a próxima escala', fontsize=16, y=0.995)
plt.tight_layout(rect=[0,0,1,0.98])
funnel_png=OUT/'synthetic_refinement_funnel_to_3x3.png'
fig.savefig(funnel_png,dpi=180,bbox_inches='tight')
plt.close(fig)

fig,axs=plt.subplots(1,len(cases),figsize=(3.2*len(cases),3.4),squeeze=False)
for j,(case,img,gt,sr,bits,bscale,pred,met) in enumerate(all_data):
    im=axs[0,j].imshow(bscale, vmin=min(scales), vmax=max(scales))
    axs[0,j].set_title(case); axs[0,j].axis('off')
fig.colorbar(im, ax=axs.ravel().tolist(), shrink=.72, label='Janela que maximizou a surpresa')
fig.suptitle('Escala dominante por pixel', fontsize=15)
best_png=OUT/'synthetic_best_scale_to_3x3.png'
fig.savefig(best_png,dpi=180,bbox_inches='tight')
plt.close(fig)

pd.DataFrame(rows).to_csv(OUT/'metrics.csv', index=False)
print(pd.DataFrame(rows).to_string(index=False))
print(main_png.resolve())
print(funnel_png.resolve())
print(best_png.resolve())
