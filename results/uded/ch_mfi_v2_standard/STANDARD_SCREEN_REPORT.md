# CH-MFI-v2 — first local standard screen on UDED

Date: 2026-10-05  
Branch: `mfi-edge-local-dev`  
Status: **candidate negative/diagnostic result; learned regime/scale banks were not enabled in this run**.

## Protocol

- preset: `standard`
- configurations: **519**
- workers: **8** on a 16-logical-CPU workstation
- development max side: **256 px**
- threshold grid: **31** values
- UDED split: 15 selection / 15 held-out
- ranking criterion: 3-fold inner-CV F1 on selection
- frozen selection threshold applied to held-out
- top 12 selection-ranked candidates evaluated on held-out
- paired bootstrap vs Scharr: 5,000 samples
- descriptor stack: grad, Laplacian, Hessian, coherence, normal contrast, normal-minus-tangent, steered Hessian, Gabor4

## Scharr baseline

Selection inner-CV:

- CV F1: **0.76610**

Selection full split:

- ODS: **0.76642**
- OIS: 0.78551
- AP: 0.76703
- R50: 0.98462

Frozen held-out:

- precision: **0.66712**
- recall: **0.88846**
- F1: **0.76204**

## Formally selected CH-MFI-v2 candidate

`v2_std__distprob_g055__global_local__conditional__g0.75__soft`

Architecture:

- distorted-probability capacity, gamma = 0.55
- global/local hierarchy
- context-conditional fuzzy operators
- granularity = 0.75
- adaptive localizer
- soft MFI-to-localizer controller
- alpha = 0.75
- uncertainty beta = 0.50
- no regime-specific Shapley in this run
- no learned scale-capacity bank in this run

Selection:

- CV F1: **0.71857**
- ODS: **0.71991**
- OIS: 0.76247
- AP: 0.71004
- R50: 0.92157
- frozen threshold: 0.297925

Held-out:

- precision: **0.61117**
- recall: **0.85628**
- F1: **0.71325**
- delta F1 vs Scharr: **-0.04879**
- 95% paired-bootstrap CI: **[-0.10097, -0.00560]**
- P(delta > 0): **0.0122**

**Interpretation:** the selected CH-MFI-v2 candidate is statistically worse than Scharr under this development protocol.  The deficit is already visible on selection/inner-CV, so this result is not merely a held-out overfitting artifact.

## Held-out finalist result

All 12 candidates chosen by selection ranking produced a negative held-out delta vs Scharr, and every reported 95% bootstrap interval remained below zero.  Therefore no model from this initial, non-learned standard screen is eligible for promotion to `main` or the WebUI registry.

The best held-out candidate was still the formal selection winner at F1 = 0.71325.  The two d-CF finalists were faster but fell to approximately 0.6975 / 0.6967 held-out F1.

## Family-level screen

| Family | n | Best CV F1 | Best selection ODS | Median CV F1 | Median runtime/image (s) |
|---|---:|---:|---:|---:|---:|
| standard contextual/hierarchical | 240 | **0.718574** | 0.719906 | **0.703272** | 0.992 |
| d-CF | 60 | 0.715364 | 0.722324 | 0.690800 | 0.528 |
| d-CC | 60 | 0.711757 | 0.723724 | 0.686775 | 0.660 |
| partition-conditioned | 18 | 0.709231 | 0.719188 | 0.686675 | **0.346** |
| Choquet-inspired | 12 | 0.707862 | 0.720659 | 0.686322 | 0.599 |
| d-XC | 60 | 0.707535 | **0.724716** | 0.689973 | 0.464 |
| regularized-pair | 9 | 0.706086 | 0.715263 | 0.685854 | 0.633 |
| SWAFED | 60 | 0.695925 | 0.696770 | 0.666774 | 0.617 |

Two different signals should not be conflated:

1. the **standard** family gave the best inner-CV candidate;
2. d-XC/d-CC/d-CF sometimes gave higher full-selection ODS, but with weaker inner-CV F1, so the strict protocol correctly did not promote those ODS-only peaks.

## Architectural signals inside the standard family

- Distorted probability with gamma 0.55 was the best individual selection candidate; gamma 0.85 was close behind.
- Conditional operators improved the standard family's average CV behavior relative to fixed operators, but cost substantially more runtime.
- `global_local` hierarchy produced the best individual model, although `flat` had better average CV across the full grid. This suggests hierarchy may be beneficial only in specific regimes/configurations rather than globally.
- granularity 0.75 produced the highest ODS peaks, while granularity 0.50 had the best average CV over all 519 configurations. This is another indication that the correct scale preference may be image/regime dependent.
- soft control produced the top individual candidate; bilateral exponential control was competitive but did not rescue held-out performance.
- local-evidence/local-reliability capacities were not competitive enough to justify promotion from this screen.

## Visual diagnosis

The generated contact sheet shows a consistent failure mode:

- MFI attention is often broad and region/texture-sensitive rather than tightly boundary-specific;
- the uncertainty map responds strongly to high-frequency structure;
- the dynamic localizer still produces dense responses in textured backgrounds;
- the final map preserves many non-GT structures and simultaneously misses part of the sparse semantic GT.

This matches the numerical precision loss: the selected model's held-out precision is 0.611 vs 0.667 for Scharr, while recall is also lower (0.856 vs 0.888).  The problem therefore cannot be fixed by threshold tuning alone.

## Runtime / parallel scaling

The standard sweep completed in **869.1 s (~14.5 min)**.

| Workers | Time for 8 profile configs (s) | Speedup vs 1 |
|---:|---:|---:|
| 1 | 35.63 | 1.00x |
| 2 | 23.23 | 1.53x |
| 4 | 17.45 | 2.04x |
| 8 | 13.80 | **2.58x** |

Eight workers were fastest among the tested values, although parallel efficiency was already flattening. Profile 10/12/16 only before a wide sweep; do not assume more workers will scale linearly.

## Scientific decision

**Do not run the wide grid yet.**  The initial standard family is clearly below Scharr, and a larger blind sweep would mostly spend compute around a weak operating point.

Proceed with the pieces intentionally absent from this run:

1. learn the scale-specific capacity bank on selection only;
2. learn regime-specific Shapley for clean/texture/blur/noise;
3. rerun standard with the learned banks appended as competitors;
4. add explicit component ablations around the winning learned variants (localizer-only, MFI gating only, fixed Scharr vs dynamic bank, uncertainty on/off, hierarchy on/off);
5. only if the continuous score closes the gap, run topology competition;
6. wide exploration remains blocked until the learned-bank standard rerun shows a credible improvement trend.

Topology repair is unlikely to solve the current main failure by itself because both precision and recall are already below Scharr before topology.

## Files generated locally

The workstation run generated:

- `baseline_scharr.json`
- `run_manifest.json`
- `selection_ranking.csv`
- `selection_per_image.csv`
- `heldout_top.csv`
- `parallel_scaling.csv`
- `summary.json`
- `best_contact_sheet.png`

The full raw ranking/per-image tables and PNG are workstation artefacts; compact scientific summaries are committed here so the research history remains readable without bloating the repository.
