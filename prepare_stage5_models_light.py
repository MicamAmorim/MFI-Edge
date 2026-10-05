from __future__ import annotations

from pathlib import Path
import argparse
import gc
import json
import os
import time

import numpy as np
import pandas as pd

import benchmark_measure_competition as bmc
from src.fuzzy_measures import measure_registry


def atomic_csv(df, path):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    df.to_csv(tmp, index=False)
    os.replace(tmp, path)


def atomic_json(obj, path):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=2, default=bmc.json_safe), encoding='utf-8')
    os.replace(tmp, path)


def phase(out, status, **extra):
    atomic_json({'status': status, 'updated_unix': time.time(), **extra}, out/'progress.json')
    print(f'STAGE5_LIGHT PHASE {status}', flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--skip-full-capacity', action='store_true')
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    phase(out, 'started')

    if not (bmc.DATA/'validation'/'manifest.csv').exists():
        phase(out, 'error_missing_synthetic_validation')
        raise FileNotFoundError('Run synthetic_v2.py first')

    # Only the 40 validation images are prepared. The original Stage-5 script also
    # prepared 60 synthetic test images before persisting learned models, which is
    # unnecessary for UDED Stage-7 and caused avoidable memory pressure on 1 GB RAM.
    phase(out, 'loading_validation')
    val = bmc.load_split('validation')
    fit_raw, val_raw = val[:20], val[20:]

    phase(out, 'preparing_fit', n_images=len(fit_raw))
    fit, names = bmc.prepare(fit_raw)
    phase(out, 'preparing_selection', n_images=len(val_raw))
    select, _ = bmc.prepare(val_raw)

    learned_path = out/'learned_measures.json'
    context_path = out/'context_router.json'
    feature_path = out/'feature_names.json'

    if learned_path.exists() and context_path.exists() and feature_path.exists():
        phase(out, 'reusing_learned_capacities')
        learned = json.loads(learned_path.read_text(encoding='utf-8'))
        context_model = json.loads(context_path.read_text(encoding='utf-8'))
        names = json.loads(feature_path.read_text(encoding='utf-8'))
    else:
        phase(out, 'learning_capacities')
        learned, context_model = bmc.fit_learned_specs(
            fit, names, full_capacity=not args.skip_full_capacity
        )
        atomic_json(learned, learned_path)
        atomic_json(context_model, context_path)
        atomic_json(names, feature_path)
        phase(out, 'learned_capacities_checkpointed', n_learned=len(learned))

    specs = measure_registry(len(names), learned=learned)
    all_path = out/'validation_all.csv'
    old = pd.read_csv(all_path) if all_path.exists() and all_path.stat().st_size else pd.DataFrame()
    done = set(old.measure.astype(str).unique()) if len(old) else set()
    rows = old.to_dict('records') if len(old) else []
    phase(out, 'evaluating_measures', completed=len(done), total=len(specs))

    for i, spec in enumerate(specs, 1):
        name = str(spec['name'])
        if name in done:
            print(f'STAGE5_LIGHT SKIP [{i}/{len(specs)}] {name}', flush=True)
            continue
        print(f'STAGE5_LIGHT RUN [{i}/{len(specs)}] {name}', flush=True)
        local = []
        for rq in bmc.ROI_QS:
            met = bmc.evaluate_spec(spec, select, context_model, rq)
            local.append({'measure': name, 'measure_kind': spec.get('kind',''), 'roi_q': rq, **met})
        rows.extend(local)
        df = pd.DataFrame(rows)
        atomic_csv(df, all_path)
        best = (df.sort_values(['ODS','AP','OIS'], ascending=False)
                .groupby('measure', as_index=False).first()
                .sort_values(['ODS','AP','OIS'], ascending=False).reset_index(drop=True))
        atomic_csv(best, out/'validation_best_per_measure.csv')
        phase(out, 'evaluating_measures', completed=int(best.measure.nunique()),
              total=len(specs), current=name)
        gc.collect()

    df = pd.read_csv(all_path)
    best = (df.sort_values(['ODS','AP','OIS'], ascending=False)
            .groupby('measure', as_index=False).first()
            .sort_values(['ODS','AP','OIS'], ascending=False).reset_index(drop=True))
    atomic_csv(best, out/'validation_best_per_measure.csv')
    phase(out, 'complete', completed=int(best.measure.nunique()), total=len(specs))
    print('STAGE5_LIGHT_DONE', flush=True)
    print(best.head(10)[['measure','roi_q','ODS','OIS','AP']].to_string(index=False), flush=True)


if __name__ == '__main__':
    main()
