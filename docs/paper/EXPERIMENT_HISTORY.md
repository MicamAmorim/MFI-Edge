# Experimental history — MFI-Edge research log

## Stage 13b/13c — protocol research and BIPEDv2 preflight

Stage 13a is a one-shot BSDS500 external transfer using a consensus/tolerant-matching proxy. Its test outcomes are excluded from all Stage-12d design and calibration decisions. The independent replication is predeclared on the authors' BIPEDv2 test split: 50 author-designated test images (from 250 total, 200 train), native 1280×720 RGB and edge-map pairs. Training images are unused. Stage 13c only checks the locally supplied dataset and frozen candidate artifact; it does not infer or score test images. Dataset terms require user acceptance before retrieval, so acquisition is a human action.

The canonical layout checked by `automation/stage13c_biped_preflight.py` is `edges/imgs/{train/rgbr/real,test/rgbr}` paired by stem with `edges/edge_maps/{train/rgbr/real,test/rgbr}`. The replication should preserve the frozen UDED-selection thresholds/configurations, report fixed-threshold transfer metrics as such, and must not optimize on BIPED test. BIPEDv2 is single-annotator edge GT, so its results are a distinct edge-dataset replication, not numerically interchangeable with multi-annotator BSDS boundary metrics.

For publication-grade BSDS claims, export full-resolution soft thinned score maps and run the Berkeley benchmark implementation: its bipartite/CSA++ matcher handles localization tolerance and multiple human segmentations; soft maps let the benchmark sweep thresholds. The official project identifies MATLAB as a requirement and reports no Windows support. A compatible MATLAB/CSA++ runtime/tool checkout must be established before implementing an evaluator adapter; do not substitute the local dilation matcher and label it official.

Sources: BIPEDv2 author repository, https://github.com/xavysp/MBIPED (dataset description, split, resolution, and non-commercial-use terms); DexiNed author repository, https://github.com/xavysp/DexiNed (dataset version and test usage); Berkeley BSDS project, https://www2.eecs.berkeley.edu/Research/Projects/CS/vision/bsds/ (official benchmark, CSA++ matching, soft boundary output, MATLAB requirement).

Stage 13c preflight passed: the local BIPEDv2 files contain 200 paired training images and 50 paired test images at 1280×720, and the frozen candidate artifact is present. Stage 13d is registered as a one-shot external replication: it leaves training unused, uses the 50 test pairs at native resolution, applies only Stage-12d frozen candidate thresholds, and fits the Scharr comparator threshold on UDED selection. Results are fixed-threshold diagnostics with paired bootstrap uncertainty; no BIPED-driven threshold selection or ranking is permitted. The runner records runtime and the single-annotator metric limitation.

Stage 13d completed on the frozen BIPEDv2 test split (50 images, native 1280×720; 54.0 s/image average). The ratio-control representative scored fixed F1 0.7461 versus 0.7370 for Scharr (paired delta +0.00906, 95% bootstrap interval [+0.00712, +0.01101]); positive control and separable bicapacity scored 0.7254 and 0.7339, respectively, both below Scharr. These are fixed-threshold, single-annotator BIPED edge-map diagnostics and cannot establish superiority under the distinct Berkeley boundary protocol. No tuning or candidate changes follow from this external result. With the earlier BSDS500 proxy diagnostic also complete, the next predeclared validation step is an official Berkeley evaluation of frozen soft maps, if a compatible benchmark runtime and adapter are available.

## Stage 14b — spatial polarity mechanism ablation (development only)

Using only the 15 UDED selection images in 5×3 repeated leakage-free CV, the
spatial positive-vs-negative ratio controller did not support the preregistered
hypothesis that aligned anti-texture localization adds value beyond negative
burden alone. Its aggregate CV F1 was 0.75669, versus 0.75922 for the
image-mean-negative control and 0.75889 for positive-only. The mean paired fold
difference against image-mean negative was −0.00213 (6 wins, 9 losses); repeated
folds are descriptive and not independent significance evidence. Spatial ratio
control also trailed positive-only by 0.00202 mean fold F1. The no-negative ratio
control (0.75144) was lower, so this test does not show that all negative
information is irrelevant; it specifically fails to support spatial alignment.
No external results or UDED held-out data informed this interpretation.

The next registered test is feature pruning: compare the fold-trained full
positive bank with the five features stable in every Stage-12d split, holding
aggregation, Scharr+NMS localization, gate, and fold-fitted threshold fixed.

## Stage 14a — literature-guided development checkpoint

The new Stage-14 cycle considers three distinct hypotheses using development
evidence only:

1. RDF-based d-Choquet/d-CF/d-XC/d-CC aggregation may help under blur, noise,
   texture, or scale heterogeneity. The earlier UDED-selection family screen
   did not beat the standard contextual family in inner-CV F1, so a targeted
   robustness test remains a later candidate rather than a reason to promote
   the family from isolated full-selection peaks.
2. Relative positive-vs-negative contextual control may add value beyond a
   positive signature. Stage 14b did not support spatial negative alignment;
   its next implication is to prune the stable positive bank before revisiting
   negative terms.
3. A compact conditional expert controller could exploit regime-specific
   complementarity, but should only be considered after development-only
   ablations establish complementary error patterns.

The single next falsification test is the registered Stage-14c positive-bank
pruning comparison. It holds positive distorted-Choquet aggregation,
Scharr+NMS, the context gate, and fold-fitted thresholds fixed while comparing
the fold-trained full bank against the five features stable in every Stage-12d
split. The runner uses repeated leakage-free CV on UDED selection only. This
is the smallest direct test of whether the currently supported mechanism can
be simplified before adding another mechanism. UDED held-out and both inspected
external tests play no role.

Stage 14c completed under the predeclared pruning rule. The five-feature bank
had aggregate repeated-CV F1 0.75905 versus 0.75889 for the full fold-trained
bank, with mean paired fold delta +0.000054 (5 wins, 10 losses); all five
features were selected in every training split. This supports provisional
pruning to the compact bank, but the tiny aggregate difference and descriptive
dependent folds do not establish a reliable improvement. The next minimal
ablation removes only `gabor4_scale_persistence` from that compact bank to test
whether the stability cue is redundant. It uses the same UDED-selection-only
repeated-CV protocol, aggregation, localizer, gate, and fold-fitted thresholds.
No external or held-out result informed this step.

Literature informed the candidate space, not the experiment ranking: Amorim
et al. study RDF Choquet-like operators for single-scale multi-channel edge
detection (https://doi.org/10.3390/app152413273), while Beliakov and Wu discuss
reducing fuzzy-measure learning complexity through k-interactivity
(https://doi.org/10.1016/j.ins.2019.04.042). The current pruning test is
empirically motivated by Stage-12d feature stability and Stage-14b ablation;
it does not claim that either paper establishes an MFI-Edge performance gain.

Stage 14d completed the predeclared persistence ablation using the same 15
UDED-selection images, 5x3 repeated leakage-free CV, positive distorted-
Choquet aggregation, Scharr+NMS localizer, gate, and fold-fitted thresholds.
The four-feature bank without `gabor4_scale_persistence` reached aggregate
CV F1 0.75473 versus 0.75889 for the five-feature compact bank; its mean
paired fold delta was -0.00322 (3 wins, 12 losses). By the predeclared rule,
scale persistence is retained and the compact five-feature bank is not
pruned further on this evidence. Fold counts are descriptive, not independent
inference. No external test or UDED held-out data informed this result.

The next scientifically distinct direction is a narrow d-CC robustness
falsification, motivated by Amorim et al. (2025). Their strongest reported
d-CC settings pair FBPC and the absolute RDF with gravitational smoothing;
this does not establish an isolated RDF benefit for the current multiscale
controller. Stage 14f therefore changes only the aggregation layer and holds
the retained five-feature positive bank, Scharr+NMS localizer, gate, and
threshold-selection procedure fixed. No external result informed this choice.

## Stage 14f — preregistered d-CC robustness falsification (development only)

Compare the frozen five-feature positive distorted-Choquet control against
d-CC with FBPC and the absolute RDF. Feature definitions and parameters come
from the Stage-12d frozen positive bank, filtered to the five features
retained after Stage 14d, with the subset weights renormalized. Both variants
retain gamma 0.55, Scharr+NMS, context-gate strength 2.0/floor 0.10, and
train-calibrated thresholds.

Use the fixed 40-item `synthetic_v2` validation manifest only. Manifest rows
0,2,...,38 generate clean calibration references; rows 1,3,...,39 generate
paired clean evaluation references and the same base shapes under Gaussian
noise, Gaussian blur, periodic texture, and compound corruption at the
generator's predeclared severities 0.35, 0.65, and 1.0. Fit each variant's
threshold on calibration-clean images with the existing threshold-selection
routine, then freeze it for all evaluation conditions. Report clean absolute
F1 separately from absolute F1 and clean-referenced degradation for each
corruption family/severity, using mean per-image F1 as the primary metric.

The predeclared support criterion is a mean improvement of at least 0.01 in
clean-referenced degradation across the 12 corruption cells, clean F1
noninferiority within 0.01, and positive mean degradation advantage in at
least three of four families. This small development experiment is a
falsification test, not a final robustness claim. If met, a separately
registered confirmation is required before retaining d-CC; otherwise it is
not promoted on these data. The primary methodological source is Amorim et
al. (2025), DOI https://doi.org/10.3390/app152413273. Their reported d-CC
advantage is coupled to gravitational smoothing, intentionally excluded here
to keep aggregation as the sole change.

Stage 14f completed on the declared synthetic validation development split.
Under the runner summary's absolute corrupted-F1 criterion, d-CC averaged
0.00191 below the standard control, its clean mean-image F1 was 0.00280 lower,
and it had no positive absolute advantage in any corruption family. The
criterion was not met. The clean-referenced degradation advantage was only
0.00088 on average (positive in three of four families), far below the
history's preregistered +0.01 threshold. Thus neither the absolute-performance
criterion reported by the runner nor the degradation criterion written here
supports retaining d-CC. The slight descriptive degradation signal does not
offset the worse absolute corrupted F1 and clean score.

Protocol record discrepancy: this section preregistered degradation advantage
of at least +0.01 as primary, while the completed runner summary labels
absolute corrupted-F1 advantage of at least +0.005 as primary. The two
criteria differ, and neither was met; record this discrepancy when interpreting
the falsification, and do not treat either as a promotion result. Thresholds
were fit on clean calibration images and fixed across conditions; the result
used synthetic validation only, with no UDED or external data. d-CC is not
promoted. The RDF robustness hypothesis remains unsupported by this test, not
universally disproven.

## Stage 14g/14h — post-RDF literature checkpoint and next test

The Stage-14g checkpoint compared three distinct next directions: further RDF
operators (deferred after the isolated d-CC test and not to be parameter-tuned),
development-only complementarity analysis before any conditional experts, and
the preprocessing mechanism paired with the strongest literature-reported
d-CC setting. Amorim et al. (2025) report that gravitational smoothing
consistently improves their single-scale RGB detector and that their strongest
d-CC setting couples absolute RDF with that smoother. This motivates testing
the smoother by itself; it does not establish a gain for MFI-Edge's grayscale
multiscale controller. The diversity literature also cautions that disagreement
statistics alone do not predict ensemble accuracy, so routing remains deferred
until paired development errors support a concrete correction mechanism.

Stage 14h is preregistered as one isolated grayscale gravitational-conditioning
ablation on the fixed synthetic validation split. It replaces the median
prefilter before both feature and Scharr branches, holding the compact positive
controller and all other settings fixed. Thresholds use only the clean
calibration half; paired corruption results are development evidence only.
Promotion requires the explicit Stage-14h criteria and separate development
confirmation. No UDED held-out, BSDS500 test, or BIPEDv2 test result informs
this choice.

Stage 14h completed on the preregistered synthetic development protocol. The
gravitational candidate met the corrupted-average threshold with mean absolute
F1 advantage `+0.00534`, but failed the other two required criteria: clean
mean-image F1 changed by `-0.27231`, far below the `-0.01` noninferiority
limit, and only one of four corruption families had positive mean advantage.
The positive result was confined to periodic texture; gravitational smoothing
was worse for Gaussian noise, blur, and compound corruption at every tested
severity. The full conjunction therefore failed and median conditioning is
retained. The deterministic preview uses the first odd-index evaluation base
image, with rows clean/Gaussian/blur/texture/compound and columns input,
ground truth, median incumbent, gravitational candidate, and retained best.
These qualitative panels are inspection artifacts only. The strong
texture-specific contrast is descriptive evidence of regime complementarity,
not support for routing on corruption labels or tuning gravitational
parameters. Further RDF/gravitational micro-tuning is deferred; the next
registered action is the autonomous literature/mechanism escalation. No
external or UDED held-out feedback informed this decision.

## Stage 14i — literature escalation and fixed topology-repair test

The October 2026 live-literature checkpoint found that the current neural
frontier increasingly separates edge-score quality from crispness and
continuity. MatchED (CVPR 2026) aligns learned raw edges to annotations through
one-to-one matching, while MS2Edge (Pattern Recognition, 2025/2026) explicitly
identifies sparse contour discontinuities as a remaining crisp-edge failure
mode. These neural mechanisms are not admissible in MFI-Edge inference and are
not copied. Their role is to sharpen the evaluation question: after retaining
Scharr+NMS localization, can a fixed non-neural topology stage improve contour
continuity without paying for it in boundary accuracy?

The repository already contains independent development-only evidence for one
such mechanism. In Stage 4, MFI-guided geodesic endpoint linking with
`max_gap=8` and `max_mean_cost=0.60` improved held-out synthetic F1 by about
`+0.0060`, increased recall by about `+0.0104`, and raised largest-component GT
coverage from `0.2827` to `0.4772`. This evidence predates the current compact
controller and is sufficient to justify a transfer falsification without a new
parameter search.

Stage 14i is therefore preregistered on UDED selection only under 5x3 repeated
leakage-free CV. It holds the five-feature positive distorted-Choquet context,
gate, and Scharr+NMS score fixed, comparing threshold-only output with the
fixed Stage-4 geodesic linker. Memberships and thresholds are fitted inside
training folds; linker parameters are not swept. Retention requires F1 and
precision noninferiority plus predeclared largest-component coverage gains.
The authoritative protocol is `docs/paper/STAGE14I_PREREGISTRATION.md`.
UDED held-out and both inspected external tests are excluded.

Stage 14i completed without promotion. The no-link control reached aggregate
CV F1 `0.77334`, versus `0.75815` for fixed geodesic linking (delta
`-0.01519`). Mean fold F1 changed by `-0.01134`, and the candidate won no F1
folds. Aggregate precision changed by `-0.00304`, within its `-0.005`
noninferiority margin. Mean paired per-image largest-component GT coverage
increased only `+0.00156`, far short of the required `+0.03`, although fold
mean coverage improved in 12/15 folds. Because the preregistration required
all four conditions, the candidate failed on F1 noninferiority and coverage
effect size; the no-link compact positive controller remains incumbent.

The fixed qualitative artifact uses the first validation image of the first
deterministic split. Its columns are conditioned input, ground truth, no-link
incumbent, fixed-geodesic candidate, and retained best. It is documentary only
and did not influence the decision. The natural-image result does not erase
the earlier synthetic continuity gain, but it shows that this transferred
linker does not preserve boundary accuracy or deliver a material coverage gain
in the current architecture. No linker sweep follows from these results. The
next registered action is the autonomous high-reasoning literature/mechanism
escalation, excluding UDED held-out and inspected external-test feedback.

## Stage 14j — phase-congruency context-feature checkpoint

The post-topology live-literature escalation considered three mechanistically
distinct non-neural directions: (1) local phase congruency as contrast-
normalized multiscale context, (2) an interpretable conditional localizer using
phase-versus-gradient complementarity, and (3) a learned classical structured
forest on a future larger development split. The second lacks development-only
complementarity evidence and the third requires a newly designated training
resource. The smallest justified next test is therefore the first direction.

Local energy theory identifies general features where Fourier components align
in phase (Morrone and Owens, 1987, DOI
`10.1016/0167-8655(87)90013-4`). Kovesi's noise-compensated PC2 construction
turns this into a dimensionless multiscale/multiorientation feature-significance
measure and uses its maximum covariance moment as an edge indicator (Kovesi,
1999; 2000, DOI `10.1007/s004260000024`). This differs from the retained
Gabor/Hessian bank, which is dominated by response amplitude even though its
Gabor channels are multiscale.

Stage 14j is preregistered as a single-feature addition on UDED selection only,
using the established 5x3 repeated leakage-free CV. It appends the fixed
`phasecong3`-default maximum moment to the five retained positive memberships;
Scharr+NMS, distorted-Choquet gamma, gate, and conditioning remain fixed.
Membership calibration, singleton weight, an established positive-direction
eligibility check, and thresholds are learned inside each training fold. No
phase parameter sweep or localizer replacement is allowed. The authoritative
protocol and promotion criteria are in
`docs/paper/STAGE14J_PREREGISTRATION.md`. The SOTA ledger was already refreshed
on 2026-10-06 and this mechanism search found no primary benchmark result that
changes its verified targets.

Stage 14j completed without promotion. The compact incumbent reached aggregate
F1 `0.759053`, while compact-plus-phase reached `0.758692` (delta
`-0.000361`). Mean fold F1 changed by `-0.000251`, aggregate precision by
`-0.000589`, and the candidate won 6/15 folds. Although the phase feature was
training-eligible in all 15 folds, the preregistered aggregate-F1, positive
mean-fold-delta, and 9/15-win criteria failed. Thus fixed-default phase
congruency is discriminative by the training-only eligibility diagnostic but
has not shown incremental benefit as a sixth positive membership in the
current gate. The five-feature compact controller remains incumbent.

The deterministic qualitative artifact uses the first validation image of the
first split. Its columns are conditioned input, ground truth, compact
incumbent, compact-plus-phase, and retained best; it was not used for model
selection. The preregistration prohibits tuning phase parameters from this
outcome. Because the minimal context test did not establish complementarity,
the deferred phase/gradient localizer router is not advanced. The next
registered action is the autonomous high-reasoning literature/mechanism
escalation, excluding held-out and inspected external-test feedback.

## Stage 14k — CIELAB vector-gradient localizer checkpoint

The post-phase live-literature escalation considered three distinct non-neural
directions: (1) a fixed vector-color gradient tensor as a more complete precise
localizer, (2) oriented half-disc CIELAB histogram contrast as a region-scale
boundary cue, and (3) a classical structured forest trained on a future larger
development split. The third requires a newly designated training resource,
while the second adds radius, binning, orientation, and cue-combination choices.
The first is therefore the smallest falsification and directly tests a known
information loss in the grayscale localizer.

Di Zenzo's multi-image gradient derives a tensor whose maximum eigenvalue and
eigenvector give the greatest vector-valued rate of change and its direction
(1986, DOI `10.1016/0734-189X(86)90223-9`). The natural-boundary literature
separately established CIELAB brightness and chromatic contrast as useful local
cues (Martin, Fowlkes, and Malik, 2004, DOI
`10.1109/TPAMI.2004.1273918`; Arbeláez et al., 2011, DOI
`10.1109/TPAMI.2010.161`). These sources motivate the mechanism but provide no
target-test feedback or parameter selection.

Stage 14k is preregistered on UDED selection only under the established 5x3
repeated leakage-free CV. The compact five-feature context, fold-trained bank,
distorted-Choquet gamma `0.55`, context gate, and independent fold-fitted
thresholds remain fixed. The sole candidate change is median conditioning in
three CIELAB channels followed by fixed Scharr derivatives, the Di Zenzo tensor,
and NMS along its maximum-change direction. No channel weights, color space,
kernel, normalization, mixture, router, or parameter sweep is permitted. The
authoritative protocol is `docs/paper/STAGE14K_PREREGISTRATION.md`.

The runner must write `best_method_preview.png` from the first validation image
of the first deterministic split. Its columns are RGB input, ground truth,
grayscale-Scharr incumbent, CIELAB-tensor candidate, and retained best; the
image is documentary only. The SOTA ledger was refreshed on 2026-10-06 and the
mechanism search found no verified primary benchmark result that changes its
current target rows.

Stage 14k completed without promotion. The grayscale incumbent reached
aggregate F1 `0.759053` and precision `0.671339`; the Lab tensor candidate
reached F1 `0.747509` and precision `0.658090`. Relative to the incumbent, the
candidate changed aggregate F1 by `-0.011544`, aggregate precision by
`-0.013249`, and mean fold F1 by `-0.012055`, with only 1/15 fold wins. It
therefore failed every preregistered promotion condition. Grayscale Scharr+NMS
remains the localizer, and no color weights, fusion, routing, or tensor
parameters may be tuned from this result.

The deterministic `best_method_preview.png` uses the preregistered first
validation image and shows RGB input, ground truth, grayscale incumbent, Lab
tensor candidate, and retained best. It is documentary only and was not used
for model selection. Because the direct fixed vector-color replacement failed
decisively, the next registered action is the repeatable high-reasoning
literature/mechanism escalation, without held-out or external-test feedback.

## Stage 14l — oriented texture-distribution context checkpoint

The post-color live-literature checkpoint compared three distinct directions.
Edge Drawing was not selected because its anchor tracing overlaps the recently
failed topology/linking family. A structured/random-forest boundary model was
deferred because it is a larger learned redesign than the next minimal
falsification requires. The selected mechanism is two-sided texture-
distribution contrast: unlike the incumbent Gabor/Hessian amplitudes, it asks
whether the distribution of texture primitives changes across a putative
boundary.

Martin, Fowlkes and Malik (2004, DOI `10.1109/TPAMI.2004.1273918`) report that
explicit texture distributions complement brightness gradients and compute
their texture gradient as chi-square distance between oriented half-disc
texton histograms. Ojala, Pietikäinen and Mäenpää (2002, DOI
`10.1109/TPAMI.2002.1017623`) provide a compact rotation-invariant uniform-LBP
texture code. Stage 14l combines these ideas as a fixed texton-free surrogate;
it is not presented as a reproduction of the learned Berkeley texton cue.

Stage 14l is preregistered on UDED selection only under the established 5x3
repeated leakage-free CV. It appends one maximum-oriented chi-square contrast
of uniform-LBP half-disc histograms to the retained five-feature positive
bank, while keeping Scharr+NMS, distorted-Choquet gamma, gate, and fold-fitted
thresholds unchanged. Candidate membership and singleton weight are fitted
inside each training fold. No radius, bin, descriptor, orientation, or fusion
sweep is permitted. The authoritative protocol and conjunction promotion rule
are in `docs/paper/STAGE14L_PREREGISTRATION.md`. UDED held-out and all inspected
external tests are excluded.

The same live refresh found an official author-repository update reporting DDN
BSDS500 ODS `0.867` under its multi-granularity strategy. That oracle-style
candidate-selection protocol is not interchangeable with one frozen edge map,
so it does not replace the single-output SOTA target or affect Stage 14l. The
protocol distinction is recorded in `docs/paper/SOTA_TARGETS.md`.

This document reconstructs the experimental decisions discussed during development so the future manuscript can distinguish **historical exploration**, **current evidence**, and **results that are publication-grade only after rerunning with the final protocol**.

## Status labels

- **Historical** — useful for the design story, but superseded by later protocol or implementation changes.
- **Exploratory** — technically meaningful, but based on synthetic data, small datasets, approximate boundary matching, or development-time calibration.
- **Candidate result** — protocol is reasonably strict (selection/held-out separation), but still needs replication with official benchmark tooling / larger datasets.
- **Final-paper target** — experiment that should be rerun before submission.

---

## Stage 0–2 — early prototype and validation correction

**Status:** Historical.

The original prototype established the core idea of using generalized Choquet-style aggregation of local image descriptors to build an MFI evidence map. Early synthetic benchmark values from the first dataset version were later **superseded** after identifying a mismatch in diagonal ground-truth generation/evaluation. Those numerical results must not be quoted in a paper.

What survived conceptually:

```text
image -> local/multiscale fuzzy evidence -> MFI ranking -> edge localization
```

Important methodological lesson: synthetic GT generation and tolerance matching must be validated independently before comparing operators.

---

## Stage 3 — orientation-aware descriptors

**Status:** Exploratory, useful architectural evidence.

### Main change

The descriptor stack was expanded from legacy/rotation-invariant cues to orientation-aware cues using the local gradient normal/tangent. Important new responses included normal contrast, normal-minus-tangent contrast, and a steered Hessian response.

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

Weakest regimes: **motion blur, compound degradation, texture**. These failures directly motivated local context routing, frequency descriptors and a dynamic localizer bank.

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

Adaptive MFI confidence was often more concentrated on GT-edge pixels, but direct score fusion failed to turn that ranking advantage into a reliable final-edge improvement. This strongly motivated separating **context/evidence** from **localization**.

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

A larger search did **not** prove a natural-image advantage. The selection winner generalized worse. This is scientifically useful: flexible fuzzy models can overfit a tiny selection set, and direct fusion is likely the bottleneck.

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

**Status:** Workstation architecture prototype; superseded by v2 for active experiments.

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

This was the first architecture explicitly designed around the hypothesis:

> **MFI should control/refine a precise edge localizer rather than merely add another edge score.**

---

## Stage 10 / local CH-MFI-v2 — second-wave literature-driven family

**Status:** **Initial workstation standard screen completed; negative/diagnostic result. Learned regime/scale phase pending.**

Added after the 2026 literature review:

- image-neighbourhood SWAFED q maps;
- d-CF, d-CC, d-XC and d-Choquet families;
- larger restricted-dissimilarity set;
- Choquet-inspired aggregation;
- partition-conditioned Choquet-inspired aggregation;
- regularized pair-interaction / k-interaction surrogate;
- exact **regime-specific Shapley** learning;
- **scale-specific learned capacity banks**;
- second-stage none/hysteresis/geodesic/hysteresis+geodesic topology competition.

### First standard screen

Protocol:

- UDED: 15 selection / 15 held-out
- max side: 256 px
- 8 descriptors
- 3-fold inner-CV for selection ranking
- 31 threshold candidates
- 519 configurations
- 8 workers
- learned regime Shapley: **not enabled**
- learned scale-capacity bank: **not enabled**

The 519-config sweep completed in approximately **869.1 s (14.5 min)**.

#### Baseline Scharr

- selection CV F1: **0.76610**
- selection ODS: **0.76642**
- held-out precision: 0.66712
- held-out recall: 0.88846
- held-out F1: **0.76204**

#### Formally selected candidate

`v2_std__distprob_g055__global_local__conditional__g0.75__soft`

- distorted-probability capacity, gamma 0.55
- global/local hierarchy
- conditional fuzzy operators
- granularity 0.75
- adaptive localizer
- soft controller

Selection:

- CV F1: **0.71857**
- ODS: **0.71991**
- OIS: 0.76247
- AP: 0.71004
- R50: 0.92157

Frozen held-out:

- precision: **0.61117**
- recall: **0.85628**
- F1: **0.71325**
- delta F1 vs Scharr: **-0.04879**
- 95% paired-bootstrap CI: **[-0.10097, -0.00560]**
- P(delta > 0): **0.0122**

All 12 finalists selected by inner-CV were below Scharr on held-out data and their reported bootstrap confidence intervals remained below zero.

### Family signals

The standard contextual/hierarchical family produced the strongest CV candidate. Among alternative families, d-CF/d-CC/d-XC produced some higher **full-selection ODS** peaks (d-XC reached approximately 0.72472), but their inner-CV F1 was weaker, so these ODS-only peaks were correctly not promoted.

The initial family-level best CV F1 values were approximately:

| Family | Best CV F1 | Best selection ODS |
|---|---:|---:|
| standard contextual/hierarchical | **0.71857** | 0.71991 |
| d-CF | 0.71536 | 0.72232 |
| d-CC | 0.71176 | 0.72372 |
| partition-conditioned | 0.70923 | 0.71919 |
| Choquet-inspired | 0.70786 | 0.72066 |
| d-XC | 0.70754 | **0.72472** |
| regularized-pair | 0.70609 | 0.71526 |
| SWAFED | 0.69593 | 0.69677 |

Granularity showed a useful tension: 0.75 produced the highest ODS peaks, while 0.50 had the best average CV across the grid. This supports the hypothesis that scale preference should be context/regime dependent rather than globally fixed.

### Visual diagnosis

The contact sheet shows that MFI attention and uncertainty are still strongly activated by texture/region structure rather than only by sparse semantic boundaries. The dynamic localizer also remains dense in textured backgrounds. Numerically this appears as a precision drop (0.611 vs 0.667 for Scharr) **and** a recall drop (0.856 vs 0.888), so threshold tuning alone is not an adequate explanation.

### Parallel profile

For eight profile configurations:

| Workers | Time (s) | Speedup |
|---:|---:|---:|
| 1 | 35.63 | 1.00x |
| 2 | 23.23 | 1.53x |
| 4 | 17.45 | 2.04x |
| 8 | 13.80 | **2.58x** |

Eight workers are currently a reasonable operating point, although parallel efficiency is already flattening.

### Consequence / next experiment

This result is stronger than a simple held-out generalization failure: Scharr already dominates the v2 candidates on selection inner-CV. Therefore **do not launch the wide sweep yet**.

Next sequence:

1. learn scale-specific capacity banks on selection only;
2. learn regime-specific Shapley on selection only;
3. rerun the standard screen with those candidates appended;
4. add explicit ablations to locate the bottleneck: fixed Scharr vs dynamic localizer, MFI gating vs controller, uncertainty on/off, hierarchy on/off;
5. only if the continuous score closes the gap, evaluate topology repair;
6. keep the wide grid blocked until a credible improvement trend appears.

Compact archived report: `results/uded/ch_mfi_v2_standard/STANDARD_SCREEN_REPORT.md`.

---

# Results that can and cannot be quoted later

## Safe as development motivation

- orientation-aware descriptors helped strongly on hard synthetic angles;
- Median3 was the best tested preconditioner in the Stage-4 synthetic benchmark;
- geodesic linking greatly improved synthetic continuity metrics;
- q=.1 is not uniquely optimal;
- UDED exposed a generalization gap between selection and held-out;
- direct MFI+Scharr fusion is not yet supported as superior to Scharr on UDED;
- the first unlearned CH-MFI-v2 screen is clearly below Scharr and therefore motivates learned regime/scale adaptation and stronger ablation rather than a blind wide sweep.

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
