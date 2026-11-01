from __future__ import annotations

"""Stage 24: corrected nested residual/error-suppression campaign."""

from collections import Counter
from itertools import combinations
from pathlib import Path
import argparse, csv, hashlib, json, sys
import numpy as np
from PIL import Image
from skimage.io import imread
from skimage.transform import resize

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from benchmark_uded import DEFAULT_UDED
from run_stage12d_bipolar_cv import _make_repeated_folds
from run_stage23c_cached_uded_descriptor_baselines import _identity as legacy_identity, _implementation_hash, _sha256
from src.stage23_cache import load_cached, validate_manifest_record
from src.stage23_descriptors import DESCRIPTOR_IDS, compute_descriptor, descriptor_parameters
from src.stage24_integrity import deterministic_seed, evaluate_scores, exact_binary_gt, load_float_artifact, resize_score_to_native, save_float_artifact, select_threshold, sha256_file
from src.stage24_residual import LogisticModel, MembershipModel, aggregate_memberships, apply_membership, apply_suppressor, fit_membership, fit_nonnegative_fusion, fit_residual_gate, model_hash, residual_features

EXPERIMENT_ID = "stage24_residual_suppression"
OUT_DEFAULT = ROOT / "results/local_dev" / EXPERIMENT_ID
CACHE_DEFAULT = ROOT / "cache/local_dev/stage24"
STOP_DEFAULT = ROOT / "automation/STOP_STAGE24"
SEED, MAX_SIDE, TOL = 20261101, 256, 0.0075


def write_json(path, obj):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp"); tmp.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str), encoding="utf-8"); tmp.replace(path)


def write_csv(path, rows):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    if not rows: path.write_text("", encoding="utf-8"); return
    fields = []
    for row in rows:
        for key in row:
            if key not in fields: fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)


def norm_image(image):
    image = np.asarray(image); h, w = image.shape[:2]; s = min(1.0, MAX_SIDE / max(h, w))
    if s >= 1: return image
    nh, nw = max(8, round(h*s)), max(8, round(w*s)); shape = (nh, nw, image.shape[2]) if image.ndim == 3 else (nh, nw)
    return resize(image, shape, order=1, mode="reflect", anti_aliasing=True, preserve_range=True)


def load_uded_native(root):
    pairs = json.loads((root / "test_pair.lst").read_text(encoding="utf-8")); items, records = [], []
    for j in range(0, len(pairs), 2):
        image_rel, gt_rel = pairs[j]; iid = Path(image_rel).stem; excluded = "35028" in iid
        row = {"position": j//2+1, "image_id": iid, "excluded": excluded, "bytes_read": False}
        if not excluded:
            ip, gp = root/image_rel, root/gt_rel; image, gt = imread(ip), exact_binary_gt(imread(gp)); inf = norm_image(image)
            row.update(bytes_read=True, source_sha256=_sha256(ip), gt_sha256=_sha256(gp), native_gt_shape=list(gt.shape), inference_shape=list(inf.shape[:2]), gt_resized=False)
            items.append({"id": iid, "img": image, "inference_img": inf, "gt": gt, "source_sha256": row["source_sha256"]})
        records.append(row)
    if len(items) != 14 or sum(r["excluded"] for r in records) != 1: raise RuntimeError("UDED overlap-clean contract drift")
    return items, {"schema_version": 2, "ground_truth": "native_never_resized", "inference": "maxside256_score_registered_to_native", "records": records}


def identity(item, descriptor_id, dataset="UDED", split="selection_overlap_clean"):
    return {"schema_version": 1, "dataset": dataset, "split": split, "image_id": item["id"], "source_sha256": item["source_sha256"],
            "descriptor_id": descriptor_id, "parameters": descriptor_parameters(descriptor_id), "code_hash": _implementation_hash(),
            "preprocessing": "downscale_maxside256_then_registered_descriptor_preprocessing_v1", "inference_shape": list(item["inference_img"].shape[:2]),
            "native_shape": list(item["native_shape"] if "native_shape" in item else item["gt"].shape), "dtype": "float32", "gt_used": False}


def cache_path(cache_root, ident):
    key = hashlib.sha256(json.dumps(ident, sort_keys=True, default=str).encode()).hexdigest()
    return Path(cache_root) / "descriptors" / ident["descriptor_id"] / f"{key}.npy"


def descriptor_native(item, descriptor_id, cache_root, allow_legacy=True):
    ident = identity(item, descriptor_id); path = cache_path(cache_root, ident); source = "stage24_cache"
    if path.is_file(): raw = load_float_artifact(path, ident)
    else:
        raw = None
        if allow_legacy:
            lid = legacy_identity({"id": item["id"], "source_sha256": item["source_sha256"]}, descriptor_id, _implementation_hash())
            old = load_cached(lid, ROOT/"cache/local_dev/stage23")
            if old is not None:
                validate_manifest_record(lid, ROOT/"cache/local_dev/stage23"); old = np.asarray(old)
                if old.shape == tuple(item["inference_img"].shape[:2]) and np.issubdtype(old.dtype, np.floating): raw, source = np.asarray(old, np.float32), "verified_stage23_float_cache"
        if raw is None: raw, source = np.asarray(compute_descriptor(descriptor_id, item["inference_img"]), np.float32), "stage24_recomputed"
        save_float_artifact(path, raw, ident)
    native = resize_score_to_native(np.asarray(raw, np.float32), item["gt"].shape)
    return native, {"image_id": item["id"], "descriptor_id": descriptor_id, "source": source, "sha256": sha256_file(path), "gt_resized": False, "dtype": str(raw.dtype)}


def load_maps(items, cache_root, stop_file):
    maps, provenance = {d: [] for d in DESCRIPTOR_IDS}, []
    for item in items:
        if stop_file.exists(): raise KeyboardInterrupt
        for d in DESCRIPTOR_IDS:
            value, row = descriptor_native(item, d, cache_root); maps[d].append(value); provenance.append(row)
    return maps, provenance


def pixel_threshold(scores, gts, n=31):
    s = np.concatenate([np.asarray(x).ravel() for x in scores]); y = np.concatenate([np.asarray(x, bool).ravel() for x in gts]); best = (-1., -1., .5)
    for t in np.unique(np.quantile(s[np.isfinite(s)], np.linspace(0, 1, n))):
        p = s >= t; tp = np.count_nonzero(p & y); fp = np.count_nonzero(p & ~y); fn = np.count_nonzero(~p & y)
        pr = tp/(tp+fp) if tp+fp else 0.; rc = tp/(tp+fn) if tp+fn else 0.; f = 0. if pr+rc == 0 else 2*pr*rc/(pr+rc)
        best = max(best, (f, pr, float(t)))
    return best[2]


def train_normalized(maps, gts, train):
    out = {}
    for d in DESCRIPTOR_IDS:
        m = fit_membership([maps[d]], gts, train); out[d] = [apply_membership([x], m)[..., 0] for x in maps[d]]
    return out


def pair_proxy(a, b, gts, train):
    cv, uq, bg, cr = [], [], [], []
    for ii in train:
        i = int(ii); aa, bb, gt = a[i], b[i], gts[i]; ha, hb = aa >= .5, bb >= .5
        if np.any(gt): cv.append(np.mean((ha|hb)[gt])); uq.append(np.mean((ha^hb)[gt]))
        if np.any(~gt): bg.append(np.mean((ha|hb)[~gt]))
        va, vb = aa.ravel(), bb.ravel()
        if np.std(va) > 1e-8 and np.std(vb) > 1e-8: cr.append(abs(np.corrcoef(va, vb)[0,1]))
    return float(np.mean(cv)+.35*np.mean(uq)-.25*np.mean(bg)-.10*np.mean(cr))


def select_pair(maps, gts, train):
    n = train_normalized(maps, gts, train); rows = []
    for a, b in combinations(DESCRIPTOR_IDS, 2): rows.append({"a": a, "b": b, "train_only_proxy": pair_proxy(n[a], n[b], gts, train)})
    rows.sort(key=lambda r: (r["train_only_proxy"], r["a"], r["b"]), reverse=True)
    return (rows[0]["a"], rows[0]["b"]), rows


def screen_recipe(pair_maps, gts, train, seed):
    mem = fit_membership(pair_maps, gts, train); ms = [apply_membership([pair_maps[0][i], pair_maps[1][i]], mem) for i in range(len(gts))]
    log = fit_nonnegative_fusion(pair_maps, gts, train, mem, seed=deterministic_seed(seed, "fusion")); tg = [gts[int(i)] for i in train]
    aggs = []
    for name in ("equal_mean", "minimum", "maximum", "median", "nonnegative_logistic"):
        ss = [aggregate_memberships(m, name, log) for m in ms]; ts = [ss[int(i)] for i in train]; t = pixel_threshold(ts, tg)
        c, _ = evaluate_scores(ts, tg, t, tolerance_ratio=TOL); aggs.append(((c.f1, c.precision, name), name, ss))
    _, agg, base = max(aggs, key=lambda x: x[0])
    gate = fit_residual_gate(base, ms, gts, train, seed=deterministic_seed(seed, "gate")); choices = []
    for kind, p in (("identity",1.),("local_coherence",2.),("local_coherence",4.),("disagreement",.5),("disagreement",1.),("compress",1.5),("learned_gate",.5),("learned_gate",1.),("learned_gate",2.)):
        ss = [apply_suppressor(base[i], ms[i], kind=kind, parameter=p, gate_model=gate) for i in range(len(gts))]; ts = [ss[int(i)] for i in train]; t = pixel_threshold(ts, tg)
        c, _ = evaluate_scores(ts, tg, t, tolerance_ratio=TOL); choices.append(((c.f1, c.precision, kind, -p), kind, p, ss))
    _, kind, p, final = max(choices, key=lambda x: x[0]); th = select_threshold([final[int(i)] for i in train], tg, count=41, tolerance_ratio=TOL)
    return {"aggregator": agg, "suppressor": kind, "parameter": float(p), "threshold": float(th["threshold"]), "train_F1": float(th["F1"])}, mem, log, gate


def apply_recipe(pair_maps, mem, log, gate, recipe):
    memberships, bases, finals = [], [], []
    for a, b in zip(*pair_maps):
        m = apply_membership([a,b], mem); f = aggregate_memberships(m, recipe["aggregator"], log); s = apply_suppressor(f,m,kind=recipe["suppressor"],parameter=recipe["parameter"],gate_model=gate)
        memberships.append(m); bases.append(f); finals.append(s)
    return memberships, bases, finals


def nested_cv(items, maps, out, stop_file):
    gts = [x["gt"] for x in items]; rows = []; fd = out/"folds"; fd.mkdir(parents=True, exist_ok=True)
    for repeat, fold, train, valid in _make_repeated_folds(len(items), 3, 5, SEED):
        fid = f"r{repeat+1}_f{fold+1}"; rp = fd/f"{fid}.json"
        if rp.is_file(): rows.append(json.loads(rp.read_text(encoding="utf-8"))); continue
        if stop_file.exists(): break
        pair, ps = select_pair(maps, gts, train); write_csv(fd/f"{fid}_pair_screen.csv", ps); pm = [maps[pair[0]], maps[pair[1]]]
        recipe, mem, log, gate = screen_recipe(pm, gts, train, deterministic_seed(SEED, repeat, fold)); _, _, final = apply_recipe(pm, mem, log, gate, recipe)
        vs, vg = [final[int(i)] for i in valid], [gts[int(i)] for i in valid]; c, per = evaluate_scores(vs, vg, recipe["threshold"], tolerance_ratio=TOL)
        row = {"repeat": repeat+1, "fold": fold+1, "pair": list(pair), "aggregator": recipe["aggregator"], "suppressor": recipe["suppressor"], "parameter": recipe["parameter"], "threshold": recipe["threshold"], "train_F1": recipe["train_F1"], "validation_precision": c.precision, "validation_recall": c.recall, "validation_F1": c.f1, "tp": c.tp, "fp": c.fp, "fn": c.fn, "valid_ids": [items[int(i)]["id"] for i in valid], "model_sha256": model_hash(pair, recipe, mem, log, gate)}
        write_json(rp, row); rows.append(row)
    return rows


def restore(payload):
    m, l, g = payload["membership"], payload["logistic"], payload.get("gate")
    mem = MembershipModel(np.asarray(m["midpoint"]), np.asarray(m["scale"])); log = LogisticModel(np.asarray(l["beta"]))
    gate = None if g is None else LogisticModel(np.asarray(g["beta"]), np.asarray(g["mean"]), np.asarray(g["scale"]))
    return tuple(payload["pair"]), payload["recipe"], mem, log, gate


def freeze(items, maps, rows, out):
    gts = [x["gt"] for x in items]; pc = Counter(tuple(r["pair"]) for r in rows); rc = Counter((r["aggregator"],r["suppressor"],float(r["parameter"])) for r in rows)
    pairs = [p for p,n in pc.items() if n == max(pc.values())]; pair = max(pairs, key=lambda p: np.mean([r["validation_F1"] for r in rows if tuple(r["pair"]) == p]))
    recs = [r for r,n in rc.items() if n == max(rc.values())]; rk = max(recs, key=lambda z: np.mean([r["validation_F1"] for r in rows if (r["aggregator"],r["suppressor"],float(r["parameter"])) == z]))
    pm, idx = [maps[pair[0]], maps[pair[1]]], np.arange(len(items)); mem = fit_membership(pm,gts,idx); log = fit_nonnegative_fusion(pm,gts,idx,mem,seed=deterministic_seed(SEED,"freeze"))
    ms = [apply_membership([pm[0][i],pm[1][i]],mem) for i in range(len(items))]; base = [aggregate_memberships(m,rk[0],log) for m in ms]; gate = fit_residual_gate(base,ms,gts,idx,seed=deterministic_seed(SEED,"gate")); final = [apply_suppressor(base[i],ms[i],kind=rk[1],parameter=rk[2],gate_model=gate) for i in range(len(items))]
    th = select_threshold(final,gts,count=101,tolerance_ratio=TOL); recipe = {"aggregator":rk[0],"suppressor":rk[1],"parameter":rk[2],"threshold":float(th["threshold"]),"all_uded_F1":float(th["F1"])}
    payload = {"schema_version":1,"pair":list(pair),"recipe":recipe,"membership":mem.to_dict(),"logistic":log.to_dict(),"gate":gate.to_dict(),"training_target":"exact native GT; no dilation","inference_geometry":"maxside256 score -> native","model_sha256":model_hash(pair,recipe,mem,log,gate)}
    write_json(out/"frozen_model.json",payload); return payload, ms, base, final


def anatomy(items, ms, base, final, payload, out):
    t = payload["recipe"]["threshold"]; rows=[]
    for item,m,b,f in zip(items,ms,base,final):
        gt=item["gt"]; pb,pf=b>=t,f>=t; feat=residual_features(b,m); tp=pb&gt; fp=pb&~gt
        rows.append({"image_id":item["id"],"successful_exact_fp_suppression":int(np.count_nonzero(pb&~pf&~gt)),"wrongly_suppressed_exact_tp":int(np.count_nonzero(pb&~pf&gt)),"base_tp_local_support_median":float(np.median(feat[...,1][tp])) if np.any(tp) else np.nan,"base_fp_local_support_median":float(np.median(feat[...,1][fp])) if np.any(fp) else np.nan,"base_tp_disagreement_median":float(np.median(feat[...,7][tp])) if np.any(tp) else np.nan,"base_fp_disagreement_median":float(np.median(feat[...,7][fp])) if np.any(fp) else np.nan})
    write_csv(out/"residual_anatomy.csv",rows); return rows


def manifest(out):
    data={"schema_version":1,"split":"val","include_incumbent":True,"methods":[{"name":EXPERIMENT_ID,"export":{"script":"run_stage24_residual_campaign.py","args":["--export-bsds","--image-dir","{image_dir}","--output-dir","{output_dir}","--split","{split}","--out",str(out.relative_to(ROOT)).replace("\\","/")]}}],"stage24_note":"UDED-only freeze before BSDS val; PNG is terminal official-evaluator adapter only."}
    write_json(out/"official_eval_manifest.json",data)


def external_descriptor(image,path,descriptor_id,native_shape,cache_root):
    inf=norm_image(image); item={"id":path.stem,"source_sha256":sha256_file(path),"inference_img":inf,"native_shape":native_shape,"gt":np.zeros(native_shape,bool)}; ident=identity(item,descriptor_id,"BSDS500","val"); cp=cache_path(cache_root,ident)
    if cp.is_file(): raw=load_float_artifact(cp,ident)
    else: raw=np.asarray(compute_descriptor(descriptor_id,inf),np.float32); save_float_artifact(cp,raw,ident)
    return resize_score_to_native(raw,native_shape)


def export_bsds(args):
    if args.split.lower() != "val": raise RuntimeError("BSDS test is protected")
    payload=json.loads((Path(args.out)/"frozen_model.json").read_text(encoding="utf-8")); pair,recipe,mem,log,gate=restore(payload); od=Path(args.output_dir); od.mkdir(parents=True,exist_ok=True); paths=sorted(Path(args.image_dir).glob("*.jpg"))
    if not paths: raise RuntimeError("no BSDS images")
    for p in paths:
        image=imread(p); h,w=image.shape[:2]; cues=[external_descriptor(image,p,d,(h,w),Path(args.cache_root)) for d in pair]; m=apply_membership(cues,mem); base=aggregate_memberships(m,recipe["aggregator"],log); score=apply_suppressor(base,m,kind=recipe["suppressor"],parameter=recipe["parameter"],gate_model=gate); Image.fromarray(np.clip(np.rint(score*255),0,255).astype(np.uint8),mode="L").save(od/f"{p.stem}.png")
    print("STAGE24_BSDS_EXPORT_COMPLETED",len(paths)); return 0


def official_eval(out):
    try:
        from automation import official_eval_hook
        cfg=json.loads((ROOT/"automation/config.json").read_text(encoding="utf-8")); spec={"role":"development_experiment","official_eval_manifest":str((out/"official_eval_manifest.json").relative_to(ROOT)).replace("\\","/"),"result_files":[str((out/"summary.json").relative_to(ROOT)).replace("\\","/")]}; return official_eval_hook.maybe_run(EXPERIMENT_ID,spec,cfg)
    except Exception as e: return {"status":"hook_exception","message":repr(e)}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--uded-root",default=str(DEFAULT_UDED)); ap.add_argument("--out",default=str(OUT_DEFAULT)); ap.add_argument("--cache-root",default=str(CACHE_DEFAULT)); ap.add_argument("--stop-file",default=str(STOP_DEFAULT)); ap.add_argument("--skip-official",action="store_true"); ap.add_argument("--export-bsds",action="store_true"); ap.add_argument("--image-dir"); ap.add_argument("--output-dir"); ap.add_argument("--split",default="val"); args=ap.parse_args()
    if args.export_bsds:
        if not args.image_dir or not args.output_dir: ap.error("export requires image/output dirs")
        return export_bsds(args)
    out,cache,stop=Path(args.out),Path(args.cache_root),Path(args.stop_file); out.mkdir(parents=True,exist_ok=True)
    pf=ROOT/"results/local_dev/stage24r0_evaluation_integrity_preflight/summary.json"
    if not pf.is_file() or json.loads(pf.read_text(encoding="utf-8")).get("status")!="completed": raise RuntimeError("Stage24R0 preflight must pass")
    if stop.exists(): print("STOP_STAGE24 already exists"); return 3
    items,dm=load_uded_native(Path(args.uded_root)); write_json(out/"native_dataset_manifest.json",dm)
    try: maps,prov=load_maps(items,cache,stop)
    except KeyboardInterrupt: write_json(out/"checkpoint.json",{"status":"stopped","phase":"descriptor_materialization"}); print("STAGE24_STOPPED_SAFELY"); return 0
    write_csv(out/"descriptor_provenance.csv",prov); rows=nested_cv(items,maps,out,stop)
    if stop.exists(): write_json(out/"checkpoint.json",{"status":"stopped","phase":"nested_cv","completed_folds":len(rows)}); print("STAGE24_STOPPED_SAFELY"); return 0
    if len(rows)!=15: raise RuntimeError(f"expected 15 folds, found {len(rows)}")
    write_csv(out/"nested_cv_folds.csv",rows); tp=sum(r["tp"] for r in rows); fp=sum(r["fp"] for r in rows); fn=sum(r["fn"] for r in rows); pr=tp/(tp+fp); rc=tp/(tp+fn); f1=2*pr*rc/(pr+rc)
    payload,ms,base,final=freeze(items,maps,rows,out); anatomy(items,ms,base,final,payload,out); manifest(out)
    transfer={"status":"guarded","rule":"legacy uint8 PNG detector maps rejected as scientific inputs","next":"materialize author/native float detector maps before literature transfer"}; write_json(out/"literature_transfer_guard.json",transfer)
    summary={"status":"completed","experiment_id":EXPERIMENT_ID,"protocol":{"gt":"native_never_resized","training_target":"exact_GT","pair_selection":"outer_train_only","threshold":"train_only","outer_cv":"5x3","matcher":"one_to_one_max_cardinality","scientific_maps":"float32_npy","bsds":"official_Berkeley_one_shot_after_freeze"},"nested_cv":{"precision":pr,"recall":rc,"F1":f1,"mean_fold_F1":float(np.mean([r["validation_F1"] for r in rows]))},"frozen_model":payload,"literature_transfer":transfer,"official_evaluation":"pending"}; write_json(out/"summary.json",summary); write_json(out/"checkpoint.json",{"status":"completed","phase":"freeze"})
    if not args.skip_official: summary["official_evaluation"]=official_eval(out); write_json(out/"summary.json",summary)
    print("STAGE24_RESIDUAL_SUPPRESSION_COMPLETED"); print(out/"summary.json"); return 0


if __name__ == "__main__": raise SystemExit(main())
