# Experimental history — MFI-Edge research log

This document reconstructs the experimental decisions discussed during development so the future manuscript can distinguish **historical exploration**, **current evidence**, and **results that are publication-grade only after rerunning with the final protocol**.

## Status labels

- **Historical** — useful for the design story, but superseded by later protocol or implementation changes.
- **Exploratory** — technically meaningful, but based on synthetic data, small datasets, approximate boundary matching, or development-time calibration.
- **Candidate result** — protocol is reasonably strict (selection/held-out separation), but still needs replication with official benchmark tooling / larger datasets.
- **Final-paper target** — experiment that should be rerun before submission.

---

## Stage 0–2 — early prototype and validation correction

**Status:** Historical.

The original prototype established the core idea of using generalized Choquet-style aggregation of local image descriptors to build an MFI evidence map.  Early synthetic benchmark values from the first dataset version were later **superseded** after identifying a mismatch in diagonal ground-truth generation/evaluation.  Those numerical results must not be quoted in a paper.

What survived conceptually:

```text
image -> local/multiscale fuzzy evidence -> MFI ranking -> edge localization
```

Important methodological lesson: synthetic GT generation and tolerance matching must be validated independently before comparing operators.

---

## Stage 3 — orientation-aware descriptors

**Status:** Exploratory, useful architectural evidence.

### Main change

The descriptor stack was expanded from legacy/rotation-invariant cues to orientation-aware cues using the local gradient normal/tangent.  Important new responses included normal contrast, normal-minus-tangent contrast, and a steered Hessian response.

### Hard-angle synthetic test

| Method | ODS |
|---|---:|
| MFI-SCHARR oriented | **0.5633** |
| MFI-SCHARR legacy | 0.4961 |
| Scharr | 0.4401 |

MFI-only oriented ROC-AUC was approximately **0.7978**, indicating that the MFI map could rank edge regions well even when it was not yet the final pixel localizer.

### Interpretation

This stage produced the first strong clue that later became central to CH-MFI:

> MFI may be more valuable as **context/evidence/ranking** than as the final subpixel localization mechanism.

---

## Stage 4 — robust synthetic pipeline + topology repair

**Status:** Exploratory; strongest synthetic evidence so far.

### Selected synthetic architecture

```text
Input
 -> Median 3x3
 -> oriented multiscale descriptors {25,13,7,5,3}
 -> CF1F2(CL,CL), power q=0.1
 -> empirical functional-information surprisal
 -> MFI percentile confidence
 -> ROI top 40% (q_ROI=0.60)
 -> Scharr fine localizer
 -> oriented NMS
 -> validation-frozen threshold
 -> MFI-guided geodesic linking
 -> edge map
```

### Operator reranking on robust validation

| Operator | ROI q | ODS | OIS | AP |
|---|---:|---:|---:|---:|
| CF1F2(CL,CL) | .60 | **.91336** | .91426 | **.94388** |
| CC(CL) | .60 | essentially tied | — | — |
| CF1F2(TM,CL) | .60 | .91069 | .90822 | .93832 |

No statistical superiority between the first two should be claimed from this screen alone.

### Conditioning screen

| Preconditioner | ODS | OIS | AP | R50 |
|---|---:|---:|---:|---:|
| Median 3x3 | **.91336** | **.93131** | **.95414** | **.97018** |
| Gaussian sigma .6 | .85988 | .88561 | .88914 | .94142 |
| Box 3x3 | .84215 | .85898 | .87644 | .91708 |
| None | .82727 | .88837 | .83137 | .93380 |

A second conditioner after Median3 was not selected; bilateral, anisotropic, gravitational and mean-shift variants did not improve ODS in that experiment.

### Geodesic linking

Selected parameters: maximum gap approximately 8 px and maximum mean cost .60.

| Variant | ODS | Recall | Components | Largest-component GT coverage | Endpoints |
|---|---:|---:|---:|---:|---:|
| MFI geodesic | **.91975** | **.85195** | **5.18** | **.53684** | **7.95** |
| None | .91336 | .84085 | 13.68 | .30312 | 24.25 |
| Morphological closing r=2 | .91181 | .83830 | 12.83 | .31719 | 22.98 |

A representative synthetic rectangle with a gap changed from roughly 19 components / .086 GT coverage / 38 endpoints to 1 component / .898 coverage / 2 endpoints, while tolerant F1 remained almost unchanged. This demonstrates why connectivity metrics need to supplement pointwise PR/F scores.

### Held-out synthetic set (60 images)

Selected using validation only:

- Median3
- oriented features
- CF1F2(CL,CL)
- q=.1
- scales 25,13,7,5,3
- ROI=.60
- Scharr+NMS
- geodesic gap=8 / cost=.60
- frozen binary threshold=1.0

Final linked binary result:

- Precision: **.9971567**
- Recall: **.8420170**
- F1: **.9130436**

Without linking:

- Precision: .9975038
- Recall: .8315966
- F1: .9070260

Continuous held-out comparison:

| Method | ODS | OIS | AP | R50 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| MFI-Edge-SCHARR | **.90703** | **.92383** | **.96024** | **.96927** | **.71896** |
| Sobel | .86314 | .90892 | .88483 | .94666 | .65445 |
| Prewitt | .84738 | .89760 | .87980 | .94693 | .60975 |
| Scharr | .82563 | .89478 | .80825 | .91293 | .67792 |

### Robustness by degradation, linked F1

| Degradation | F1 |
|---|---:|
| Salt-and-pepper | .99490 |
| Clean | .98139 |
| Illumination | .96717 |
| Blur | .94000 |
| Gaussian noise | .93463 |
| Artificial gap | .92972 |
| Speckle | .92429 |
| Texture | .82715 |
| Compound | .78601 |
| Motion blur | **.76868** |

Weakest regimes: **motion blur, compound degradation, texture**.  These failures directly motivated local context routing, frequency descriptors and a dynamic localizer bank.

---

## Stage 5 — fuzzy-measure competition

**Status:** Exploratory/candidate; established that q=.1 should not be treated as canonical.

### Selection split preliminary screen

| Measure | ODS | OIS | AP | R50 | ROI-GT coverage |
|---|---:|---:|---:|---:|---:|
| Sugeno-lambda, singleton sum .60 | **.9141** | **.9212** | **.9524** | **.9758** | **.9901** |
| Power q=1.5 | .9137 | .9205 | .9498 | .9712 | .9817 |
| Power q=.1 | .9131 | .9199 | .9486 | .9696 | .9707 |
| Power q=.4 | .9128 | .9192 | .9484 | .9694 | .9754 |
| Power q=.2 | .9123 | .9202 | .9497 | .9722 | .9823 |
| Sugeno-lambda singleton sum .80 | .9093 | .9139 | .9464 | .9686 | .9811 |
| learned 2-additive | .9079 | .9134 | .9443 | .9666 | .9796 |
| learned additive | .9063 | .9113 | .9422 | .9633 | .9779 |

### Synthetic held-out reordering

| Measure | ODS | OIS | AP | R50 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| Power q=1.5 | **.9209** | **.9215** | **.9578** | **.9830** | **.7344** |
| Sugeno-lambda .60 | .9199 | .9208 | .9564 | .9790 | .7331 |
| Power q=.2 | .9192 | .9193 | .9543 | .9744 | .7327 |
| Power q=.1 | .9178 | .9116 | .9510 | .9693 | .7319 |

### Interpretation

- The best capacity can change between selection and held-out.
- The original highly concave power q=.1 is not uniquely privileged.
- Learned/contextual capacities deserved explicit investigation.
- Shapley/interactions indicated that the orientation-aware descriptors, especially normal contrast and normal-minus-tangent, were important but partly redundant with Gabor-like evidence.

---

## Stage 6 — first strict natural-image test on UDED

**Status:** Candidate result; small dataset and approximate matching.

Dataset protocol:

- UDED 30 natural images
- 15 selection, 15 held-out
- threshold selected only on selection and then frozen
- paired bootstrap: 5,000 samples

### Baseline

Scharr+NMS held-out:

- Precision .6671
- Recall .8885
- F1 **.76204**

### Formally selected model

Power q=.2 + residual lambda=.25:

- Held-out F1 **.76210**
- Delta F1 vs Scharr: approximately **+.000056**
- 95% paired-bootstrap CI: approximately **[-.00226, .00261]**
- P(Delta F1 > 0): approximately **.503**

Interpretation: effective tie with Scharr.

### Interesting non-winning signal

`context_additive_estimated + residual .25`:

- Held-out F1 .76354
- Delta approximately +.00149
- CI approximately [-.00080, .00395]
- P(Delta>0) approximately .891

A post-hoc residual .50 variant reached approximately .76434 but **must not be called the winner**, because it was noticed after opening held-out results.

### Architectural consequence

Adaptive MFI confidence was often more concentrated on GT-edge pixels, but direct score fusion failed to turn that ranking advantage into a reliable final-edge improvement.  This strongly motivated separating **context/evidence** from **localization**.

---

## Stage 7 — exhaustive UDED measure × fusion screen

**Status:** Candidate negative/diagnostic result.

- 35 fuzzy measures
- 45 fusion strategies per measure
- **1,575 configurations**
- threshold selection separated from held-out
- paired bootstrap for finalists

### Selection winner

`local_additive_evidence + soft_e0.25_g0.5`

Selection ODS approximately **.77059**.

### Frozen held-out

- selected model F1 approximately **.75644**
- Scharr baseline approximately **.76204**
- Delta F1 approximately **-.00561**
- 95% bootstrap CI approximately **[-.01344, .00370]**

### Interpretation

A larger search did **not** prove a natural-image advantage.  The selection winner generalized worse. This is scientifically useful: flexible fuzzy models can overfit a tiny selection set, and direct fusion is likely the bottleneck.

This result motivated:

- inner cross-validation;
- compact/regularized capacities;
- context-conditioned routing;
- CH-MFI bilateral architecture;
- moving heavyweight sweeps to a 32 GB local workstation rather than the 1 GB Railway service.

---

## Stage 8 — contextual inner-CV experiment on Railway

**Status:** **Pending final result** at the time this research log was written.

Stage 8 added:

- local heterogeneity context;
- contextual residual/exponential/soft/hysteresis controllers;
- local mixture-of-measure routing;
- 3-fold inner-CV on the selection half before held-out evaluation;
- persisted checkpoints and 5,000-bootstrap finalization.

Infrastructure history:

1. one attempt failed before processing because UDED was not materialized as expected;
2. the downloader was rewritten to fetch/extract the UDED archive and explicitly verify `test_pair.lst`;
3. a later Railway run reached `PREPARE_UDED_OK` and began the benchmark, but the 1 GB service was operating very near its RAM ceiling.

Do **not** insert a Stage-8 performance number into a manuscript until `summary.json` and the frozen held-out output have been retrieved and audited.

---

## Stage 9 / local CH-MFI-v1

**Status:** Current workstation development family.

First local branch introduced:

- context maps (heterogeneity, blur, texture, noise, HF/LF, coherence);
- hierarchical coarse/fine MFI;
- conditional fuzzy operator experts;
- distorted-probability capacities;
- generic restricted-dissimilarity branch;
- dynamic localizer bank;
- model uncertainty from scale disagreement/entropy;
- bilateral MFI-to-localizer control;
- exact global descriptor Shapley on selection only;
- smoke / standard / wide parameter grids;
- checkpoint/resume and thread-scaling benchmark.

This is the first architecture explicitly designed around the hypothesis:

> **MFI should control/refine a precise edge localizer rather than merely add another edge score.**

---

## Stage 10 / local CH-MFI-v2 — second-wave literature-driven family

**Status:** Implemented, awaiting workstation execution.

Added after the 2026 literature review:

- image-neighbourhood SWAFED q maps (faithful to the official source structure, including a separate literal-repository Lukasiewicz option);
- d-CF, d-CC, d-XC and d-Choquet families;
- larger restricted-dissimilarity set;
- Choquet-inspired aggregation;
- partition-conditioned Choquet-inspired aggregation;
- regularized pair-interaction / k-interaction surrogate;
- exact **regime-specific Shapley** learning;
- **scale-specific learned capacity banks**;
- second-stage none/hysteresis/geodesic/hysteresis+geodesic topology competition.

The v2 experiments live in the `mfi-edge-local-dev` branch and should be run first with smoke, then standard, then wide only after profiling the Ryzen workstation.

---

# Results that can and cannot be quoted later

## Safe as development motivation

- orientation-aware descriptors helped strongly on hard synthetic angles;
- Median3 was the best tested preconditioner in the Stage-4 synthetic benchmark;
- geodesic linking greatly improved synthetic continuity metrics;
- q=.1 is not uniquely optimal;
- UDED exposed a generalization gap between selection and held-out;
- direct MFI+Scharr fusion is not yet supported as superior to Scharr on UDED.

## Must be rerun before final claims

- every headline ODS/OIS/AP number using the current morphology-based tolerance matcher;
- learned capacity comparisons on only 15 UDED selection images;
- any model selected after observing held-out behavior;
- H0/surprisal calibration that uses the same image under evaluation;
- final SOTA comparison against modern learned edge detectors.

---

# Final-paper experimental target

The publication-grade pipeline should eventually be:

```text
BSDS500 train
 -> learn/freeze H0, capacities, Shapley/regime models and any trainable router
BSDS500 val
 -> architecture/hyperparameter/threshold selection
BSDS500 test
 -> official Berkeley boundary evaluation
UDED + BIPED (+ optional Multicue/NYUD)
 -> untouched cross-dataset/generalization tests
```

Report:

- ODS / OIS / AP under official protocol;
- precision / recall / F1 for fixed-threshold deployment experiments;
- paired bootstrap / permutation intervals across images;
- family-level ablations;
- worst-regime / robustness metrics;
- connectivity metrics for topology variants;
- runtime, memory, throughput and parameter count where applicable;
- Shapley and interaction analyses as explanatory outputs rather than only leaderboard metrics.
