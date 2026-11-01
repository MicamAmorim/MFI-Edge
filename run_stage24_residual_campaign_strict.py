from __future__ import annotations

"""Strict Stage-24 entry point.

Hardens the base Stage-24 runner so every aggregator/suppressor threshold used
for scientific selection is chosen with the same canonical one-to-one matcher.
It also records the official-Berkeley reference-reproduction guard after the
campaign.  The BSDS exporter remains the frozen, GT-blind base exporter.

This entry point also owns the terminal progress display.  Progress reporting
is presentation-only and does not alter scientific selection, seeds, caches,
thresholds, checkpoints, or output artifacts.
"""

from pathlib import Path
import json
import sys
import numpy as np

import run_stage24_residual_campaign as base
from src.stage24_integrity import deterministic_seed, evaluate_scores, select_threshold
from src.stage24_progress import TerminalProgress
from src.stage24_residual import (
    aggregate_memberships,
    apply_membership,
    apply_suppressor,
    fit_membership,
    fit_nonnegative_fusion,
    fit_residual_gate,
    model_hash,
)


PROGRESS = TerminalProgress()
_CURRENT_FOLD = ""
_ORIGINAL_FREEZE = base.freeze
_ORIGINAL_ANATOMY = base.anatomy
_ORIGINAL_OFFICIAL_EVAL = base.official_eval


def _progress_detail(text: str) -> None:
    prefix = f"{_CURRENT_FOLD} | " if _CURRENT_FOLD else ""
    PROGRESS.detail(prefix + text)


def strict_screen_recipe(pair_maps, gts, train, seed):
    _progress_detail("fit memberships")
    membership = fit_membership(pair_maps, gts, train)
    memberships = [
        apply_membership([pair_maps[0][i], pair_maps[1][i]], membership)
        for i in range(len(gts))
    ]
    _progress_detail("fit nonnegative logistic fusion")
    logistic = fit_nonnegative_fusion(
        pair_maps,
        gts,
        train,
        membership,
        seed=deterministic_seed(seed, "fusion"),
    )
    train_gts = [gts[int(i)] for i in train]

    aggregators = (
        "equal_mean",
        "minimum",
        "maximum",
        "median",
        "nonnegative_logistic",
    )
    aggregate_candidates = []
    for pos, aggregator in enumerate(aggregators, 1):
        _progress_detail(f"aggregator {pos}/{len(aggregators)}: {aggregator}")
        scores = [aggregate_memberships(m, aggregator, logistic) for m in memberships]
        train_scores = [scores[int(i)] for i in train]
        selected = select_threshold(
            train_scores,
            train_gts,
            count=41,
            tolerance_ratio=base.TOL,
        )
        aggregate_candidates.append(
            ((float(selected["F1"]), float(selected["precision"]), aggregator), aggregator, scores)
        )
    _, aggregator, base_scores = max(aggregate_candidates, key=lambda x: x[0])

    _progress_detail(f"fit residual gate after {aggregator}")
    gate = fit_residual_gate(
        base_scores,
        memberships,
        gts,
        train,
        seed=deterministic_seed(seed, "gate"),
    )
    suppressors = (
        ("identity", 1.0),
        ("local_coherence", 2.0),
        ("local_coherence", 4.0),
        ("disagreement", 0.5),
        ("disagreement", 1.0),
        ("compress", 1.5),
        ("learned_gate", 0.5),
        ("learned_gate", 1.0),
        ("learned_gate", 2.0),
    )
    suppressor_candidates = []
    for pos, (kind, parameter) in enumerate(suppressors, 1):
        _progress_detail(f"suppressor {pos}/{len(suppressors)}: {kind}({parameter:g})")
        scores = [
            apply_suppressor(
                base_scores[i],
                memberships[i],
                kind=kind,
                parameter=parameter,
                gate_model=gate,
            )
            for i in range(len(gts))
        ]
        train_scores = [scores[int(i)] for i in train]
        selected = select_threshold(
            train_scores,
            train_gts,
            count=41,
            tolerance_ratio=base.TOL,
        )
        suppressor_candidates.append(
            (
                (
                    float(selected["F1"]),
                    float(selected["precision"]),
                    kind,
                    -float(parameter),
                ),
                kind,
                float(parameter),
                float(selected["threshold"]),
            )
        )
    _, kind, parameter, threshold = max(suppressor_candidates, key=lambda x: x[0])

    _progress_detail("canonical threshold for selected recipe")
    final_scores = []
    for i in range(len(gts)):
        fusion = aggregate_memberships(memberships[i], aggregator, logistic)
        final_scores.append(
            apply_suppressor(
                fusion,
                memberships[i],
                kind=kind,
                parameter=parameter,
                gate_model=gate,
            )
        )
    train_selected = select_threshold(
        [final_scores[int(i)] for i in train],
        train_gts,
        count=41,
        tolerance_ratio=base.TOL,
    )
    recipe = {
        "aggregator": aggregator,
        "suppressor": kind,
        "parameter": parameter,
        "threshold": float(train_selected["threshold"]),
        "train_F1": float(train_selected["F1"]),
        "train_precision": float(train_selected["precision"]),
        "train_recall": float(train_selected["recall"]),
        "threshold_contract": "canonical_one_to_one_matcher_only",
    }
    return recipe, membership, logistic, gate


def progress_load_maps(items, cache_root, stop_file):
    maps, provenance = {d: [] for d in base.DESCRIPTOR_IDS}, []
    total = len(items) * len(base.DESCRIPTOR_IDS)
    done = 0
    PROGRESS.update("maps", 0, total, "preparando mapas float")
    for item in items:
        if stop_file.exists():
            raise KeyboardInterrupt
        for descriptor_id in base.DESCRIPTOR_IDS:
            if stop_file.exists():
                raise KeyboardInterrupt
            PROGRESS.update(
                "maps",
                done,
                total,
                f"{item['id']} | {descriptor_id}",
            )
            value, row = base.descriptor_native(item, descriptor_id, cache_root)
            maps[descriptor_id].append(value)
            provenance.append(row)
            done += 1
            PROGRESS.update(
                "maps",
                done,
                total,
                f"{item['id']} | {descriptor_id}",
            )
    return maps, provenance


def progress_nested_cv(items, maps, out, stop_file):
    global _CURRENT_FOLD
    gts = [x["gt"] for x in items]
    rows = []
    fold_dir = out / "folds"
    fold_dir.mkdir(parents=True, exist_ok=True)
    folds = list(base._make_repeated_folds(len(items), 3, 5, base.SEED))
    total = len(folds)
    PROGRESS.update("cv", 0, total, "iniciando nested CV leakage-free")

    for position, (repeat, fold, train, valid) in enumerate(folds, 1):
        fid = f"r{repeat+1}_f{fold+1}"
        _CURRENT_FOLD = fid
        result_path = fold_dir / f"{fid}.json"
        if result_path.is_file():
            rows.append(json.loads(result_path.read_text(encoding="utf-8")))
            PROGRESS.update("cv", position, total, f"{fid} | checkpoint reutilizado")
            continue
        if stop_file.exists():
            PROGRESS.detail(f"{fid} | parada segura solicitada")
            break

        PROGRESS.update("cv", position - 1, total, f"{fid} | selecionar par no outer-train")
        pair, pair_screen = base.select_pair(maps, gts, train)
        base.write_csv(fold_dir / f"{fid}_pair_screen.csv", pair_screen)
        pair_maps = [maps[pair[0]], maps[pair[1]]]

        PROGRESS.detail(f"{fid} | receita: {pair[0]} + {pair[1]}")
        recipe, membership, logistic, gate = strict_screen_recipe(
            pair_maps,
            gts,
            train,
            deterministic_seed(base.SEED, repeat, fold),
        )
        _, _, final = base.apply_recipe(pair_maps, membership, logistic, gate, recipe)
        validation_scores = [final[int(i)] for i in valid]
        validation_gts = [gts[int(i)] for i in valid]
        counts, _ = evaluate_scores(
            validation_scores,
            validation_gts,
            recipe["threshold"],
            tolerance_ratio=base.TOL,
        )
        row = {
            "repeat": repeat + 1,
            "fold": fold + 1,
            "pair": list(pair),
            "aggregator": recipe["aggregator"],
            "suppressor": recipe["suppressor"],
            "parameter": recipe["parameter"],
            "threshold": recipe["threshold"],
            "train_F1": recipe["train_F1"],
            "validation_precision": counts.precision,
            "validation_recall": counts.recall,
            "validation_F1": counts.f1,
            "tp": counts.tp,
            "fp": counts.fp,
            "fn": counts.fn,
            "valid_ids": [items[int(i)]["id"] for i in valid],
            "model_sha256": model_hash(pair, recipe, membership, logistic, gate),
        }
        base.write_json(result_path, row)
        rows.append(row)
        PROGRESS.update(
            "cv",
            position,
            total,
            f"{fid} | F1={counts.f1:.4f} | {recipe['aggregator']} + {recipe['suppressor']}",
        )

    _CURRENT_FOLD = ""
    return rows


def progress_freeze(items, maps, rows, out):
    PROGRESS.update("freeze", 0, 1, "ajustando modelo final apenas no UDED")
    result = _ORIGINAL_FREEZE(items, maps, rows, out)
    PROGRESS.update("freeze", 1, 1, "modelo congelado")
    return result


def progress_anatomy(items, memberships, base_scores, final_scores, payload, out):
    PROGRESS.update("anatomy", 0, 1, "caracterizando residuos TP/FP")
    result = _ORIGINAL_ANATOMY(items, memberships, base_scores, final_scores, payload, out)
    PROGRESS.update("anatomy", 1, 1, f"{len(items)} imagens analisadas")
    return result


def progress_official_eval(out):
    PROGRESS.update("official", 0, 1, "handoff para Berkeley/reference hook")
    PROGRESS.newline()
    result = _ORIGINAL_OFFICIAL_EVAL(out)
    PROGRESS.update("official", 1, 1, "hook concluido")
    return result


def _find_reference_verified(obj) -> bool:
    if isinstance(obj, dict):
        if obj.get("reference_reproduction_verified") is True:
            return True
        return any(_find_reference_verified(v) for v in obj.values())
    if isinstance(obj, list):
        return any(_find_reference_verified(v) for v in obj)
    return False


def _record_final_claim_guard() -> None:
    summary_path = base.OUT_DEFAULT / "summary.json"
    if not summary_path.is_file():
        return
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    official = summary.get("official_evaluation")
    verified = _find_reference_verified(official)
    completed = isinstance(official, dict) and official.get("status") == "completed"
    summary["final_claim_guard"] = {
        "official_evaluation_completed": bool(completed),
        "reference_reproduction_verified": bool(verified),
        "final_claim_eligible": bool(completed and verified),
        "rule": (
            "BSDS validation can be reported as development evidence when completed, "
            "but final benchmark/SOTA claims remain blocked until the pinned official "
            "Berkeley path has reproduced its registered reference output."
        ),
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True, default=str), encoding="utf-8")


def main() -> int:
    base.screen_recipe = strict_screen_recipe
    base.load_maps = progress_load_maps
    base.nested_cv = progress_nested_cv
    base.freeze = progress_freeze
    base.anatomy = progress_anatomy
    base.official_eval = progress_official_eval

    try:
        rc = int(base.main())
    except BaseException:
        PROGRESS.newline()
        raise

    if "--export-bsds" not in sys.argv:
        _record_final_claim_guard()
        if base.STOP_DEFAULT.exists():
            PROGRESS.stop("parada segura registrada")
        elif rc == 0:
            detail = "concluido" if "--skip-official" not in sys.argv else "concluido (official skipped)"
            PROGRESS.finish(detail)
        else:
            PROGRESS.newline()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
