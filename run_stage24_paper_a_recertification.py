from __future__ import annotations
"""Stage 24G-L: corrected Paper A recertification.

Reads local Stage24 float descriptor caches; never rewrites Stage24 results.
Default runs the full UDED campaign and official BSDS500 validation. Literature
transfer requires author/native float detector maps and is explicitly guarded.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image
from scipy.stats import wilcoxon, friedmanchisquare
from skimage.io import imread

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmark_uded import DEFAULT_UDED
from run_stage12d_bipolar_cv import _make_repeated_folds
from run_stage24_residual_campaign import (
    load_uded_native, load_maps, norm_image, external_descriptor, select_pair,
)
from src.stage23_descriptors import DESCRIPTOR_IDS
from src.stage24_recertification_cv import (
    write_json, write_csv, train_pair_screen, choose_groups, run_group,
    geometry_audit, individual_descriptor_baselines, memberships_on_split,
    HISTORIC_PAIRS, HISTORIC_TRIPLES, TRANSFER_MODES,
)
from src.stage24_recertification_ops import (
    AGGREGATORS, SUPPRESSORS, deterministic_seed, fit_aggregator,
    apply_aggregator, choose_threshold, serialize_model, inference_recipe,
)
from src.stage24_integrity import sha256_file, one_to_one_boundary_counts
from src.stage24_residual import fit_residual_gate, apply_suppressor
from src.stage24_integrity import load_float_artifact

EXPERIMENT = "stage24_paper_a_recertification"
OUT = ROOT / "results" / "local_dev" / EXPERIMENT
STOP = ROOT / "automation" / "STOP_STAGE24_PAPER_A"
CACHE = ROOT / "cache" / "local_dev" / "stage24"
SEED = 20261101  # exact same outer fold plan as Stage24
FOLDS = 15


def assert_preflight():
    path = ROOT / "results/local_dev/stage24r0_evaluation_integrity_preflight/summary.json"
    if not path.exists():
        raise FileNotFoundError("Missing Stage24R0 integrity preflight: " + str(path))
    p = json.loads(path.read_text(encoding="utf-8"))
    if p.get("status") != "completed" or p.get("blockers"):
        raise RuntimeError("Stage24R0 preflight not certified")
    if not all(c.get("passed") for c in p.get("checks", [])):
        raise RuntimeError("At least one Stage24R0 integrity check failed")
    # Require snapshot archived, or abort rather than silently alter original campaign.
    summary = ROOT / "results/local_dev/stage24_residual_suppression/summary.json"
    if not summary.exists() or json.loads(summary.read_text(encoding="utf-8")).get("status") != "completed":
        raise RuntimeError("Archived completed Stage24 summary required")
    return p


def local_dataset(args):
    items, manifest = load_uded_native(Path(args.uded_root))
    if len(items) != 14:
        raise RuntimeError("UDED 14-image native geometry contract drift")
    maps, provenance = load_maps(items, Path(args.cache_root), STOP)
    if set(maps) != set(DESCRIPTOR_IDS):
        raise RuntimeError("Descriptor registry mismatch")
    return items, maps, manifest, provenance


def preflight_math():
    """Math/operator invariants, independent of dataset and MATLAB."""
    from src.stage24_recertification_ops import (
        capacity_coefficients, capacity_from_mobius, choquet, sugeno,
        thin_score, binary_map, apply_aggregator,
    )
    rng = np.random.default_rng(11)
    checks = []
    for n in (2, 3):
        x = rng.uniform(0.1, .9, (48, n))
        y = rng.integers(0, 2, size=48)
        for signed in (False, True):
            co = capacity_coefficients(x, y, signed=signed)
            cap = capacity_from_mobius(co, n)
            checks.append({"test": "capacity_monotone", "arity": n,
                           "signed": signed, "passed": np.isclose(cap[-1], 1)})
        for aggregator in ("equal_mean", "minimum", "maximum", "median",
                           "choquet_distorted_055"):
            out = apply_aggregator(x, {"n_inputs": n, "family": aggregator})
            if not np.all(np.isfinite(out)) or np.any(out < 0) or np.any(out > 1):
                raise RuntimeError("Aggregator out of [0,1]: " + aggregator)
        cap = np.array([mask.bit_count()/n for mask in range(1 << n)])
        if not np.allclose(choquet(x, cap), np.mean(x, axis=-1), atol=1e-7):
            raise RuntimeError("Additive Choquet != equal mean")
        if not np.all((sugeno(x, cap) >= 0) & (sugeno(x, cap) <= 1)):
            raise RuntimeError("Sugeno invalid")
    score = np.zeros((27, 27), np.float32)
    score[13, 4:23] = .9
    image = np.repeat(np.arange(27)[:, None], 27, axis=1).astype(float)
    nms = thin_score(score, "nms_image", image)
    if nms.shape != score.shape:
        raise RuntimeError("NMS geometry changed")
    if binary_map(score, .5, "binary_thin_diagnostic").shape != score.shape:
        raise RuntimeError("Diagnostic thinning geometry changed")
    return checks


def _fold_plan(items, max_folds):
    folds = list(_make_repeated_folds(len(items), 3, 5, SEED))
    if len(folds) != FOLDS:
        raise RuntimeError("Outer CV contract drift")
    return folds[:max_folds]


def _fold_path(out, key, fold):
    return out / "folds" / fold / (key + ".json")


def _load_or_make(path, fn):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    value = fn()
    write_json(path, value)
    return value


def run_uded(args, items, maps, out):
    cfg = {"seed": SEED, "threshold_count": args.thresholds,
           "inner_threshold_count": args.inner_thresholds,
           "inner_top": args.inner_top}
    summary = []
    for pos, (repeat, fold, train, valid) in enumerate(_fold_plan(items, args.max_folds), 1):
        fid = f"r{repeat+1}_f{fold+1}"
        if STOP.exists():
            print("STAGE24GL_STOPPED_SAFELY at", fid, flush=True)
            return False
        print(f"STAGE24GL_OUTER {pos}/{args.max_folds} {fid}", flush=True)
        candidates = _load_or_make(
            _fold_path(out, "pair_screen", fid),
            lambda: train_pair_screen(items, maps, train))
        if len(candidates) != 78:
            raise RuntimeError("Expected 78 pair scores")
        pairs, triples = choose_groups(candidates, args.top_pairs, args.top_triples)
        if args.phase in ("all", "g0"):
            _load_or_make(_fold_path(out, "geometry_audit", fid), lambda:
                          geometry_audit(items, maps, train, [
                              r for r in candidates if tuple(sorted((r["a"],r["b"]))) in
                              {tuple(sorted(p)) for p in HISTORIC_PAIRS + (("hessian_s7", "halfdisc_distribution_contrast"),)}
                          ], fid))
            _load_or_make(_fold_path(out, "individual_descriptor", fid),
                          lambda: dict(zip(("summary", "per_image"),
                              individual_descriptor_baselines(items, maps, train,
                                 valid, fid, args.thresholds))))
        if args.phase == "g0":
            continue
        groups = (pairs if args.phase in ("all", "g", "i") else [])
        groups += (triples if args.phase in ("all", "h", "i") else [])
        for group in groups:
            if STOP.exists():
                print("STAGE24GL_STOPPED_SAFELY after", fid, flush=True)
                return False
            print("STAGE24GL_GROUP", fid, "|".join(group), flush=True)
            run_group(group, items, maps, train, valid, fid, out, cfg)
        summary.append({"fold_id":fid, "pairs":pairs, "triples":triples})
    write_json(out / "campaign_progress.json", {"processed":len(summary),
               "expected":args.max_folds, "phase":args.phase,
               "warning":"Outer folds repeated on the same 14 images; not independent replicates"})
    return True


def _gather(out, args):
    results = []
    plan = list(_make_repeated_folds(14, 3, 5, SEED))[:args.max_folds]
    for repeat, fold, train, valid in plan:
        fid = f"r{repeat+1}_f{fold+1}"
        fn = _fold_path(out, "pair_screen", fid)
        if not fn.exists():
            continue
        pairs, triples = choose_groups(json.loads(fn.read_text(encoding="utf-8")),
                                       args.top_pairs, args.top_triples)
        for group in pairs + triples:
            p = _fold_path(out, "__".join(group), fid)
            if p.exists():
                results.append(json.loads(p.read_text(encoding="utf-8")))
    return results


def collate(args, out):
    records = _gather(out, args)
    def dump(name, key):
        write_csv(out / name, [dict(fold_id=r["fold_id"], **x)
              for r in records for x in r[key]])
    if records:
        dump("aggregator_landscape_fold.csv", "landscape")
        dump("aggregator_landscape_per_image.csv", "landscape_per_image")
        dump("inner_cv_trials.csv", "inner")
        dump("suppressor_ablation_fold.csv", "suppression_ablation")
        dump("suppressor_ablation_per_image.csv", "suppression_ablation_per_image")
        write_csv(out / "selected_recipes_fold.csv",
                  [{**r["selected_outer"], "fold_id":r["fold_id"]}
                   for r in records])
        write_csv(out / "selected_recipes_per_image.csv",
                  [{**x,"fold_id":r["fold_id"]} for r in records
                   for x in r["selected_per_image"]])
    # Aggregate all raw 78 scored pair screens, not just the selected pairs.
    screens = []
    for p in sorted((out/"folds").glob("r*_f*/pair_screen.json")):
        for rank,r in enumerate(json.loads(p.read_text(encoding="utf-8")),1):
            screens.append({"fold":p.parent.name,"rank":rank,**r})
    write_csv(out / "pair_complementarity_all_folds.csv", screens)
    if screens:
        grouped = defaultdict(list)
        for r in screens:grouped[(r["a"],r["b"])].append(r["score"])
        ranking = [{"a":a,"b":b,"mean_score":float(np.mean(v)),
                    "std_score":float(np.std(v)),"folds_scored":len(v)}
                   for (a,b),v in grouped.items()]
        ranking.sort(key=lambda r:-r["mean_score"])
        for rank,r in enumerate(ranking,1):r["rank"]=rank
        write_csv(out / "pair_complementarity_ranked.csv", ranking)
    audit = []
    baselines = []
    image_b = []
    for p in sorted((out/"folds").glob("r*_f*/geometry_audit.json")):
        audit.extend(json.loads(p.read_text(encoding="utf-8")))
    for p in sorted((out/"folds").glob("r*_f*/individual_descriptor.json")):
        obj = json.loads(p.read_text(encoding="utf-8"))
        baselines.extend(obj["summary"]); image_b.extend(obj["per_image"])
    write_csv(out / "geometry_impact_stage24_proxy.csv", audit)
    write_csv(out / "individual_descriptors_corrected_fold.csv", baselines)
    write_csv(out / "individual_descriptors_corrected_per_image.csv", image_b)
    # One winning group per outer fold, using only inner-CV results.
    best = {}
    for r in records:
        score = r["selected"]["mean_inner_F1"]
        fid = r["fold_id"]
        if fid not in best or score > best[fid]["selected"]["mean_inner_F1"]:
            best[fid] = r
    write_csv(out / "inner_selected_heldout.csv",
              [{"fold":fid, **r["selected"], **r["selected_outer"]}
               for fid,r in sorted(best.items())])
    write_csv(out / "inner_selected_heldout_per_image.csv",
              [dict(fold=fid, **x) for fid,r in sorted(best.items())
               for x in r["selected_per_image"]])
    return best


def freeze_recipe(best, items, maps, out):
    if len(best) != 15:
        raise RuntimeError("Final model freeze requires all 15 completed folds")
    counts = Counter((tuple(r["group"]), r["selected"]["aggregator"],
                      r["selected"]["mode"], r["selected"]["suppressor"],
                      float(r["selected"]["strength"])) for r in best.values())
    # Select by inner-CV selection frequency; no outer-heldout F1 used.
    key = sorted(counts, key=lambda x:(-counts[x], x))[0]
    group, agg_name, mode, suppressor, strength = key
    gts = [it["gt"] for it in items]
    idx = np.arange(len(items), dtype=int)
    mem, memberships = memberships_on_split(group, maps, gts, idx)
    agg = fit_aggregator(agg_name, memberships, gts, idx,
                         seed=deterministic_seed(SEED,"freeze",group,agg_name))
    base = [apply_aggregator(x, agg) for x in memberships]
    gate = fit_residual_gate(base, memberships, gts, idx,
                            seed=deterministic_seed(SEED,"gate",group)) if suppressor=="learned_gate" else None
    models = {}
    for variant, name, p in (("winner", suppressor, strength), ("identity", "identity", 1.0)):
        scores = [apply_suppressor(base[i], memberships[i], kind=name,
                                  parameter=p, gate_model=gate) for i in idx]
        threshold, fit = choose_threshold(scores,gts,[it["img"] for it in items],mode,count=41)
        m = serialize_model(group,mem,agg,(name,p),mode,gate)
        m["threshold"] = threshold
        m["fit_all_UDED_F1_NOT_HELDOUT"] = fit.f1
        m["selection_source"] = "frequency_of_outer_train_inner_CV_winners"
        m["source_commit_note"] = "Stage24 original experiment remains immutable"
        models[variant] = m
    write_json(out/"frozen_models.json",
               {"models":models,"selection_counts":[{"model":list(k),"n":v}
                  for k,v in counts.most_common()],
                "training_dataset":"UDED_overlap_clean_14",
                "outer_split_validation_used_in_freeze":False})
    manifest = {
        "schema_version":1,"split":"val","include_incumbent":True,
        "methods":[{"name":"stage24gl_"+variant,
                    "export":{"script":"run_stage24_paper_a_recertification.py",
                              "args":["--export-bsds","--variant",variant,
                                      "--image-dir","{image_dir}","--output-dir","{output_dir}",
                                      "--split","{split}","--out",str(out.relative_to(ROOT)).replace("\\","/")]}}
                   for variant in models],
        "warning":"Development validation only; reference reproduction must be verified externally."
    }
    write_json(out/"official_eval_manifest.json",manifest)
    return models


def run_bsds_export(args):
    if args.split != "val":
        raise RuntimeError("BSDS test split protected, export blocked")
    out = Path(args.out)
    data = json.loads((out/"frozen_models.json").read_text(encoding="utf-8"))
    model = data["models"][args.variant]
    source = Path(args.image_dir)
    target = Path(args.output_dir)
    target.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.glob("*.jpg")):
        original = imread(path)
        shape = original.shape[:2]
        cues = [external_descriptor(original,path,name,shape,Path(args.cache_root))
                for name in model["descriptors"]]
        score = inference_recipe(cues,model,original)
        if not np.isfinite(score).all() or score.shape != shape:
            raise RuntimeError("Invalid BSDS export score " + path.name)
        # Final PNG is an official-evaluator adapter only; never a scientific cache.
        Image.fromarray(np.rint(np.clip(score,0,1)*255).astype(np.uint8),mode="L").save(target/(path.stem+".png"))
    print("STAGE24GL_BSDS_EXPORT_DONE",len(list(source.glob("*.jpg"))))


def run_official(out):
    path = out/"official_eval_manifest.json"
    if not path.exists():
        raise RuntimeError("BSDS evaluation requires frozen UDED-only model")
    cmd = [sys.executable,str(ROOT/"evaluation/bsds_official/run_official_bsds.py"),
           "--experiment-id",EXPERIMENT,"--manifest",str(path),
           "--out",str(ROOT/"results/official_eval"/EXPERIMENT)]
    print("OFFICIAL_BERKELEY_START",flush=True)
    subprocess.run(cmd,cwd=ROOT,check=True)
    p = ROOT/"results/official_eval"/EXPERIMENT/"summary.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    write_json(out/"official_bsds_summary.json",data)
    guard = {"official_evaluation_completed":data.get("status")=="completed",
             "reference_reproduction_verified":bool(data.get("evaluator",{}).get("reference_reproduction_verified",False)),
             "final_claim_eligible":False,
             "note":"BSDS validation is development evidence; protected multi-benchmark gate pending"}
    write_json(out/"final_claim_guard.json",guard)


def run_literature(args, items, maps, out):
    manifest = Path(args.literature_manifest)
    if not manifest.is_file():
        write_json(out/"literature_transfer_guard.json",{
            "status":"guarded","reason":"Author/native float detector manifest not provided",
            "required_manifest_fields":["dataset","split","method","image_id","score_path","sha256"],
            "quantized_png_permitted":False})
        return
    entries = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(entries,list):
        raise ValueError("Literature manifest must be a JSON list")
    id_to_item={i["id"]:i for i in items}
    per_method=defaultdict(dict)
    for entry in entries:
        if entry["dataset"]!="UDED" or entry["split"]!="selection_overlap_clean":
            continue  # BSDS images validated only during official external evaluation.
        if entry["image_id"] not in id_to_item:
            raise ValueError("Unknown literature UDED image id")
        p=Path(entry["score_path"])
        if not p.is_absolute():p=ROOT/p
        if p.suffix!=".npy" or not p.is_file():
            raise RuntimeError("Float scientific literature map missing: "+str(p))
        if sha256_file(p)!=entry["sha256"]:
            raise RuntimeError("Literature map hash mismatch: "+str(p))
        arr=np.load(p,allow_pickle=False)
        if arr.dtype!=np.float32 or arr.shape!=id_to_item[entry["image_id"]]["gt"].shape:
            raise RuntimeError("Detector map is not native float32: "+str(p))
        per_method[entry["method"]][entry["image_id"]]=arr
    rows=[]
    for method,entry_maps in per_method.items():
        if set(entry_maps)!=set(id_to_item):
            raise RuntimeError("Incomplete UDED float detector maps: "+method)
        source=[entry_maps[item["id"]] for item in items]
        for repeat,fold,train,valid in _make_repeated_folds(14,3,5,SEED):
            fid=f"r{repeat+1}_f{fold+1}"
            for mode in TRANSFER_MODES:
                t,_=choose_threshold([source[int(i)] for i in train],
                                     [items[int(i)]["gt"] for i in train],
                                     [items[int(i)]["img"] for i in train],mode)
                vals=[]
                from src.stage24_recertification_ops import thin_score,binary_map
                for i in valid:
                    j=int(i)
                    pred=binary_map(thin_score(source[j],mode,items[j]["img"]),t,mode)
                    c=one_to_one_boundary_counts(pred,items[j]["gt"])
                    vals.append({"method":method,"fold":fid,"image_id":items[j]["id"],
                                 "mode":mode,"tp":c.tp,"fp":c.fp,"fn":c.fn,
                                 "F1":c.f1,"threshold":t})
                rows.extend(vals)
    write_csv(out/"literature_baselines_uded_per_image.csv",rows)
    write_json(out/"literature_transfer_guard.json",{
        "status":"uded_baselines_complete_external_transfer_pending",
        "methods":list(per_method),
        "note":"BSDS author-native float maps and complement+suppression train-only experiments still required"})


def stats_and_claims(out):
    p=out/"suppressor_ablation_per_image.csv"
    rows=[]
    if p.is_file():
        with p.open(encoding="utf-8",newline="") as f:rows=list(csv.DictReader(f))
    by=defaultdict(dict)
    for r in rows:
        key=(r["fold_id"],r["group"],r["aggregator"],r["thinning"],r["image_id"])
        by[key][(r["suppressor"],r["strength"])]=float(r["F1"])
    per_img=defaultdict(list)
    for key,rec in by.items():
        iden=rec.get(("identity","1.0"))
        for name,val in rec.items():
            if name[0]!="identity" and iden is not None:
                per_img[(key[-1],name)].append(val-iden)
    tests=[]
    by_name=defaultdict(dict)
    for (image,typ),vals in per_img.items():
        by_name[typ][image]=float(np.mean(vals))
    for typ,images in sorted(by_name.items()):
        dif=np.asarray(list(images.values()))
        if len(dif)<6 or np.allclose(dif,0):
            continue
        test=wilcoxon(dif,alternative="two-sided",zero_method="wilcox")
        tests.append({"comparison":str(typ),"n_unique_images":len(dif),
                      "mean_delta_F1":float(np.mean(dif)),"median_delta_F1":float(np.median(dif)),
                      "p_unadjusted":float(test.pvalue),
                      "sampling":"per-image mean over repeated folds; exploratory, dependencies remain"})
    tests.sort(key=lambda r:r["p_unadjusted"])
    m=len(tests)
    running=0.0
    for i,r in enumerate(tests):
        running=max(running,min(1.,(m-i)*r["p_unadjusted"]))
        r["p_holm"]=running
    write_csv(out/"statistical_tests_exploratory.csv",tests)
    official_path=out/"official_bsds_summary.json"
    official=json.loads(official_path.read_text(encoding="utf-8")) if official_path.is_file() else None
    claims=[
      {"claim":"Native GT correctness","status":"PROTOCOL_VERIFIED"},
      {"claim":"Full 78-pair corrected proxy landscape","status":"REQUIRES_ALL_15_FOLDS"},
      {"claim":"Pair/triple and aggregator factorial","status":"REQUIRES_COMPLETE_CV"},
      {"claim":"Suppression helps heldout F1","status":"CONDITIONAL_ON_PAIRED_ABLATIONS"},
      {"claim":"BSDS validation","status":"DEVELOPMENT_ONLY" if official else "PENDING"},
      {"claim":"BSDS reference reproduction","status":"BLOCKED_UNTIL_INDEPENDENT_REFERENCE"},
      {"claim":"Literature detector transfer","status":"GUARDED_BY_AUTHOR_NATIVE_FLOAT_MAPS"},
      {"claim":"Publication/SOTA","status":"BLOCKED_UNTIL_PROTECTED_BENCHMARK_GATE"},
    ]
    write_csv(out/"claim_status.csv",claims)
    report=out/"PAPER_A_METHODS_RESULTS_STATUS.md"
    report.write_text(
        "# Stage 24G-L — auditoria para Paper A\n\n"
        "GTs nativos preservados; descritores float, 5x3 outer CV, inner CV real.\n\n"
        "As comparacoes de agregadores e suppressors usam as mesmas particoes; "
        "thresholds ajustados apenas nos dados de treino.\n\n"
        "Modos: raw, NMS orientado pela imagem e thinning binario apenas diagnostico. "
        "O avaliador Berkeley oficial usa thinpb=true; nenhum thinning morfologico "
        "Python deve ser apresentado como identico ao Berkeley.\n\n"
        "A avaliacao BSDS500 val nao valida claims SOTA nem autoriza tuning no test.\n\n"
        "Os dados estatisticos de folds repetidos nao sao 15 observacoes independentes. "
        "Testes agregados por imagem ainda sao exploratorios.\n\n"
        "Consultar claim_status.csv e final_claim_guard.json antes de atualizar o paper.\n",
        encoding="utf-8",
    )


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phase",choices=("all","preflight","g0","g","h","i","j","k","l"),
                    default="all")
    ap.add_argument("--out",default=str(OUT))
    ap.add_argument("--uded-root",default=str(DEFAULT_UDED))
    ap.add_argument("--cache-root",default=str(CACHE))
    ap.add_argument("--literature-manifest",default=str(ROOT/"external/literature_float_manifest.json"))
    ap.add_argument("--thresholds",type=int,default=21)
    ap.add_argument("--inner-thresholds",type=int,default=13)
    ap.add_argument("--inner-top",type=int,default=3)
    ap.add_argument("--top-pairs",type=int,default=3)
    ap.add_argument("--top-triples",type=int,default=2)
    ap.add_argument("--max-folds",type=int,default=15)
    ap.add_argument("--skip-official",action="store_true")
    ap.add_argument("--export-bsds",action="store_true")
    ap.add_argument("--image-dir")
    ap.add_argument("--output-dir")
    ap.add_argument("--variant",choices=("winner","identity"),default="winner")
    ap.add_argument("--split",default="val")
    args=ap.parse_args()
    if args.max_folds < 1 or args.max_folds > 15:
        ap.error("--max-folds must be 1..15")
    if args.export_bsds:
        if not args.image_dir or not args.output_dir:ap.error("--export-bsds requires image/output directories")
        run_bsds_export(args)
        return 0
    out=Path(args.out)
    out.mkdir(parents=True,exist_ok=True)
    preflight=assert_preflight()
    checks=preflight_math()
    write_json(out/"preflight.json",{"status":"passed","n_tests":len(checks),
                "checks":checks,"inherited_R0":True,"GT":"native_never_resized",
                "berkeley_thinpb_not_equated_to_python_thinning":True})
    if args.phase=="preflight":
        print("STAGE24GL_PREFLIGHT_OK")
        return 0
    if args.phase in ("all","g0","g","h","i"):
        items,maps,manifest,provenance=local_dataset(args)
        write_json(out/"native_dataset_manifest.json",manifest)
        write_csv(out/"descriptor_provenance.csv",provenance)
        finished=run_uded(args,items,maps,out)
        if not finished:return 0
        best=collate(args,out)
        if args.phase=="all":
            if args.max_folds!=15:raise RuntimeError("Full campaign requires 15 outer folds")
            freeze_recipe(best,items,maps,out)
            run_literature(args,items,maps,out)
    if args.phase=="j":
        items,maps,_,_=local_dataset(args)
        run_literature(args,items,maps,out)
    if args.phase in ("all","k") and not args.skip_official:
        run_official(out)
    if args.phase in ("all","l"):
        stats_and_claims(out)
    write_json(out/"summary.json",{
        "experiment":EXPERIMENT,"phase":args.phase,
        "status":"completed" if args.phase=="all" and args.max_folds==15 else "phase_completed",
        "full_cv_folds":args.max_folds,"native_gt":True,
        "no_validation_decisions":True,
        "final_claim_eligible":False,
        "official_reference_reproduction_verified":False,
        "literature_transfer_requires_author_float_data":True})
    print("STAGE24GL_PHASE_COMPLETED",args.phase,str(out),flush=True)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
