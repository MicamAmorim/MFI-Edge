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

The project has moved through four active research phases:

1. **MFI-Classic** — multiscale fuzzy evidence, ROI/refinement, classical localizer, NMS/linking.
2. **MFI-Fuzzy++ / Stage 5–7** — broad fuzzy-measure/operator/fusion competition and UDED generalization testing.
3. **CH-MFI-v2 / Stage 9–10** — context-aware, hierarchical, uncertainty-aware fuzzy evidence that controls spatial localization rather than merely being added to it.
4. **Stage 11 — Edge Signature Discovery** — current active diagnostic phase: use GT to discover image-derived structural properties that distinguish true boundaries from texture/near-edge hard negatives, then translate only the stable properties into an analytical/fuzzy Stage-12 model.

The new guiding question is no longer only “which fuzzy measure is best?” but:

> **What properties make a true image boundary different from a high-gradient non-boundary, and can those properties be represented by an interpretable multiscale fuzzy model that generalizes across datasets?**

---

## Latest evidence — CH-MFI-v2 learned-bank rerun

### First standard screen

The initial **519-configuration** UDED screen used 3-fold inner-CV on the 15-image selection half and frozen thresholds on 15 held-out images. The formal winner was:

`v2_std__distprob_g055__global_local__conditional__g0.75__soft`

but did **not** beat Scharr:

| Metric | CH-MFI-v2 winner | Scharr |
|---|---:|---:|
| selection CV F1 | 0.71857 | **0.76610** |
| selection ODS | 0.71991 | **0.76642** |
| held-out F1 | 0.71325 | **0.76204** |

Held-out delta F1 was **-0.04879**, with paired-bootstrap 95% CI **[-0.10097, -0.00560]**.

### Learned scale/regime rerun

The second standard run resumed the 519 completed configurations and appended 12 learned variants, for **531 configurations total**.

Best learned variants by selection CV F1:

| Learned variant | CV F1 | Selection ODS |
|---|---:|---:|
| scale bank, additive, g=.75 | **0.71133** | 0.71230 |
| scale bank, distorted gamma=.85, g=.75 | **0.71133** | 0.71237 |
| scale bank, regularized pair, g=.75 | **0.71133** | 0.71197 |
| regime Shapley, g=.50 | **0.70811** | 0.70679 |

The original unlearned winner remained the formal selection winner and its frozen held-out result remained **0.71325 F1**. Therefore the first learned scale/regime additions did **not** close the Scharr gap.

### Important diagnostic findings

- The scale-capacity analysis is informative: feature relevance changes between coarse and fine scales, while 3x3 and 5x5 are nearly redundant under the current descriptors.
- Several current descriptors are strongly correlated/redundant, especially gradient/normal-contrast families and Laplacian/Hessian families.
- The first regime-Shapley utility was not sufficiently discriminative: for several regimes, re-optimizing final F1 threshold made non-empty descriptor coalitions effectively equivalent. Those Shapley values must not be treated as meaningful scientific attribution.
- This motivates threshold-free descriptor utility (AUC/AP/ranking) and a direct study of true-edge vs hard-negative signatures.

**Wide remains blocked.** More brute-force combinations of the same descriptor space are not justified yet.

---

# Track A — Stage 11: Edge Signature Discovery

| Milestone | Status | Definition / next action |
|---|:---:|---|
| Stage-11 signature primitives | 🟢 | `src/edge_signature.py` computes scale-resolved and structural properties |
| GT population sampler | 🟢 | edge / near-edge / high-gradient texture / easy-background populations |
| selection-only signature discovery | 🟢 code / 🟡 **run now** | AUC, AP, mutual information, effect size and redundancy filtering |
| held-out signature check | 🟢 code / 🟡 **run now** | candidate signature frozen from selection and evaluated on held-out samples |
| structural descriptors | 🟢 code / 🟡 validate | orientation consistency, normal/tangent ratio, step consistency, step-likeness, scale persistence, coarse/fine balance |
| candidate analytical signature | 🟢 code / 🟡 validate | fuzzy-ready membership parameters selected without held-out tuning |
| diagnostic learned upper bound | 🟡 optional | logistic diagnostic exists conceptually; first campaign is intentionally analytical |
| cross-dataset signature stability | 🔴 | repeat on BSDS500/BIPED; only stable properties should drive final architecture |
| Stage-12 signature-informed MFI | 🔴 | convert stable signature properties into explicit fuzzy memberships/capacities |

Run now:

```powershell
git pull
.\run_stage11_signature.bat
```

Expected outputs under `results/local_dev/edge_signature/`:

- `SIGNATURE_REPORT.md`
- `candidate_signature.json`
- `diagnostic_results.json`
- `descriptor_pairwise_summary.csv`
- `group_statistics.csv`
- `population_counts.csv`
- `top_feature_distributions.png`
- `cross_scale_auc.png`
- `candidate_signature_correlation.png`

The first Stage-11 run is intentionally **not** the final detector. GT is used only to discover properties; inference-time Stage 12 must compute those properties from the image alone.

---

# Track B — CH-MFI-v2 ablation campaign

Run after Stage 11 tells us which evidence is actually informative.

| Milestone | Status | Definition / latest result |
|---|:---:|---|
| v2 architecture modules | 🟢 | contextual/hierarchical/uncertainty/localizer paths execute |
| first standard screen, 519 configs | 🟢 | negative vs Scharr |
| scale-specific capacity bank | 🟢 | learned and tested; did not improve winner |
| regime-specific Shapley v1 | 🟢 run / 🟡 method revision | final-F1 utility collapsed for several regimes; replace with threshold-free utility |
| standard rerun, 531 configs | 🟢 | learned variants appended; winner unchanged |
| fixed Scharr vs dynamic localizer | 🔴 | isolate whether adaptive localizer is a major source of degradation |
| MFI gating on/off | 🔴 | isolate contextual evidence contribution |
| uncertainty on/off | 🔴 | current uncertainty map is texture-sensitive |
| hierarchy flat vs global/local | 🔴 | test after signature descriptors are available |
| topology competition | 🟢 code / 🟡 deferred | only after continuous score approaches baseline |
| wide overnight sweep | 🔴 **blocked** | no wide sweep until signature/ablation phase shows credible improvement |
| image-size sensitivity | 🔴 | repeat finalists above 256-px development resolution |

---

# Track C — model-family coverage

| Research idea | Status | Current implementation / next action |
|---|:---:|---|
| context analyzer: blur/noise/texture/frequency/coherence/heterogeneity | 🟢 | implemented; texture leakage remains a key failure mode |
| hierarchical coarse/fine multiscale MFI | 🟢 | global/local available; signature stage may redefine the hierarchy |
| conditional fuzzy operators | 🟢 | implemented; best v2 candidate uses conditional mode |
| distorted-probability capacities | 🟢 | gamma .55 produced best initial v2 candidate |
| scale-specific learned capacities | 🟢 | learned/tested; not enough by themselves |
| global Shapley gating | 🟢 | exact coalition machinery exists |
| regime-specific Shapley | 🟡 | code works, but utility must change from threshold-optimized final F1 to AUC/AP/ranking |
| regularized pair interactions | 🟢 | available; current descriptor redundancy is high |
| formal/general k-interactive learning | 🔴 | defer until interaction evidence is stronger |
| SWAFED local adaptive exponent | 🟢 | retained for scientific comparison |
| d-Choquet / d-CF / d-CC / d-XC | 🟢 | implemented experimental families |
| Choquet-inspired aggregation | 🟢 experimental | retain; theorem-level audit still needed |
| partition-conditioned aggregation | 🟢 experimental | retain as alternative grouping mechanism |
| dynamic classical localizer bank | 🟢 | needs fixed-Scharr ablation |
| MFI bilateral/soft controller | 🟢 | implemented; current versions remain below baseline |
| model uncertainty from multiscale disagreement/entropy | 🟢 | implemented; needs texture-aware redesign/ablation |
| granularity control | 🟡 | evidence suggests scale preference should be contextual |
| topology repair/linking | 🟢 code | deferred until continuous score improves |
| **signature-derived structural evidence** | 🟢 code / 🟡 active | Stage 11: move from filter responses toward properties of boundaries |
| explicit Fourier/multiband branch | 🔴 | frequency is currently contextual only |
| learned operator/localizer router | 🔴 | future v3 direction |
| learned dynamic convolution | 🔴 | future Mask2Edge-inspired direction |
| annotator/GT uncertainty | 🔴 | planned for BSDS multi-annotator supervision |
| ranking loss / RankED-style supervision | 🔴 | future learned/ranking stage |
| fuzzy detector ensemble (TEED/PiDiNet/etc.) | 🔴 | future CH-MFI-Hybrid generation |

---

# Track D — validation and datasets

| Milestone | Status | Notes |
|---|:---:|---|
| deterministic synthetic primitives | 🟢 | exact GT; mechanism diagnosis |
| robust synthetic benchmark v2 | 🟢 | clean + degradation families |
| UDED selection/held-out development protocol | 🟢 | useful small natural-image diagnostic dataset |
| UDED edge-signature study | 🟢 code / 🟡 active | current Stage 11 development basis |
| official BSDS500 train/val/test | 🔴 | required before strong publication claims |
| official Berkeley bipartite boundary matching | 🔴 | current tolerant matcher is a prototype, not official evaluation |
| BSDS individual-annotator signature/uncertainty | 🔴 | preserve individual annotations rather than immediately collapsing GT |
| BIPED signature replication | 🔴 | important for cross-dataset stability of discovered properties |
| cross-dataset generalization | 🔴 | freeze on one dataset and evaluate on another |
| resolution sensitivity | 🔴 | 256 px is a development compromise |

---

# Track E — Stage 12: Signature-informed analytical MFI

This is the intended next model generation if Stage 11 succeeds.

Conceptual target:

```text
image
  -> multiscale structural measurements
  -> fuzzy memberships for stable edge properties
       - normal dominance
       - orientation consistency
       - multiscale persistence
       - step-likeness
       - texture rejection
       - other properties supported by Stage 11
  -> non-additive/contextual aggregation
  -> precise localizer control
  -> NMS / threshold / optional topology
  -> edge map
```

Three model classes must remain distinct:

1. **Signature-informed analytical MFI** — preferred scientific line; no trained classifier at inference.
2. **Signature-calibrated MFI** — a small number of membership/capacity parameters learned on train and frozen.
3. **Signature-learned diagnostic model** — logistic/GAM/small network used only to test whether the feature space contains enough information.

If a learned diagnostic performs strongly but analytical MFI does not, the bottleneck is aggregation/modeling. If neither works, the descriptor/signature space itself is inadequate.

---

# Track F — CH-MFI-v3 / Hybrid

Only after the interpretable Stage-11/12 evidence is understood:

- learned context/router network;
- learned dynamic convolution/localizer kernels;
- explicit frequency/Fourier branch;
- annotation-aware uncertainty target;
- ranking loss on boundary confidence;
- detector-level fuzzy ensemble with TEED/PiDiNet or similar compact detectors;
- optional end-to-end differentiable fuzzy-capacity layer.

Keeping this later protects scientific attribution: determine how far the fuzzy/analytical architecture goes before deep learned components are introduced.

---

# Track G — WebUI and promotion

The WebUI is an inspection/deployment surface, not a benchmark.

A model is eligible for the `mfi-edge-webui` registry only when all are recorded:

1. exact code/config identifier;
2. validation protocol and ranking metric;
3. frozen threshold or explicit visualization-only fallback;
4. held-out/test metric reported only after selection;
5. qualitative outputs checked for obvious failure modes;
6. benchmark result preserved reproducibly.

**No current CH-MFI-v2 candidate is eligible for promotion.**

Promotion flow:

```text
mfi-edge-local-dev
      -> validated configuration
      -> main
      -> mfi-edge-webui registry
```

---

# Track H — paper/research record

Maintained under `docs/paper/`:

- `ARCHITECTURE_MAP.md` — editable diagrams;
- `BIBLIOGRAPHY_MATRIX.md` — architecture-driving current literature;
- `LEGACY_REVIEW_CORPUS.md` — historical SLR corpus;
- `EXPERIMENT_HISTORY.md` — chronological evidence/failures;
- `PAPER_WRITING_PLAN.md` — manuscript evidence map;
- `references.bib` — working BibTeX library.

Before manuscript freeze:

- verify all TODO bibliographic metadata;
- resolve the 2026 FSS PII `S0165011426003714` if cited;
- label external-method implementations as faithful reproduction, paper-inspired, or our generalization;
- rerun promoted models under official evaluation;
- create publication-quality vector diagrams;
- preserve environment, commit SHA, configs and raw result tables;
- verify that signature properties reproduce across datasets before presenting them as general edge properties.

## Roadmap maintenance rule

Update this file whenever a model family, benchmark, dataset, paper or negative result changes the scientific direction. Update the corresponding `docs/paper/` record in the same development cycle so roadmap status, evidence and future manuscript claims remain synchronized.
