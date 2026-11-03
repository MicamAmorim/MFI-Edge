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
import re
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
    quantile_mapping_fit, quantile_mapping_apply, thin_score,
)
from src.stage24_integrity import sha256_file, one_to_one_boundary_counts
from src.stage24_residual import fit_residual_gate, apply_suppressor
from src.stage24_integrity import load_float_artifact
from src.stage24_paper_a_historical import (
    historical_score_comparison, synthetic_contract as historical_formula_contract,
)
from src.stage24_paper_a_controls import (
    null_and_random_controls, rank_equivalence_on_uded,
    select_best_single, variance_decomposition,
    complementarity_predictive_test, scale_audit,
)
from src.stage24_paper_a_berkeley_bootstrap import (
    load_official_counts, load_archived_counts, paired_bootstrap,
    write_results, synthetic_contract as bsds_bootstrap_contract,
)

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
        y = (x.mean(axis=-1) > 0.5).astype(float)
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
        if args.phase in ("all","g0"):
            def fold_controls():
                return {
                    "baselines":null_and_random_controls(items,train,valid,fid,seed=SEED),
                    "logistic_rank_equivalence":rank_equivalence_on_uded(
                        items,maps,train,valid,fid),
                }
            _load_or_make(_fold_path(out,"scientific_controls",fid),fold_controls)
            def old_score_control():
                wanted=set(tuple(sorted(z)) for z in
                    HISTORIC_PAIRS + (("hessian_s7","halfdisc_distribution_contrast"),))
                return historical_score_comparison(
                    items,maps,train,fid,[p for p in wanted])
            _load_or_make(_fold_path(out,"historical_score_formula",fid),
                          old_score_control)
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
        dump("calibration_ablation_fold.csv", "calibration_ablation")
        dump("calibration_ablation_per_image.csv", "calibration_ablation_per_image")
        dump("membership_score_histograms.csv", "membership_score_histograms")
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
    historic=[]
    for path in sorted((out/"folds").glob("r*_f*/historical_score_formula.json")):
        historic.extend(json.loads(path.read_text(encoding="utf-8")))
    write_csv(out/"historical_stage23d_formula_control.csv",historic)
    write_csv(out / "individual_descriptors_corrected_fold.csv", baselines)
    write_csv(out / "individual_descriptors_corrected_per_image.csv", image_b)
    best_singles,best_single_images=select_best_single(baselines,image_b)
    write_csv(out/"best_single_train_selected_fold.csv",best_singles)
    write_csv(out/"best_single_train_selected_per_image.csv",best_single_images)
    scientific_controls=[]
    logistic_ranks=[]
    for path in sorted((out/"folds").glob("r*_f*/scientific_controls.json")):
        obj=json.loads(path.read_text(encoding="utf-8"))
        scientific_controls.extend(obj.get("baselines",[]))
        logistic_ranks.extend(obj.get("logistic_rank_equivalence",[]))
    write_csv(out/"trivial_density_baselines_per_image.csv",scientific_controls)
    write_csv(out/"logistic_weighted_rank_equivalence_per_image.csv",logistic_ranks)
    if records:
        base_landscape=[dict(fold_id=r["fold_id"], **x)
                        for r in records for x in r["landscape"]]
        write_json(out/"factorial_variance_decomposition.json",
                   variance_decomposition(base_landscape))
        prediction=complementarity_predictive_test(screens,base_landscape)
        write_json(out/"complementarity_predictive_test.json",prediction)
        if prediction.get("rows"):
            write_csv(out/"complementarity_predictive_pairs.csv",prediction["rows"])
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
        # Berkeley calibration audit: same rank (apart from quantization/ties)
        # but redistribution over the 99 fixed official thresholds.
        processed=[thin_score(z,mode,item["img"]) for z,item in zip(scores,items)]
        calib=quantile_mapping_fit(processed,n=256)
        qm={**m,"score_quantile_mapping":calib}
        qm["selection_source"]="deterministic_train_only_monotone_quantile_diagnostic"
        models[variant+"_quantile"]=qm

    # Best individual descriptor: choose solely by TRAIN-only selection frequency.
    single_path=out/"best_single_train_selected_fold.csv"
    if not single_path.exists():
        raise RuntimeError("Best-single fold audit required before external freeze")
    with single_path.open(encoding="utf-8",newline="") as reader:
        singles=list(csv.DictReader(reader))
    if len(singles)!=15:raise RuntimeError("15 best-single fold selections required")
    single_name=Counter(r["descriptor_id"] for r in singles).most_common(1)[0][0]
    one=(single_name,)
    one_mem,one_ms=memberships_on_split(one,maps,gts,idx)
    one_agg={"family":"equal_mean","n_inputs":1}
    one_scores=[apply_aggregator(m,one_agg) for m in one_ms]
    one_t,one_fit=choose_threshold(one_scores,gts,[it["img"] for it in items],
                                   "nms_image",count=41)
    one_model=serialize_model(one,one_mem,one_agg,("identity",1.0),"nms_image")
    one_model["threshold"]=one_t
    one_model["fit_all_UDED_F1_NOT_HELDOUT"]=one_fit.f1
    one_model["selection_source"]="15_train_only_best_single_fold_votes"
    models["best_single"]=one_model

    # Rank-equivalence control for historical Pair 04: learned nonnegative
    # logistic and weighted sum with IDENTICAL learned positive weights.
    historical=("gabor4_scale_persistence","halfdisc_distribution_contrast")
    hm,hms=memberships_on_split(historical,maps,gts,idx)
    logistic=fit_aggregator("nonnegative_logistic",hms,gts,idx,
                           seed=deterministic_seed(SEED,"pair04_logistic"))
    beta=np.asarray(logistic["logistic"]["beta"],float)
    if np.any(beta[1:] < -1e-8) or beta[1:].sum()<=1e-8:
        raise RuntimeError("Pair04 nonnegative logistic weights are degenerate")
    weights=np.maximum(beta[1:],0)/np.sum(np.maximum(beta[1:],0))
    weighted={"family":"weighted_mean","n_inputs":2,"weights":weights.tolist()}
    for label,operator in (("pair04_logistic",logistic),
                           ("pair04_weighted",weighted)):
        ss=[apply_aggregator(m,operator) for m in hms]
        t,fit=choose_threshold(ss,gts,[it["img"] for it in items],
                               "nms_image",count=41)
        model=serialize_model(historical,hm,operator,("identity",1.0),"nms_image")
        model["threshold"]=t
        model["fit_all_UDED_F1_NOT_HELDOUT"]=fit.f1
        model["selection_source"]="predeclared_rank_equivalence_control"
        models[label]=model
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
    source = Path(args.image_dir)
    target = Path(args.output_dir)
    target.mkdir(parents=True, exist_ok=True)
    paths = sorted(source.glob("*.jpg"))
    if not paths:
        raise RuntimeError("No BSDS validation images supplied by official evaluator")
    literature_role = args.variant.startswith("literature::")
    if literature_role:
        _, method, role = args.variant.split("::", 2)
        if role not in ("baseline", "fusion"):
            raise ValueError("Unknown literature export role")
        frozen = json.loads((out/"frozen_literature_models.json").read_text(encoding="utf-8"))
        if method not in frozen or not frozen[method]["ready_for_bsds"]:
            raise RuntimeError("Author-native BSDS float maps incomplete: "+method)
        literature = frozen[method]
        manifest = json.loads(Path(args.literature_manifest).read_text(encoding="utf-8"))
        external = {e["image_id"]:e for e in manifest
                    if e["dataset"]=="BSDS500" and e["split"]=="val" and e["method"]==method}
        if set(external)!={p.stem for p in paths}:
            raise RuntimeError("Literature BSDS float image IDs do not match 100 official images")
        model = literature["model"]
    else:
        data=json.loads((out/"frozen_models.json").read_text(encoding="utf-8"))
        model=data["models"][args.variant]
    for path in paths:
        original=imread(path)
        shape=original.shape[:2]
        if literature_role:
            raw=_float_literature_score(external[path.stem],shape)
            if role=="baseline":
                lo,hi=literature["baseline_uded_quantiles"]
                score=np.clip((raw-lo)/(hi-lo),0.,1.).astype(np.float32)
            else:
                cue=external_descriptor(original,path,literature["cue"],shape,Path(args.cache_root))
                score=inference_recipe([raw,cue],model,original)
        else:
            cues=[external_descriptor(original,path,name,shape,Path(args.cache_root))
                  for name in model["descriptors"]]
            score=inference_recipe(cues,model,original)
            if "score_quantile_mapping" in model:
                score=quantile_mapping_apply(score,model["score_quantile_mapping"])
        if not np.isfinite(score).all() or score.shape!=shape:
            raise RuntimeError("Invalid native BSDS export score "+path.name)
        # PNG is a terminal Berkeley adapter only; author maps and descriptor
        # scientific caches remain floating-point and SHA-verified.
        Image.fromarray(np.rint(np.clip(score,0,1)*255).astype(np.uint8),mode="L").save(
            target/(path.stem+".png"))
    print("STAGE24GL_BSDS_EXPORT_DONE",len(paths),args.variant,flush=True)

def _bootstrap_historical_stage24(out):
    """No evaluator re-run: consume archived Stage24 200×99 Berkeley counts."""
    archived=ROOT/"results/paper_a_evidence/stage24/official_bsds/per_image_threshold_counts.csv"
    previous=ROOT/"results/local_dev/stage24_residual_suppression/summary.json"
    if not archived.is_file() or not previous.is_file():
        write_json(out/"historical_stage24_bootstrap_guard.json",{
            "status":"PENDING_ARCHIVED_BERKELEY_COUNTS"})
        return
    summary=json.loads(previous.read_text(encoding="utf-8")).get("official_evaluation",{})
    methods=load_archived_counts(archived)
    comparisons=[("stage24_residual_suppression","incumbent_compact_positive_choquet")]
    analysis=paired_bootstrap(methods,comparisons,summary,seed=20261104,replicates=1000)
    hist=out/"historical_stage24_paired_bootstrap"
    write_results(hist,analysis)
    write_json(out/"historical_stage24_bootstrap_guard.json",{
        "status":"complete" if analysis["confidence_intervals"] else "BLOCKED_REFERENCE_MISMATCH",
        "integrity_checks":analysis["verification"],
        "contrasts":analysis["comparisons"]})


def _bootstrap_new_official(out,summary):
    source=ROOT/"results/official_eval"/EXPERIMENT
    method_maps=load_official_counts(source)
    tests=[
        ("stage24gl_winner","stage24gl_identity"),
        ("stage24gl_winner","stage24gl_winner_quantile"),
        ("stage24gl_identity","stage24gl_identity_quantile"),
        ("stage24gl_winner","stage24gl_best_single"),
        ("stage24gl_winner","incumbent_compact_positive_choquet"),
        ("stage24gl_pair04_logistic","stage24gl_pair04_weighted"),
    ]
    for meth in sorted(method_maps):
        if meth.startswith("lit_") and meth.endswith("_fusion"):
            base=meth[:-7]+"_baseline"
            if base in method_maps: tests.append((meth,base))
    analysis=paired_bootstrap(method_maps,tests,summary,seed=20261104,replicates=1000)
    write_results(out,analysis)
    return analysis


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
    analysis=_bootstrap_new_official(out,data)
    if not analysis["confidence_intervals"]:
        print("WARNING_BERKELEY_BOOTSTRAP_BLOCKED: reference verification mismatch",
              flush=True)


def _float_literature_score(entry, expected_shape=None):
    """Only author-native float32 NPY, with hash. Never accept 8-bit PNG."""
    path = Path(entry["score_path"])
    if not path.is_absolute():
        path = ROOT / path
    if path.suffix.lower() != ".npy" or not path.is_file():
        raise RuntimeError("Native float detector map missing: " + str(path))
    if sha256_file(path) != entry["sha256"]:
        raise RuntimeError("Detector float map SHA256 mismatch: " + str(path))
    score = np.load(path, allow_pickle=False)
    if score.ndim != 2 or score.dtype != np.float32 or not np.isfinite(score).all():
        raise RuntimeError("Detector map must be finite 2-D float32: " + str(path))
    if expected_shape is not None and score.shape != tuple(expected_shape):
        raise RuntimeError("Literature map/native GT geometry mismatch: " + str(path))
    return score


def run_literature(args, items, maps, out):
    """Recertify float literature baselines, matched complement/aggregation ablations.

    Transfer configurations are fixed by the UDED-only main campaign.
    The official BSDS exporter consumes author/native float scores and never
    uses BSDS labels in fitting. Missing author maps are an explicit guard.
    """
    manifest = Path(args.literature_manifest)
    if not manifest.is_file():
        write_json(out/"literature_transfer_guard.json",{
            "status":"guarded","reason":"Author/native float detector manifest not provided",
            "required_manifest_fields":["dataset","split","method","image_id","score_path","sha256"],
            "quantized_png_permitted":False})
        return
    frozen_path=out/"frozen_models.json"
    if not frozen_path.exists():
        raise RuntimeError("First freeze the UDED-only Stage24G-L recipe")
    winner=json.loads(frozen_path.read_text(encoding="utf-8"))["models"]["winner"]
    entries=json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(entries,list) or not entries:
        raise ValueError("Literature manifest must be a nonempty JSON array")
    id_to_item={i["id"]:i for i in items}
    uded=defaultdict(dict)
    bsds=defaultdict(dict)
    for e in entries:
        for field in ("dataset","split","method","image_id","score_path","sha256"):
            if not e.get(field):
                raise ValueError("Incomplete literature manifest entry: "+field)
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", str(e["method"])):
            raise ValueError("Unsafe or ambiguous detector method identifier")
        if e["dataset"]=="UDED" and e["split"]=="selection_overlap_clean":
            if e["image_id"] not in id_to_item:
                raise ValueError("Unknown UDED ID in literature manifest")
            score=_float_literature_score(e,id_to_item[e["image_id"]]["gt"].shape)
            if e["image_id"] in uded[e["method"]]:
                raise RuntimeError("Duplicate literature UDED image")
            uded[e["method"]][e["image_id"]]=score
        elif e["dataset"]=="BSDS500" and e["split"]=="val":
            if e["image_id"] in bsds[e["method"]]:
                raise RuntimeError("Duplicate literature BSDS image")
            # Load/check lazily against BSDS image native dimensions in exporter.
            bsds[e["method"]][e["image_id"]]=e
        else:
            raise ValueError("Unsupported detector manifest scope; only UDED selection and BSDS val")
    if not uded:
        raise RuntimeError("No native float UDED literature detectors")
    historical_cues={
        "compass":"gabor4_scale_persistence","sco":"gabor4_scale_persistence",
        "sed":"halfdisc_distribution_contrast","qfrd":"fh_region_boundary",
    }
    from src.stage24_recertification_cv import fit_and_score, memberships_on_split, clear_group_cache
    from src.stage24_recertification_ops import fit_aggregator,apply_aggregator
    from src.stage24_integrity import aggregate_counts
    from src.stage24_residual import fit_residual_gate
    all_result=[]; per_image=[]; frozen_lit={}
    current_manifest=json.loads((out/"official_eval_manifest.json").read_text(encoding="utf-8"))
    methods_heldout=[]
    for method,entry_maps in sorted(uded.items()):
        if set(entry_maps)!=set(id_to_item):
            raise RuntimeError("Incomplete 14 UDED images for detector: "+method)
        cue=historical_cues.get(method.lower(),winner["descriptors"][0])
        source=[entry_maps[item["id"]] for item in items]
        key="literature_"+method
        extended={**maps,key:source}
        group=(key,cue)
        for repeat,fold,train,valid in _make_repeated_folds(14,3,5,SEED):
            clear_group_cache()
            fid=f"r{repeat+1}_f{fold+1}"
            cp=out/"literature_folds"/method/(fid+".json")
            if cp.exists():
                result=json.loads(cp.read_text(encoding="utf-8"))
            else:
                result=[]
                # Individual native-float detector baseline, on the SAME folds.
                from src.stage24_recertification_ops import thin_score, binary_map
                from src.stage24_integrity import aggregate_counts
                for mode in TRANSFER_MODES:
                    tt,_=choose_threshold([source[int(i)] for i in train],
                        [items[int(i)]["gt"] for i in train],
                        [items[int(i)]["img"] for i in train],mode,
                        count=args.thresholds)
                    counts=[];individual=[]
                    for i in valid:
                        idx=int(i)
                        c=one_to_one_boundary_counts(
                            binary_map(thin_score(source[idx],mode,items[idx]["img"]),tt,mode),
                            items[idx]["gt"])
                        counts.append(c)
                        individual.append({"method":method,"fold":fid,"image_id":items[idx]["id"],
                            "group":key,"aggregator":"detector_baseline",
                            "thinning":mode,"suppressor":"identity","strength":1.,
                            "threshold":tt,"tp":c.tp,"fp":c.fp,"fn":c.fn,
                            "precision":c.precision,"recall":c.recall,"F1":c.f1})
                    total=aggregate_counts(counts)
                    result.append({"group":key,"arity":1,"aggregator":"detector_baseline",
                        "suppressor":"identity","strength":1.,"thinning":mode,
                        "method":method,"fold":fid,"threshold":tt,
                        "validation_F1":total.f1,"validation_precision":total.precision,
                        "validation_recall":total.recall,
                        "tp":total.tp,"fp":total.fp,"fn":total.fn,
                        "per_image":individual})
                for ag in AGGREGATORS:
                    for mode in TRANSFER_MODES:
                        candidate=fit_and_score(group,ag,items,extended,train,valid,mode,
                              count=args.thresholds,
                              seed=deterministic_seed(SEED,"literature",method,fid,ag,mode))
                        candidate.pop("model")
                        candidate["method"]=method;candidate["fold"]=fid
                        result.append(candidate)
                # Isolate suppression for fixed preselected aggregator/mode.
                for sup in (("identity",1.0),tuple(winner["suppression"])):
                    candidate=fit_and_score(group,winner["aggregator"]["family"],
                          items,extended,train,valid,winner["thinning"],
                          count=args.thresholds,
                          seed=deterministic_seed(SEED,"literature_supp",method,fid),
                          suppression=sup)
                    candidate.pop("model")
                    candidate["method"]=method;candidate["fold"]=fid
                    result.append(candidate)
                write_json(cp,result)
            for row in result:
                details=row.pop("per_image",[]) if "per_image" in row else []
                per_image.extend([{"method":method,"fold":fid,**x} for x in details])
                all_result.append(row)
        # Freeze transferred D+C model with fixed UDED-selected operator and mode.
        gt=[i["gt"] for i in items]
        train=np.arange(len(items))
        mem,membership=memberships_on_split(group,extended,gt,train)
        agg=fit_aggregator(winner["aggregator"]["family"],membership,gt,train,
                      seed=deterministic_seed(SEED,"litfreeze",method))
        base=[apply_aggregator(x,agg) for x in membership]
        gate=fit_residual_gate(base,membership,gt,train,
              seed=deterministic_seed(SEED,"litgate",method)) if winner["suppression"][0]=="learned_gate" else None
        supp=tuple(winner["suppression"])
        scores=[apply_suppressor(base[i],membership[i],kind=supp[0],
                                 parameter=supp[1],gate_model=gate) for i in train]
        threshold,_=choose_threshold(scores,gt,[it["img"] for it in items],
                                     winner["thinning"],count=41)
        model=serialize_model(group,mem,agg,supp,winner["thinning"],gate)
        model["threshold"]=threshold
        model["selected_without_BSDS_labels"]=True
        flat=np.concatenate([x.ravel() for x in source])
        lo,hi=np.quantile(flat,[0.01,.99])
        if hi<=lo: raise RuntimeError("Literature baseline UDED calibration is degenerate")
        frozen_lit[method]={"cue":cue,"model":model,
                             "baseline_uded_quantiles": [float(lo),float(hi)],
                             "ready_for_bsds":len(bsds.get(method,{}))==100}
        if len(bsds.get(method,{}))==100:
            for role in ("baseline","fusion"):
                # Only registered native float author detector maps are allowed.
                safe="".join(c if c.isalnum() else "_" for c in method)
                variant="literature::"+method+"::"+role
                method_name="lit_"+safe+"_"+role
                if any(x.get("name")==method_name for x in current_manifest["methods"]):
                    continue
                current_manifest["methods"].append({
                    "name":method_name,
                    "export":{"script":"run_stage24_paper_a_recertification.py",
                              "args":["--export-bsds","--variant",variant,
                                      "--image-dir","{image_dir}","--output-dir","{output_dir}",
                                      "--split","{split}","--out",str(out.relative_to(ROOT)).replace("\\","/"),
                                      "--literature-manifest",str(manifest)]}})
            methods_heldout.append(method)
    write_csv(out/"literature_aggregator_landscape_fold.csv",all_result)
    write_csv(out/"literature_aggregator_landscape_per_image.csv",per_image)
    write_json(out/"frozen_literature_models.json",frozen_lit)
    write_json(out/"official_eval_manifest.json",current_manifest)
    write_json(out/"literature_transfer_guard.json",{
        "status":"ready_for_official_bsds_val" if len(methods_heldout)==len(uded)
                 else "partial_author_native_float_maps",
        "uded_methods":sorted(uded),
        "bsds_val_complete_methods":methods_heldout,
        "required_per_method_bsds_float_maps":100,
        "selection":"UDED-only main recipe; all literature alternatives reported as exploratory",
        "quantized_png_permitted":False})

def stats_and_claims(out):
    """Image-paired tests with one observation per unique UDED image.

    Repeated folds are averaged within the same image; no BSDS aggregate metric
    is treated as 100 independent ODS values.
    """
    def read_csv(name):
        path=out/name
        if not path.is_file():return []
        with path.open(encoding="utf-8",newline="") as f:
            return list(csv.DictReader(f))

    rows=read_csv("suppressor_ablation_per_image.csv")
    by=defaultdict(dict)
    for r in rows:
        key=(r["fold_id"],r["group"],r["aggregator"],r["thinning"],r["image_id"])
        by[key][(r["suppressor"],r["strength"])]=float(r["F1"])
    per_img=defaultdict(list)
    for key,rec in by.items():
        identity=rec.get(("identity","1.0"))
        if identity is None:continue
        for (name,strength),val in rec.items():
            if name!="identity":
                per_img[(*key[1:4],name,strength,key[-1])].append(val-identity)
    per_test=defaultdict(dict)
    for (*group,name,strength,image),vals in per_img.items():
        per_test[(*group,name,strength)][image]=float(np.mean(vals))
    tests=[]
    for key,images in sorted(per_test.items()):
        dif=np.asarray(list(images.values()))
        if len(dif)<6 or np.allclose(dif,0):continue
        try:p=float(wilcoxon(dif,alternative="two-sided",zero_method="wilcox").pvalue)
        except ValueError:continue
        tests.append({"group":key[0],"aggregator":key[1],"thinning":key[2],
                      "suppressor":key[3],"strength":key[4],
                      "n_unique_images":len(dif),"mean_delta_F1":float(np.mean(dif)),
                      "median_delta_F1":float(np.median(dif)),
                      "p_unadjusted":p,
                      "unit":"unique image (repeat-average); exploratory"})
    tests.sort(key=lambda r:r["p_unadjusted"])
    running=0.
    for j,r in enumerate(tests):
        running=max(running,min(1.,(len(tests)-j)*r["p_unadjusted"]))
        r["p_holm"]=running
    write_csv(out/"statistical_tests_exploratory.csv",tests)

    landscape=read_csv("aggregator_landscape_per_image.csv")
    pivot=defaultdict(list)
    for r in landscape:
        pivot[(r["group"],r["thinning"],r["aggregator"],r["image_id"])].append(float(r["F1"]))
    by_group=defaultdict(dict)
    for (group,mode,agg,image),vals in pivot.items():
        by_group[(group,mode)][(agg,image)]=float(np.mean(vals))
    friedman=[]
    aggregate=[]
    family_shortlist=("equal_mean","minimum","maximum","nonnegative_logistic",
                      "choquet_positive_2add","choquet_signed_2add",
                      "sugeno_additive","choquet_generalized_055")
    for (group,mode),arr in sorted(by_group.items()):
        images=sorted({im for _,im in arr})
        names=[n for n in family_shortlist if all((n,im) in arr for im in images)]
        if len(names)>=3 and len(images)>=6:
            test=friedmanchisquare(*[np.asarray([arr[(n,im)] for im in images]) for n in names])
            friedman.append({"group":group,"thinning":mode,"n_images":len(images),
                            "operators":"|".join(names),"statistic":float(test.statistic),
                            "p_unadjusted":float(test.pvalue),"unit":"unique UDED image"})
        for name in AGGREGATORS:
            values=[arr[(name,im)] for im in images if (name,im) in arr]
            if not values:continue
            aggregate.append({"group":group,"thinning":mode,"aggregator":name,
                              "n_unique_images":len(values),
                              "mean_image_F1":float(np.mean(values)),
                              "median_image_F1":float(np.median(values)),
                              "std_image_F1":float(np.std(values)),
                              "descriptive_only":True})
    friedman.sort(key=lambda r:r["p_unadjusted"])
    running=0.
    for i,r in enumerate(friedman):
        running=max(running,min(1.,(len(friedman)-i)*r["p_unadjusted"]))
        r["p_holm"]=running
    write_csv(out/"friedman_aggregator_image_tests.csv",friedman)
    write_csv(out/"paper_a_aggregator_group_descriptives.csv",aggregate)

    official_path=out/"official_bsds_summary.json"
    official=json.loads(official_path.read_text(encoding="utf-8")) if official_path.is_file() else None
    guardpath=out/"literature_transfer_guard.json"
    literature=json.loads(guardpath.read_text(encoding="utf-8")) if guardpath.exists() else {}
    selected=read_csv("inner_selected_heldout.csv")
    complete=(len(selected)==15)
    claims=[
      {"claim":"Native GT correctness","status":"PROTOCOL_VERIFIED"},
      {"claim":"Full 78-pair corrected proxy landscape","status":"COMPLETED" if complete else "INCOMPLETE_CV"},
      {"claim":"Pair/triple and aggregator factorial","status":"EXPLORATORY_COMPLETE" if complete else "INCOMPLETE_CV"},
      {"claim":"Matched suppressor ablation","status":"HELDOUT_COMPARISONS_AVAILABLE" if tests else "PENDING"},
      {"claim":"BSDS validation","status":"DEVELOPMENT_ONLY" if official else "PENDING"},
      {"claim":"Bootstrap Berkeley ODS/OIS/AP 95% CI","status":"RECALCULATED_WITH_REFERENCES"
       if (out/"bootstrap_paired_ods_ois_ap.csv").is_file() else "BLOCKED_OR_PENDING"},
      {"claim":"Scores AP quantile-calibrated","status":"BSDS_DEVELOPMENT_DIAGNOSTIC"
       if official else "PENDING"},
      {"claim":"BSDS reference reproduction","status":"BLOCKED_UNTIL_INDEPENDENT_REFERENCE"},
      {"claim":"Literature detector transfer","status":literature.get("status","GUARDED")},
      {"claim":"Stage23D same-score GT correction","status":"REQUIRES_EXACT_HISTORICAL_IMPLEMENTATION"},
      {"claim":"Exact Paper A generalized Choquet operators","status":"REQUIRES_MANUSCRIPT_FORMULA_AUDIT"},
      {"claim":"Publication/SOTA","status":"BLOCKED_UNTIL_PROTECTED_BENCHMARK_GATE"},
    ]
    write_csv(out/"claim_status.csv",claims)
    (out/"PAPER_A_METHODS_RESULTS_STATUS.md").write_text(
        "# Stage 24G-L — status para Paper A\n\n"
        "Os GTs nativos foram preservados; as comparacoes de agregadores e "
        "suppressors usam os mesmos folds e thresholds ajustados somente no treino.\n\n"
        "A recertificacao inclui raw, NMS orientado pela imagem e thinning binario "
        "apenas diagnostico UDED. O BSDS continua com thinpb=true oficial; "
        "nao equiparar os algoritmos de afinamento.\n\n"
        "Os scores Stage23D e Stage24 usam formulas diferentes; G0 isola geometria "
        "somente na formula Stage24.\n\n"
        "Os testes estatisticos usam medias por imagem entre repeticoes e sao "
        "exploratorios; os folds repetidos nao sao 15 observacoes independentes.\n\n"
        "O BSDS val e desenvolvimento. Sem reproducao independente de referencia "
        "e teste protegido multi-benchmark, SOTA/final claims estao bloqueados.\n\n"
        "Consultar claim_status.csv, final_claim_guard.json e literature_transfer_guard.json.\n",
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
    ap.add_argument("--variant",default="winner")
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
    if not bsds_bootstrap_contract() or not historical_formula_contract():
        raise RuntimeError('Scientific bootstrap or historical-formula contract failed')
    write_json(out/"preflight.json",{"status":"passed","n_tests":len(checks),
                "checks":checks,"inherited_R0":True,"GT":"native_never_resized",
                "berkeley_thinpb_not_equated_to_python_thinning":True})
    if args.phase in ("all","preflight","l"):
        _bootstrap_historical_stage24(out)
    if args.phase=="preflight":
        print("STAGE24GL_PREFLIGHT_OK")
        return 0
    if args.phase in ("all","g0","g","h","i"):
        items,maps,manifest,provenance=local_dataset(args)
        write_json(out/"native_dataset_manifest.json",manifest)
        write_csv(out/"descriptor_provenance.csv",provenance)
        write_csv(out/"descriptor_scale_audit.csv",scale_audit(items))
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
