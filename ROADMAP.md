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
4. **Edge Signature / Stage 11** — use GT as a scientific instrument to discover which image-derived properties distinguish true boundaries from hard negatives, then translate only stable properties into a generalizable analytical/fuzzy detector.

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

## Stage 11 first signature

Historical `oriented` descriptors produced a modest held-out analytical signature, but post-analysis found **22 exact duplicate descriptor/scale pairs** among nominal fine scales because parameter floors collapsed 3/5/7 responses.

## Stage 11b scale-sensitive rerun — completed

`oriented_ms` fixes the scale-collapse artifact:

- historical `oriented`: **22 / 80** exact duplicate descriptor/scale pairs;
- `oriented_ms`: **0 / 80** exact duplicate pairs.

Stage-11b diagnostics:

| score | selection AUC | selection AP | held-out AUC | held-out AP |
|---|---:|---:|---:|---:|
| analytical signature | 0.6293 | 0.4169 | 0.6606 | 0.4257 |
| logistic diagnostic | 0.6887 | 0.4879 | **0.6992** | **0.5029** |

Interpretation:

- the corrected descriptor space contains reproducible boundary information;
- edge-v-texture discrimination is substantially easier than exact-edge-v-near-edge localization;
- the logistic upper bound uses both positive and negative coefficients, suggesting relational/contrastive information that a simple all-positive fuzzy score misses;
- near-edge pixels should be treated primarily as an **ambiguous localization population**, not as clean semantic negatives;
- descriptor relevance is genuinely scale-specific (e.g. fine-scale Gabor is strong while curvature families prefer different scales).

Full note: `docs/paper/STAGE11B_SCALE_SENSITIVE_RESULTS.md`.

**Wide remains blocked.**

---

# Track A — active workstation campaign

| Milestone | Status | Definition / latest result |
|---|:---:|---|
| CH-MFI-v2 modules | 🟢 | context/hierarchy/fuzzy families/uncertainty/localization execute |
| first standard screen (519) | 🟢 | negative vs Scharr |
| scale-bank + regime-Shapley rerun (531) | 🟢 | learned additions did not improve formal winner |
| Stage 11 analytical signature | 🟢 diagnostic | exposed fine-scale collapse |
| `oriented_ms` | 🟢 | genuinely distinct 25/13/7/5/3 schedules |
| multiscale audit | 🟢 | 22 duplicates -> 0 |
| Stage 11b signature | 🟢 | analytical + logistic diagnostics completed |
| context-vs-localization split | 🟡 **next** | separate texture rejection from ambiguous near-edge localization |
| cross-scale relational descriptors | 🔴 **next** | generic fine-minus-coarse, scale peak/centroid, entropy/persistence |
| Stage 12 fixed-Scharr signature gate | 🔴 **next** | test signature as context controller before dynamic localizer |
| dual/bipolar fuzzy evidence | 🔴 **next** | compare positive+negative evidence against all-positive aggregation |
| CH-MFI component ablations | 🔴 | fixed Scharr vs dynamic localizer; uncertainty; hierarchy |
| topology competition | 🟢 code / 🟡 deferred | only after continuous score is competitive |
| wide sweep | 🔴 **blocked** | wait for information/modeling bottleneck to be resolved |
| resolution sensitivity | 🔴 | 256 px is development resolution only |

---

# Track B — Stage 12 target architecture

Stage 12 should **not** be another monolithic learned classifier. Preferred line:

```text
image
  -> scale-sensitive descriptors + cross-scale structural relations
  -> context / texture-rejection memberships
  -> positive boundary evidence -----> fuzzy aggregation
  -> anti-boundary/texture evidence -> fuzzy aggregation
  -> context gate

image -> fixed precise localizer (Scharr first)
     -> context gate
     -> optional localization signature
     -> NMS / frozen threshold
     -> edge map
```

Compare at least:

1. **all-positive analytical signature**;
2. **dual-Choquet**: `C_plus - lambda*C_minus` (or equivalent monotone transformed memberships);
3. **bipolar Choquet / bi-capacity** if theory/implementation is stable;
4. **logistic diagnostic only as an upper bound**, never as the proposed detector.

Only after a fixed-Scharr signature gate matches or improves Scharr should the dynamic localizer be reintroduced.

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
| dynamic classical localizer bank | 🟢; fixed-Scharr ablation pending |
| multiscale uncertainty | 🟢; redesign/ablation pending |
| granularity control | 🟡 |
| `oriented_ms` scale-sensitive descriptors | 🟢 |
| signature structural evidence | 🟢 diagnostic |
| cross-scale relational signature features | 🔴 next |
| dual/bipolar fuzzy evidence | 🔴 next |
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
| UDED 15/15 development split | 🟢 | current development protocol |
| official BSDS500 train/val/test | 🔴 | required before publication claims |
| official Berkeley matching | 🔴 | current tolerant matcher is a development proxy |
| BSDS individual-annotator signature | 🔴 | preserve annotation uncertainty |
| BIPED signature replication | 🔴 | cross-dataset stability |
| cross-dataset detector generalization | 🔴 | freeze on one dataset, evaluate another |
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

No current CH-MFI-v2 or Stage-11 candidate is promoted.

Promotion requires exact config, selection rule, frozen threshold, held-out/test result, qualitative validation and preserved reproducible outputs.

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
- `PAPER_WRITING_PLAN.md`
- `references.bib`

## Roadmap maintenance rule

Update this file whenever a model family, benchmark, dataset, paper or negative result changes the scientific direction. Update the corresponding `docs/paper/` record in the same development cycle so roadmap status, evidence and future manuscript claims remain synchronized.
