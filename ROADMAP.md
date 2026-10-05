# MFI-Edge research roadmap

Last updated: **2026-10-05**

This is the project-level roadmap for MFI-Edge / CH-MFI. `docs/paper/EXPERIMENT_HISTORY.md` records what happened; this file records **what is done, what is active, what is next, and what qualifies a model for promotion**.

Legend: 🟢 implemented/completed · 🟡 implemented but still under validation / partial · 🔴 planned · ⚪ parked / optional.

## Branch responsibilities

| Branch | Role | Promotion rule |
|---|---|---|
| `main` | stable/reproducible line | only validated models, scripts and frozen benchmark artefacts |
| `mfi-edge-local-dev` | active workstation research | broad model competition; failures and negative results are allowed |
| `mfi-edge-webui` | qualitative inference/comparison UI | only intentionally promoted models should appear in the deployable registry |
| `experiment/uded-railway` | server-side UDED experiments/history | infrastructure/benchmark lineage; not the current primary development line |

## Current scientific position

The project has moved through four practical phases:

1. **MFI-Classic** — multiscale fuzzy evidence, ROI/refinement, classical localizer, NMS/linking.
2. **MFI-Fuzzy++ / Stage 5–7** — broad fuzzy-measure/operator/fusion competition and UDED generalization testing.
3. **CH-MFI-v2 / Stage 10** — context-aware, hierarchical, uncertainty-aware fuzzy evidence controlling localization.
4. **Edge Signature / Stage 11** — use GT as a scientific instrument to discover which image-derived properties distinguish true boundaries from texture and near-edge negatives, then turn stable properties into a generalizable analytical/fuzzy model.

The guiding question is now:

> **What properties make a true image boundary different from a high-gradient non-boundary, and can those properties be represented by an interpretable multiscale fuzzy model that generalizes across datasets?**

---

## Latest evidence

### CH-MFI-v2

The first 519-config workstation screen selected `v2_std__distprob_g055__global_local__conditional__g0.75__soft`, but it remained clearly below Scharr:

| Metric | CH-MFI-v2 winner | Scharr |
|---|---:|---:|
| selection CV F1 | 0.71857 | **0.76610** |
| selection ODS | 0.71991 | **0.76642** |
| held-out F1 | 0.71325 | **0.76204** |

Held-out delta F1 was **-0.04879**, 95% paired-bootstrap CI **[-0.10097, -0.00560]**.

The later standard rerun appended learned scale-bank and regime-Shapley candidates. Those learned additions did not replace the original winner. Therefore the problem is not adequately explained by simply reweighting the same descriptor set.

### Stage 11 first edge-signature run

A selection-frozen analytical signature produced:

| Score | Selection AUC | Selection AP | Held-out AUC | Held-out AP |
|---|---:|---:|---:|---:|
| analytical signature | 0.6263 | 0.4233 | **0.6613** | **0.4372** |

This is modest but encouraging: the discovered structural score improved on held-out rather than collapsing.

However, post-analysis exposed a critical multiscale implementation fact: the historical `oriented` descriptor mode contains exact duplicate fine-scale responses because parameter floors/clips cause multiple 3/5/7 operators to become identical. The Stage-11 sample matrix contained **22 exact duplicate descriptor/scale column pairs**.

Therefore the first Stage-11 run is retained as diagnostic evidence, but **Stage 12 is blocked until a genuinely scale-sensitive rerun is complete**.

Full note: `docs/paper/STAGE11_EDGE_SIGNATURE_RESULTS.md`.

---

# Track A — active workstation campaign

| Milestone | Status | Definition / latest result |
|---|:---:|---|
| CH-MFI-v2 architecture modules | 🟢 | context, hierarchy, fuzzy families, uncertainty and localization paths execute |
| first standard screen (519 configs) | 🟢 | negative vs Scharr; archived |
| scale-capacity learning | 🟢 | learned/tested; did not improve formal winner |
| regime-Shapley v1 | 🟡 | learned/tested; threshold-optimized F1 utility partly collapsed |
| Stage 11 analytical edge signature | 🟢 diagnostic | held-out AUC 0.6613; useful but moderate |
| historical multiscale-collapse diagnosis | 🟢 | 22 exact duplicate descriptor/scale pairs found in Stage-11 sample matrix |
| `oriented_ms` feature mode | 🟢 code / 🟡 validate | genuine 25/13/7/5/3 scale schedules; historical `oriented` preserved |
| multiscale feature audit | 🟢 code / 🟡 **run now** | `audit_multiscale_features.py` compares old vs new modes |
| Stage 11b scale-sensitive signature | 🟢 code / 🟡 **run now** | corrected signature discovery with `oriented_ms` |
| logistic signature upper bound | 🟢 code / 🟡 **run now** | diagnostic only; not proposed detector |
| Stage 12 signature-informed MFI | 🔴 blocked pending 11b | convert stable properties to fuzzy memberships/capacities and localizer control |
| CH-MFI component ablations | 🔴 | fixed Scharr vs dynamic localizer; gating; uncertainty; hierarchy |
| topology competition | 🟢 code / 🟡 deferred | after continuous score is competitive |
| wide sweep | 🔴 **blocked** | no brute-force sweep before information bottleneck is understood |
| image-size sensitivity | 🔴 | 256 px is development resolution only |

### Run now

```powershell
git fetch
git switch mfi-edge-local-dev
git pull
.\run_stage11_signature.bat
```

The launcher now runs:

1. `audit_multiscale_features.py`;
2. `analyze_gt_edge_signatures_ms.py` using `oriented_ms`;
3. analytical signature validation;
4. the small logistic diagnostic upper bound.

Send the files printed by the launcher before Stage 12 is frozen.

---

# Track B — model-family coverage

| Research idea | Status | Current implementation / next action |
|---|:---:|---|
| context analyzer: blur/noise/texture/frequency/coherence/heterogeneity | 🟢 | implemented; texture leakage remains key failure mode |
| hierarchical coarse/fine MFI | 🟢 | implemented; fine-scale independence now being audited |
| conditional fuzzy operators | 🟢 | implemented |
| distorted-probability capacities | 🟢 | implemented |
| scale-specific learned capacities | 🟢 | implemented/tested; no headline gain yet |
| global / regime Shapley | 🟡 | machinery exists; utility definition needs threshold-free revision |
| SWAFED | 🟢 | implemented |
| d-CF / d-CC / d-XC / d-Choquet | 🟢 | implemented |
| Choquet-inspired aggregation | 🟢 experimental | implemented |
| partition-conditioned aggregation | 🟢 experimental | implemented |
| dynamic classical localizer bank | 🟢 | implemented; still needs fixed-Scharr ablation |
| uncertainty from multiscale disagreement | 🟢 | implemented; texture-sensitive |
| granularity control | 🟡 | useful signal, not yet cross-dataset validated |
| genuinely scale-sensitive oriented descriptors | 🟢 code / 🟡 validation | new `oriented_ms`; historical mode preserved |
| signature-derived structural evidence | 🟢 code / 🟡 active | Stage 11b |
| edge-signature fuzzy memberships | 🔴 Stage 12 | derive only from stable Stage-11b properties |
| formal/general k-interactive learning | 🔴 | future if compact interactions prove useful |
| explicit Fourier/multiband branch | 🔴 | frequency currently contextual only |
| learned operator/localizer router | 🔴 | CH-MFI-v3 |
| learned dynamic convolution | 🔴 | CH-MFI-v3 |
| annotator/GT uncertainty | 🔴 | planned for BSDS |
| ranking loss | 🔴 | future learned/ranking stage |
| fuzzy detector ensemble (TEED/PiDiNet/etc.) | 🔴 | CH-MFI-Hybrid |

---

# Track C — validation and datasets

| Milestone | Status | Notes |
|---|:---:|---|
| deterministic synthetic primitives | 🟢 | exact GT; mechanism diagnosis |
| robust synthetic benchmark v2 | 🟢 | clean + degradations |
| UDED development protocol | 🟢 | 15 selection / 15 held-out convention preserved |
| UDED edge-signature study | 🟢 code / 🟡 active | current Stage 11b development basis |
| official BSDS500 train/val/test | 🔴 | required before publication claims |
| official Berkeley bipartite matching | 🔴 | current tolerant matcher is a development proxy |
| BSDS individual-annotator signature/uncertainty | 🔴 | preserve individual annotations |
| BIPED signature replication | 🔴 | test cross-dataset stability of discovered properties |
| cross-dataset detector generalization | 🔴 | freeze on one dataset and evaluate on another |
| resolution sensitivity | 🔴 | repeat finalists beyond 256 px |

---

# Track D — intended Stage 12 logic

If Stage 11b confirms stable structure, do **not** train an end-to-end black-box detector. Derive image-only memberships such as:

```text
image
 -> genuinely multiscale structural properties
 -> frozen fuzzy memberships
 -> non-additive signature aggregation
 -> signature/context score
 -> precise fixed/dynamic localizer control
 -> NMS
 -> final boundary score
```

Keep three classes distinct:

1. **Signature-informed analytical MFI** — preferred scientific line; no trained classifier at inference.
2. **Signature-calibrated MFI** — a small number of membership/capacity parameters learned on train and frozen.
3. **Signature-learned diagnostic model** — logistic/GAM/small network used only to test whether the feature space contains enough information.

If the learned diagnostic is strong but analytical MFI is weak, the bottleneck is aggregation/modeling. If both are weak, revise the descriptor/signature space before another large sweep.

---

# Track E — CH-MFI-v3 / Hybrid

Only after the interpretable v2/signature line is understood:

- learned context/router network;
- learned dynamic localizer kernels;
- explicit Fourier branch;
- annotation-aware uncertainty;
- ranking loss;
- fuzzy detector ensemble with TEED/PiDiNet or similar compact learned detectors;
- optional differentiable fuzzy-capacity layer.

---

# Track F — WebUI and promotion

The WebUI is an inspection/deployment surface, not a benchmark. A model is eligible only when exact config, validation rule, frozen threshold, held-out/test result and qualitative outputs are preserved reproducibly.

No current CH-MFI-v2 or Stage-11 signature candidate is promoted yet.

Promotion flow:

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
- `PAPER_WRITING_PLAN.md`
- `references.bib`

Before manuscript freeze, rerun promoted models under official evaluation, verify bibliographic metadata, preserve commit/config/environment, and verify that claimed signature properties reproduce across independent datasets.

## Roadmap maintenance rule

Update this file whenever a model family, benchmark, dataset, paper or negative result changes the scientific direction. Update the corresponding `docs/paper/` record in the same development cycle so roadmap status, evidence and future manuscript claims remain synchronized.
