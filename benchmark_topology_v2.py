from __future__ import annotations

"""Second-stage topology competition for top CH-MFI-v2 continuous models.

The main sweep selects continuous-score architectures first.  This script then
compares none/hysteresis/geodesic/hysteresis+geodesic post-processing on only the
selection-ranked finalists, fitting threshold+topology parameters on selection
and freezing them on held-out.
"""

from pathlib import Path
import argparse
import json
import math
import os

import numpy as np
import pandas as pd

from benchmark_uded import DEFAULT_UDED, load_uded, prepare
from benchmark_uded_quick import resize_items
from benchmark_uded_stage7 import bootstrap_delta
from prepare_uded_runtime import prepare_uded
from src.ch_mfi_v2 import run_ch_mfi_v2
from src.context_maps import analyze_context
from src.evaluation import counts_to_prf, tolerant_counts
from src.linking import postprocess_binary, continuity_metrics
from src.research_grid_v2 import build_grid

ROOT = Path(__file__).resolve().parent


def ensure(root):
    if not (root / "test_pair.lst").exists():
        prepare_uded(root)
    return root


def topology_specs():
    out = [("none", {})]
    for low in (0.40,0.50,0.60):
        out.append(("hysteresis", {"low_ratio":low}))
    for gap in (6.0,8.0,10.0):
        for cost in (0.50,0.60,0.70):
            out.append(("geodesic", {"max_gap":gap, "max_mean_cost":cost}))
    for low in (0.45,0.55):
        for gap in (6.0,8.0):
            for cost in (0.55,0.65):
                out.append(("hyst_geo", {"low_ratio":low, "max_gap":gap, "max_mean_cost":cost}))
    return out


def run_outputs(cfg, items):
    out=[]
    for d in items:
        r=run_ch_mfi_v2(d["pre_img"], cfg, precomputed=d["features"], context=d["ch_context"])
        out.append((np.asarray(r.score,float), np.asarray(r.mfi,float), d["orientation"]))
    return out


def counts_for(outputs, items, threshold, method, params):
    counts=[]; cont=[]
    for (score,mfi,theta),d in zip(outputs,items):
        pred=postprocess_binary(score,float(threshold),method=method,mfi_confidence=mfi,theta_normal=theta,**params)
        tol=max(1,int(round(0.0075*math.hypot(*d["gt"].shape))))
        counts.append(tuple(int(x) for x in tolerant_counts(pred,d["gt"],tol)))
        cont.append(continuity_metrics(pred,d["gt"],tol=tol))
    return counts,cont


def metric(counts):
    c=np.asarray(counts,dtype=np.int64).sum(axis=0)
    p,r,f=counts_to_prf(*c)
    return float(p),float(r),float(f)


def fit_topology(outputs,items,method,params,n_thresholds=17):
    vals=np.concatenate([x[0][np.isfinite(x[0])].ravel() for x in outputs])
    thresholds=np.unique(np.quantile(vals,np.linspace(0.02,0.995,int(n_thresholds))))
    best=None
    for t in thresholds:
        counts,cont=counts_for(outputs,items,t,method,params)
        p,r,f=metric(counts)
        row=(f,p,r,float(t),counts,cont)
        if best is None or row[0]>best[0]: best=row
    return best


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--uded-root",default=str(DEFAULT_UDED))
    ap.add_argument("--ranking",default="results/local_dev/ch_mfi_v2/selection_ranking.csv")
    ap.add_argument("--out",default="results/local_dev/topology_v2")
    ap.add_argument("--preset",choices=("smoke","standard","wide"),default="standard")
    ap.add_argument("--max-side",type=int,default=256)
    ap.add_argument("--top",type=int,default=8)
    ap.add_argument("--thresholds",type=int,default=17)
    ap.add_argument("--bootstrap",type=int,default=5000)
    args=ap.parse_args()

    regime=os.environ.get("MFI_REGIME_SHAPLEY")
    scale=os.environ.get("MFI_SCALE_CAPACITY_BANK")
    root=ensure(Path(args.uded_root))
    raw=resize_items(load_uded(root),int(args.max_side))
    items,names=prepare(raw)
    for d in items: d["ch_context"]=analyze_context(d["pre_img"])
    sel=items[0::2]; test=items[1::2]

    configs=build_grid(args.preset,len(names),regime_file=regime,scale_file=scale)
    by_name={c.name:c for c in configs}
    rank=pd.read_csv(args.ranking).sort_values(["cv_F1","selection_ODS"],ascending=False).head(int(args.top))
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)

    # Frozen Scharr baseline threshold from selection.
    bvals=np.concatenate([d["scharr"].ravel() for d in sel])
    bthr=np.unique(np.quantile(bvals,np.linspace(.02,.995,int(args.thresholds))))
    bbest=None
    for t in bthr:
        cc=[]
        for d in sel:
            tol=max(1,int(round(.0075*math.hypot(*d["gt"].shape))))
            cc.append(tolerant_counts(d["scharr"]>=t,d["gt"],tol))
        p,r,f=metric(cc)
        if bbest is None or f>bbest[0]: bbest=(f,p,r,float(t))
    btest=[]
    for d in test:
        tol=max(1,int(round(.0075*math.hypot(*d["gt"].shape))))
        btest.append(tuple(int(x) for x in tolerant_counts(d["scharr"]>=bbest[3],d["gt"],tol)))
    bp,br,bf=metric(btest)

    rows=[]
    for ri,row in rank.reset_index(drop=True).iterrows():
        name=str(row["name"])
        if name not in by_name:
            print("SKIP missing config",name,flush=True); continue
        cfg=by_name[name]
        print(f"TOPO MODEL {ri+1}/{len(rank)} {name}",flush=True)
        so=run_outputs(cfg,sel); to=run_outputs(cfg,test)
        for method,params in topology_specs():
            best=fit_topology(so,sel,method,params,args.thresholds)
            f,p,r,t,_sc,_scont=best
            tc,tcont=counts_for(to,test,t,method,params)
            tp,tr,tf=metric(tc)
            boot=bootstrap_delta(btest,tc,n_boot=int(args.bootstrap),seed=7000+len(rows))
            rows.append({
                "selection_model_rank":ri+1,"name":name,"method":method,
                "params":json.dumps(params,sort_keys=True),"selection_threshold":t,
                "selection_F1":f,"heldout_precision":tp,"heldout_recall":tr,"heldout_F1":tf,
                "delta_F1_vs_scharr":tf-bf,
                "bootstrap_ci_low":boot["delta_F1_ci95_low"],
                "bootstrap_ci_high":boot["delta_F1_ci95_high"],
                "bootstrap_p_positive":boot["p_delta_gt_0"],
                "mean_components":float(np.mean([x["edge_components_on_gt"] for x in tcont])),
                "mean_largest_component_gt_coverage":float(np.mean([x["largest_component_gt_coverage"] for x in tcont])),
                "mean_endpoints":float(np.mean([x["endpoint_count"] for x in tcont])),
            })
        pd.DataFrame(rows).to_csv(out/"topology_competition.csv",index=False)

    result=pd.DataFrame(rows).sort_values(["selection_F1","heldout_F1"],ascending=False)
    result.to_csv(out/"topology_competition.csv",index=False)
    (out/"summary.json").write_text(json.dumps({
        "baseline_scharr":{"threshold":bbest[3],"heldout_F1":bf},
        "selection_winner":result.iloc[0].to_dict() if len(result) else None,
        "note":"topology and threshold selected only on selection split; held-out is frozen evaluation"
    },indent=2,default=float),encoding="utf-8")
    print("TOPOLOGY_V2_DONE",flush=True)

if __name__=="__main__": main()
