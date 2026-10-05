from __future__ import annotations

"""Stage 11b — edge-signature discovery with genuinely scale-sensitive descriptors.

The first Stage-11 run was scientifically useful but exposed a parameter-floor
artifact: several historical `oriented` responses at windows 3, 5 and 7 were
exactly identical.  This rerun preserves the same protocol while using the
backward-compatible `oriented_ms` feature mode.  It also runs the small logistic
diagnostic upper bound by default; that model is diagnostic only, not the
proposed detector.
"""

from pathlib import Path
import argparse
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from benchmark_uded import DEFAULT_UDED, SCALES, load_uded
from benchmark_uded_quick import resize_items
from prepare_uded_runtime import prepare_uded
from src.conditioning import apply_conditioning
from src.pipeline import precompute_multiscale_features
from src.edge_signature import (
    GROUPS, analytical_signature_score, correlation_matrix, diagnostic_metrics,
    extract_signature_samples, feature_group_statistics, fit_logistic_diagnostic,
    logistic_score, pair_summary, select_candidate_signature,
)

ROOT=Path(__file__).resolve().parent
DEFAULT_OUT=ROOT/'results'/'local_dev'/'edge_signature_ms'


def ensure_uded(root:Path):
    if not (root/'test_pair.lst').exists(): prepare_uded(root)
    return root


def prepare_ms(items):
    out=[]; names=None
    for k,d in enumerate(items,start=1):
        print(f'SIGNATURE_MS_PREP {k:02d}/{len(items)} {d["id"]}',flush=True)
        pre_img=apply_conditioning(d['img'],'median',size=3)
        pre,names=precompute_multiscale_features(pre_img,SCALES,feature_mode='oriented_ms')
        out.append({**d,'pre_img':pre_img,'features':pre})
    return out,names


def write_json(path,obj):
    path.write_text(json.dumps(obj,indent=2,default=lambda x:x.tolist() if hasattr(x,'tolist') else float(x)),encoding='utf-8')


def plot_distributions(samples,chosen,out):
    names=[x['feature'] for x in chosen][:8]
    if not names:return
    fig,axes=plt.subplots(len(names),1,figsize=(9,2.6*len(names)),squeeze=False)
    for ax,name in zip(axes[:,0],names):
        j=samples.feature_names.index(name)
        for gi,g in enumerate(GROUPS):
            v=samples.X[samples.groups==gi,j]
            if len(v): ax.hist(v,bins=45,density=True,histtype='step',linewidth=1.3,label=g)
        ax.set_title(name); ax.set_ylabel('density'); ax.legend(fontsize=8)
    axes[-1,0].set_xlabel('feature value')
    fig.tight_layout(); fig.savefig(out/'top_feature_distributions.png',dpi=160,bbox_inches='tight'); plt.close(fig)


def plot_cross_scale(pair_df,out):
    rows=pair_df[(pair_df.negative_group=='texture') & pair_df.feature.str.contains(r'_s(25|13|7|5|3)$',regex=True)].copy()
    if rows.empty:return
    rows['scale']=rows.feature.str.extract(r'_s(25|13|7|5|3)$').astype(int)
    rows['base']=rows.feature.str.replace(r'_s(25|13|7|5|3)$','',regex=True)
    piv=rows.pivot_table(index='base',columns='scale',values='auc_separation',aggfunc='max').reindex(columns=[25,13,7,5,3])
    fig,ax=plt.subplots(figsize=(9,max(4,.48*len(piv))))
    im=ax.imshow(piv.values,aspect='auto',vmin=.5,vmax=max(.75,float(np.nanmax(piv.values))))
    ax.set_xticks(np.arange(len(piv.columns)),[str(x) for x in piv.columns]); ax.set_yticks(np.arange(len(piv.index)),list(piv.index))
    ax.set_xlabel('scale'); ax.set_title('Edge vs texture: per-scale AUC separation — oriented_ms')
    fig.colorbar(im,ax=ax,label='max(AUC, 1-AUC)'); fig.tight_layout(); fig.savefig(out/'cross_scale_auc.png',dpi=160,bbox_inches='tight'); plt.close(fig)


def plot_corr(samples,chosen,out):
    names=[x['feature'] for x in chosen]
    if not names:return
    ids=[samples.feature_names.index(x) for x in names]
    corr=correlation_matrix(samples)[np.ix_(ids,ids)]
    fig,ax=plt.subplots(figsize=(8,7)); im=ax.imshow(corr,vmin=-1,vmax=1)
    ax.set_xticks(np.arange(len(names)),names,rotation=60,ha='right'); ax.set_yticks(np.arange(len(names)),names)
    ax.set_title('Candidate-signature correlation — oriented_ms'); fig.colorbar(im,ax=ax,label='correlation')
    fig.tight_layout(); fig.savefig(out/'candidate_signature_correlation.png',dpi=160,bbox_inches='tight'); plt.close(fig)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--uded-root',default=str(DEFAULT_UDED)); ap.add_argument('--out',default=str(DEFAULT_OUT))
    ap.add_argument('--max-side',type=int,default=256); ap.add_argument('--max-samples-per-group',type=int,default=2500)
    ap.add_argument('--candidate-features',type=int,default=8); ap.add_argument('--max-abs-corr',type=float,default=.90)
    ap.add_argument('--no-linear-diagnostic',action='store_true')
    args=ap.parse_args(); out=Path(args.out); out.mkdir(parents=True,exist_ok=True)

    raw=resize_items(load_uded(ensure_uded(Path(args.uded_root))),args.max_side)
    prepared,base_names=prepare_ms(raw)
    selection_items=prepared[0::2]; heldout_items=prepared[1::2]
    selection=extract_signature_samples(selection_items,base_names,args.max_samples_per_group,seed=20261005)
    heldout=extract_signature_samples(heldout_items,base_names,args.max_samples_per_group,seed=20261006)
    if selection.feature_names!=heldout.feature_names: raise RuntimeError('signature feature spaces differ')

    pd.concat([pd.DataFrame(selection.counts_per_image).assign(split='selection'),pd.DataFrame(heldout.counts_per_image).assign(split='heldout')],ignore_index=True).to_csv(out/'population_counts.csv',index=False)
    pd.DataFrame(feature_group_statistics(selection)).to_csv(out/'group_statistics.csv',index=False)
    tex=pair_summary(selection,'texture'); near=pair_summary(selection,'near_edge'); bg=pair_summary(selection,'background')
    pair_df=pd.DataFrame(tex+near+bg); pair_df.to_csv(out/'descriptor_pairwise_summary.csv',index=False)
    chosen=select_candidate_signature(selection,tex,near,max_features=args.candidate_features,max_abs_corr=args.max_abs_corr)
    write_json(out/'candidate_signature.json',{'dataset':'UDED','selection_only':True,'feature_mode':'oriented_ms + Stage11 structural descriptors','max_side':args.max_side,'features':chosen})

    s0=analytical_signature_score(selection.X,selection.feature_names,chosen); s1=analytical_signature_score(heldout.X,heldout.feature_names,chosen)
    a0=diagnostic_metrics(selection,s0); a1=diagnostic_metrics(heldout,s1)
    logistic=None;l0=l1=None
    if not args.no_linear_diagnostic:
        print('SIGNATURE_MS_LOGISTIC fitting diagnostic upper bound...',flush=True)
        logistic=fit_logistic_diagnostic(selection); l0=diagnostic_metrics(selection,logistic_score(selection,logistic)); l1=diagnostic_metrics(heldout,logistic_score(heldout,logistic))
    diagnostic={'analytical_signature_selection':a0,'analytical_signature_heldout':a1,'logistic_selection':l0,'logistic_heldout':l1,'logistic_success':None if logistic is None else bool(logistic['success']),'logistic_message':None if logistic is None else str(logistic['message'])}
    if logistic is not None:
        order=np.argsort(-np.abs(np.asarray(logistic['weights'],float)))[:20]
        diagnostic['logistic_top_coefficients']=[{'feature':selection.feature_names[int(i)],'coefficient':float(logistic['weights'][int(i)])} for i in order]
    write_json(out/'diagnostic_results.json',diagnostic)
    np.savez_compressed(out/'signature_samples_compact.npz',selection_X=selection.X,selection_groups=selection.groups,heldout_X=heldout.X,heldout_groups=heldout.groups,feature_names=np.asarray(selection.feature_names,dtype=object))

    plot_distributions(selection,chosen,out); plot_cross_scale(pair_df,out); plot_corr(selection,chosen,out)
    tdf=pair_df[pair_df.negative_group=='texture'].sort_values('auc_separation',ascending=False)
    ndf=pair_df[pair_df.negative_group=='near_edge'].sort_values('auc_separation',ascending=False)
    lines=['# Stage 11b — Edge Signature Discovery (scale-sensitive)','',
           'This rerun was triggered because Stage 11 revealed exact descriptor collapse among nominal windows 3/5/7 in the historical `oriented` mode. `oriented_ms` preserves distinct scale parameters while the historical mode remains untouched for reproducibility.','',
           '## Diagnostics','', '| score | selection AUC | selection AP | held-out AUC | held-out AP |','|---|---:|---:|---:|---:|',
           f"| analytical | {a0['auc']:.4f} | {a0['ap']:.4f} | {a1['auc']:.4f} | {a1['ap']:.4f} |"]
    if l0 is not None: lines.append(f"| logistic diagnostic | {l0['auc']:.4f} | {l0['ap']:.4f} | {l1['auc']:.4f} | {l1['ap']:.4f} |")
    lines += ['','## Candidate signature','', '| feature | weight | direction | texture AUC | near-edge AUC |','|---|---:|---:|---:|---:|']
    for r in chosen: lines.append(f"| {r['feature']} | {r['weight']:.4f} | {r['direction']:+.0f} | {r['texture_auc']:.4f} | {r['near_auc']:.4f} |")
    lines += ['','## Top edge-v-texture properties','', '| feature | AUC separation | MI | Cohen d |','|---|---:|---:|---:|']
    for _,r in tdf.head(15).iterrows(): lines.append(f"| {r.feature} | {r.auc_separation:.4f} | {r.mutual_information:.4f} | {r.cohens_d:.3f} |")
    lines += ['','## Top edge-v-near-edge properties','', '| feature | AUC separation | MI | Cohen d |','|---|---:|---:|---:|']
    for _,r in ndf.head(15).iterrows(): lines.append(f"| {r.feature} | {r.auc_separation:.4f} | {r.mutual_information:.4f} | {r.cohens_d:.3f} |")
    (out/'SIGNATURE_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

    print('SIGNATURE_MS_CANDIDATE',[x['feature'] for x in chosen],flush=True)
    print('SIGNATURE_MS_ANALYTICAL_SELECTION',json.dumps(a0),flush=True); print('SIGNATURE_MS_ANALYTICAL_HELDOUT',json.dumps(a1),flush=True)
    if l1 is not None: print('SIGNATURE_MS_LOGISTIC_HELDOUT',json.dumps(l1),flush=True)
    print('EDGE_SIGNATURE_MS_DONE',out,flush=True)


if __name__=='__main__': main()
