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
not a reproduction of the continuous shearlet transform. It failed the UDED
gate: precision rose, but recall and aggregate F1 fell substantially and only
1/15 folds improved. Present it as a rejected fixed-bank sharpening trade-off,
not as evidence against continuous shearlet theory. The repaired official
BSDS-val attachment likewise showed sharpening rather than consistent benefit:
ODS rose by `0.00334`, while OIS fell by `0.00089` and AP by `0.01526`. The
candidate failed the preregistered conjunction and was not promoted.

Stage 14r did not establish an orientation-consistent continuity improvement.
The fixed `SE(2)` lift increased official BSDS-val ODS/OIS/AP by
`+0.00381/+0.00169/+0.00779`, but UDED aggregate F1 and precision changed by
`-0.00276/-0.00699`, and largest-component GT coverage changed by `-0.00201`.
Only `5/15` folds improved F1 and `4/15` improved coverage. Report this as a
mixed development result and a falsification of the fixed repository-specific
hard lift/diffusion/projection, not of invertible orientation-score theory.
No positive continuity claim or promotion is supported.

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
| Interval membership width and a reliability-conditioned capacity improve trust calibration | fixed Stage-14o candidate versus compact incumbent on UDED repeated CV and official BSDS500 validation | not established; UDED F1 fell by 0.00980 with 0/15 fold wins and precision fell by 0.01532; BSDS-val ODS/OIS rose slightly but AP fell by 0.00100 |
| Fixed SE(2) score diffusion improves contour continuity without sacrificing detection | Stage-14r UDED repeated CV, preregistered component coverage, and official BSDS500 validation | not established; BSDS ODS/OIS/AP improved, but UDED F1 and precision fell and largest-component coverage changed by -0.00201 with only 4/15 wins |
| A fixed half-order spectral Riesz localizer improves cross-dataset boundary detection | Stage-14s UDED repeated CV and official BSDS500 validation | not established; BSDS ODS/OIS/AP improved by 0.01161/0.00505/0.01804, but UDED aggregate F1 fell by 0.03599 with 0/15 fold wins |
| A connected-support a-contrario reliability gate suppresses accidental edges across domains | Stage-14t UDED repeated CV and official BSDS500 validation | not established; aggregate UDED F1/precision fell by 0.01725/0.02083 with 1/15 wins, and BSDS-val ODS/OIS/AP fell by 0.01257/0.01761/0.02830 |
| Exact author-code SED provides a stronger strictly untrained contextual reference than the current MFI incumbent on BSDS500 validation | Pinned author implementation, complete native-resolution validation maps, common official attachment, runtime and deterministic preview | established as development/reproduction evidence: SED scored ODS/OIS/AP `0.678546/0.709152/0.712814` versus incumbent `0.545424/0.579337/0.534296`; local matcher remains reference-uncertified, so this is not a final SOTA claim |
| Exact author-code EDPF supplies a reproducible strictly untrained chain-first/a-contrario reference | Pinned author implementation, exact build provenance, complete native-resolution validation maps, common official attachment, runtime and deterministic preview | established as development/reproduction evidence: EDPF scored ODS/OIS/AP `0.548048/0.548596/0.000000` versus incumbent `0.545470/0.579328/0.534289`; native binary output gives only one nontrivial operating point, so AP is not a dense-ranking comparison, and the reference-uncertified matcher prevents a final claim |
| Modified spatial sparseness adds value to the exact CO color-opponent baseline | Paired exact author CO/SCO implementations at the same published setting, complete native-resolution validation maps, common official attachment, runtime and deterministic preview | established as development/reproduction evidence: SCO improved ODS/OIS/AP over paired CO by `+0.020656/+0.017076/+0.043173` and scored `0.656582/0.682564/0.694939`; this does not authorize MFI integration before Stage 15o, and the reference-uncertified matcher prevents a final claim |
| Exact author-code Compass supplies a strong strictly untrained distribution-gradient reference | Pinned author implementation, fixed published sigma-4 setting, complete native-resolution validation maps, common official attachment, runtime and deterministic preview | established as development/reproduction evidence: Compass scored ODS/OIS/AP `0.630841/0.656565/0.518359`, changing the incumbent by `+0.085418/+0.077086/-0.015936`; the mixed ranking result awaits Stage-15 complementarity diagnosis, and the reference-uncertified matcher prevents a final claim |
| Exact author-code QFrD supplies a contemporary parameter-fixed fractional reference | Pinned author implementation, immutable source manifest, complete native-resolution validation maps, common official attachment, runtime and deterministic preview | established as development/reproduction evidence: QFrD scored ODS/OIS/AP `0.587261/0.618621/0.583650`, improving the incumbent by `+0.041849/+0.039265/+0.049373`; paper/code multiplication order is not claimed equivalent, fractional tuning remains closed, and the reference-uncertified matcher prevents a final claim |
| Frozen non-trained references provide spatially complementary BSDS responses | Fixed-threshold frozen-map proximity and component analysis with no detector/matcher rerun | established descriptively: SED has much less unsupported response and larger supported components than MFI, while MFI and SED retain `35.6%` and `32.0%` unique supported response relative to one another; these are not Berkeley matching metrics and do not authorize routing |
| Fixed analytic cross-boundary texture contrast is a cross-dataset-stable positive boundary cue | Image-blocked incremental AUC/AP beyond gradient plus persistence and beyond all other fixed cues on both UDED selection and BSDS500 validation | not established; Stage 15o improved both metrics in all 5 BSDS folds but reduced aggregate AUC/AP on UDED and was positive in only 2/5 UDED folds, so the preregistered Stage-15p gate failed |
| A fixed equal mean of compact MFI and exact SED dominates both constituent detectors across development datasets | UDED-selection repeated leakage-free CV plus official BSDS500-validation ODS/OIS/AP against both constituents under the preregistered Stage-16b conjunction | not established; the mean improved UDED aggregate F1 over MFI by `+0.003764` but lost precision and won only `5/15` folds, while on BSDS it remained below exact SED by `-0.049178/-0.055314/-0.066815` ODS/OIS/AP; no fusion-weight or router tuning is authorized |
| Recent non-trained headline F/F1 values near 0.89 establish a Berkeley ODS frontier | Primary-source split, threshold scope, matcher/tolerance, all-annotator handling, thinning/NMS, output multiplicity, and executable fidelity | not established; Stage 15j found the Gao Gabor-Sobel `0.888` and BPAED generic F1 claims protocol-incompatible with Berkeley ODS, while FACAFCV's own paper separates noisy-image optimal F `0.891` from BSDS500 ODS `0.589` |
| Compact measures generalize better than free capacity | family-level validation/test gap comparison | pending |
| Shapley gating improves robustness/interpretability | regime/scale ablation and frozen test | pending |
| CH-MFI outperforms modern learned methods | official BSDS/BIPED metrics | not tested |

This ledger should be updated after every major run. If a claim cannot point to a frozen experiment, it does not go into the abstract/conclusion.

Stage 16d adds a planned negative-or-positive mechanism result for
component-tree-inspired region-boundary shape stability. The manuscript must
label the implementation a fixed repository-specific surrogate, keep the
original ETHZ/Weizmann binary-edge evidence separate from local UDED/BSDS
development metrics, and avoid claiming an exact reproduction. If the joint
gate fails, report the structural-stability hypothesis as bounded negative
evidence rather than tuning its published constants.

Stage 16d is now bounded negative evidence. The repository-specific stability
gate reduced UDED aggregate F1 by `0.009035` with only `4/15` fold wins and
reduced official BSDS-validation ODS/OIS/AP by
`0.000319/0.000637/0.001587`. The paper must not present this as a falsification
of Donoser et al.'s complete method; it tests only the registered surrogate.
Report the deterministic preview and both development axes, retain the compact
controller, and state that all stability and gating constants were closed to
post-result tuning.

Stage 16f is the next planned single-mechanism result. Frame rolling guidance
as a scale-aware image-domain conditioning hypothesis: suppress small
structures before the retained Scharr+NMS localizer while iteratively restoring
larger boundaries. The method must be labeled an equation-level grayscale
repository reimplementation, not an exact reproduction of Zhang et al.'s code
or a literature benchmark replication. Report the fixed parameters, both
development axes, the precision-specific mechanism endpoint, runtime and fixed
preview. If rejected, state only that this fixed realization failed; do not
generalize to all scale-aware filtering or tune from its outcome.

Stage 16f is now bounded negative evidence with a marked cross-dataset
reversal. Report that the fixed grayscale RGF realization improved official
BSDS-validation ODS/OIS/AP by `0.035113/0.028126/0.009010` while reducing UDED
aggregate F1 by `0.103203`, recall by `0.195051`, and winning `0/15` folds.
The manuscript must not average these axes into a favorable claim, generalize
the result to all rolling-guidance conditioning, or imply that the local
reference-uncertified matcher supports a final benchmark claim. The compact
controller remains incumbent and Stage 16g is a literature checkpoint rather
than an RGF tuning stage.

Stage 16h is now bounded negative evidence. Report that the fixed soft
hysteresis-persistence transform preserved its pointwise-floor and exact-
support invariants but reduced UDED aggregate F1 by `0.004328` and recall by
`0.005380`, with `3/15` fold wins. Official BSDS-validation ODS/OIS/AP changed
by `-0.000783/+0.002205/-0.020691`. The isolated OIS gain does not offset the
conjunctive failure. Do not present this as falsifying classical Canny
hysteresis or connected filtering generally, and do not imply that the local
reference-uncertified matcher supports a final benchmark claim. The compact
controller remains incumbent; Stage 16i is a literature checkpoint rather
than persistence tuning.

Stage 16j is the next planned bounded context-feature result. Frame it as a
local edge-profile model test: a fixed family of centered tanh templates is
compared with smooth linear shading along the unchanged Scharr normal, and the
result enters only as a positive contextual membership. Attribute the
one-dimensional step-model rationale to Nalwa and Binford and the variable-
blur motivation to Elder and Zucker. Label the implementation a repository-
specific surrogate, report both development axes and eligibility frequency,
and do not imply an exact reproduction. A failure closes this fixed profile
geometry and calibration to outcome-driven tuning; it does not falsify
parametric edge fitting or local scale control generally.

Stage 16j is now a negative-result paragraph. Report that the cue was eligible
in `14/15` folds, won `12/15` UDED fold comparisons, and improved UDED F1 by
`+0.001584`, but missed the registered `+0.002` margin; also report the mixed
BSDS changes `-0.001980/-0.001964/+0.001585` for ODS/OIS/AP. The safe claim is
that fixed local profile evidence was individually discriminative and stable
on UDED but did not add jointly transferable context under the registered
fusion. Do not describe this as a general failure of parametric edge models.

Stage 16l is now a cross-dataset negative-result paragraph. Frame it as an
exact-author-detector/repository-integration decomposition: EDPF supplied fixed
contiguous chains with chain-level Helmholtz validation, while MFI retained its
own Scharr+NMS localization and used the chain map only as an eligible positive
context membership. The cue was eligible in `15/15` UDED folds, but aggregate
F1 and mean fold F1 changed by `-0.000191/-0.000013`, with only `8/15` fold-F1
and `3/15` coverage wins. In contrast, official BSDS ODS/OIS/AP improved by
`+0.013847/+0.005044/+0.014949`. The safe claim is that the fixed chain cue
was discriminative and beneficial on BSDS validation but did not establish
stable cross-dataset incremental context value. State that the one-pixel
8-neighbourhood expansion was a preregistered repository alignment adapter,
not part of author EDPF. The failure closes this exact support integration to
outcome-driven tuning and must not be described as falsifying Edge Drawing or
EDPF generally.

Stage 16n is the next bounded context-feature test. Frame it as a derivative-
free, centre-referenced local-self-similarity experiment grounded in Smith and
Brady's SUSAN principle. State explicitly that the repository implements only
the published initial 37-pixel USAN-area response as an MFI membership; it is
not a reproduction of the complete SUSAN direction, NMS, thinning, or subpixel
detector. Report eligibility and both development axes under the preregistered
joint rule. A failure closes this fixed mask/threshold/calibration realization
to outcome-driven tuning but does not falsify SUSAN generally.

Stage 16n is now a mixed cross-dataset negative-result paragraph. Report that
the cue was eligible in `15/15` folds and changed UDED aggregate F1 and mean
fold F1 by only `+0.000302/+0.000185`, with `7/15` fold wins, while official
BSDS ODS/OIS/AP improved by `+0.004674/+0.002200/+0.006049`. The safe claim is
that the fixed initial USAN response was discriminative and mildly beneficial
but did not meet the preregistered stable cross-dataset increment. Do not
describe this as a falsification of complete SUSAN edge detection.

Stage 16p is the next bounded generation-2 experiment. Frame it as a
marginal-invariance test over the retained five memberships, not as a new edge
cue and not as a reproduction of Zabih-Woodfill correspondence. Each image and
membership channel is mapped to deterministic empirical-CDF midranks before
the unchanged Choquet aggregation. The safe prospective claim is that this
tests whether stable within-image ordering can transfer better than absolute
fold-calibrated membership marginals under the recurring UDED/BSDS reversal.
Report both development axes and the registered rank invariants; a failure
closes this fixed per-image empirical-copula realization to outcome-driven
tuning.

Stage 16p is now a mixed cross-dataset negative-result paragraph. Report that
all deterministic rank invariants passed, but UDED aggregate F1 and mean fold
F1 changed by `-0.009028/-0.007685`, with only `2/15` fold wins. Official BSDS
ODS/OIS/AP changed by `+0.008482/-0.000650/+0.001349`; therefore even the
official axis failed its conjunctive condition. The safe claim is that this
fixed image-internal removal of membership marginals improved BSDS ODS but
materially harmed UDED precision and recall, so stable transferable value was
not established. Do not generalize the result to all copula or rank methods.

Stage 16r is the next bounded aggregation result. Frame it as a direct
quantitative-versus-qualitative fuzzy-integral comparison over exactly the
same five memberships, singleton weights, and gamma-0.55 capacity. The
prospective mechanism is reduced arithmetic compensation: Sugeno takes the
maximum of membership/capacity bottlenecks instead of summing Choquet
increments. Attribute the formal distinction to de Campos and Bolaños and the
edge-application precedent to Marco-Detchart et al. Label Stage 16r an
equation-level repository application rather than a complete detector
reproduction. Report both development axes, algebraic checks, diagnostics,
and the fixed preview. A failure closes this fixed Sugeno realization and any
outcome-driven Choquet/Sugeno mixture or capacity tuning.

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

## Stage 16r writing update

Stage 16r is bounded negative evidence. Report that all algebraic checks
passed and UDED aggregate F1 rose by only `+0.000378`, with `8/15` fold wins,
missing the registered improvement and stability requirements. Official BSDS
ODS/OIS/AP changed by `+0.001498/+0.000473/-0.013481`; the AP loss and missed
ODS margin reject the candidate. The safe claim is that replacing arithmetic
Choquet compensation with this fixed qualitative max-min bottleneck did not
establish jointly transferable benefit. Do not generalize to all Sugeno
integrals or tune a Choquet/Sugeno mixture from this outcome.

## Stage 16t prospective writing note

Frame Stage 16t as a bounded local scale-selection experiment, not another
multiscale cue and not an exact reproduction of Lindeberg's full scale-space
edge method. The equation-level mechanism is the maximum over the fixed
`sigma={1,2,4}` bank of the gamma-`1/2` normalized Gaussian gradient, subject
to spatial NMS at the selected scale. State that continuous curve tracing,
closed-edge construction, subscale interpolation, and integrated saliency are
omitted. Report the synthetic scale contract, selected-scale distributions,
both development axes, and the fixed preview. A failure closes this precise
finite bank and normalization to outcome-driven tuning but does not falsify
automatic scale selection generally.

## Stage 16v prospective writing note

Frame Stage 16v as the first complete learned non-neural replacement in the
generation-2 sequence, not as another MFI feature and not as a continuation of
Stage 14n tuning. The candidate is exact pinned Dollár-Zitnick author inference
with the shipped BSDS500-train `modelBsds`, structured patch masks, author
sharpening/aggregation, and the NMS setting used by `edgesEval.m`. Classify it
as supervised and non-neural; do not call it untrained. Keep published test
numbers separate from our UDED-selection and BSDS-validation development
results. Report the MSR-LA dependency license, commits, model hash, tree/node
complexity, runtime, both development axes, and the fixed preview. A failure
closes this exact author model as the generation-2 replacement and forbids
outcome-driven forest/fusion tuning; it does not generalize to all structured
prediction forests.

## Stage 16v writing update

Report Stage 16v as a sharp cross-dataset negative result. The exact fixed
author forest improved official BSDS500-validation ODS/OIS/AP by
`+0.167315/+0.144560/+0.223159`, yet reduced UDED aggregate F1 by `0.035385`
and recall by `0.142871`, with only `2/15` fold wins. The safe claim is that
the BSDS-train structured-mask model is a strong supervised non-neural BSDS
reference but did not establish joint transfer to UDED under the frozen rule.
Do not present the BSDS result as promotion, generalize the failure to all
structured forests, or motivate outcome-driven retraining, calibration,
fusion, or routing. Retain the local evaluator's reference-reproduction caveat.

## Stage 16x prospective writing note

Frame Stage 16x as a bounded spectral-globalization context experiment, not
an exact gPb reproduction. The paper-derived core is the intervening-contour
affinity with radius `5` and `rho=0.1`, followed by gradients of `16`
nontrivial normalized-Laplacian eigenvectors. Explicitly disclose the fixed
maximum-side-96 graph, ordinary gradient magnitude, monotone compression, and
fold-fitted membership as repository choices. Report cue eligibility,
precision and recall separately, score-support invariance, runtime, the
synthetic step/repeatability contract, both development axes, and the fixed
preview. A failure closes only this surrogate and integration; it must not be
described as falsifying spectral clustering or exact gPb.

## Stage 16x writing update

Report Stage 16x as bounded negative evidence. The spectral cue was eligible
in all folds and passed its numerical and support contracts, but UDED aggregate
F1 changed by `-0.000430`, precision by `-0.000190`, and mean fold F1 by
`-0.000364`, with only `6/15` fold wins. Official BSDS ODS/OIS/AP changed by
`+0.001975/+0.001748/+0.011216`; ODS narrowly missed the fixed `+0.002`
margin. The safe claim is that this coarse intervening-contour spectral cue did
not establish jointly transferable incremental context value. Do not describe
the result as a falsification of normalized cuts, spectral Pb, or exact gPb,
and do not motivate graph or integration tuning from it.

## Stage 16z prospective writing note

Frame Stage 16z as a fixed local orientation-organization context test, not a
new tensor localizer and not coherence-enhancing diffusion. The paper-derived
core is the scalar second-moment matrix at noise/integration scales `0.5/4.0`;
the cue is the continuous eigenvalue difference
`lambda_max-lambda_min`, which vanishes in flat or isotropic neighborhoods.
Explicitly contrast this with Stage 14k's per-pixel CIELAB Di Zenzo tensor and
disclose outer-fold membership calibration and eligibility as repository
integration choices. Report cue eligibility, precision/recall, exact score-
support preservation, runtime, the step/flat/checkerboard contract, both
development axes, and the fixed preview. A failure closes only this scalar
fixed-scale context realization and must not be generalized to structure-
tensor analysis, color tensors, multiscale tensors, or coherence-enhancing
diffusion.

## Stage 16z writing update

Report Stage 16z as a narrow conjunctive negative with meaningful UDED
evidence. The fixed scalar tensor cue passed all UDED conditions: aggregate F1
improved by `+0.003263`, precision by `+0.002639`, recall by `+0.004184`, and
mean fold F1 by `+0.002705`, with `14/15` fold wins and `15/15` eligibility.
Official BSDS ODS/OIS/AP changed by `+0.001414/+0.000628/+0.010279`; ODS
missed the registered `+0.002` margin, so the candidate was not promoted. The
safe claim is that this fixed scalar orientation-evidence integration was
stable and useful on UDED and improved BSDS ranking quality, but did not meet
the required joint margin. Do not generalize the rejection to structure
tensors, and do not motivate color, multiscale, diffusion, or integration
tuning from the result.

## Stage 17b prospective writing note

Frame Stage 17b as a fixed distribution-free local boundary-context test, not
an image-wide rank normalization and not a complete reproduction of either
published detector. The literature-derived core is the normalized
Mann-Whitney ordering contrast between opposed spatial samples; the repository
fixes a radius-2 support, four partitions, half credit for ties, and maximum
absolute orientation response before outer-fold membership calibration.
Explicitly distinguish it from the failed empirical-copula transform,
parametric step-profile fit, and LBP-histogram half-disc cue. Report monotone-
transform invariance, cue eligibility, precision/recall, exact score-support
preservation, runtime, both development axes, and the fixed preview. A failure
closes this exact local rank realization and must not be generalized to all
nonparametric edge statistics or used to justify multiscale, variance, color,
or learned rank variants.

## Stage 17b writing update

Report Stage 17b as a fixed-cue ineligibility result. The local Mann-Whitney
cue's training AUC did not reach `0.56` in any of 15 folds, so the candidate
exactly matched compact MFI on UDED and supplied no candidate-specific UDED
performance evidence. Official BSDS ODS/OIS/AP changed by only
`-0.000012/-0.000201/+0.000098`. The safe claim is that this fixed radius-2
four-orientation rank evidence did not qualify as positive context under the
registered calibration and showed no matched BSDS benefit. Do not generalize
the result to all nonparametric edge tests or motivate multiscale, variance,
color, learned-rank, or relaxed-eligibility variants from it. Retain the local
evaluator's reference-reproduction caveat.

## Stage 17d prospective writing note

Frame Stage 17d as a fixed information-geometric context test, not a complete
GMRF edge detector and not a fitted probabilistic classifier. The paper-
derived core is the isotropic Gaussian conditional model, analytic maximum-
pseudo-likelihood fit, and local type-I/type-II observed-Fisher ratio. State
that the ratio is evaluated through its algebraically equivalent squared
standardized conditional innovation. Disclose the paper's second-order eight-
neighbour option, repository reflection boundary convention, degenerate-
constant-image branch, and outer-fold membership calibration/eligibility.
Report fitted beta and variance diagnostics, affine-intensity invariance, cue
eligibility, precision/recall, exact score-support preservation, runtime, both
development axes, and the fixed preview. A failure closes only this fixed
isotropic local realization and must not motivate multiscale, anisotropic,
color, mixture, or learned-random-field variants.

## Stage 17d writing update

Report Stage 17d as a fixed-cue conjunctive negative despite reliable cue
eligibility. The GMRF membership was eligible in `15/15` folds; UDED aggregate
F1/precision/recall and mean fold F1 changed by
`+0.000719/-0.000108/+0.002133/+0.000715`, with `10/15` fold wins. The F1
margin and precision condition failed. Official BSDS ODS/OIS/AP changed by
`+0.000312/-0.002259/-0.003687`, failing all three BSDS requirements. The safe
claim is that the fixed isotropic conditional-innovation cue was individually
discriminative and slightly recall-positive on UDED but did not provide
transferable incremental context value. Do not generalize the rejection to
GMRF information geometry or motivate multiscale, anisotropic, color, mixture,
learned-field, or integration tuning. Retain the local evaluator's reference-
reproduction caveat.

## Stage 17f prospective writing note

Frame Stage 17f as a fixed physics-based context test, not as a complete color
edge detector or exact reproduction. The selected equation removes the RGB
derivative component attributable to achromatic shadow/shading changes and
uses only the residual energy as one positive membership. Emphasize that the
grayscale localizer and retained fuzzy controller remain unchanged, and
distinguish the test from Stage 14k's CIELAB vector-tensor localizer. Report the
predeclared equal-RGB-norm chromatic-versus-achromatic synthetic contract, fold eligibility,
UDED precision/recall/F1 stability, BSDS ODS/OIS/AP, runtime, support
invariance, and fixed preview. A failure closes only this sigma-1
shadow-shading quasi-invariant integration; it does not falsify photometric
invariance theory or authorize specular/hue/color-space variants.

## Stage 17f writing update

Report Stage 17f as a mixed but conjunctively negative result. The fixed cue
was eligible in `12/15` folds and changed UDED aggregate F1/precision/recall
and mean fold F1 by `+0.000756/+0.000826/+0.000594/+0.000509`, but won only
`7/15` folds and missed the `+0.002` F1 margin. Official BSDS ODS/OIS/AP
improved by `+0.003855/+0.002520/+0.008468`. The safe claim is that the
selected photometric residual provided BSDS benefit but did not establish
stable incremental value across both development datasets. Do not generalize
the rejection to photometric quasi-invariants or motivate specular, hue,
alternative-color-space, multiscale, learned, or integration variants. Retain
the local evaluator's reference-reproduction caveat.

## Stage 17h prospective writing note

Frame Stage 17h as a bounded local stochastic-scaling context test, not an
exact reproduction or a multifractal detector. The literature-derived core is
that deterministic edges disturb fractional-Brownian local behavior; the
repository fixes dyadic lags `1/2/4`, their minimal centered `9x9` support,
four axes, and evidence `clip(H) * clip(R2) * S1(4)`. Explicitly distinguish
this from the retained descriptor-scale persistence cue: Stage 17h estimates
an image-domain structure-function exponent and goodness of fit, while the
localizer and fuzzy parameters remain unchanged. Report eligibility,
precision/recall, exact score-support preservation, runtime, the
flat/step/checker/noise contract, both development axes, and the fixed preview.
A failure closes only this fixed surrogate and must not motivate alternative
fractal dimensions, lags, supports, multifractal/wavelet/color variants, or
integration tuning.

## Stage 17h writing update

Report Stage 17h as a stable but submargin conjunctive negative. The fixed cue
was eligible in `15/15` folds and changed UDED aggregate
F1/precision/recall and mean fold F1 by
`+0.000164/+0.000385/-0.000232/+0.000073`, with `11/15` fold wins, but missed
the required `+0.002` aggregate-F1 margin. Official BSDS ODS/OIS/AP changed by
`+0.001978/+0.000972/+0.011064`; ODS narrowly missed the separate `+0.002`
margin. The safe claim is that this fixed stochastic-scaling membership was
individually eligible and improved ranking quality, but did not establish the
preregistered cross-dataset effect size. Do not generalize the rejection to
local fractal analysis or motivate alternative estimators, lags, supports,
multifractal/wavelet/color variants, or integration tuning. Retain the local
evaluator's reference-reproduction caveat.

## Stage 17j prospective writing note

Frame Stage 17j as a fixed local information-concentration context test, not a
complete entropy edge detector and not an entropy-family search. The primary
paper-derived core is Shiozaki's `3x3` brightness probability
`p_i=I_i/sum I` and its lower Shannon entropy at severe local changes; the
repository exposes the bounded deficit `1-H/log(9)` as one fold-calibrated
positive membership. Explicitly distinguish it from cross-half histogram
contrast, image-wide empirical ranks, GMRF conditional surprise, and local
fractal scaling. Report cue eligibility, precision/recall, exact score-support
preservation, multiplicative intensity-scale invariance, runtime, the fixed
synthetic contract, both development axes, and the positions 1/8/15 preview.
A failure closes only this fixed brightness-entropy integration and must not
motivate multiscale, clustered, Renyi/Tsallis, color, spatial, histogram-binned,
cross-half, or learned entropy variants.

## Stage 17j writing update

Report Stage 17j as a stable but submargin conjunctive negative. The fixed cue
was eligible in `15/15` folds and changed UDED aggregate F1/precision/recall
and mean fold F1 by `+0.001106/+0.000175/+0.002682/+0.001305`, with `12/15`
fold wins, but missed the required `+0.002` aggregate-F1 margin. Official BSDS
ODS/OIS/AP improved by `+0.007561/+0.003648/+0.012971`, satisfying that axis.
The safe claim is that fixed local brightness information concentration was
individually discriminative and improved both development datasets, but did
not establish the preregistered cross-dataset effect size. Do not generalize
the rejection to entropy edge analysis or motivate alternative windows,
entropy families, spatial/color/multiscale/cross-half variants, or integration
tuning. Retain the local evaluator's reference-reproduction caveat.

## Stage 17r writing update

Report Stage 17r as a stable but conjunctively submargin negative. The fixed
cue changed UDED aggregate F1/precision/recall and mean fold F1 by
`+0.001396/+0.000554/+0.002800/+0.001231`, with `14/15` fold wins and
eligibility in `15/15`; only the registered `+0.002` aggregate-F1 margin was
missed on that axis. Official BSDS ODS/OIS/AP changed by
`+0.001872/+0.000782/+0.003748`; ODS narrowly missed its separate `+0.002`
margin. The safe claim is that this fixed directional nonlocal-residual
integration was individually discriminative and stable but did not establish
the preregistered magnitude of cross-dataset incremental value. Do not
generalize the rejection to patch recurrence or the complete Xu-Xu-Quan
decomposition, and do not motivate recurrence or integration tuning. Retain
the local evaluator's reference-reproduction caveat.

## Stage 17l prospective writing note

Frame Stage 17l as a bounded annular feature-density context test, not an exact
surround-suppression detector reproduction. The literature-derived core is the
positive part of the `sigma`/`4*sigma` difference-of-Gaussians surround and the
suppression slope `atan(t/M)`; the repository fixes `sigma=1`, radius `12`, and
uses its normalized complement as one fold-calibrated positive membership.
Explicitly distinguish it from learned negative evidence, opposed texture-
distribution contrast, connected-threshold persistence, and SED's complete
multi-stage surround/feedback model. Report eligibility, precision/recall,
exact score-support preservation, positive-scale invariance, runtime, the
isolated/dense/random-edge contract, both development axes, and the positions
1/8/15 preview. A failure closes only this fixed isotropic integration and must
not motivate adaptive, anisotropic, multiscale, color, end-stopped,
facilitated, or learned surround variants.

## Stage 17l writing update

Report Stage 17l as a conjunctive negative with a small BSDS-positive signal.
The fixed cue changed UDED aggregate F1/precision/recall and mean fold F1 by
`-0.000046/-0.000767/+0.001221/+0.000010`, with only `5/15` fold wins and
`10/15` eligible folds. Official BSDS ODS/OIS/AP changed by
`+0.001673/+0.001578/+0.007118`; ODS missed the required `+0.002` margin.
The safe claim is that this fixed isotropic annular-isolation evidence did not
establish stable cross-dataset incremental value in the retained Choquet gate.
Do not generalize the rejection to complete surround-suppression theory or use
it to motivate adaptive, anisotropic, multiscale, color, end-stopped,
facilitated, learned, or integration-tuned variants. Retain the local
evaluator's reference-reproduction caveat.

## Stage 17n prospective writing note

Frame Stage 17n as a bounded topological-sensitivity context test, not an
exact reproduction of the complete Amstutz-Fehrenbach detector. The
literature-derived core is the `h4` one-point approximation: fixed `T=2`,
analytic `beta=1-sqrt(1-4/pi^2)`, two heat-kernel gradients, and the extremal
eigenvalue of their symmetrized bilinear form. The repository uses that
positive crack-insertion sensitivity only as a fold-calibrated sixth
membership; Scharr+NMS localization is unchanged. Explicitly distinguish it
from Stage 16t's scale-selected localizer and Stage 14p's evolved phase field.
Report eligibility, precision/recall, exact score-support preservation,
quadratic intensity scaling, runtime, synthetic controls, both development
axes, and the positions 1/8/15 preview. A failure closes only this fixed `h4`
integration and must not motivate alternative heat times, quadratures,
topological costs, PDEs, color/multiscale variants, or integration tuning.

## Stage 17n writing update

Report Stage 17n as a conjunctive negative with a clear BSDS-positive signal.
The fixed cue changed UDED aggregate F1/precision/recall and mean fold F1 by
`-0.000350/-0.000556/+0.000028/-0.000330`, with only `3/15` fold wins despite
`14/15` eligibility. Official BSDS ODS/OIS/AP changed by
`+0.006420/+0.004441/+0.014245`. The safe claim is that this fixed equation-
level `h4` crack-insertion sensitivity did not establish stable cross-dataset
incremental value in the retained Choquet gate. Do not generalize the rejection
to complete topological-gradient theory or use it to motivate alternative heat
times, quadratures, costs/PDEs, color/multiscale/anisotropic variants,
restoration, or integration tuning. Retain the local evaluator's reference-
reproduction caveat.

## Stage 17p prospective writing note

Frame Stage 17p as a bounded robust local-significance context test, not an
exact reproduction of Black and Sapiro's anisotropic smoothing. The
literature-derived core is the interpretation of edges as local gradient
outliers and the `1.4826`-normalized median absolute deviation; the repository
fixes one reflected `9x9` window and maps positive excess to `d/(d+s)` before
outer-fold membership calibration. Explicitly distinguish this from Stage
17d's globally fitted GMRF innovation, Stage 17b's opposed rank test, Stage
17l's annular surround isolation, and any image-conditioning operation.
Report eligibility, precision/recall, exact score-support preservation,
positive intensity-scale invariance, runtime, synthetic controls, both
development axes, and the positions 1/8/15 preview. A failure closes only this
fixed local robust-outlier integration and must not motivate alternative
windows, estimators, mappings, adaptive/oriented/multiscale/color variants,
diffusion, restoration, or integration tuning.

## Stage 17p writing update

Report Stage 17p as a complete UDED-ineligibility negative with negligible,
mixed BSDS movement. The fixed cue was ineligible in `15/15` UDED folds, so
candidate and compact-control aggregate and fold metrics were identical.
Official BSDS ODS/OIS/AP changed by `+0.000035/-0.000086/+0.000100`, missing
the ODS margin and nonnegative OIS condition. The safe claim is that this fixed
`9x9` local median/MAD positive-excess statistic did not discriminate UDED
edge from texture samples sufficiently to enter the retained gate and did not
establish matched BSDS benefit. Do not generalize the rejection to robust
statistics or Black-Sapiro anisotropic smoothing, and do not motivate window,
estimator, mapping, adaptive/oriented/multiscale/color, diffusion, restoration,
or integration variants. Retain the local evaluator's reference-reproduction
caveat.

## Stage 17t writing update

Report Stage 17t as a stable but submargin UDED result paired with a clear
BSDS-validation improvement. The fixed cue changed UDED aggregate
F1/precision/recall and mean fold F1 by
`+0.000590/+0.000108/+0.001404/+0.000790`, was eligible in `15/15` folds,
and won `10/15`, but missed the registered `+0.002` aggregate-F1 requirement.
Official BSDS ODS/OIS/AP improved by
`+0.005624/+0.002471/+0.013006`. The safe claim is that fixed soft Frei-Chen
edge-subspace occupancy was locally discriminative and benchmark-helpful but
did not establish the required cross-dataset incremental value in the retained
Choquet gate. Do not generalize the rejection to Frei-Chen analysis or the
complete sequential detector, and do not motivate basis, subspace,
normalization, support, scale, color, learned, sequential, calibration, or
integration variants. Retain the local evaluator's reference-reproduction
caveat.

## Stage 17x prospective writing note

Frame Stage 17x as a bounded test of semi-global scanline segmentation support,
not an exact reproduction of Jevnisek and Avidan's SGBD. The fixed cue uses
exact dynamic-programming piecewise-constant partitions of complete rows and
columns on a maximum-side-256 working grid, a first-difference-noise-scaled
Schwarz/BIC `log(N)` penalty, symmetric contrast assignment to the two samples
bordering each selected change point, and maximum direction merging. It enters
only as a fold-calibrated sixth membership; median conditioning, the compact
Choquet gate, and Scharr+NMS localization remain unchanged. Explicitly record
that textons, color, semi-global smoothing, fitted MDL weighting, segment-count
marginalization, and UCM postprocessing are absent. Report eligibility,
precision/recall, exact score-support preservation, synthetic and photometric
contracts, runtime, both development axes, and the positions 1/8/15 preview.
A failure closes this fixed surrogate and must not motivate alternative grids,
directions, segment models, penalties, noise estimators, raster supports,
merges, diagonal/multiscale/color/texton/full-SGBD variants, calibration, or
integration tuning. Retain the local evaluator's reference-reproduction
caveat.

Stage 17x ultimately passed every registered condition except the UDED
aggregate-F1 margin. Report UDED deltas of
`+0.001916/+0.000546/+0.004221/+0.001692` for aggregate F1, precision,
recall, and mean fold F1, with `13/15` wins and `15/15` eligibility. Report
the official BSDS500-validation ODS/OIS/AP gains of
`+0.004943/+0.002056/+0.011994` separately, retain the matcher caveat, and
characterize the result as a cross-dataset-consistent but preregistered-
submargin negative result rather than a promotion.

## Stage 17v prospective writing note

Frame Stage 17v as an equation-level test of two-sided morphological
transition support, not a reproduction of Van Vliet et al.'s complete
nonlinear-Laplacian detector. The fixed cue is
`min(max_3x3(I)-I, I-min_3x3(I))` on the unchanged median-conditioned grayscale
image with unit square coefficients and reflected finite-raster boundaries.
It enters only as a fold-calibrated sixth membership; it adds no smoothing,
zero-crossing segmentation, distance transform, contour extraction, or
threshold. Explicitly distinguish it from local range, the one-sided robust
gradient outlier, the ranklet, the parametric step profile, and Frei-Chen's
linear patch subspace. Report eligibility, precision/recall, exact
score-support preservation, ramp/step/checkerboard/impulse behavior,
fixed-small-noise, offset/polarity/positive-scale contracts, runtime, both development axes, and
the fixed positions 1/8/15 preview. A failure closes only this fixed Eq.-4
integration and must not motivate alternative supports, shapes, weights,
scales, color, SNR adaptation, morphology hierarchies, zero-crossing or full
detector variants, or calibration/integration tuning. Retain the local
evaluator's reference-reproduction caveat.

## Stage 17r prospective writing note

Frame Stage 17r as a bounded directional patch-recurrence context test, not an
exact reproduction of Xu, Xu, and Quan's complete structure-texture
decomposition. The literature-derived core is the spatial anisotropy of
recurrent contour patches versus isotropic texture recurrence, the published
`5x5`/`51x51`/four-band/width-8/16-match/`h=0.3` contract, and the normalized
directional nonlocal residual in Eq. 6. The repository averages the absolute
four-direction residual into one fold-calibrated sixth membership; it does not
run the wavelet/DCT transforms or Bregman solver. Report realized raster-band
counts, eligibility, precision/recall, exact score-support preservation,
runtime, synthetic flat/step/checkerboard and repeatability contracts, both
development axes, and the positions 1/8/15 preview. A failure closes only
this fixed residual integration and must not motivate alternative patch/search
geometry, bands, directions, match counts, similarity, multiscale/color or
learned patches, full decomposition, smoothing, restoration, or integration
tuning. Retain the local evaluator's reference-reproduction caveat.

## Stage 17t prospective writing note

Frame Stage 17t as an equation-level soft use of Frei and Chen's local
orthogonal patch basis, not an exact reproduction of their thresholded
sequential detector. The fixed cue is the cosine of the angle between a
median-conditioned `3x3` grayscale patch and its projection onto the
published four-dimensional edge subspace, computed from all nine normalized
basis responses. It enters only as a fold-calibrated sixth membership; the
localizer and retained controller remain unchanged. Explicitly distinguish
the mechanism from Stage 16z's averaged derivative tensor, Stage 16j's
normal-profile fitting, Stage 14l's half-disc texture distribution, and Stage
17r's nonlocal recurrence geometry. Report basis orthonormality, eligibility,
precision/recall, exact score-support preservation, positive intensity-scale
invariance, runtime, synthetic controls, both development axes, and the fixed
positions 1/8/15 preview. A failure closes only this fixed soft edge-subspace
integration and must not motivate basis, subspace, denominator, support,
orientation, scale, color, learned, sequential-detector, calibration, or
integration variants. Retain the local evaluator's reference-reproduction
caveat.

## Stage 17z prospective writing note

Frame Stage 17z as an exact-code integration of one continuous signal from
PolyEdge, not a reproduction of its archaeological-image demonstrations or
percentile-thresholded detector. Record the pinned MIT author commit and the
published Section-7 degree, Chebyshev-node, quadtree-depth, minimum-cell,
RMSE-tolerance, Gaussian-sigma, residual-normalization, and equal-average
contract. Explain that approximation failure supplies spatially adaptive
representation evidence distinct from the preceding scanline change-point
and fixed local-patch cues. Report cue eligibility, precision/recall, exact
score-support preservation, source cleanliness, flat/step/checkerboard/noise,
affine-photometric and repeatability contracts, runtime, both development
axes, and the positions 1/8/15 preview. A failure closes the fixed PolyEdge
residual integration and must not motivate polynomial-degree/node,
subdivision, residual-selection/fusion, threshold, color, multiscale,
coefficient-analysis, calibration, or integration tuning. Retain the local
evaluator's reference-reproduction caveat.

## Stage 17z result writing note

Report the fixed PolyEdge residual as a stable but preregistered-submargin
negative result. UDED aggregate F1/precision/recall and mean fold F1 changed by
`+0.001554/+0.000345/+0.003594/+0.001405`, with `14/15` fold wins and
`15/15` eligibility, but the F1 gain missed `+0.002`. Separately report the
official BSDS500-validation ODS/OIS/AP changes of
`+0.001034/-0.000566/+0.006465`; ODS and OIS failed their conditions. Preserve
the pinned-source and evaluator caveats and do not frame the AP gain as a
promotion or as permission to tune the adaptive-polynomial family.

## Stage 18b prospective writing note

Frame Stage 18b as an equation-level integration of the
Felzenszwalb-Huttenlocher adaptive internal-variation boundary predicate, not
an exact author-code reproduction or a segmentation benchmark. Record the
fixed grayscale eight-neighbour graph, absolute-difference weights, Gaussian
sigma `0.8`, `tau(C)=300/|C|`, disabled minimum-size postprocessing, and
symmetric two-endpoint boundary rasterization. Explain that the cue represents
region-relative boundary evidence rather than another residual, derivative,
or globalization of the incumbent response. Report eligibility,
precision/recall, exact score-support preservation, flat/step/checkerboard/
noise and repeatability contracts, runtime, both development axes, and the
positions 1/8/15 preview. A failure must close this fixed realization without
motivating graph scale, smoothing, connectivity, region processing, color,
feature-space, hierarchy, calibration, or integration tuning. Retain the
local evaluator's stochastic/reference-reproduction caveat.

## Stage 18b result writing note

Report the fixed FH adaptive-region boundary cue as a cross-dataset negative
result. UDED aggregate F1/precision/recall and mean fold F1 changed by
`-0.000307/-0.000632/+0.000277/-0.000248`, with `6/15` fold wins and
`14/15` eligibility. Separately report the official BSDS500-validation
ODS/OIS/AP gains of `+0.002858/+0.002241/+0.009290`, which passed that axis
but cannot override the conjunctive UDED failures. Preserve the equation-level
implementation and evaluator caveats; do not frame the BSDS gains as promotion
or permission to tune the FH/region-partition family.

## Stage 18d prospective writing note

Frame Stage 18d as one fixed active-sampling context test motivated by
Schmittwilken and Maertens' `S-V-N` variance control, not as exact reproduction
of their display simulation or correlation evaluation. Record the official
repository commit and the fixed pixels/degree, diffusion, fixation duration,
sampling rate, ten-trial seed and paths, five DoG scales, 2:1 surround ratio,
reflection, scale-mean normalization, and `E/(1+E)` contract. Explain that the
new information is temporal variation induced by micro-shifts while the
median-conditioned Scharr+NMS localizer remains unchanged. Report eligibility,
precision/recall, exact score-support preservation, flat/step/checkerboard/
noise, positive-affine and repeatability contracts, runtime, both development
axes, and the positions 1/8/15 preview. A failure closes this fixed active-
drift realization without motivating stochastic ensembles, subpixel drift,
temporal filters, event-camera, adaptive, oriented, color, learned,
calibration, or integration variants. Retain the local evaluator's stochastic/
reference-reproduction caveat.

## Stage 18l outcome writing note

Report that the fixed closure-participation cue was individually eligible in
all folds and improved official BSDS500-validation ODS/OIS/AP by
`+0.003934/+0.001900/+0.012284`, but changed UDED aggregate
F1/precision/recall and mean fold F1 by
`+0.000573/-0.000342/+0.002149/+0.000483`. It won `9/15` folds yet failed
the preregistered aggregate-F1 and precision conditions. Frame this as another
BSDS-positive/UDED-submargin context result and a rejection of the fixed
repository torque realization, not image torque generally. Do not imply that
the positive BSDS axis authorizes torque, attention, segmentation, calibration,
or integration tuning. Preserve the deterministic positions 1/8/15 preview
and the stochastic/reference-uncertified evaluator caveat.

## Stage 18d result writing note

Report the fixed active micro-drift variance membership as a cross-dataset
negative result. UDED aggregate F1/precision/recall and mean fold F1 changed by
`-0.000845/-0.000523/-0.001363/-0.000724`, with `4/15` fold wins despite
`15/15` eligibility. Separately report the official BSDS500-validation
ODS/OIS/AP gains of `+0.002372/+0.001440/+0.009916`, which passed that axis
but cannot override the conjunctive UDED failures. Preserve the equation-level
adaptation and evaluator caveats; do not frame the BSDS gains as promotion or
permission to tune the active-sampling family.

## Stage 18f prospective writing note

Frame Stage 18f as an immutable-author-code integration of Ofir et al.'s
hierarchical triangle-partition faint-curve response, not as exact native-
resolution reproduction of the published detector. Record the pinned commit
and tree, missing explicit source license, parameter-index-zero defaults, one
fixed reflected-letterbox `129x129` whole-image block, disabled shifted pass,
bilinear native-support projection, and non-finite-to-zero flat-field adapter.
Explain that the cue accumulates statistical contrast and shape support over a
combinatorial two-dimensional curve family while the median-conditioned
Scharr+NMS localizer remains unchanged. Report eligibility, precision/recall,
exact score-support preservation, source cleanliness, flat/orthogonal-step and
repeatability contracts, runtime, both development axes, and positions 1/8/15
preview. A failure closes this fixed tree/curve-response integration and must
not motivate tiling, multiple blocks/scales, score or noise estimation,
alternative author modes, detector replacement, calibration, or integration
tuning. Retain the local evaluator's stochastic/reference-reproduction caveat.

## Stage 18f result writing note

Report the fixed one-block author triangle-partition response as a mixed
cross-dataset negative result. UDED aggregate F1/precision/recall and mean
fold F1 changed by `-0.000864/-0.000920/-0.000720/-0.000786`, with `0/15`
fold wins and only `11/15` eligibility. Separately report the official
BSDS500-validation ODS/OIS/AP gains of
`+0.006363/+0.004455/+0.020200`, which passed that axis but cannot override
the conjunctive UDED failures. Preserve the immutable-author-code integration,
fixed raster-adapter, missing-license, and evaluator caveats; do not frame the
BSDS gains as promotion or permission to tune hierarchical curve search.

## Stage 18h prospective writing note

Frame Stage 18h as one fixed global statistical-innovation context test based
on Hou and Zhang's spectral-residual equations, not as exact author-code
reproduction or a standalone edge detector. Record the published 64-pixel
visual scale, `3x3` local log-spectrum average, retained Fourier phase, squared
inverse-transform magnitude and sigma-8 smoothing, plus the disclosed
aspect-preserving resize, amplitude floor, maximum scaling, constant-image
rule, and native projection. Explain that proto-object saliency only gates the
unchanged Scharr+NMS localizer. Report eligibility, precision/recall, exact
score-support preservation, rare-object concentration/localization, periodic/
noise, multiplicative-scale and repeatability contracts, runtime, both
development axes, and positions 1/8/15 preview. A failure closes this fixed
spectral-residual realization without motivating color, multiscale, patchwise,
alternative-saliency, saliency-gradient, learned, calibration, or integration
variants. Retain the local evaluator's stochastic/reference-reproduction
caveat.

## Stage 18j prospective writing note

Frame Stage 18j as one fixed equation-level isolation of Isola et al.'s
image-internal PMI affinity principle, not as exact reproduction of their
complete detector. Record the pinned BSD-licensed author source, 256-level
grayscale alphabet, four centered pair axes, symmetric image-wide joint table,
Laplace-one regularization, density conversion, fixed `rho=1.25`, and bounded
negative-PMI mapping. Explicitly state that KDE, the learned PMI approximation,
multiscale affinity graph, spectral clustering, OWT, and UCM are excluded.
Report eligibility, precision/recall, exact score-support preservation,
flat/step/checkerboard/noise, label-reassignment and repeatability contracts,
runtime, both development axes, and the positions 1/8/15 preview. A failure
closes this discrete dependency-deficit realization without motivating color,
variance features, KDE, multiscale/graph/spectral, conditional PMI,
calibration, or integration variants. Retain the local evaluator's stochastic/
reference-reproduction caveat.

## Stage 18l prospective writing note

Frame Stage 18l as one fixed equation-level closure-participation test based on
Nishigaki et al.'s image-torque operator, not as an exact reproduction of the
paper's learned boundary-strengthening experiment. Record the continuous
Scharr edge measure, clockwise tangent convention, published `5x5`, `21x21`,
and `45x45` square supports, radial-bound coherence, analytic positive
backprojection, maximum across supports, reflection, and exact-zero rule.
Explain that this mid-level cue tests coherent closed-contour participation
while the median-conditioned Scharr+NMS localizer remains unchanged. Report
eligibility, precision/recall, exact score-support preservation,
closed-circle/open-step/checkerboard, polarity and repeatability contracts,
runtime, both development axes, and the positions 1/8/15 preview. A failure
closes this fixed torque realization without motivating support/shape,
edge-threshold, color/depth/motion, learned torque, attention, segmentation,
boundary ownership, calibration, integration, or fusion variants. Retain the
local evaluator's stochastic/reference-reproduction caveat.

## Stage 18n prospective writing note

Frame Stage 18n as one fixed noise-normalized local surface-change test based
on Haralick's sloped-facet F-statistic edge model and Chow's nested-regression
test, not as an exact reproduction of Haralick's iterative facet detector.
Record the two disjoint `3x3` neighborhoods at offset two, four fixed axes,
intercept-plus-row/column plane, pooled-versus-separate RSS formula, numerical
zero-residual rule, `F/(1+F)` bounding, maximum-axis fusion, and reflection.
Explain that the cue only gates the unchanged Scharr+NMS localizer. Report
eligibility, precision/recall, exact score-support preservation, flat/affine-
ramp/step/checkerboard/noise, polarity/positive-affine and repeatability
contracts, runtime, both development axes, and positions 1/8/15 preview. A
failure closes this fixed facet-break realization without motivating geometry,
model-order, robust/higher-order surface, adaptive orientation/window,
alternative-test, segmentation, calibration, or integration variants. Retain
the local evaluator's stochastic/reference-reproduction caveat.

## Stage 18n outcome note

Report Stage 18n as a negative fixed-mechanism result. The cue was eligible in
only `2/15` UDED folds and changed aggregate F1/precision/recall and mean fold
F1 by `-0.000162/-0.000171/-0.000138/-0.000130`, with `1/15` fold wins.
Official BSDS500-validation ODS/OIS/AP changed by
`-0.000021/+0.000078/+0.000098`. State that the fixed local sloped-facet
surrogate did not provide discriminative incremental context under the joint
rule; do not generalize this to Haralick's full iterative facet detector. Keep
the deterministic positions 1/8/15 preview documentary and retain the local
evaluator's stochastic/reference-reproduction caveat.

## Stage 18z outcome note

Report Stage 18z as a negative fixed unsupervised-representation result. The
fold-fitted ICA concentration cue was ineligible in all `15/15` UDED folds,
so candidate and incumbent UDED metrics were identical. Official BSDS500-
validation ODS/OIS/AP changed by
`-0.000056/+0.000027/+0.000074`, failing the ODS margin. The passing fit-
convergence, whitening, orthogonality, repeatability, positive-affine,
exact-support, runtime, model-hash, and fixed-preview contracts establish
implementation behavior only. Do not use the result to motivate alternate
ICA banks, sparse or overcomplete dictionaries, independent subspaces,
color/multiscale representations, supervised atom selection, classifiers,
neural implementations, calibration changes, or rejected-cue combinations.
Retain the local evaluator's stochastic/reference-reproduction caveat.

## Stage 18p prospective writing note

Frame Stage 18p as a fixed aggregation-semantic falsification based on Yager's
OWA framework, not as a new descriptor or a published detector reproduction.
Record that the same five retained fold-calibrated memberships are sorted and
the central order statistic `x_(3)` is used, equivalently OWA weights
`[0,0,1,0,0]`. Explain that this encodes three-of-five support, omits singleton
weights and capacity only in the candidate aggregation, and differs from the
closed Sugeno max-min test. Report precision/recall, fold wins, exact support,
algebraic checks, both development axes, and the fixed positions 1/8/15
preview. A failure closes fixed median OWA without motivating alternative
quantifiers, weighted/adaptive OWA, trimming, mixtures, cue selection, or
dataset conditioning. Retain the local evaluator's stochastic/reference-
reproduction caveat.

## Stage 18p outcome note

Report Stage 18p as a negative fixed-aggregation result. UDED aggregate
F1/precision/recall and mean fold F1 changed by
`-0.001998/-0.001055/-0.003541/-0.001747`, with `1/15` fold wins. Official
BSDS500-validation ODS/OIS/AP changed by
`+0.000666/-0.000988/-0.012906`. State that the fixed three-of-five median
semantics reduced performance and that the result does not motivate other OWA
weights, quantifiers, adaptive/spatial variants, mixtures, or cue selection.
Report the passing algebraic/support contracts and fixed positions 1/8/15
preview as documentary evidence, and retain the local evaluator's stochastic/
reference-reproduction caveat.

## Stage 18r prospective writing note

Frame Stage 18r as a fixed signed-contrast grouping falsification, not as an
exact reproduction of Geisler and Perry's natural-statistics ideal observer.
The method requires bilateral same-polarity unit-gradient alignment at three
predeclared tangent offsets and appends only one fold-eligible context
membership. Emphasize the distinction from signless structure-tensor
coherence, unsigned SE(2) diffusion, binary chains, torque closure, and the
Stage-14b negative-evidence placement study. Report eligibility, UDED paired
fold behavior, official BSDS ODS/OIS/AP, support invariance, synthetic polarity
reversal and photometric contracts, runtime, and the fixed preview regardless
of outcome. Do not describe the cue as contour completion or a learned
association field.

Stage 18r ultimately supplied no eligible UDED integration: the cue failed the
outer-training-fold AUC criterion in all `15/15` folds, and official BSDS500-
validation ODS/OIS/AP changed only by
`-0.000044/-0.000018/+0.000101`. Report this as rejection of the fixed local
signed-gradient realization, not as evidence against contrast polarity in
natural contour grouping. The passed synthetic and invariance contracts are
implementation checks, not detector-performance support.

## Stage 18t prospective writing note

Frame Stage 18t as a fixed calibration-semantic test over the five retained
memberships, not as a new cue, multivariate classifier, or probability claim.
Record the unchanged initial sigmoid memberships, class-balanced edge/texture
weights, exact-tie aggregation, weighted squared-loss PAV solution,
piecewise-constant mapping, nearest-terminal extrapolation, and outer-fold-only
fit. Contrast the mechanism explicitly with the closed multivariate logistic
fusion and label-free empirical-CDF normalization. Report precision/recall,
fold wins, calibrated-membership diagnostics, exact score-support preservation,
algebraic contracts, both development axes, runtime, and the fixed positions
1/8/15 preview. A failure closes this fixed isotonic realization without
motivating alternative class weights, labels, samples, losses, bins,
smoothing, shrinkage, splines, calibration families, feature selection,
aggregation, gate, localizer, or threshold tuning. Retain the local evaluator's
stochastic/reference-reproduction caveat.

## Stage 18t outcome note

Report Stage 18t as a negative fixed-calibration result. UDED aggregate
F1/precision/recall and mean fold F1 changed by
`+0.000574/+0.000822/+0.000110/+0.000676`, with `11/15` fold wins. Official
BSDS500-validation ODS/OIS/AP changed by
`+0.001623/+0.000700/+0.003573`. State that both axes moved positively but
missed their preregistered `+0.002` primary margins, so the conjunctive rule
rejects the candidate. The passing calibration, repeatability, exact-support,
and fixed positions 1/8/15 preview contracts are implementation evidence, not
promotion evidence. Do not present the maps as posterior probabilities or use
the result to motivate alternate isotonic/calibration variants. Retain the
local evaluator's stochastic/reference-reproduction caveat.

## Stage 18v prospective writing note

Frame Stage 18v as a fixed structure-versus-texture coherence falsification
using Xu et al.'s windowed variation primitives, not as an exact reproduction
of their iterative RTV smoother. Record the unchanged conditioned grayscale
input, forward differences, sigma-3 reflected 15x15 Gaussian window, signed
inherent variation, absolute total variation, analytic bounded ratio, and zero
flat rule. Explain that signed oscillations cancel in this statistic, unlike
signless structure-tensor energy, while Scharr+NMS localization remains
unchanged. Report eligibility, precision/recall, fold wins, exact score-support
preservation, synthetic and photometric contracts, runtime, both development
axes, and the fixed positions 1/8/15 preview. A failure closes this fixed
relative-variation realization without motivating iterative RTV smoothing,
alternative TV penalties, scale/support changes, color/multiscale variants,
calibration changes, or rejected-cue combinations. Retain the local evaluator's
stochastic/reference-reproduction caveat.

## Stage 18v outcome note

Report Stage 18v as a negative fixed relative-variation result. The cue was
training-ineligible in all `15/15` UDED folds and therefore reduced exactly to
compact MFI. Official BSDS500-validation ODS/OIS/AP changed by only
`+0.000016/+0.000554/+0.000107`, missing the ODS margin. The passing
synthetic, photometric, repeatability, support, runtime, and fixed-preview
contracts establish implementation behavior only. Do not use the result to
motivate RTV smoothing, derivative/window/scale/ratio variants, calibration,
integration, or rejected-cue combinations.

## Stage 18x prospective writing note

Frame Stage 18x as a fixed nonlinear instantaneous-energy falsification, not
as a reproduction of Boudraa and Diop's contrast-enhancement pipeline. Record
the unchanged median-conditioned grayscale input, published axial and diagonal
2-D Teager-Kaiser stencils, positive rectification, fixed geometric consensus,
analytic division-by-two bound, and reflected `3x3` support. Explain that the
consensus requires both complementary stencil responses and adds only one
outer-fold-eligible positive membership while leaving Choquet aggregation and
Scharr+NMS unchanged. Report eligibility, precision/recall, fold wins, exact
score-support preservation, flat/step/checkerboard/noise and quadratic-scale
contracts, runtime, both development axes, and the fixed positions 1/8/15
preview. Failure closes this realization without motivating alternative TKEO
stencils, max/mean fusion, higher-order energy, wavelet/multiscale/color
variants, demodulation, contrast enhancement, calibration, or integration.
Retain the local evaluator's stochastic/reference-reproduction caveat.

## Stage 18x outcome note

Report Stage 18x as a negative fixed nonlinear-energy result. UDED aggregate
F1/precision/recall and mean fold F1 changed by
`+0.000813/+0.000071/+0.002072/+0.000708`, with only `3/15` fold wins and
eligibility in `3/15`. Official BSDS500-validation ODS/OIS/AP changed by
`+0.000002/+0.000867/+0.000088`. State that the cue missed the UDED aggregate-
F1, fold-win, eligibility, and BSDS ODS conditions despite passing synthetic,
quadratic-scale, repeatability, support, runtime, and fixed-preview contracts.
Do not use the result to motivate other stencils, fusion rules, higher-order
energy, demodulation, contrast enhancement, calibration, or integration.
Retain the local evaluator's stochastic/reference-reproduction caveat.

## Stage 18z prospective writing note

Frame Stage 18z as a fixed leakage-free information-theoretic representation
falsification. Cite Bell and Sejnowski for localized oriented independent
components of natural images and Hyvarinen for robust fixed-point ICA. State
explicitly that inference is a linear filter bank plus a closed-form
concentration statistic, not a neural network or exact author edge detector.
Record the outer-fold-only unlabeled fit, `7x7` patches, 256 patches per
training image, 16 components, PCA whitening, symmetric tanh FastICA, fixed
iteration/tolerance, and maximum-response/L2 concentration mapping. Report
eligibility, precision/recall, fold wins, exact score-support preservation,
fit convergence/whitening/orthogonality/model hashes, runtime, both development
axes, and the fixed positions 1/8/15 preview. Failure closes fixed ICA
concentration without motivating sparse coding, overcomplete or color/
multiscale dictionaries, supervised atom selection, neural implementations,
calibration changes, or rejected-cue combinations. Retain the local
evaluator's stochastic/reference-reproduction caveat.

## Stage 19 bounded-analysis writing plan

Present Stage 19 as a preregistered response to Generation-2 stagnation, not
as post-hoc cue shopping. State the finite budget explicitly: three analysis
experiments, then a fully frozen queue of at most four candidate experiments.
Separate explanatory GT-guided targets from official detector metrics and make
clear that the compact controller is unchanged throughout Stage 19.

For Stage 19B, report a twelve-row descriptor atlas across BSDS500 train and
overlap-clean UDED selection. Include per-domain image-grouped AUC/AP,
nonparametric dependence, effect direction/magnitude and image-bootstrap
intervals; human-consensus strata; monotone empirical boundary-probability
curves; and runtime. Document that all BSDS annotators are preserved, the
tolerant explanatory target uses the fixed `0.0075`-diagonal geometry, and
UDED item `03-35028` is excluded by filename lineage because it is BSDS-test
image `35028`. The qualitative figure uses fixed BSDS-train positions
1/100/200 and shows input, mean human GT, and all twelve descriptor maps. Do
not describe Stage 19B as selecting a feature or improving a detector; its
role is to supply preregistered evidence for Stage 19C.

For Stage 19C, report the machine-derived six-cue shortlist in its frozen
order: structure-tensor coherence, `gabor4_s13`, semi-global change-point,
`hessian_s13`, brightness entropy, and `gabor4_s5`. Explain that Frei-Chen was
pruned only by the preregistered bilateral redundancy/complementarity rule.
Do not present the shortlist as a detector improvement. The incumbent-only
BSDS-train ODS/OIS/AP `0.535462/0.574704/0.514451` is evaluator provenance,
not a candidate result.

For Stage 19D, present exactly three analysis families: incumbent distorted
Choquet, nonnegative additive/logistic, and monotone 2-additive Choquet. Report
image-grouped within-domain and cross-domain probabilistic/ranking evidence,
parameter stability, Shapley importance, and pair interaction indices. Make
clear that Stage 19D only supplies the Stage-19E synthesis and cannot promote
or alter MFI; the complete Stage-20 queue is frozen afterward and before any
BSDS-validation candidate result.

For Stage 19E, report the full queue as a preregistered finite campaign, not as
four adaptive follow-ups. The frozen order is full six-cue shortlist,
four-cue interaction core, dominant Gabor-13/change-point pair, then the
incumbent five-cue bank with only aggregation changed. Explain that all use the
same monotone 2-additive Choquet fitting rule and that the additive/logistic
family was excluded by its Stage-19D transfer-collapse classification. State
that known UDED item `03-35028` is excluded throughout Stage 20 by protected
BSDS-test lineage and that the complete queue preceded every candidate BSDS-
validation outcome. Each Stage-20 result must report both development axes,
fit and support contracts, capacity Shapley/interaction diagnostics, runtime,
and the fixed positions 1/7/14 preview. If a candidate passes, stop the queue;
if all four fail, end with synthesis and do not imply an unreported fifth test.

## Stage 20a outcome note

Report Stage 20A as a conjunctive rejection with cross-metric tension, not as
a near-promotion. The full-shortlist 2-additive model passed all UDED and
fit/support requirements (`+0.007589` aggregate F1, `+0.013213` precision,
`-0.002227` recall, `+0.006121` mean fold F1, `13/15` wins, `15/15`
converged fits). On official BSDS500 validation it improved ODS/OIS by
`+0.007402/+0.003711` but reduced AP by `-0.043929`; the registered
nonnegative-AP condition therefore rejects it. Preserve the evaluator caveat,
the fixed preview, and the fact that Stage 20B was frozen before this result.
Do not imply that the AP loss licenses weight, calibration, descriptor, or
capacity tuning.

## Stage 20b outcome note

Report Stage 20B as a second conjunctive rejection with the same cross-metric
pattern, not as evidence for post-hoc calibration. The four-cue interaction-
core candidate passed UDED and all implementation contracts (`+0.007539`
aggregate F1, `+0.013211` precision, `-0.002354` recall, `+0.006079` mean
fold F1, `13/15` wins, and `15/15` converged fits). Official BSDS500
validation improved ODS/OIS by `+0.007330/+0.004178` but reduced AP by
`-0.043939`; the nonnegative-AP requirement rejects it. Preserve the
reference-unverified evaluator caveat, fixed preview, unchanged incumbent,
and the fact that Stage 20C was frozen before both Stage-20 outcomes.

## Stage 20c outcome note

Report Stage 20C as a third conjunctive rejection despite the strongest UDED
and ODS/OIS movement in the frozen queue so far. The dominant-pair candidate
passed UDED and all implementation contracts (`+0.008839` aggregate F1,
`+0.011107` precision, `+0.004564` recall, `+0.006457` mean fold F1,
`12/15` wins, and `15/15` converged fits). Official BSDS500 validation
improved ODS/OIS by `+0.014305/+0.008814` but reduced AP by `-0.026222`; the
nonnegative-AP requirement rejects it. Preserve the reference-unverified
evaluator caveat, fixed preview, unchanged incumbent, and the fact that Stage
20D was frozen before all three outcomes. Do not interpret the smaller AP loss
as permission to tune calibration, descriptors, capacity constraints, or the
queue.

## Stage 20d outcome and bounded-program synthesis note

Report Stage 20D as the final conjunctive rejection. The aggregation-only
compact-bank candidate passed UDED and all implementation contracts
(`+0.008531` aggregate F1, `+0.014096` precision, `-0.001226` recall,
`+0.007238` mean fold F1, `15/15` wins, and `15/15` converged fits), but
official BSDS500-validation ODS/OIS/AP changed by
`-0.001575/-0.003695/-0.003835`. Preserve the fixed positions 1/7/14
preview and the reference-unverified evaluator caveat.

Synthesize Stages 20A--20D as one preregistered finite campaign. All four
candidates cleared the UDED aggregate-F1 margin; none cleared the joint BSDS
rule. The three Stage-19-pruned cue sets improved ODS/OIS while reducing AP,
whereas the compact-bank aggregation fallback reduced all three metrics. The
safe claim is that the selected monotone 2-additive family improved the
overlap-clean UDED operating-point objective but failed cross-domain ranking
transfer under the frozen fitting and serialization contract. Do not portray
any entry as nearly promoted, average results across incompatible endpoints,
or imply an unreported fifth candidate or post-hoc calibration study. Compact
distorted-Choquet MFI remains the retained controller, and this bounded program
ends without meeting the generalized SOTA objective.

## Stage 21 protocol-certification and diagnosis note

Present Stage 21 as a bounded protocol and causal-diagnosis program, not a
continuation of the Stage-20 candidate queue. Keep three endpoints visibly
separate: primary Berkeley matching at `maxDist=0.0075`, Berkeley tolerance
sensitivity at `0.025`, and the Estrada--Jepson fuzzy-literature comparison at
`0.025`. Loose-tolerance results cannot promote a model and metrics from the
two matchers must not be interchanged. Until a public reference output is
reproduced, retain `reference_reproduction_verified=false` on local Berkeley
scores and explain the pinned matcher's unrecorded random-sampling state.
Stage 21A is infrastructure-only; Stage 21B is the first scientific result and
must use the frozen incumbent and Stage-20A--20D artifacts without refitting.

Stage 21A ultimately passed its stop rule while preserving the unresolved
Berkeley reference-RNG caveat. In the Stage-21 methods narrative, describe the
KITT Estrada--Jepson path as micro-case-verified best-public-source fidelity,
not an exact private-code reproduction. Stage 21B is preregistered to hash and
rescore the identical five frozen map sets, with `0.5` fixed-threshold and
99-point best-threshold fuzzy results explicitly separated from Berkeley
ODS/OIS/AP and from each other.

Stage 21B is now complete. Its main table should show that Stage 20C has the
best standard-Berkeley ODS/OIS among the frozen candidates but lower AP than
the incumbent, while the `0.025` Berkeley sensitivity track increases all
three metrics without erasing the candidate's AP deficit. Put the separate
Estrada--Jepson best-threshold-F table beside, not inside, the Berkeley table;
Stage 20C's higher fuzzy F is protocol-comparison evidence only. Retain the
best-public-KITT and reference-unverified caveats in the table caption.

Stage 21C supplies the planned PR anatomy figure/table: curve crossings,
precision at fixed recalls, AP area by recall band, threshold-dependent edge
density, and per-image deltas. Label its per-image precision-envelope area as a
diagnostic quantity rather than official aggregate AP.

Stage 21C shows why both raw and enveloped PR summaries are needed: Stage 20C
has higher envelope precision at every registered fixed recall and positive
common-range envelope area, yet loses the earliest recall-band area and official
raw-curve AP. Do not describe the AP regression as uniform across recall, and
do not substitute per-image/envelope area for Berkeley AP. Stage 21D will supply
the ranking-versus-localization table using explicitly non-official
union-distance and near-GT multiplicity diagnostics.

Stage 21E adds the full tolerance-response figure. Report that Stage 20C's ODS
advantage persists from `0.00375` through `0.025`, but its AP deficit also
persists and becomes larger at looser tolerances. This is evidence against a
simple fixed-displacement account, not evidence that tolerance is a tunable
detector parameter. Keep `0.0075` visually primary and label the other curves
as non-promotional sensitivity results. Stage 21F should place context,
pre-NMS Scharr, pre-NMS context-local coupling, and final post-NMS diagnostic
rows side by side, while reserving official Berkeley terminology for the
unchanged final outputs only.

Stage 21F supplies the pipeline-attribution table. Report that Stage 20C's
context has a clear tolerant-union ranking advantage, that shared-Scharr
coupling narrows but preserves it, and that NMS sharply compresses both methods'
descriptive AUC/AP while preserving a small Stage-20C advantage. These are
non-official attribution measures, not an explanation that rescues the
candidate. Stage 21G should report consensus-rank correlation, higher-versus-
lower consensus pairwise accuracy, consensus strata, and deterministic weak-
over-strong examples before the single Stage-21H design decision.

## Stage 21H outcome and finite-program synthesis note

Report the consensus-pairwise 2-additive Choquet candidate as a conjunctive
rejection, not as an AP-only near miss. On overlap-clean UDED it improved
aggregate F1/precision and won `12/15` folds, but recall changed by
`-0.009200`, beyond the registered `-0.003` floor. On standard Berkeley
validation it improved ODS/OIS by `+0.014168/+0.008702` but reduced AP by
`-0.033638`. Preserve both independent failure reasons, the fixed preview,
the unchanged compact-MFI incumbent, and the reference-unverified matcher
caveat.

The Stage-21 synthesis should state that consensus-aware pairwise capacity
fitting did not repair raw ranking transfer under the frozen two-cue pipeline:
operating-point gains again coexisted with a material AP loss, while UDED
recall also collapsed beyond tolerance. Do not imply a second Stage-21H
candidate, post-hoc loss balancing, pair reweighting, calibration repair, or
automatic literature continuation. The finite program ends without promotion
and without satisfying the generalized SOTA objective.

## Stage 22 thesis-legacy and causal-resolution note

Keep the Stage-22B legacy table separate from every Berkeley and aggregate-
KITT table. The exact historical best-per-annotation procedure gives mean
best-match F0.5 `0.571790` for compact MFI and `0.602663` for Stage 20C, while
the transparent all-GT means are `0.497851` and `0.525383`. Present this as a
longitudinal protocol bridge, not a detector promotion or a repair of the
standard-Berkeley AP deficit. Retain the reference-unverified caveat and show
the per-GT distribution beside the best-match summary to expose annotation
selection.

Stage 22C is a causal calibration diagnostic with its dominance score frozen
before inspection. Its GT-derived per-image monotone mapping is an upper bound
only, and its unlabeled normalization families are non-selective simulations.
Neither may be reported as a candidate detector.

Stage 22D should be reported as a negative causal diagnosis: the competition-
dominance components were `0.02180/0/0` (score `0.00727`), no registered early
false positive was assigned to local competition, and Stage 20C did not show
excess near-GT multiplicity. Do not infer that NMS is universally harmless;
the conclusion is limited to the fixed Stage-22D attribution contract.

The mechanical branch therefore authorizes exactly one Stage-22E calibration
candidate. Describe its positive-support empirical-midrank to outer-training
median-quantile-reference mapping as a final-score calibration only: the
Stage-20C descriptors, capacity, context gate, Scharr localizer, and NMS remain
unchanged, and within-image ordering/support are invariant. Report its final
joint UDED and standard-Berkeley outcome regardless of sign, followed by the
required causal table and explicit finite-program stop. Legacy and loose-
tolerance scores remain descriptive and cannot rescue Stage 22E.
