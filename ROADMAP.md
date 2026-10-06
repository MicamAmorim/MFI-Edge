# MFI-Edge research roadmap

Last updated: **2026-10-05**

This file records what is done, what is active, what comes next, and what qualifies a model for promotion. Scientific evidence/history lives under `docs/paper/`.

Legend: 🟢 implemented/completed · 🟡 active/partial validation · 🔴 planned · ⚪ parked.

## Branch responsibilities

| Branch | Role |
|---|---|
| `main` | stable/reproducible line; only validated/promoted models |
| `mfi-edge-local-dev` | active workstation research |
| `mfi-edge-webui` | qualitative inference/comparison UI |
| `experiment/uded-railway` | server-side experiment/infrastructure history |

## Current scientific position

The project has moved through four practical generations:

1. **MFI-Classic** — multiscale fuzzy evidence, ROI/refinement, classical localizer, NMS/linking.
2. **MFI-Fuzzy++ / Stage 5–7** — broad fuzzy-measure/operator/fusion competition and UDED generalization tests.
3. **CH-MFI-v2 / Stage 10** — context-aware, hierarchical, uncertainty-aware fuzzy evidence controlling localization.
4. **Edge Signature / Stage 11–12** — use GT as a scientific instrument to discover which image-derived properties distinguish true boundaries from hard negatives, then translate only stable properties into a generalizable analytical/fuzzy detector.

Guiding question:

> **What properties make a true image boundary different from a high-gradient non-boundary, and can those properties be represented by an interpretable multiscale fuzzy model that generalizes across datasets?**

---

# Latest evidence

## CH-MFI-v2

The first 519-config UDED workstation screen selected `v2_std__distprob_g055__global_local__conditional__g0.75__soft`, but remained below Scharr:

| Metric | CH-MFI-v2 | Scharr |
|---|---:|---:|
| selection CV F1 | 0.71857 | **0.76610** |
| selection ODS | 0.71991 | **0.76642** |
| held-out F1 | 0.71325 | **0.76204** |

Held-out delta F1: **-0.04879**, paired-bootstrap 95% CI **[-0.10097, -0.00560]**. Later scale-bank/regime-Shapley variants did not replace the winner. Brute-force reweighting of the same descriptor space is therefore not enough.

## Stage 11 / 11b

Historical `oriented` descriptors contained **22 / 80** exact duplicate descriptor/scale pairs among nominal fine scales. `oriented_ms` corrected this to **0 / 80**.

Stage-11b diagnostics:

| score | selection AUC | selection AP | held-out AUC | held-out AP |
|---|---:|---:|---:|---:|
| analytical signature | 0.6293 | 0.4169 | 0.6606 | 0.4257 |
| logistic diagnostic | 0.6887 | 0.4879 | **0.6992** | **0.5029** |

The corrected descriptor space contains reproducible information. Edge-v-texture separation is markedly easier than exact edge-v-near-edge localization, and signed logistic coefficients suggest that relational/contrastive information is not fully represented by the current all-positive analytical aggregation.

## Stage 12a — fixed Scharr + analytical signature gate

The best inner-CV gate was `siggate__multiply__a2__floor0.25`.

| Metric | Scharr | Stage-12a winner |
|---|---:|---:|
| selection CV F1 | 0.73351 | **0.73587** |
| held-out F1 | 0.76204 | **0.76225** |

Held-out delta F1: **+0.000203**, 95% CI **[-0.001326, 0.001842]**. Context/localization separation removed the large CH-MFI-v2 degradation, but the additive gate was effectively tied with Scharr.

## Stage 12b — non-additive and dual fuzzy signature

The formal selection winner was positive-only:

`fuzzypos__g0.55__a2__floor0.1`

with selection CV F1 **0.764758**, but held-out F1 **0.761234**, slightly below Scharr (**0.762042**).

However, the top selection-ranked set revealed a strong **dual positive/texture evidence** signal. Four of the five dual candidates promoted among the top seven had bootstrap CIs entirely above zero on the development held-out subset. The strongest observed member (selection rank 7, not the formal winner) reached:

- held-out F1 **0.770204**;
- delta vs Scharr **+0.008162**;
- 95% CI **[0.002532, 0.014814]**;
- precision **0.678338** and recall **0.890851**.

This supports the family-level hypothesis that explicit anti-texture evidence matters. It does **not** justify choosing the rank-7 configuration by held-out performance.

### Important methodological correction

Stage-12b CV fitted thresholds out-of-fold, but the evidence banks themselves were selected once on all 15 selection images before CV. Thus Stage-12b `cv_F1` is not fully leakage-free with respect to feature-bank construction.

Stage 12c fixes this by rebuilding evidence banks inside each CV training fold.

Also, because the same UDED held-out subset has now been inspected repeatedly across architectural stages, it is henceforth a **development-confirmation split**, not a pristine publication test. Final generalization claims must use an untouched external protocol.

Full notes:

- `docs/paper/STAGE11B_SCALE_SENSITIVE_RESULTS.md`
- `docs/paper/STAGE12A_SIGNATURE_GATE_RESULTS.md`
- `docs/paper/STAGE12B_FUZZY_SIGNATURE_RESULTS.md`

**Wide remains blocked.**

---

# Track A — active workstation campaign

| Milestone | Status | Definition / latest result |
|---|:---:|---|
| CH-MFI-v2 modules | 🟢 | context/hierarchy/fuzzy families/uncertainty/localization execute |
| first standard screen (519) | 🟢 | negative vs Scharr |
| scale-bank + regime-Shapley rerun (531) | 🟢 | learned additions did not improve formal winner |
| Stage 11 analytical signature | 🟢 diagnostic | exposed fine-scale collapse |
| `oriented_ms` + multiscale audit | 🟢 | 22 duplicates -> 0 |
| Stage 11b signature | 🟢 | analytical + logistic diagnostics completed |
| cross-scale relational descriptors | 🟢 | balance/delta/persistence/entropy/centroid/peak added |
| Stage 12a fixed-Scharr analytical gate | 🟢 | essentially tied with Scharr |
| Stage 12b fuzzy/dual signature | 🟢 diagnostic | positive-only formal winner null; dual family shows first positive signal |
| **Stage 12c leakage-free bank CV** | 🟡 **run now** | rebuild evidence banks inside every CV training fold; verify dual-family stability |
| formal bipolar / bi-capacity model | 🔴 conditional next | only if Stage 12c confirms dual-family signal |
| external BSDS/BIPED validation | 🔴 **next after 12c** | untouched protocol required before promotion/publication claims |
| CH-MFI component ablations | ⚪ parked | dynamic localizer/uncertainty remain excluded while signature line is studied |
| topology competition | 🟢 code / 🟡 deferred | only after continuous score is externally competitive |
| wide sweep | 🔴 **blocked** | do not return to brute-force until architecture/generalization is established |
| resolution sensitivity | 🔴 | 256 px is development resolution only |

### Run now

```powershell
git fetch
git switch mfi-edge-local-dev
git pull
.\run_stage12c_leakfree_cv.bat
```

Send the files printed by the launcher before implementing formal bipolar aggregation.

---

# Track B — current target architecture

Preferred interpretable line:

```text
image
  -> oriented_ms descriptors + cross-scale structural relations
  -> positive boundary memberships -------> C+(x)
  -> texture / anti-boundary memberships -> C-(x)
  -> contrastive / bipolar context score

image -> fixed precise localizer (Scharr+NMS)
     -> context gate
     -> frozen threshold
     -> edge map
```

Current hypotheses to test in order:

1. evidence-bank selection remains useful under leakage-free CV;
2. dual evidence is more robust than positive-only fuzzy evidence;
3. the dual effect transfers to an untouched external dataset;
4. only then formalize a bipolar Choquet / bi-capacity formulation;
5. only after that revisit dynamic localization/topology.

The logistic model remains an **upper-bound diagnostic only**, never the proposed detector.

---

# Track C — model-family coverage

| Research idea | Status |
|---|:---:|
| context analyzer | 🟢 |
| hierarchical coarse/fine MFI | 🟢 |
| conditional fuzzy operators | 🟢 |
| distorted-probability capacities | 🟢 |
| scale-specific capacities | 🟢 tested |
| global/regime Shapley | 🟡 utility needs threshold-free revision |
| SWAFED | 🟢 |
| d-CF / d-CC / d-XC / d-Choquet | 🟢 |
| Choquet-inspired aggregation | 🟢 experimental |
| partition-conditioned aggregation | 🟢 experimental |
| dynamic classical localizer bank | 🟢; parked pending signature evidence |
| multiscale uncertainty | 🟢; parked/redesign pending |
| granularity control | 🟡 |
| `oriented_ms` scale-sensitive descriptors | 🟢 |
| cross-scale relational signature | 🟢 |
| fixed-Scharr analytical gate | 🟢 near-null vs baseline |
| distorted-capacity positive Choquet | 🟢 tested; formal winner did not improve held-out |
| dual positive/texture fuzzy evidence | 🟡 **promising family signal** |
| leakage-free evidence-bank CV | 🟡 active Stage 12c |
| formal bipolar / bi-capacity aggregation | 🔴 conditional next |
| formal k-interactive learning | 🔴 |
| explicit Fourier/multiband branch | 🔴 |
| learned router/dynamic convolution | 🔴 v3 |
| annotator uncertainty / ranking loss | 🔴 |
| fuzzy detector ensemble (TEED/PiDiNet/etc.) | 🔴 hybrid generation |

---

# Track D — validation and datasets

| Milestone | Status | Notes |
|---|:---:|---|
| synthetic primitives + robust synthetic v2 | 🟢 | mechanism diagnosis |
| UDED 15/15 development split | 🟢 | useful development protocol; held-out no longer pristine final test |
| leakage-free selection CV | 🟡 Stage 12c | evidence banks rebuilt within folds |
| official BSDS500 train/val/test | 🔴 **high priority** | required before publication claims |
| official Berkeley matching | 🔴 | current tolerant matcher is a development proxy |
| BSDS individual-annotator signature | 🔴 | preserve annotation uncertainty |
| BIPED signature replication | 🔴 **high priority** | cross-dataset stability |
| cross-dataset detector generalization | 🔴 **high priority** | freeze UDED-developed family, evaluate elsewhere |
| resolution sensitivity | 🔴 | rerun finalists above 256 px |

---

# Track E — CH-MFI-v3 / Hybrid

Only after the interpretable signature line is understood:

- learned context/router network;
- learned dynamic localizer kernels;
- explicit frequency/Fourier branch;
- annotation-aware uncertainty;
- ranking loss;
- fuzzy detector ensemble with TEED/PiDiNet or similar compact detectors;
- optional differentiable fuzzy-capacity layer.

---

# Track F — WebUI and promotion

No current Stage-12 candidate is promoted.

Promotion requires exact config, leakage-controlled selection rule, frozen threshold, untouched external test result, qualitative validation and preserved reproducible outputs.

```text
mfi-edge-local-dev
      -> validated configuration
      -> main
      -> mfi-edge-webui registry
```

---

# Track G — paper/research record

Maintained under `docs/paper/`:

- `ARCHITECTURE_MAP.md`
- `BIBLIOGRAPHY_MATRIX.md`
- `LEGACY_REVIEW_CORPUS.md`
- `EXPERIMENT_HISTORY.md`
- `STAGE11_EDGE_SIGNATURE.md`
- `STAGE11_EDGE_SIGNATURE_RESULTS.md`
- `STAGE11B_SCALE_SENSITIVE_RESULTS.md`
- `STAGE12A_SIGNATURE_GATE_RESULTS.md`
- `STAGE12B_FUZZY_SIGNATURE_RESULTS.md`
- `PAPER_WRITING_PLAN.md`
- `references.bib`

## Roadmap maintenance rule

Update this file whenever a model family, benchmark, dataset, paper or negative result changes the scientific direction. Update the corresponding `docs/paper/` record in the same development cycle so roadmap status, evidence and future manuscript claims remain synchronized.
