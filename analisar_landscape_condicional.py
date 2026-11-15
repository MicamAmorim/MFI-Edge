#!/usr/bin/env python3
"""Análise exploratória Stage24G–L, reutilizando métricas e mapas float congelados.

Não executa detectores, treinamento, escolha de limiares nem Berkeley MATLAB.
Não modifica arquivos científicos. Saídas novas são exclusivamente exploratórias.

Uso:
    python analisar_landscape_condicional.py --research-root C:\\...\\MFI-Edge --out .\\analise_condicional
    python analisar_landscape_condicional.py --research-root C:\\...\\MFI-Edge --out .\\analise_condicional --no-maps
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import itertools
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

DATA = Path('results/paper_a_evidence/stage24_image_groups')
REPRO = Path('results/paper_a_evidence/stage24gl')
ALIASES = {'owa_median': 'median', 'owa_optimistic': 'maximum',
           'owa_pessimistic': 'minimum', 'owa_centered': 'equal_mean'}
METHOD_CONTRASTS = [
    ('gabor4_scale_persistence|halfdisc_distribution_contrast', 'maximum', 'equal_mean'),
    ('gabor4_scale_persistence|halfdisc_distribution_contrast', 'nonnegative_logistic', 'equal_mean'),
    ('halfdisc_distribution_contrast|hessian_s7', 'choquet_signed_2add', 'equal_mean'),
    ('gabor4_scale_persistence|pmi_dependency_deficit|structure_tensor_coherence', 'median', 'equal_mean'),
    ('fh_region_boundary|halfdisc_distribution_contrast', 'equal_mean', 'best_member'),
]


def read_csv(path):
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def save_csv(path, rows, columns=None):
    if not rows:
        return
    columns = columns or list(rows[0])
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        w.writeheader(); w.writerows(rows)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for blk in iter(lambda: f.read(1024*1024), b''):
            h.update(blk)
    return h.hexdigest()


def mean(x):
    return float(np.mean(x))


def corr_rank(x, y):
    """Spearman descritivo, com rank médio para empates exatos."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    if len(x) < 4 or np.std(x) < 1e-15 or np.std(y) < 1e-15:
        return float('nan')
    def ranks(a):
        idx = np.argsort(a, kind='stable'); z = np.empty(len(a), float)
        k = 0
        while k < len(a):
            j = k+1
            while j < len(a) and abs(a[idx[j]] - a[idx[k]]) <= 1e-10:
                j += 1
            z[idx[k:j]] = (k+j+1)/2.0
            k = j
        return z
    return float(np.corrcoef(ranks(x), ranks(y))[0, 1])


def canonical(operator, arity):
    op = ALIASES.get(operator, operator)
    return 'equal_mean' if op == 'median' and arity == 2 else op


def load_reference(root):
    rows = read_csv(root / DATA / 'common_candidate_scores.csv')
    features = read_csv(root / DATA / 'image_features.csv')
    by_image = defaultdict(dict)
    groups = defaultdict(set)
    for r in rows:
        img, model = r['image_id'], r['model']
        if model in by_image[img]:
            raise ValueError(f'Modelo duplicado: {img} {model}')
        by_image[img][model] = float(r['mean_heldout_F1'])
        if '|' in model:
            group, op = model.split('::', 1)
            groups[group].add(op)
    ims = sorted(by_image)
    assert len({len(by_image[i]) for i in ims}) == 1, 'Cobertura desigual: usar somente universo comum'
    assert all(len(groups[g]) for g in groups)
    f = {x['image_id']: x for x in features}
    assert set(f) == set(ims), 'IDs das características não correspondem às métricas'
    return ims, by_image, groups, f


def summarize_u(root, out):
    ims, scores, groups, features = load_reference(root)
    all_rows, method_rows, stability = [], [], []
    n_fusion = 0
    for group, raw_ops in sorted(groups.items()):
        desc = group.split('|')
        arity = len(desc)
        assert 'equal_mean' in raw_ops, f'Sem controle média: {group}'
        canon_values = {}
        for img in ims:
            v = {}
            for op in raw_ops:
                name = canonical(op, arity)
                val = scores[img][group+'::'+op]
                if name in v and abs(v[name] - val) > 1e-9:
                    raise ValueError(f'Alias matemático não confere: {group}, {name}, {img}')
                v[name] = val
            canon_values[img] = v
        operators = sorted(canon_values[ims[0]])
        n_fusion += len(operators)
        assert all(set(canon_values[i]) == set(operators) for i in ims)
        ranks = []
        votes = Counter()
        for img in ims:
            v = canon_values[img]
            best = max(v.values())
            winners = [op for op in operators if v[op] >= best-1e-10]
            for op in winners:
                votes[op] += 1.0/len(winners)
            ranks.append([v[op] for op in operators])
            best_member = max(scores[img][d+'::single'] for d in desc)
            for op in operators:
                value = v[op]
                all_rows.append({
                    'dataset': 'UDED', 'image_id': img, 'group': group, 'arity': arity,
                    'aggregator': op, 'F1_heldout_mean5': value,
                    'control_equal_mean_F1': v['equal_mean'],
                    'delta_F1_vs_equal_mean': value - v['equal_mean'],
                    'retrospective_best_member_F1': best_member,
                    'delta_vs_retrospective_best_member': value - best_member,
                    'criterion': 'same image, same group, NMS, identity, legacy sigmoid; 5 heldout repeats',
                })
        pair_corr = [corr_rank(ranks[a], ranks[b])
                     for a in range(len(ims)) for b in range(a+1, len(ims))]
        pair_corr = [v for v in pair_corr if np.isfinite(v)]
        mode, votes_mode = votes.most_common(1)[0]
        stability.append({'group': group, 'n_images': len(ims),
                          'n_unique_canonical_operators': len(operators),
                          'distinct_retrospective_winners': len(votes),
                          'retrospective_modal_operator': mode,
                          'modal_fraction': votes_mode/len(ims),
                          'mean_cross_image_spearman': mean(pair_corr) if pair_corr else float('nan'),
                          'negative_cross_image_rank_fraction':
                              sum(c < 0 for c in pair_corr)/max(len(pair_corr),1),
                          'analysis_is_posthoc': True})
        for op in operators:
            d = np.array([canon_values[i][op]-canon_values[i]['equal_mean'] for i in ims])
            ds = np.array([canon_values[i][op]-max(scores[i][x+'::single'] for x in desc)
                           for i in ims])
            method_rows.append({
                'group': group, 'aggregator': op, 'n_images': len(ims),
                'mean_delta_vs_equal_mean': mean(d), 'median_delta_vs_equal_mean': float(np.median(d)),
                'min_delta': float(d.min()), 'max_delta': float(d.max()),
                'n_strict_positive': int((d > 1e-9).sum()),
                'n_strict_negative': int((d < -1e-9).sum()),
                'n_gain_ge_0p01': int((d >= .01).sum()),
                'n_loss_le_minus_0p01': int((d <= -.01).sum()),
                'mean_delta_vs_best_member_posthoc': mean(ds),
                'n_above_best_member_posthoc': int((ds > 1e-9).sum()),
                'scope': '14 unique images; repeated folds averaged; exploratory, no multiplicity correction',
            })
    save_csv(out/'uded_conditional_gain_per_image.csv', all_rows)
    save_csv(out/'uded_conditional_gain_by_model.csv', method_rows)
    save_csv(out/'uded_operator_rank_instability.csv', stability)
    ftable = []
    for r in all_rows:
        g = r['group']; img = r['image_id']; ds = g.split('|')
        z = {'image_id': img, 'group': g, 'aggregator': r['aggregator'],
             'delta_vs_mean': r['delta_F1_vs_equal_mean']}
        for feature in ['mean','std','q90','fraction_gt_0.5','gradient','orientation_coherence']:
            values = [float(features[img][d+'::'+feature]) for d in ds]
            z[feature+'_average'] = mean(values)
            z[feature+'_range'] = max(values)-min(values)
        ftable.append(z)
    save_csv(out/'uded_marginal_feature_and_gain.csv', ftable)
    associations = []
    fields = [x for x in ftable[0] if x.endswith('_average') or x.endswith('_range')]
    for g in sorted(groups):
        for op in sorted({x['aggregator'] for x in method_rows if x['group']==g}):
            rr = sorted((x for x in ftable if x['group']==g and x['aggregator']==op), key=lambda x:x['image_id'])
            for f in fields:
                associations.append({'group':g,'aggregator':op,'feature':f,
                                     'spearman_exploratory':corr_rank([x[f] for x in rr], [x['delta_vs_mean'] for x in rr]),
                                     'n_independent_images':len(rr), 'posthoc_no_multiple_test_inference':True})
    save_csv(out/'uded_marginal_exploratory_associations.csv', associations)
    return {'n_images': len(ims), 'n_groups': len(groups),
            'n_operators_reported_in_source':len(set().union(*groups.values())),
            'n_canonical_group_operators':n_fusion,
            'n_fusion_scores':len(all_rows), 'n_candidate_models_with_singles':len(scores[ims[0]]),
            'models':method_rows, 'stability':stability,
            'primary_cases': [r for r in method_rows if (r['group'],r['aggregator'])
                              in {(a,b) for a,b,_ in METHOD_CONTRASTS}],
            'source_sha256': {str(DATA/x): digest(root/DATA/x)
                              for x in ('common_candidate_scores.csv','image_features.csv')},
            'notes': [
                'O ganho contra o melhor descritor por imagem usa controle retrospectivo (oráculo), não seletor implantável.',
                'As cinco repetições da mesma imagem são agregadas e NÃO contadas como cinco imagens independentes.',
                'Correlações entre 78 resumos marginais e ganhos são exploratórias; não medem acordo espacial diretamente.',
                'Operadores algebricamente equivalentes são colapsados, com validação de consistência numérica.',
            ]}


def map_spatial(root, out, u):
    """Usa APENAS mapas float já cacheados e com SHA do manifesto, sem GT."""
    cache = root/'cache/local_dev/stage24/descriptors'
    provenance = root/REPRO/'campaign/descriptor_provenance.csv'
    if not cache.exists() or not provenance.exists():
        return {'status':'not_available', 'reason':'Cache float ou manifesto de proveniência não presente no checkout'}
    prov = read_csv(provenance)
    expected = {}
    for r in prov:
        if r.get('dataset','UDED') not in ('UDED',''):
            continue
        expected[(r['image_id'], r['descriptor_id'])] = r['sha256']
    desc = sorted({d for _,d in expected});imgs = sorted({i for i,_ in expected})
    arrays = {}
    for d in desc:
        for side in sorted((cache/d).glob('*.json')):
            try:
                ident = json.loads(side.read_text(encoding='utf-8')).get('identity',{})
                k = (ident.get('image_id'),d)
                if ident.get('dataset') != 'UDED' or k not in expected:continue
                npy = side.with_suffix('.npy')
                if not npy.exists() or digest(npy) != expected[k]:continue
                a = np.load(npy, allow_pickle=False)
                assert a.ndim == 2 and a.dtype==np.float32 and np.isfinite(a).all()
                assert ident.get('gt_used') is False
                arrays[k] = a
            except (OSError, ValueError, KeyError, json.JSONDecodeError):
                continue
    if set(arrays) != set(expected):
        missing = sorted(set(expected)-set(arrays))
        return {'status':'not_available','reason':'Mapas float ausentes ou SHA divergente',
                'expected':len(expected),'valid':len(arrays),'missing_examples':missing[:8]}
    # Normalização por ranks de pixels POSITIVOS: evita o erro de q90=0 ativar todo o fundo.
    def top_fraction(a, fract=.10):
        valid = np.flatnonzero(a.ravel() > 0)
        b = np.zeros(a.size,bool)
        if valid.size:
            count = max(1, int(math.ceil(fract*valid.size)))
            top = valid[np.argpartition(a.ravel()[valid], -count)[-count:]]
            b[top] = True
        return b.reshape(a.shape)
    groups = sorted({r['group'] for r in u['models']})
    spatial = []
    for im,group in itertools.product(imgs,groups):
        ds = group.split('|');maps = [arrays[im,d] for d in ds]
        if len({a.shape for a in maps}) != 1:
            raise ValueError(f'Geometria dos mapas incompatível: {im} {group}')
        tuples = []
        for a,b in itertools.combinations(maps,2):
            am,bm=top_fraction(a),top_fraction(b)
            union = np.count_nonzero(am|bm)
            inter = np.count_nonzero(am&bm)
            exclusive = np.count_nonzero(am^bm)
            va,vb=a.ravel().astype(np.float64), b.ravel().astype(np.float64)
            pearson = float(np.corrcoef(va,vb)[0,1]) if va.std()>1e-12 and vb.std()>1e-12 else float('nan')
            tuples.append((inter/max(union,1),exclusive/max(union,1),pearson))
        means = [float(a.mean()) for a in maps]
        spatial.append({'image_id':im,'group':group,'arity':len(ds),
                        'top_positive_10pct_iou':mean([x[0] for x in tuples]),
                        'top_positive_10pct_exclusivity':mean([x[1] for x in tuples]),
                        'mean_pairwise_float_pearson':mean([x[2] for x in tuples]),
                        'descriptor_mean_range':max(means)-min(means),
                        'ground_truth_used':False,'source':'verified cached UDED float32 NPY'})
    save_csv(out/'uded_spatial_group_features.csv',spatial)
    m = {(r['image_id'],r['group']):r for r in spatial}
    all_scores = read_csv(out/'uded_conditional_gain_per_image.csv')
    grouped=defaultdict(list)
    for r in all_scores:
        if (r['image_id'],r['group']) in m:
            grouped[(r['group'],r['aggregator'])].append((r,m[r['image_id'],r['group']]))
    analysis = []
    for (group,agg),vals in sorted(grouped.items()):
        vals.sort(key=lambda x:x[0]['image_id'])
        gain = [float(x['delta_F1_vs_equal_mean']) for x,_ in vals]
        for col in ('top_positive_10pct_iou','top_positive_10pct_exclusivity',
                    'mean_pairwise_float_pearson','descriptor_mean_range'):
            v=[float(y[col]) for _,y in vals]
            analysis.append({'group':group,'aggregator':agg,'image_feature':col,
                             'spearman_exploratory':corr_rank(v,gain),'n_images':len(vals),
                             'confirmatory':False})
    save_csv(out/'uded_spatial_regime_associations.csv', analysis)
    return {'status':'complete','verified_descriptor_maps':len(arrays),
            'group_image_records':len(spatial),'note':'Sem GT ou reextração; correlações exploratórias (muitos testes)'}


def bsds_counts(root, out):
    """Reconstrói F1 em cada imagem no limiar mais próximo do ODS do método.

    IMPORTANTE: limiar escolhido na mesma validation, não avaliação prospectiva.
    P/R vêm de contagens Berkeley multi-anotador; NÃO usar TP/FN binários simples.
    """
    csvpath=root/REPRO/'official_bsds/per_image_threshold_counts.csv'
    summarypath=root/REPRO/'campaign/official_bsds_summary.json'
    if not csvpath.exists() or not summarypath.exists():
        return {'status':'not_available', 'reason':'Contagens oficiais por imagem ou resumo ausentes no checkout'}
    summary=json.loads(summarypath.read_text(encoding='utf-8'))
    targets={method:float(v['ODS_threshold']) for method,v in summary['methods'].items()}
    selected={}
    n_rows=0
    with csvpath.open(encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            n_rows+=1
            k=(r['method'],r['image_id'])
            if r['method'] not in targets:
                continue
            d=abs(float(r['threshold'])-targets[r['method']])
            if k not in selected or d < selected[k][0]:
                selected[k]=(d,r)
    vals=[]
    for (method,img),(d,r) in sorted(selected.items()):
        cr,sr,cp,sp=(float(r[k]) for k in ['cntR','sumR','cntP','sumP'])
        rec=cr/sr if sr else 0.0;prec=cp/sp if sp else 0.0
        if not (0<=rec<=1+1e-6 and 0<=prec<=1+1e-6):
            raise ValueError(f'Contagens Berkeley inválidas para {method}, {img}')
        f1=2*rec*prec/(rec+prec) if rec+prec else 0.0
        vals.append({'image_id':img,'method':method,'F1_at_nearest_method_ODS_threshold':f1,
                     'precision':prec,'recall':rec,'selected_ODS_threshold':targets[method],
                     'actual_grid_threshold':float(r['threshold']),
                     'grid_distance':d,'source':'Berkeley per_image_threshold_counts'})
    save_csv(out/'bsds_per_image_at_development_ODS_threshold.csv',vals)
    vi={(r['image_id'],r['method']):r for r in vals};imgs=sorted({r['image_id'] for r in vals})
    methods=sorted(targets)
    assert len(imgs)==100 and all((im,m) in vi for im in imgs for m in methods), 'BSDS incompleto'
    contrasts=[]
    pairs=[(m,'incumbent_compact_positive_choquet') for m in methods if m!='incumbent_compact_positive_choquet']
    pairs.append(('stage24gl_winner','stage24gl_identity'))
    for method,ref in pairs:
        for img in imgs:
            r=vi[img,method]; rr=vi[img,ref]
            contrasts.append({'image_id':img,'method':method,'reference':ref,
                              'delta_per_image_F1':r['F1_at_nearest_method_ODS_threshold']-rr['F1_at_nearest_method_ODS_threshold'],
                              'method_F1':r['F1_at_nearest_method_ODS_threshold'],
                              'reference_F1':rr['F1_at_nearest_method_ODS_threshold'],
                              'description':'development diagnostic at each model own val-ODS nearest discrete threshold'})
    save_csv(out/'bsds_conditional_per_image_contrasts.csv',contrasts)
    summary_rows=[]
    for method,ref in pairs:
        v=np.array([r['delta_per_image_F1'] for r in contrasts if r['method']==method and r['reference']==ref])
        summary_rows.append({'method':method,'reference':ref,'n_images':len(v),'mean_per_image_delta':mean(v),
                             'median_per_image_delta':float(np.median(v)),
                             'n_positive':int((v>1e-9).sum()),'n_negative':int((v< -1e-9).sum()),
                             'n_ge_0p01':int((v>=0.01).sum()),'n_le_minus_0p01':int((v<=-0.01).sum()),
                             'limitation':'Not official ODS delta: per-image F1 at nearest method-specific ODS thresholds chosen on validation'})
    save_csv(out/'bsds_conditional_summary.csv',summary_rows)
    return {'status':'complete','original_threshold_rows':n_rows,'methods':len(methods),
            'images':len(imgs),'contrasts':summary_rows,
            'warning':'Esses deltas F1 por imagem NÃO substituem os deltas ODS/OIS/AP oficiais; thresholds são da validation.'}


def bsds_final_map_features(root, out, bsds):
    """Carrega somente predições finais BSDS float32 preexistentes.

    São mapas agregados CONGELADOS: nunca descrevê-los como mapas de descritores
    individuais, nem como explicação causal de complementaridade de fontes.
    """
    manifest = root/REPRO/'campaign/bsds_float_prediction_manifest.csv'
    if not manifest.exists():
        return {'status':'not_available','reason':'Manifesto de mapas float BSDS não presente'}
    rows=read_csv(manifest)
    variants=defaultdict(dict)
    missing=[]
    spatial=[]
    for r in rows:
        variant=r['variant']; img=r['image_id']
        p=root/r['relative_path']
        if not p.exists() or digest(p)!=r['sha256']:
            missing.append((variant,img))
            continue
        a=np.load(p,allow_pickle=False)
        if a.dtype!=np.float32 or a.ndim!=2 or not np.isfinite(a).all():
            raise ValueError(f'Mapa inválido {p}')
        gy,gx=np.gradient(a.astype(np.float64))
        spatial.append({'image_id':img,'variant':variant,
                        'float_mean':float(a.mean()),'float_std':float(a.std()),
                        'float_q95':float(np.quantile(a,.95)),
                        'float_nonzero_fraction':float(np.mean(a>0)),
                        'float_gt_half_fraction':float(np.mean(a>.5)),
                        'float_gradient_mean':float(np.hypot(gx,gy).mean()),
                        'sha256_verified':True})
        # Reter somente os mapas comparados diretamente para limitar uso de RAM.
        if variant in ('winner','identity'):
            variants[img][variant]=a
    if not spatial:
        return {'status':'not_available','reason':'Nenhum mapa float recuperado com SHA correto',
                'missing_count':len(missing)}
    save_csv(out/'bsds_final_scoremap_features.csv',spatial)
    contrasts=[]
    f1path=out/'bsds_conditional_per_image_contrasts.csv'
    byid={}
    if f1path.exists():
        for z in read_csv(f1path):
            if z['method']=='stage24gl_winner' and z['reference']=='stage24gl_identity':
                byid[z['image_id']]=float(z['delta_per_image_F1'])
    for img,grp in sorted(variants.items()):
        if not all(k in grp for k in ('winner','identity')):continue
        a=grp['winner'];b=grp['identity']
        if a.shape!=b.shape:raise ValueError('Mapas winner/identity com geometrias distintas: '+img)
        diff=a.astype(np.float64)-b
        contrasts.append({'image_id':img,'mean_winner_minus_identity':float(diff.mean()),
                          'mean_abs_score_difference':float(np.mean(np.abs(diff))),
                          'fraction_winner_less_than_identity':float(np.mean(diff < -1e-8)),
                          'fraction_winner_greater_than_identity':float(np.mean(diff > 1e-8)),
                          'delta_F1_at_nearest_val_ODS':byid.get(img,float('nan')),
                          'map_class':'frozen_final_aggregate_not_individual_descriptors'})
    save_csv(out/'bsds_frozen_map_changes_and_gain.csv',contrasts)
    comparable=[z for z in contrasts if np.isfinite(z['delta_F1_at_nearest_val_ODS'])]
    associa=[]
    for feat in ('mean_winner_minus_identity','mean_abs_score_difference',
                 'fraction_winner_less_than_identity','fraction_winner_greater_than_identity'):
        associa.append({'feature':feat,'n_images':len(comparable),
                        'spearman_exploratory':corr_rank([z[feat] for z in comparable],
                            [z['delta_F1_at_nearest_val_ODS'] for z in comparable]) if comparable else float('nan'),
                        'warning':'Posthoc: final prediction maps only; not proof of complementarity mechanism'})
    save_csv(out/'bsds_frozen_map_exploratory_associations.csv',associa)
    return {'status':'complete' if not missing else 'partial',
            'expected':len(rows),'verified':len(spatial),'missing':len(missing),
            'winner_identity_pairs':len(contrasts),
            'note':'Somente scores agregados finais; não substituem 13 mapas de descritores BSDS'}


def render_report(out, u, spatial, bsds, bsds_map):
    def fmt(x): return f'{x:+.4f}' if isinstance(x,(int,float)) else str(x)
    parts=['# MFI-EDGE — landscape condicional de complementaridade e agregação',
           '', '## Escopo e integridade',
           'Reanálise exploratória de **resultados arquivados** da Stage24G–L. Não houve extração, refitting, seleção de limiares ou reexecução de benchmarks. Não são resultados de teste independente.',
           f"UDED: {u['n_images']} imagens distintas, {u['n_groups']} conjuntos de descritores, {u['n_candidate_models_with_singles']} candidatos incluindo controles individuais.",
           '', '## Casos fixados para exame',
           '| Grupo | Operador | Δ F1 médio vs média | Ganhos/perdas por imagem |', '|---|---|---:|---:|']
    for x in u['primary_cases']:
        parts.append(f"| `{x['group']}` | `{x['aggregator']}` | {fmt(x['mean_delta_vs_equal_mean'])} | {x['n_strict_positive']}/{x['n_strict_negative']} |")
    parts+=['', '## Rankings entre imagens',
            '| Grupo | Modal retrospectivo | Fração modal | Spearman médio entre rankings de imagens | Fração de correlações negativas |',
            '|---|---|---:|---:|---:|']
    for x in u['stability']:
        parts.append(f"| `{x['group']}` | `{x['retrospective_modal_operator']}` | {x['modal_fraction']:.1%} | {x['mean_cross_image_spearman']:.3f} | {x['negative_cross_image_rank_fraction']:.1%} |")
    parts+=['','## Mapas espaciais de descritores',json.dumps(spatial,ensure_ascii=False),
            '', '## BSDS500 validation',json.dumps(bsds,ensure_ascii=False)[:5000],
            '', '## Mapas agregados BSDS existentes',json.dumps(bsds_map,ensure_ascii=False),
            '', '## Limitações inferenciais',
            '1. Identificar quais imagens favorecem uma fórmula e correlacionar esse rótulo com características é **análise retrospectiva**, sujeita a seleção e multiplicidade.',
            '2. Para cada imagem UDED, cinco repetições não são cinco observações independentes. A quantidade de imagens distintas permanece 14.',
            '3. Uma fusão que supera a média de seus componentes não necessariamente supera o melhor descritor individual; o melhor indivíduo por imagem também é um oráculo retrospectivo.',
            '4. Resumos marginais não identificam, por si, complementaridade espacial. Use `uded_spatial_group_features.csv` quando os mapas float com SHA estiverem disponíveis.',
            '5. No BSDS, as variantes congeladas não constituem o landscape completo de descritores/agregadores. Comparações no limiar ODS obtido na própria validation são descritivas.',
            '6. Não inferir uma política de seleção de agregadores ou causalidade a partir das correlações observadas. Exige treino/teste externo para alegação preditiva.',
            '', '## Fontes originais',
            'https://github.com/MicamAmorim/MFI-Edge/tree/mfi-edge-stage24-residual-suppression/results/paper_a_evidence/stage24_image_groups',
            'https://github.com/MicamAmorim/MFI-Edge/tree/mfi-edge-stage24-residual-suppression/results/paper_a_evidence/stage24gl',
            '']
    (out/'relatorio_recalculado.md').write_text('\n'.join(parts),encoding='utf-8')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--research-root',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--no-maps',action='store_true',help='Não acessar caches float; usar apenas métricas e características já salvas')
    p.add_argument('--no-bsds',action='store_true',help='Pular per-image Berkeley (contagens locais)')
    args=p.parse_args();root=args.research_root.resolve();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    u=summarize_u(root,out)
    spatial={'status':'skipped_by_request'} if args.no_maps else map_spatial(root,out,u)
    bsds={'status':'skipped_by_request'} if args.no_bsds else bsds_counts(root,out)
    bsds_map = {'status':'skipped_by_request'} if args.no_maps else bsds_final_map_features(root,out,bsds)
    summary={'experiment':'stage24_conditional_landscape_posthoc',
             'source_campaign':'stage24_paper_a_recertification',
             'original_experiment_modified':False,'no_refitting':True,
             'UDED':{k:v for k,v in u.items() if k not in ('models','stability')},
             'spatial':spatial,'BSDS500':bsds,'BSDS_final_maps':bsds_map,
             'status':'completed_exploratory_not_confirmatory'}
    (out/'auditoria_condicional.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
    render_report(out,u,spatial,bsds,bsds_map)
    print(json.dumps({'status':'ok','out':str(out),'UDED_images':u['n_images'],
                      'models':u['n_candidate_models_with_singles'],
                      'spatial':spatial['status'],'BSDS':bsds['status'],'BSDS_maps':bsds_map['status']},ensure_ascii=False))

if __name__=='__main__':main()