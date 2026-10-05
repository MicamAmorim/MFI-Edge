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

Stage 12a separated context from localization and kept Scharr+NMS fixed. The best gate selected on inner-CV was:

`siggate__multiply__a2__floor0.25`

| Metric | Scharr | Stage-12a winner |
|---|---:|---:|
| selection CV F1 | 0.73351 | **0.73587** |
| selection ODS | 0.76642 | **0.76816** |
| held-out precision | 0.66712 | **0.66863** |
| held-out recall | **0.88846** | 0.88634 |
| held-out F1 | 0.76204 | **0.76225** |

Held-out delta F1: **+0.000203**, paired-bootstrap 95% CI **[-0.001326, 0.001842]**, P(delta>0)=**0.5748**.

Interpretation: separating context from localization removes the large CH-MFI-v2 degradation, but a smooth additive signature gate is essentially tied with Scharr. The gate slightly trades recall for precision. The next test is therefore not stronger gating; it is whether **non-additive fuzzy aggregation and explicit texture/anti-edge evidence** can exploit information that the weighted analytical score misses.

Full notes:

- `docs/paper/STAGE11B_SCALE_SENSITIVE_RESULTS.md`
- `docs/paper/STAGE12A_SIGNATURE_GATE_RESULTS.md`

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
| Stage 12a fixed-Scharr signature gate | 🟢 | held-out effectively tied with Scharr; +0.00020 F1, CI crosses zero |
| Stage 12b fuzzy signature | 🟡 **run now** | distorted-capacity Choquet + optional dual texture/anti-edge bank with fixed Scharr |
| bipolar / bi-capacity formalization | 🔴 conditional | only if Stage 12b shows value from separated positive/negative evidence |
| CH-MFI component ablations | 🔴 | dynamic localizer and uncertainty remain excluded until fixed-Scharr context becomes useful |
| topology competition | 🟢 code / 🟡 deferred | only after continuous score is competitive |
| wide sweep | 🔴 **blocked** | wait for information/modeling bottleneck to be resolved |
| resolution sensitivity | 🔴 | 256 px is development resolution only |

### Run now

```powershell
git fetch
git switch mfi-edge-local-dev
git pull
.\run_stage12b_fuzzy_signature.bat
```

Send the files printed by the launcher before any new wide/monolithic experiment.

---

# Track B — Stage 12 target architecture

Stage 12 should **not** be another monolithic learned classifier. Current preferred line:

```text
image
  -> oriented_ms descriptors + cross-scale structural relations
  -> positive boundary memberships -------> fuzzy aggregation C+
  -> texture / anti-boundary memberships -> fuzzy aggregation C-
  -> context contrast / gate

image -> fixed precise localizer (Scharr+NMS)
     -> context gate
     -> frozen threshold
     -> edge map
```

Stage 12b explicitly compares:

1. additive-capacity control (`gamma=1`);
2. distorted-capacity Choquet (`gamma != 1`) over positive boundary memberships;
3. dual positive/texture evidence if independent texture-oriented features exist on selection;
4. Scharr baseline under the same selection/held-out protocol.

A formal bipolar Choquet / bi-capacity model should be implemented only if the pilot shows that separated negative evidence contributes reproducibly.

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
| dynamic classical localizer bank | 🟢; parked pending fixed-Scharr evidence |
| multiscale uncertainty | 🟢; parked/redesign pending |
| granularity control | 🟡 |
| `oriented_ms` scale-sensitive descriptors | 🟢 |
| signature structural evidence | 🟢 diagnostic |
| cross-scale relational signature features | 🟢 |
| fixed-Scharr analytical signature gate | 🟢 near-null vs baseline |
| distorted-capacity signature Choquet | 🟡 active Stage 12b |
| dual positive/texture fuzzy evidence | 🟡 active Stage 12b |
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

No current CH-MFI-v2 or Stage-11/12 candidate is promoted.

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
- `STAGE12A_SIGNATURE_GATE_RESULTS.md`
- `PAPER_WRITING_PLAN.md`
- `references.bib`

## Roadmap maintenance rule

Update this file whenever a model family, benchmark, dataset, paper or negative result changes the scientific direction. Update the corresponding `docs/paper/` record in the same development cycle so roadmap status, evidence and future manuscript claims remain synchronized.
