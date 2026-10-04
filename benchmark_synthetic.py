from __future__ import annotations
import argparse
from pathlib import Path
import itertools
import json
import pandas as pd
from skimage.io import imread
from tqdm import tqdm

from src.operators import FUNCTIONS, COPULA_LIKE, check_cf1f2_pair
from src.pipeline import precompute_multiscale_features, multiscale_from_precomputed
from src.postprocess import gradient_orientation, non_maximum_suppression
from src.evaluation import benchmark_metrics

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "datasets" / "sintetics" / "test"

def load_dataset():
    mf = pd.read_csv(DATA / "manifest.csv")
    items=[]
    for row in mf.itertuples(index=False):
        img=imread(ROOT / row.image)
        gt=imread(ROOT / row.ground_truth) > 0
        items.append((row.case, img, gt))
    return items

def admissible_pairs():
    out=[]
    for a,fa in FUNCTIONS.items():
        for b,fb in FUNCTIONS.items():
            c=check_cf1f2_pair(fa,fb)
            if c.dominates and c.f1_first_increasing and c.boundary_ok:
                out.append((a,b))
    return out

def operator_specs():
    specs=[]
    for f in FUNCTIONS:
        specs.append({"family":"CF", "F":f, "name":f"CF_{f}"})
    for f in sorted(COPULA_LIKE):
        specs.append({"family":"CC", "F":f, "name":f"CC_{f}"})
    for a,b in admissible_pairs():
        specs.append({"family":"CF1F2", "F1":a, "F2":b, "name":f"CF1F2_{a}_{b}"})
    return specs

def run(args):
    items=load_dataset()
    scale_sets={
        "S3":"33-17-9",
        "S5":"33-17-9-5-3",
        "S7":"33-25-17-11-7-5-3",
    }
    if args.quick:
        scale_sets={"S7":"33-25-17-11-7-5-3"}
    if args.scale_labels:
        scale_sets={k:v for k,v in scale_sets.items() if k in set(args.scale_labels)}
    scale_sets={k:tuple(map(int,v.split("-"))) for k,v in scale_sets.items()}
    q_values=args.q_values if args.q_values else ([0.05,0.1,0.2,0.4,0.7,1.0] if not args.quick else [0.1])

    cache={}
    orientations={}
    for label,scales in scale_sets.items():
        for case,img,gt in items:
            cache[(label,case)],_ = precompute_multiscale_features(img,scales)
            orientations[case]=gradient_orientation(img,sigma=1.0)

    specs=operator_specs()
    if args.quick:
        keep={"CF_TP","CF_FGL","CC_TP","CC_TM","CF1F2_TP_TL","CF1F2_FGL_TM"}
        specs=[s for s in specs if s["name"] in keep]

    rows=[]
    total=len(specs)*len(q_values)*len(scale_sets)
    iterator=tqdm(itertools.product(specs,q_values,scale_sets.items()), total=total)
    for spec,q,(scale_label,scales) in iterator:
        iterator.set_postfix_str(f"{spec['name']} q={q} {scale_label}")
        raw_scores=[]; nms_scores=[]; gts=[]
        for case,img,gt in items:
            kwargs={k:v for k,v in spec.items() if k in ("family","F","F1","F2")}
            _,score,_=multiscale_from_precomputed(
                cache[(scale_label,case)], img.shape[:2], q=q,
                refine_quantile=args.refine_quantile,
                heterogeneity_quantile=args.heterogeneity_quantile,
                dilation_radius=args.dilation_radius,
                **kwargs,
            )
            raw_scores.append(score)
            nms_scores.append(non_maximum_suppression(score,orientations[case]))
            gts.append(gt)

        for protocol,scores in (("CEval_raw",raw_scores),("SEval_nms",nms_scores)):
            for tol in args.tolerances:
                m=benchmark_metrics(scores,gts,tol=tol,n_thresholds=args.thresholds)
                rows.append({
                    "operator":spec["name"], "family":spec["family"],
                    "F":spec.get("F",""), "F1":spec.get("F1",""), "F2":spec.get("F2",""),
                    "q":q, "scale_set":scale_label, "scales":"-".join(map(str,scales)),
                    "refine_quantile":args.refine_quantile,
                    "heterogeneity_quantile":args.heterogeneity_quantile,
                    "dilation_radius":args.dilation_radius,
                    "protocol":protocol, "tolerance_px":tol,
                    **{k:v for k,v in m.items() if k!="curve"},
                })

    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    df=pd.DataFrame(rows)
    df.to_csv(out/"all_results.csv",index=False)
    canonical=df[(df.protocol=="SEval_nms") & (df.tolerance_px==2)].copy()
    canonical=canonical.sort_values(["ODS","AP","OIS"],ascending=False)
    canonical.to_csv(out/"ranking_SEval_tol2.csv",index=False)
    canonical.head(100).to_csv(out/"top100_SEval_tol2.csv",index=False)
    raw=df[(df.protocol=="CEval_raw") & (df.tolerance_px==2)].copy()
    raw.sort_values(["ODS","AP","OIS"],ascending=False).to_csv(out/"ranking_CEval_tol2.csv",index=False)
    meta={
        "n_images":len(items), "operators":len(specs), "q_values":q_values,
        "scale_sets":{k:list(v) for k,v in scale_sets.items()},
        "tolerances":args.tolerances, "thresholds":args.thresholds,
        "note":"Synthetic benchmark. tol=2 is a fast BSDS-like proxy; official BSDS comparison must use boundaryBench matching on BSDS500 itself."
    }
    (out/"benchmark_config.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    print("\nTOP 20 — SEval/NMS, tol=2")
    print(canonical.head(20)[["operator","q","scale_set","ODS","OIS","AP","R50","ROC_AUC"]].to_string(index=False))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out",default="benchmark_outputs/synthetic_exhaustive")
    ap.add_argument("--thresholds",type=int,default=79)
    ap.add_argument("--tolerances",type=int,nargs="+",default=[0,1,2])
    ap.add_argument("--refine-quantile",type=float,default=0.82)
    ap.add_argument("--heterogeneity-quantile",type=float,default=0.82)
    ap.add_argument("--dilation-radius",type=int,default=3)
    ap.add_argument("--quick",action="store_true")
    ap.add_argument("--q-values",type=float,nargs="+",default=None)
    ap.add_argument("--scale-labels",nargs="+",choices=["S3","S5","S7"],default=None)
    run(ap.parse_args())

if __name__=="__main__":
    main()
