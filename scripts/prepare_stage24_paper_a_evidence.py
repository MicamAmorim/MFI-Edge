#!/usr/bin/env python3
"""Archive the completed Stage 24 evidence needed to audit Paper A.

Does not retrain, run MATLAB, commit, or push. Uses only Python stdlib.
Never copies descriptor caches, GTs, datasets, predictions, PNGs or MEX files.
"""
from __future__ import annotations
import argparse
import ast
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = "stage24_residual_suppression"
LOCAL = ROOT / "results/local_dev" / EXPERIMENT
EVAL = ROOT / "results/official_eval" / EXPERIMENT
OUT = ROOT / "results/paper_a_evidence/stage24"
CORE = (
    "summary.json", "nested_cv_folds.csv", "descriptor_provenance.csv",
    "residual_anatomy.csv", "frozen_model.json", "literature_transfer_guard.json",
    "official_eval_manifest.json",
)
MAX_COPY = 5 * 1024 * 1024


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()


def relative(path):
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def csv_read(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def csv_write(path, columns, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def json_write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False,
                               sort_keys=True) + "\n", encoding="utf-8")


class Evidence:
    def __init__(self):
        self.sources = []
        self.missing = []
        self.notes = []
        self.generated = []

    def source(self, p, role, dest=None, required=False):
        if not p.is_file():
            (self.missing if required else self.notes).append("Ausente: " + relative(p))
            return False
        item = {"source": relative(p), "role": role, "size_bytes": p.stat().st_size,
                "sha256": digest(p), "archived_as": relative(dest) if dest else ""}
        self.sources.append(item)
        return True

    def copy(self, p, dest, role, required=False):
        if not self.source(p, role, dest, required):
            return False
        if p.stat().st_size > MAX_COPY:
            self.notes.append("Grande demais para copia: " + relative(p))
            self.sources[-1]["archived_as"] = ""
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dest)
        if digest(p) != digest(dest):
            raise RuntimeError("Hash divergente: " + relative(p))
        return True

    def output(self, path):
        self.generated.append(path.relative_to(OUT).as_posix())


def folds_archive(ev):
    base = LOCAL / "folds"
    screens = sorted(base.glob("r*_f*_pair_screen.csv"))
    checkpoints = sorted(base.glob("r*_f*.json"))
    if len(screens) != 15 or len(checkpoints) != 15:
        raise RuntimeError("Esperados 15 pair screens e 15 fold JSONs; encontrados %s e %s" %
                           (len(screens), len(checkpoints)))
    by_pair = defaultdict(list)
    long_rows = []
    for f in screens:
        fid = f.stem.removesuffix("_pair_screen")
        rep, fold = (int(s[1:]) for s in fid.split("_"))
        rows = csv_read(f)
        if len(rows) != 78:
            raise RuntimeError("Esperados 78 pares em " + f.name)
        seen = set()
        for r in rows:
            pair = tuple(sorted((r["a"], r["b"])))
            if pair in seen:
                raise RuntimeError("Par duplicado em " + f.name)
            seen.add(pair)
            value = float(r["train_only_proxy"])
            by_pair[pair].append(value)
            long_rows.append({"repeat": rep, "fold": fold,
                              "descriptor_a": pair[0], "descriptor_b": pair[1],
                              "train_only_proxy": value})
        ev.copy(f, OUT / "folds" / f.name, "stage24_pair_screen", required=True)
    for f in checkpoints:
        ev.copy(f, OUT / "folds" / f.name, "stage24_fold_checkpoint", required=True)
    if len(by_pair) != 78 or any(len(v) != 15 for v in by_pair.values()):
        raise RuntimeError("Matriz de 78 pares x 15 folds incompleta")
    chosen = Counter()
    for r in csv_read(LOCAL / "nested_cv_folds.csv"):
        chosen[tuple(sorted(ast.literal_eval(r["pair"])))] += 1
    ranked = []
    for (a, b), s in by_pair.items():
        ranked.append({
            "descriptor_a": a, "descriptor_b": b,
            "score_mean": round(statistics.mean(s), 9),
            "score_std": round(statistics.pstdev(s), 9),
            "score_median": round(statistics.median(s), 9),
            "score_min": round(min(s), 9), "score_max": round(max(s), 9),
            "folds_scored": len(s), "folds_selected": chosen[(a, b)],
        })
    ranked.sort(key=lambda r: (-r["score_mean"], r["descriptor_a"], r["descriptor_b"]))
    for i, row in enumerate(ranked, 1):
        row["rank_mean_score"] = i
    p = OUT / "pair_scores_all_15_folds.csv"
    csv_write(p, ["repeat","fold","descriptor_a","descriptor_b","train_only_proxy"], long_rows)
    ev.output(p)
    p = OUT / "pair_scores_stage24_ranked.csv"
    csv_write(p, ["rank_mean_score","descriptor_a","descriptor_b","score_mean",
                  "score_std","score_median","score_min","score_max",
                  "folds_scored","folds_selected"], ranked)
    ev.output(p)
    return {"screens": 15, "fold_jsons": 15, "pairs": 78, "scores": len(long_rows)}


def official_archive(ev):
    summary = EVAL / "summary.json"
    if not ev.copy(summary, OUT / "official_bsds/summary.json",
                   "official_Berkeley_summary", required=True):
        return {"status": "absent"}
    data = json.loads(summary.read_text(encoding="utf-8"))
    if data.get("status") != "completed":
        raise RuntimeError("BSDS official summary nao foi concluido")
    methods = data.get("methods", {})
    if not methods:
        raise RuntimeError("BSDS official methods vazio")
    metrics, detail, index = [], [], []
    per_method = {}
    for method, info in sorted(methods.items()):
        metrics.append({"method": method, "split": data.get("split"),
                        "ODS": info.get("ODS"), "OIS": info.get("OIS"), "AP": info.get("AP"),
                        "ODS_precision": info.get("ODS_precision"),
                        "ODS_recall": info.get("ODS_recall"),
                        "OIS_precision": info.get("OIS_precision"),
                        "OIS_recall": info.get("OIS_recall")})
        folder = EVAL / "matlab" / method
        ev.copy(folder / "official_summary.json",
                OUT / "official_bsds/method_summaries" / (method + ".json"),
                "official_Berkeley_method_summary", required=True)
        files = sorted(folder.glob("*_ev1.txt"))
        per_method[method] = len(files)
        expected_n = int(info.get("n_images", 100))
        if len(files) != expected_n:
            ev.missing.append("%s: esperados %s arquivos de imagem; encontrados %s" %
                              (method, expected_n, len(files)))
        for f in files:
            iid = f.name[:-len("_ev1.txt")]
            ev.source(f, "Berkeley_per_image_threshold_source")
            cnt = 0
            for line in f.read_text(encoding="utf-8-sig", errors="replace").splitlines():
                line = line.strip()
                if not line or line[0] in "#%":
                    continue
                cells = line.split()
                if len(cells) != 5:
                    raise RuntimeError("BSDS espera 5 colunas em " + relative(f))
                for cell in cells:
                    float(cell)
                cnt += 1
                detail.append({"method": method, "image_id": iid, "threshold_index": cnt,
                               "threshold": cells[0], "cntR": cells[1], "sumR": cells[2],
                               "cntP": cells[3], "sumP": cells[4]})
            index.append({"method": method, "image_id": iid, "source": relative(f),
                          "sha256": digest(f), "bytes": f.stat().st_size,
                          "threshold_rows": cnt})
            if cnt != int(info.get("nthresh", 99)):
                ev.missing.append("Thresholds incompletos em " + relative(f))
        # Save extra compact evaluator reports, not predictions or MATLAB temp files.
        for p in sorted(folder.glob("*")):
            if (p.is_file() and p.suffix.lower() in (".csv", ".json", ".txt")
                    and not p.name.endswith("_ev1.txt")
                    and p.name != "official_summary.json"):
                ev.copy(p, OUT / "official_bsds/other_outputs" / method / p.name,
                        "Berkeley_aggregate_report")
    p = OUT / "official_bsds/method_metrics.csv"
    csv_write(p, ["method","split","ODS","OIS","AP","ODS_precision",
                  "ODS_recall","OIS_precision","OIS_recall"], metrics)
    ev.output(p)
    p = OUT / "official_bsds/per_image_threshold_counts.csv"
    csv_write(p, ["method","image_id","threshold_index","threshold",
                  "cntR","sumR","cntP","sumP"], detail)
    ev.output(p)
    p = OUT / "official_bsds/per_image_source_manifest.csv"
    csv_write(p, ["method","image_id","source","sha256","bytes","threshold_rows"], index)
    ev.output(p)
    return {"status": "completed", "methods": per_method,
            "threshold_rows": len(detail), "split": data.get("split"),
            "reference_reproduction_verified":
                data.get("evaluator", {}).get("reference_reproduction_verified", False)}


def preflight_archive(ev):
    folder = ROOT / "results/local_dev/stage24r0_evaluation_integrity_preflight"
    if not folder.is_dir():
        ev.notes.append("Stage24R0 preflight nao encontrado")
        return
    for f in sorted(folder.rglob("*")):
        if f.is_file() and f.suffix.lower() in (".json", ".csv", ".txt", ".md"):
            ev.copy(f, OUT / "preflight" / f.relative_to(folder),
                    "stage24r0_integrity_preflight")


def legacy_archive(ev, include=True):
    if not include:
        return {"enabled": False}
    base = ROOT / "results/local_dev"
    dirs = sorted((d for d in base.glob("stage23*") if d.is_dir()), reverse=True)
    words = ("descriptor","complement","aggregat","rank","pair","triple",
             "transfer","fold","per_image","baseline","summary","statistic",
             "manifest","incumbent","candidate")
    copied, total = 0, 0
    for folder in dirs:
        for f in sorted(folder.rglob("*")):
            if not f.is_file() or f.suffix.lower() not in (".csv", ".json"):
                continue
            if any(x in f.parts for x in ("cache","maps","matlab","images",
                                          "predictions","masks")):
                continue
            if not any(w in f.name.lower() for w in words):
                continue
            size = f.stat().st_size
            if copied >= 100 or total + size > 20 * 1024 * 1024:
                ev.notes.append("Limite do arquivo Stage23 atingido: " + relative(f))
                continue
            if ev.copy(f, OUT / "historical_stage23_NOT_CORRECTED" /
                       f.relative_to(base), "legacy_stage23_uncorrected"):
                copied += 1
                total += size
    return {"enabled": True, "directories": len(dirs), "copied": copied,
            "bytes": total, "protocol": "HISTORICAL_NOT_CORRECTED"}




def historical_official_summaries(ev):
    """Preserve earlier official stage23 result summaries for Paper A comparison."""
    base = ROOT / "results/official_eval"
    if not base.is_dir():
        return {"available": False, "summaries": 0}
    count = 0
    for src in sorted(base.glob("*/summary.json")):
        exp = src.parent.name.lower()
        if not exp.startswith("stage23"):
            continue
        if count >= 30:
            ev.notes.append("Limite de 30 summaries historicos de official eval atingido")
            break
        if ev.copy(src, OUT / "historical_stage23_OFFICIAL_validation_summaries" /
                   src.parent.name / "summary.json", "historical_stage23_Berkeley_summary"):
            count += 1
    return {"available": True, "summaries": count,
            "note": "Historical model selection/protocol; not a new corrected-GT experiment"}

def cache_metadata_archive(ev):
    """Retain Stage24 float-map identity and hashes, never binary .npy maps."""
    folder = ROOT / "cache/local_dev/stage24/descriptors"
    if not folder.is_dir():
        ev.notes.append("Metadados do cache Stage24 nao encontrados")
        return {"available": False}
    sources, rows = sorted(folder.rglob("*.json")), []
    if len(sources) > 1000:
        raise RuntimeError("Mais de 1000 sidecars: confira cache de descritores antes de arquivar")
    for src in sources:
        data = json.loads(src.read_text(encoding="utf-8"))
        ident = data.get("identity", {})
        binary = src.with_suffix(".npy")
        if binary.is_file() and data.get("artifact_sha256") != digest(binary):
            raise RuntimeError("Hash do mapa float divergente: " + relative(binary))
        ev.copy(src, OUT / "descriptor_cache_metadata" / src.relative_to(folder),
                "float_descriptor_sidecar_copy")
        rows.append({
            "dataset": ident.get("dataset"), "split": ident.get("split"),
            "image_id": ident.get("image_id"), "descriptor_id": ident.get("descriptor_id"),
            "native_shape": json.dumps(ident.get("native_shape")),
            "inference_shape": json.dumps(ident.get("inference_shape")),
            "dtype": data.get("dtype"), "map_sha256": data.get("artifact_sha256"),
            "sidecar_sha256": digest(src), "binary_exists_locally": binary.is_file(),
        })
    p = OUT / "descriptor_float_cache_manifest.csv"
    csv_write(p, ["dataset","split","image_id","descriptor_id","native_shape",
                  "inference_shape","dtype","map_sha256","sidecar_sha256",
                  "binary_exists_locally"], rows)
    ev.output(p)
    # Stage23 supplied verified float maps in 182/182 UDED cases.
    upstream = ROOT / "cache/local_dev/stage23/manifests"
    if upstream.is_dir():
        for src in sorted(upstream.glob("*descriptor*.jsonl")):
            ev.copy(src, OUT / "stage23_descriptor_cache_manifests" / src.name,
                    "historical_upstream_float_descriptor_manifest")
    return {"available": True, "sidecars": len(rows),
            "note": "metadata/hashes only; no floating-point map binaries"}

def finalize(ev, folds, official, historical):
    gaps = [
        ("individual_descriptor_corrected_heldout",
         "NOT_PRODUCED", "Stage24 nao avaliou individualmente os 13 descritores com GT nativo."),
        ("heldout_per_image_fold_counts",
         "NOT_PRODUCED", "Stage24 salvou TP/FP/FN agregados por fold, nao por imagem."),
        ("matched_identity_vs_suppressor_ablation",
         "NOT_PRODUCED", "residual_anatomy.csv registra pixels exatos, nao delta F1 one-to-one."),
        ("old_vs_new_same_complementarity_formula",
         "NOT_PRODUCED", "Scores Stage23D e Stage24 possuem formulas diferentes."),
        ("full_choquet_sugeno_owa_landscape",
         "NOT_PERFORMED", "Stage24 avaliou apenas cinco agregadores e pares."),
        ("triples_recertification",
         "NOT_PERFORMED", "Stage24 nao avaliou triplas."),
        ("literature_float_detector_transfer",
         "GUARDED", "Os mapas historicos PNG sao rejeitados para transferencia corrigida."),
        ("official_Berkeley_reference_reproduction",
         "PENDING", "Flag de reproducao independente nao verificada."),
        ("protected_BSDS_test",
         "NOT_PERFORMED", "A avaliacao Stage24 cobriu BSDS validation."),
    ]
    gaps_data = [{"item": a, "status": b, "reason": c} for a, b, c in gaps]
    p = OUT / "paper_a_evidence_gaps.json"
    json_write(p, gaps_data)
    ev.output(p)
    p = OUT / "source_provenance.csv"
    csv_write(p, ["source","role","size_bytes","sha256","archived_as"], ev.sources)
    ev.output(p)
    p = OUT / "archive_manifest.json"
    json_write(p, {"archive_schema": 1, "source_experiment": EXPERIMENT,
                   "not_a_new_experiment": True, "folds": folds,
                   "official": official, "historical_stage23": historical,
                   "source_count": len(ev.sources),
                   "missing_required": ev.missing, "notes": ev.notes,
                   "generated": sorted(ev.generated), "evidence_gaps": gaps_data})
    ev.output(p)
    p = OUT / "README.md"
    p.write_text("""# Stage 24 — evidencias para Paper A

Pacote gerado localmente sem rodar novamente a campanha.
Verifique archive_manifest.json e source_provenance.csv.

Arquivos principais:
- pair_scores_stage24_ranked.csv: ranking dos 78 pares com media, dispersao e frequencia.
- pair_scores_all_15_folds.csv: 1170 scores de treino por fold.
- folds/: 15 pair screens originais e 15 checkpoints.
- official_bsds/: resumo oficial e contagens Berkeley por imagem/threshold.
- stage24_additional/: manifest da geometria nativa e checkpoint.
- descriptor_cache_metadata/: identidade e SHA dos mapas float (sem .npy).
- preflight/: relatorios de integridade Stage24R0, se presentes.
- historical_stage23_NOT_CORRECTED/: registros antigos, identificados como legado.
- historical_stage23_OFFICIAL_validation_summaries/: summaries Berkeley antigos, se presentes.
- paper_a_evidence_gaps.json: metricas/ablacoes que AINDA NAO EXISTEM.

Os sete arquivos originais da Stage24 estao no commit 0c9af74 em
results/local_dev/stage24_residual_suppression.

ATENCAO: os scores Stage23D e Stage24 nao usam a mesma formula.
Nao calcule deltas numericos entre eles. Os dados Berkeley presentes
sao do split validation; a reproducao da referencia permanece pendente.
A consolidacao exclui os GTs, mapas float, PNGs, datasets e arquivos
temporarios. Os hashes ligam os registros aos arquivos originais locais.
""", encoding="utf-8")
    ev.output(p)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage", action="store_true",
                    help="git add somente pasta curada; nunca commit/push")
    ap.add_argument("--no-legacy", action="store_true",
                    help="nao copiar dados historicos Stage23")
    ap.add_argument("--allow-incomplete", action="store_true",
                    help="permitir fontes ausentes, devidamente registradas")
    ap.add_argument("--replace", action="store_true",
                    help="substituir pacote curado existente")
    args = ap.parse_args()
    if not (ROOT / ".git").exists():
        ap.error("Execute dentro de um checkout Git do MFI-Edge")
    if not (LOCAL / "summary.json").is_file():
        ap.error("summary.json da Stage24 nao existe")
    if json.loads((LOCAL / "summary.json").read_text(encoding="utf-8")).get("status") != "completed":
        ap.error("A Stage24 nao esta marcada completed")
    if OUT.is_symlink():
        ap.error("Destino nao pode ser symlink")
    if OUT.exists():
        if not args.replace:
            ap.error("Pacote ja existe. Use --replace para recriar apos revisao.")
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    ev = Evidence()
    for filename in CORE:
        ev.source(LOCAL / filename, "already_committed_stage24", required=True)
    for filename in ("native_dataset_manifest.json", "checkpoint.json"):
        ev.copy(LOCAL / filename, OUT / "stage24_additional" / filename,
                "stage24_native_manifest_or_checkpoint",
                required=(filename == "native_dataset_manifest.json"))
    preflight_archive(ev)
    cache_metadata_archive(ev)
    folds = folds_archive(ev)
    official = official_archive(ev)
    historical_official = historical_official_summaries(ev)
    historical = legacy_archive(ev, not args.no_legacy)
    historical["official_summaries"] = historical_official
    finalize(ev, folds, official, historical)
    files = [p for p in OUT.rglob("*") if p.is_file()]
    total = sum(p.stat().st_size for p in files)
    print("PACOTE:", relative(OUT), "| arquivos:", len(files),
          "| bytes:", total)
    print("PARES:", folds, "| BSDS:", official,
          "| HISTORICO:", historical)
    for miss in ev.missing:
        print("FONTE OBRIGATORIA AUSENTE:", miss)
    for note in ev.notes[:20]:
        print("AVISO:", note)
    if ev.missing and not args.allow_incomplete:
        print("Pacote parcial gerado, mas nao preparado para commit. Confira as fontes.",
              file=sys.stderr)
        return 2
    if args.stage:
        subprocess.run(["git", "add", "--", relative(OUT)],
                       cwd=ROOT, check=True)
        print("Arquivos curados adicionados ao staging. Revise com git diff --cached --stat")
    else:
        print("Nada foi staged. Para preparar staging, execute novamente com --stage --replace")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
