from __future__ import annotations

"""Audit whether nominally different MFI scales actually produce distinct maps.

Stage 11 exposed exact duplicates among several 3/5/7 descriptors in the
historical `oriented` feature mode.  This script compares that reproducibility
mode against the new scale-sensitive `oriented_ms` mode before signature
analysis is rerun.
"""

from pathlib import Path
import argparse
import itertools
import json
import numpy as np

from benchmark_uded import DEFAULT_UDED, SCALES, load_uded
from benchmark_uded_quick import resize_items
from prepare_uded_runtime import prepare_uded
from src.conditioning import apply_conditioning
from src.features import feature_scale_schedule
from src.pipeline import precompute_multiscale_features

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "results" / "local_dev" / "edge_signature_ms"


def ensure_uded(root: Path):
    if not (root / "test_pair.lst").exists():
        prepare_uded(root)
    return root


def audit_mode(img, mode: str, atol: float = 1e-7):
    pre, names = precompute_multiscale_features(img, SCALES, feature_mode=mode)
    by_scale = {int(w): np.asarray(X, np.float32) for w, X, _ in pre}
    rows=[]
    for di,name in enumerate(names):
        for a,b in itertools.combinations(SCALES,2):
            xa=by_scale[int(a)][...,di]
            xb=by_scale[int(b)][...,di]
            diff=float(np.max(np.abs(xa-xb)))
            mae=float(np.mean(np.abs(xa-xb)))
            rows.append({"descriptor":str(name),"scale_a":int(a),"scale_b":int(b),
                         "max_abs_diff":diff,"mean_abs_diff":mae,"exact_duplicate":bool(diff<=atol)})
    return rows


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--uded-root',default=str(DEFAULT_UDED))
    ap.add_argument('--out',default=str(DEFAULT_OUT))
    ap.add_argument('--max-side',type=int,default=256)
    ap.add_argument('--image-index',type=int,default=0)
    args=ap.parse_args()

    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    root=ensure_uded(Path(args.uded_root))
    raw=resize_items(load_uded(root),args.max_side)
    d=raw[int(args.image_index)%len(raw)]
    img=apply_conditioning(d['img'],'median',size=3)

    results={}
    for mode in ('oriented','oriented_ms'):
        rows=audit_mode(img,mode)
        results[mode]={
            'n_pairs':len(rows),
            'n_exact_duplicates':sum(int(r['exact_duplicate']) for r in rows),
            'duplicates':[r for r in rows if r['exact_duplicate']],
            'schedule':[feature_scale_schedule(int(s),mode) for s in SCALES],
            'rows':rows,
        }

    (out/'scale_audit.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
    lines=['# Multiscale descriptor audit','',f"Image: `{d['id']}`",'']
    for mode in ('oriented','oriented_ms'):
        r=results[mode]
        lines += [f'## {mode}','',f"Exact duplicate descriptor/scale pairs: **{r['n_exact_duplicates']} / {r['n_pairs']}**",'',
                  '| scale | sigma | structure rho | normal r1 | normal r2 | Gabor freq |',
                  '|---:|---:|---:|---:|---:|---:|']
        for s in r['schedule']:
            lines.append(f"| {s['window']} | {s['sigma']:.4f} | {s['structure_rho']:.4f} | {s['normal_radius_1']:.4f} | {s['normal_radius_2']:.4f} | {s['gabor_frequency']:.4f} |")
        lines += ['','Exact duplicate pairs:','']
        if r['duplicates']:
            for x in r['duplicates']:
                lines.append(f"- `{x['descriptor']}`: {x['scale_a']} == {x['scale_b']}")
        else:
            lines.append('- none')
        lines.append('')
    (out/'SCALE_AUDIT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('SCALE_AUDIT', {m:results[m]['n_exact_duplicates'] for m in results}, flush=True)
    print('SCALE_AUDIT_DONE', out, flush=True)


if __name__=='__main__':
    main()
