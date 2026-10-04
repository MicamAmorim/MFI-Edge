
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd
from skimage.io import imsave
from src.bsds import download_bsds_subset, load_image, load_gt, DEFAULT_IDS
from src.pipeline import precompute_multiscale_features, multiscale_from_precomputed
from src.evaluation import best_f1
from src.viz import save_heatmap, save_panel
from src.operators import FUNCTIONS, check_cf1f2_pair, KNOWN_CF1F2_PAIRS

def operator_specs(mode="default"):
    if mode=="default":
        return [
            {"family":"CF","F":"TP","name":"CF_TP"},
            {"family":"CF1F2","F1":"TP","F2":"TL","name":"CF1F2_TP_TL"},
        ]
    if mode=="cf21":
        return [{"family":"CF","F":k,"name":f"CF_{k}"} for k in FUNCTIONS]
    if mode=="diagonal21":
        return [{"family":"CF1F2","F1":k,"F2":k,"name":f"CF1F2_{k}_{k}"} for k in FUNCTIONS]
    if mode=="knownpairs":
        return [{"family":"CF1F2","F1":a,"F2":b,"name":f"CF1F2_{a}_{b}"} for a,b in KNOWN_CF1F2_PAIRS]
    if mode=="allpairs":
        out=[]
        for a in FUNCTIONS:
            for b in FUNCTIONS:
                chk=check_cf1f2_pair(FUNCTIONS[a],FUNCTIONS[b])
                if chk.dominates and chk.f1_first_increasing and chk.boundary_ok:
                    out.append({"family":"CF1F2","F1":a,"F2":b,"name":f"CF1F2_{a}_{b}"})
        return out
    raise ValueError(mode)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",default="data/bsds500")
    ap.add_argument("--out",default="outputs")
    ap.add_argument("--split",default="val")
    ap.add_argument("--download",action="store_true")
    ap.add_argument("--n-images",type=int,default=10)
    ap.add_argument("--operator-mode",choices=["default","cf21","diagonal21","knownpairs","allpairs"],default="default")
    ap.add_argument("--scales",nargs="+",type=int,default=[33,17,9])
    ap.add_argument("--q",type=float,default=0.1)
    ap.add_argument("--tol",type=int,default=2)
    args=ap.parse_args()
    data=Path(args.data); out=Path(args.out)
    ids=DEFAULT_IDS[:args.n_images]
    if args.download: download_bsds_subset(data,args.split,ids)
    rows=[]
    specs=operator_specs(args.operator_mode)
    for iid in ids:
        img=load_image(data,iid,args.split)
        gt_prob,gt=load_gt(data,iid,args.split)
        precomputed,names=precompute_multiscale_features(img,args.scales)
        for spec in specs:
            kwargs={k:v for k,v in spec.items() if k in ("family","F","F1","F2")}
            sr,final_bits,best_scale=multiscale_from_precomputed(
                precomputed,img.shape[:2],q=args.q,**kwargs)
            met=best_f1(final_bits,gt,tol=args.tol)
            run_dir=out/spec["name"]/iid
            run_dir.mkdir(parents=True,exist_ok=True)
            for r in sr:
                save_heatmap(r.bits,run_dir/f"bits_s{r.window}.png",
                             f"{spec['name']} - {iid} - {r.window}x{r.window}")
                imsave(run_dir/f"refine_s{r.window}.png",(r.active*255).astype("uint8"))
            save_heatmap(final_bits,run_dir/"final_bits.png",f"{spec['name']} - final surprisal")
            save_heatmap(best_scale,run_dir/"best_scale.png",f"{spec['name']} - best scale",cmap="viridis")
            save_panel(img,sr,final_bits,best_scale,gt_prob,run_dir/"panel.png",
                       title=f"{spec['name']} | {iid} | F1={met['F1']:.3f}")
            row={"operator":spec["name"],"image":iid,**met}
            rows.append(row)
            print(row,flush=True)
    df=pd.DataFrame(rows)
    out.mkdir(parents=True,exist_ok=True)
    df.to_csv(out/"metrics.csv",index=False)
    if len(df):
        summary=df.groupby("operator")[["F1","precision","recall"]].mean().sort_values("F1",ascending=False)
        summary.to_csv(out/"summary.csv")
        print(summary)

if __name__=="__main__":
    main()
