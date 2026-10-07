# Future paper writing plan — MFI-Edge / CH-MFI

This is not a manuscript draft. It is an **evidence map** telling us what must be read, what figures/tables should exist, and which experiment supports each claim. It should prevent the final article from becoming a reconstruction from memory.

## Provisional scientific story

The current evidence supports a stronger story than “we tried several fuzzy measures.” The emerging research question is:

> **Can a context-aware non-additive information-fusion model decide what evidence to aggregate, how to aggregate it, at which scale to trust it, and how that evidence should control precise edge localization under heterogeneous natural-image conditions?**

The paper should therefore compare **families/architectural hypotheses**, not merely list thousands of parameter configurations.

---

# 1. Introduction

## Problem to establish

Edge detection must reconcile conflicting objectives:

- precise localization;
- robustness to noise/blur/texture;
- multiscale structure;
- ambiguity among human annotations;
- generalization across datasets/degradations;
- computational efficiency and interpretability.

## Literature to read closely

- E01 Arbelaez/BSDS evaluation.
- E02 TEED/UDED for generalization.
- E05 NBED for spatial/context decoupling.
- E07 UAED + E08 RankED for annotation uncertainty.
- E09 MuGE for granularity.
- F06/F07 for our systematic-review positioning.

## Motivation from our experiments

Use Stage 4 vs Stage 6/7 contrast:

- synthetic MFI gating can produce strong gains and continuity improvements;
- natural UDED data showed that good MFI ranking does not automatically become better edge localization;
- therefore context and localization should be treated as related but distinct tasks.

Do not present Stage-4 synthetic numbers as final SOTA evidence; use them as motivation/ablation history unless rerun under the final evaluator.

---

# 2. Related work

Recommended subsections:

## 2.1 Classical and learned edge detection

HED → RCF → BDCN → PiDiNet → EDTER → TEED → UAED/RankED/MuGE → Mask2Edge/NBED/DiffusionEdge.

Main angle: modern systems repeatedly rediscover multiscale, local/global separation, uncertainty, difference operators and context-dependent processing.

## 2.2 Fuzzy aggregation and Choquet-based edge detection

F01, F03–F09.

Explain:

- capacities and non-additivity;
- CF/CC/CF1F2 generalized Choquet family;
- adaptive fuzzy measures;
- restricted dissimilarity functions;
- why descriptors may be synergistic or redundant.

## 2.3 Learning and simplifying fuzzy measures

F10–F12.

Contrast:

```text
fully free capacity
<-> expressive but data-hungry / exponential

additive capacity
<-> stable but cannot represent interactions

compact distorted / regularized interaction families
<-> intermediate point tested here
```

## 2.4 Contextual, hierarchical and input-dependent fuzzy aggregation

F13–F19.

This subsection leads directly into the method:

- Shapley as **active feature selection**, not only explanation;
- hierarchical Choquet across different semantic levels;
- conditional operators;
- Choquet-inspired / partition-conditioned aggregation.

---

# 3. Method

## 3.1 Overview figure

Use the global diagram from `ARCHITECTURE_MAP.md` as the basis for **Figure 1**.

The diagram should emphasize two principal branches:

```text
Fuzzy context/evidence branch
Spatial localization branch
```

They are coupled by a contextual controller.

## 3.2 Input conditioning and oriented descriptors

Document the current descriptor names exactly from `src/features.py` before writing the final equations.

Include Stage-3 orientation ablation as supporting evidence.

## 3.3 Context analyzer

Define context vector/map:

\[
z(x)=[h(x), b(x), t(x), n(x), f_{HF}(x), f_{LF}(x), c(x), \theta(x)]
\]

where the terms represent heterogeneity, blur, texture, noise proxy, frequency information, coherence and orientation.

Make clear these are currently **handcrafted context proxies**, not calibrated posterior probabilities.

## 3.4 Descriptor selection by Shapley

Read F13 carefully before finalizing notation.

Global candidate:

\[
\phi_i = \sum_{S\subseteq N\setminus\{i\}} \frac{|S|!(n-|S|-1)!}{n!}[v(S\cup\{i\})-v(S)].
\]

Regime version:

\[
\phi_i^{(r)},\quad r\in\{clean,texture,blur,noise\}.
\]

Explain that the utility must be fitted only on development/training data.

## 3.5 Within-scale nonadditive aggregation

Present the competing family, not every grid value:

- classical CF / CC / CF1F2;
- SWAFED local power capacity;
- distorted probability;
- regularized pair-interaction capacity;
- d-CF/d-CC/d-XC;
- Choquet-inspired;
- partition-conditioned aggregation.

Parameter tables go to supplementary material.

## 3.6 Hierarchical multiscale aggregation

Core equation:

\[
E_s(x)=A_{m_s,z}(D_s(x)),
\]

\[
E_C=A_C(E_{25},E_{13}),\qquad
E_F=A_F(E_7,E_5,E_3),
\]

\[
M(x)=A_T(E_C,E_F;g),
\]

where `g` is the granularity control.

Read F14 and E04/E09 carefully here.

## 3.7 Model uncertainty

Current inference uncertainty:

\[
U(x)=\alpha_U\,\mathrm{rank}(\operatorname{Var}_s E_s(x))
 +(1-\alpha_U)H(\tilde E_s(x)).
\]

Explicitly distinguish this from **annotation uncertainty**, which belongs to the future UAED/RankED training extension.

Stage 14o adds a narrower inference-time uncertainty hypothesis for the compact
controller: disagreement among the five fitted memberships produces an
interval width, a convex Choquet-to-additive capacity field, and explicit
reliability attenuation. Keep this separate from both the older broad CH-MFI
scale/entropy uncertainty expression above and human-annotation uncertainty.
It is preregistered for UDED repeated CV plus official BSDS500-validation
ODS/OIS/AP; no positive claim is allowed until both development axes complete.

Stage 14o ultimately failed its conjunctive rule: all UDED non-collapse
conditions failed, and the completed official BSDS-val attachment improved
ODS/OIS slightly while reducing AP. Present this as a mixed operating-point
shift, not as a benchmark improvement. Stage 14p then tested a mechanistically
distinct fixed Ambrosio–Tortorelli phase field. It raised UDED precision and
BSDS-val ODS, but caused a large UDED recall/F1 loss and reduced BSDS-val OIS
and AP. Present it as a rejected operating-point sharpening effect, not a
variational improvement or retained model.

Stage 14q tests a fixed small anisotropic directional atom bank
as a shearlet-motivated singularity localizer under the unchanged compact
Choquet gate. Be explicit that this is a bounded discrete operationalization,
not a reproduction of the continuous shearlet transform. No positive claim is
allowed until both UDED repeated CV and official BSDS-val criteria pass.

## 3.8 Dynamic localization branch

Current bank:

- Scharr;
- Sobel;
- DoG sigma 1;
- DoG sigma 2.

Context routes localizer weights. Position this as an interpretable analogue of the dynamic pixel-difference idea motivating E06, not as a reproduction of Mask2Edge.

## 3.9 Bilateral/contextual controller

Current exponential candidate:

\[
S(x)=L(x)\exp[\alpha(M(x)-0.5)-\beta U(x)].
\]

This is a crucial equation because it encodes the core natural-image lesson: MFI changes the **confidence in a localizer**, rather than replacing localization.

## 3.10 Thresholding and topology

Compare:

- frozen single threshold;
- hysteresis;
- geodesic linking;
- hysteresis + geodesic linking.

Report both boundary metrics and continuity metrics.

---

# 4. Experimental methodology

## Datasets

Minimum final set:

- BSDS500 — train/val/test, multiple annotators, official boundary evaluation;
- UDED — untouched generalization/cross-dataset test;
- BIPED — real edge-specific dataset;
- optional Multicue / NYUD if the paper needs a stronger cross-domain claim.

Synthetic data should remain as a **controlled robustness study**, not the primary benchmark.

## Data separation

Target protocol:

```text
TRAIN
  learn H0 / capacities / Shapley / trainable context router

VALIDATION
  model family / hyperparameters / threshold / topology selection

TEST
  one-shot frozen evaluation

EXTERNAL DATASETS
  cross-dataset test without tuning
```

For the current UDED development branch, retain alternating selection/held-out only as a temporary small-data protocol.

## Metrics

Boundary quality:

- ODS;
- OIS;
- AP;
- fixed-threshold precision/recall/F1 for deployment analysis.

Topology:

- edge components overlapping GT;
- largest-component GT coverage;
- endpoint count;
- optionally contour length / gap statistics.

Generalization/robustness:

- per degradation/domain;
- worst-group metric;
- standard deviation/CV across regimes;
- validation-to-test gap.

Efficiency:

- runtime/image;
- throughput;
- peak RAM;
- thread scaling;
- parameter count for learned baselines.

Statistics:

- paired bootstrap CI;
- paired permutation/Wilcoxon where appropriate;
- Holm correction for multiple finalist comparisons;
- effect size, not only p-value.

---

# 5. Ablation plan

A good final ablation table should grow cumulatively from the same strong base:

| Ablation | Question |
|---|---|
| Scharr/NMS | How much comes from the localizer alone? |
| MFI-Classic | Does original fuzzy ROI gating help? |
| + orientation descriptors | Are orientation cues responsible for gain? |
| + compact/adaptive measure | Does measure adaptation help? |
| + Shapley gate | Does selection-before-fusion help? |
| + hierarchy | Are descriptor and scale interactions distinct? |
| + conditional operator | Should aggregation law change with regime? |
| + uncertainty | Does disagreement help suppress false positives? |
| + dynamic localizer | Does context improve precise localization? |
| + topology | Does MFI improve contour continuity? |

Do not build an ablation where each row was independently cherry-picked from held-out performance.

---

# 6. Main result tables we should eventually produce

## Table A — dataset benchmark

Rows: classical + learned baselines + our promoted variants.
Columns: ODS/OIS/AP/runtime.

## Table B — model-family comparison

Rows:

- MFI-Classic;
- MFI-Fuzzy++;
- CH-MFI;
- future MFI-Hybrid.

Columns: validation metric, test metric, generalization gap, runtime, memory.

## Table C — fuzzy aggregation study

Group by capacity/operator **family**, not by every hyperparameter.
Report best validation-selected member of each family and its frozen test result.

## Table D — robustness by degradation/domain

Clean/noise/blur/motion/texture/compound, plus real datasets.

## Table E — topology study

F1 + components + coverage + endpoints.

## Table F — interpretability

Descriptor Shapley and strongest positive/negative pair interactions, globally and by regime/scale.

---

# 7. Figures to prepare

1. **Overall CH-MFI architecture** — `ARCHITECTURE_MAP.md` global diagram.
2. **Model-family comparison** — Classic vs Fuzzy++ vs CH-MFI vs Hybrid.
3. **Scale hierarchy** — per-scale attention, coarse/fine fusion and granularity slider.
4. **Context routing examples** — blur/texture/noise maps and resulting operator/localizer weights.
5. **Qualitative edge examples** — input / GT / MFI / uncertainty / localizer / final / TP-FP-FN.
6. **Failure analysis** — texture, motion blur, compound degradation.
7. **PR curves** for final baselines only.
8. **Shapley/interactions heatmap** by regime.
9. **Runtime scaling** vs workers.
10. **Generalization-gap plot** selection/validation vs held-out/test.

---

# 8. Claims ledger

Before writing each claim, attach it to evidence.

| Possible claim | Evidence required | Current status |
|---|---|---|
| Orientation-aware cues improve edge evidence | controlled orientation ablation + final dataset ablation | synthetic evidence exists; rerun needed |
| Adaptive fuzzy measures beat a fixed q | final validation-selected capacity family on BSDS test | not established yet |
| Context-dependent aggregation generalizes better | CH-MFI/Fuzzy++ vs fixed counterpart on multiple datasets | pending local v2 experiments |
| MFI improves localization | final pixel metrics vs localizer-only | **not yet established on UDED** |
| MFI improves topology | fixed geodesic-linking ablation with F1 + connectivity endpoints | synthetic gain did not transfer in Stage 14i; fixed linker failed F1 and coverage-effect criteria |
| Phase congruency adds complementary context | fixed-default phase-moment addition with leakage-free repeated CV | not established; Stage 14j was eligible in all folds but slightly reduced aggregate and mean-fold F1 |
| Fixed vector-color gradients improve localization | CIELAB Di Zenzo replacement under leakage-free repeated CV | not established; Stage 14k reduced F1 and precision and won only 1/15 folds |
| Two-sided texture-distribution contrast adds context beyond pointwise amplitudes | fixed half-disc uniform-LBP chi-square feature with leakage-free repeated CV | not established; Stage 14l gained only +0.00031 aggregate F1, won 6/15 folds, and was eligible in 7/15 folds, so it failed promotion |
| Fold-fitted linear cue calibration improves the compact analytical gate | fixed-form logistic fusion of Scharr+NMS and retained memberships under leakage-free repeated CV | not established; Stage 14m converged in all folds but reduced aggregate F1 by 0.00497 and won only 4/15 folds |
| A shallow non-neural forest can exploit nonlinear compact-cue interactions and recover a stronger dense localizer | fixed randomized forest versus compact Choquet gate under leakage-free repeated CV | not established; Stage 14n reduced aggregate F1 by 0.02493 and precision by 0.03856, with only 2/15 wins; this bounded binary test is not a full structured-forest reproduction |
| Interval membership width and a reliability-conditioned capacity improve trust calibration | fixed Stage-14o candidate versus compact incumbent on UDED repeated CV and official BSDS500 validation | not established; UDED F1 fell by 0.00980 with 0/15 fold wins and precision fell by 0.01532; official BSDS-val attachment is pending a plumbing-only retry |
| Compact measures generalize better than free capacity | family-level validation/test gap comparison | pending |
| Shapley gating improves robustness/interpretability | regime/scale ablation and frozen test | pending |
| CH-MFI outperforms modern learned methods | official BSDS/BIPED metrics | not tested |

This ledger should be updated after every major run. If a claim cannot point to a frozen experiment, it does not go into the abstract/conclusion.

---

# 9. Supplementary-material candidates

Move the combinatorial search detail out of the main paper:

- complete parameter grids;
- all measure/operator definitions;
- all 500+ / wide-search rankings;
- learned capacity tables;
- every per-image metric;
- additional visualizations;
- hardware/thread-scaling details;
- exact seeds and command lines;
- Git commit hashes used for final experiments.

---

# 10. Writing sequence when experiments are mature

1. Freeze final experimental protocol.
2. Rerun promoted families from clean checkout/commit.
3. Complete `references.bib` metadata checks.
4. Write **Method** first from code + equations.
5. Write **Experiments** from frozen CSV/JSON outputs.
6. Write **Related Work** using the priority-A reading list.
7. Write **Introduction** after knowing the actual supported contribution.
8. Write abstract/conclusion last.

This order prevents the paper narrative from promising a result the final benchmarks do not support.
