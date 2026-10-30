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

### Stage 14l result

Stage 14l completed on the 15 UDED selection images under the preregistered
5x3 repeated leakage-free CV. Appending the fixed half-disc uniform-LBP
chi-square feature changed aggregate F1 from `0.759053` to `0.759362`
(`+0.000310`) and aggregate precision by `-0.000040`. Mean fold F1 changed by
`+0.000370`, but the candidate won only 6/15 folds and the feature met its
training-only eligibility rule in only 7/15 folds. The preregistration required
at least `+0.001` aggregate F1, 9/15 wins, and eligibility in 12/15 folds, so
the conjunction promotion rule failed.

The compact five-feature positive controller remains incumbent. The small
positive aggregate change is descriptive only and does not authorize tuning
the LBP code, half-disc radius/orientations, eligibility rule, or fusion. The
deterministic `best_method_preview.png` shows conditioned input, ground truth,
incumbent, candidate, and retained best for the first validation image of the
first split; it was documentary only. The next registered action is the
repeatable high-reasoning live-literature escalation, which must choose a
mechanistically distinct development-only falsification without held-out or
external-test feedback.

## Stage 14m — linear probability-of-boundary cue-fusion checkpoint

The post-texture live-literature checkpoint compared three mechanistically
distinct non-neural directions: (1) fold-fitted linear probability-of-boundary
fusion of the retained localizer and compact memberships, (2) spectral
globalization of local contours, and (3) a structured random forest that
predicts local edge masks. Arbeláez et al. (2011, DOI
`10.1109/TPAMI.2010.161`) and Dollár and Zitnick (2015, DOI
`10.1109/TPAMI.2014.2377715`) establish the latter two as credible classical
families, but each is a substantially larger representation and inference
change. The first direction directly follows unresolved repository evidence:
Stage 11b's linear diagnostic generalized, while subsequent analytical context
variants have not established that the available information is being
calibrated optimally as a detector.

Martin, Fowlkes and Malik (2004, DOI `10.1109/TPAMI.2004.1273918`) frame local
boundary detection as supervised posterior estimation from local cues and
report that a simple linear logistic model was adequate for cue combination.
Stage 14m transfers only that methodological principle. It is not a
reproduction of Pb and imports no external model or target-test feedback.

Stage 14m is preregistered on UDED selection only under the established 5x3
repeated leakage-free CV. The control remains the five-feature compact
distorted-Choquet gate. The candidate fits a class-balanced L2 logistic model
inside each outer training fold from Scharr+NMS, compact Choquet context, their
product, and the five retained membership maps; its predictions are restricted
to Scharr+NMS support. Regularization, samples, interactions, and classifier
family are fixed before scoring, with no sweep. Independent fold-trained
thresholds are frozen on the paired validation fold. The authoritative
protocol and conjunction promotion rule are in
`docs/paper/STAGE14M_PREREGISTRATION.md`.

The deterministic `best_method_preview.png` must use the first validation
image of the first split and show conditioned input, GT, compact incumbent,
linear-logistic candidate, and retained best. It is documentary only. The
2026-10-06 SOTA ledger remains current; this mechanism search found no new
verified matched-protocol result requiring a target-row change.

Stage 14m completed without promotion. The compact incumbent achieved
aggregate F1 `0.759053` at precision `0.671339`; the linear fusion achieved
F1 `0.754080` at precision `0.676571`. Thus aggregate F1 changed by
`-0.004972`, aggregate precision by `+0.005232`, and mean fold F1 by
`-0.006046`, with only 4/15 fold wins. All 15 optimizers converged, so the
failure is not attributable to incomplete fitting, but the candidate failed
three required performance criteria. The compact five-feature positive
controller remains incumbent. Per the preregistration, regularization,
sampling, interactions, and classifier variants must not be tuned from this
outcome. The deterministic preview contains conditioned input, ground truth,
incumbent, candidate, and retained best for the predeclared first validation
image and remains documentary only. The next action is the repeatable
high-reasoning live-literature escalation for a mechanistically distinct
development-only falsification.

## Stage 14n — shallow edge-forest localizer checkpoint

The post-linear-fusion live-literature checkpoint revisited the classical
learned-localizer branch that Stage 14m had deliberately deferred. The primary
sources were Dollár and Zitnick's Structured Forests (DOI
`10.1109/TPAMI.2014.2377715`) and Hallman and Fowlkes' Oriented Edge Forests
(DOI `10.1109/CVPR.2015.7298782`). They establish class-balanced randomized
forests over simple image channels as a credible non-neural boundary family,
with posterior averaging and explicit localization. The OEF paper also warns
that large nonparametric systems can be hard to diagnose, so the next test is
intentionally smaller than either published system.

Three distinct directions were considered: graph-spectral globalization, a
full structured-patch forest, and a shallow nonlinear forest over the retained
MFI signature. Spectral globalization was deferred because Stage 14i already
failed a topology/global-consistency intervention. A full structured forest
would simultaneously introduce patch labels, offsets, orientation classes,
sharpening, and compositing. Stage 14n therefore selects the smallest remaining
question after Stage 14m: whether stable nonlinear interactions and dense
scoring, rather than another descriptor or linear calibration, are missing.

Stage 14n is preregistered on UDED selection only under the established 5x3
leakage-free repeated CV. Its candidate is a fixed 48-tree, depth-8 randomized
binary forest over dense raw Scharr, Scharr+NMS, compact Choquet context, two
localizer-context products, and the five retained memberships. The forest is
fit inside each outer training fold with balanced sampling and fixed
regularization-by-depth/leaf-size, then its dense posterior is localized by
the existing grayscale gradient-direction NMS. This is an OEF/Structured-
Edges-inspired falsification, not a reproduction or a structured-mask claim.
The incumbent remains the compact Choquet gate, and each method receives an
independently fold-fitted threshold.

The authoritative parameters, conjunction promotion rule, and prohibition on
post-result forest tuning are in `docs/paper/STAGE14N_PREREGISTRATION.md`.
The runner must emit a deterministic `best_method_preview.png` with conditioned
input, GT, incumbent, shallow forest, and retained best for the first
validation image of the first split. The 2026-10-06 SOTA ledger remains
current; this checkpoint found no new matched-protocol frontier result that
changes its target rows.

Stage 14n completed without promotion. The compact incumbent achieved
aggregate F1 `0.759053` at precision `0.671339`; the shallow forest achieved
F1 `0.734127` at precision `0.632782`. Aggregate F1 therefore changed by
`-0.024925`, aggregate precision by `-0.038556`, and mean fold F1 by
`-0.025724`, with only 2/15 fold wins. All 15 forest models produced finite
predictions, and recall was nearly unchanged (`+0.000993`), so the failure is
specifically a large precision deficit rather than invalid fitting or a recall
collapse. The full preregistered conjunction failed. The compact five-feature
positive controller with grayscale Scharr+NMS remains incumbent; forest size,
depth, leaves, sampling, channels, and calibration must not be tuned from this
outcome. This bounded binary forest does not falsify full structured-patch
forests. The deterministic preview contains conditioned input, ground truth,
incumbent, candidate, and retained best for the predeclared first validation
image and remains documentary only. The next action is the repeatable
high-reasoning live-literature escalation for a mechanistically distinct
development-only falsification.

## Stage 14o — interval uncertainty and reliability-conditioned capacity checkpoint

The post-forest live-literature escalation selected the first priority in the
active mechanism agenda: explicit ignorance over the retained fuzzy context.
Primary-source verification confirmed that Marco-Detchart et al. (Expert
Systems 42(2):e13730, DOI `10.1111/exsy.13730`) adapt fuzzy measures from local
image evidence, while Bustince et al. (Fuzzy Sets and Systems 160(13), DOI
`10.1016/j.fss.2008.08.005`) construct interval-valued image memberships whose
width encodes neighborhood-derived uncertainty. These mechanisms address the
current trust-calibration bottleneck without introducing another learned
classifier or descriptor. Jacquey et al. (ICIP 2007, DOI
`10.1109/ICIP.2007.4379243`) independently support interpreting interval
gradient width as local response reliability under noise.

Stage 14o is preregistered as one fixed synthesis. Pixelwise standard
deviation across the five compact memberships is normalized by the outer-
training-fold 95th percentile. The resulting uncertainty defines symmetric
interval memberships, convexly interpolates the retained gamma-0.55 Choquet
capacity toward the additive capacity, and attenuates the powered interval-
envelope midpoint once by one minus envelope width. The compact bank, grayscale Scharr+NMS,
gate strength 2.0, floor 0.10, and threshold grid remain unchanged. There is
no uncertainty-width, quantile, gamma, or capacity sweep.

The primary natural-image axis remains 5x3 leakage-free repeated CV on UDED
selection. Unlike earlier Stage-14 runs, the new default-on official module
also evaluates the full-development-fitted frozen candidate on BSDS500
validation with the original MATLAB multi-annotator ODS/OIS/AP protocol.
Promotion is conjunctive: bounded UDED non-collapse plus BSDS-val ODS delta at
least `+0.002` and nonnegative OIS/AP deltas. A failed official attachment
pauses promotion for exporter/evaluator repair but does not authorize changing
the candidate. The authoritative protocol is
`docs/paper/STAGE14O_PREREGISTRATION.md`.

The runner must emit `best_method_preview.png` from the first validation image
of the first deterministic split, with conditioned input, GT, incumbent,
candidate, uncertainty field, and current retained incumbent pending the
required official decision. It also emits an
`official_eval_manifest.json` and a repository-local native-resolution BSDS
export mode that never reads BSDS ground truth. Protected UDED held-out,
BSDS500 test, and BIPEDv2 test remain excluded.

The same live frontier check found author-reported GED headline results above
some current target rows, but the granularity-conditioned output-selection
protocol and official code remain unresolved; an independent EasyControlEdge
reimplementation reports a lower GED number. The SOTA ledger records this as
an unresolved frontier rather than changing the matched target from an
incomparable headline.

### Stage 14o UDED result and pending official attachment

The leakage-free UDED-selection result rejects the fixed interval/capacity
candidate under every preregistered non-collapse criterion. Relative to the
compact incumbent, aggregate F1 changed by `-0.009801`, aggregate precision by
`-0.015321`, and mean fold F1 by `-0.007976`; the candidate won `0/15` folds.
Recall was essentially unchanged (`+0.000244`), so the interval-width penalty
primarily amplified the precision problem it was intended to solve. The
compact five-feature Choquet controller remains incumbent, and the interval
width, q95 normalization, capacity endpoints, gamma, and gate must not be
micro-tuned from this outcome.

The required official BSDS500-validation attachment initially failed before
any evaluation because `evaluation/bsds_official/export_incumbent.py`, launched
by absolute path, did not place the repository root on Python's import path and
could not import `benchmark_uded`. This is an evaluator plumbing defect, not a
scientific rerun condition. After that path was repaired, the first retry
exposed the equivalent absolute-path import assumption in the Stage-14o
candidate exporter before any candidate map was scored. The candidate runner
received the same explicit repository-root bootstrap, so the second retry
reached MATLAB. It then stopped in wrapper preflight because MATLAB reports an
existing MEX binary as `exist(..., 'file') == 3`, while the wrapper incorrectly
accepted only type 2. The MEX is present at the pinned source size; the wrapper
now accepts MATLAB file types 2 or 3. The third retry passed preflight and
reached the pinned Berkeley per-image evaluator, but MATLAB R2023a rejected its
chained `groundTruth{i}.Boundaries` syntax before scoring the first image. The
wrapper now creates a run-local compatibility mirror that makes the dynamic
ground-truth load explicit, assigns the cell element to an intermediate
variable, and otherwise preserves the pinned source;
the vendored file is not edited, and the transform aborts if the audited source
expressions are absent. The fourth retry reached the mirror but MATLAB R2023a
then rejected the pinned source's four-output `fileparts` call; the fourth
output is unused and modern MATLAB supports three. The audited run-local
transform now removes only that unused output, and a fifth attachment-only
retry is registered. Stage-14o CV, vendor sources, predictions, and frozen
exported methods remain unchanged. Although no BSDS result can rescue promotion
after the UDED conjunction failed, the attachment remains required documentary
development evidence.

The fifth retry completed native matching and the aggregation pass read all 100
incumbent result files, after which MATLAB terminated with Windows heap
corruption before writing its summary. This is still evaluator plumbing, not a
score or candidate result. A sixth attachment-only retry separates the native
`correspondPixels` lifecycle from pure-MATLAB aggregation by running those
unchanged phases in fresh MATLAB processes. Cached predictions, the audited
run-local compatibility transform, and pinned vendor sources remain unchanged.

ODS/OIS/AP remain required documentary development evidence before Stage 14o
is closed and work advances to the Ambrosio–Tortorelli phase-field family.

### Stage 14o official result and final decision

The sixth attachment-only retry completed the original Berkeley
BSDS500-validation evaluation for all 100 images. The incumbent obtained ODS
`0.54545`, OIS `0.57957`, and AP `0.53428`; the interval candidate obtained
ODS `0.54770`, OIS `0.58139`, and AP `0.53328`. The deltas were ODS `+0.00225`,
OIS `+0.00182`, and AP `-0.00100`. Although ODS and OIS improved, AP failed
the preregistered nonnegative requirement, and all four conjunctive UDED
conditions had already failed. Stage 14o is closed without promotion. This
mixed result suggests an operating-point shift rather than stable ranking
improvement and does not justify interval micro-tuning. Reference-detector
reproduction remains unverified, so these development metrics cannot support
a final SOTA claim.

### Stage 14p — MFI-coupled Ambrosio–Tortorelli preregistration

Stage 14p follows the mechanism agenda rather than tuning Stage 14o. It
restores the retained compact crisp Choquet context and inserts it as a weak
nonnegative prior in a fixed classical Ambrosio–Tortorelli phase-field energy.
The candidate map is NMS of the optimized diffuse discontinuity field along
the unchanged image-gradient orientation; the comparator remains compact
Choquet-gated grayscale Scharr+NMS.

One normalized configuration is frozen: alpha `1.0`, beta `0.10`, epsilon
`1.5` pixels, context coupling `0.005`, and 16 alternating iterations. UDED
uses 5x3 leakage-free repeated CV, with bank and threshold fitting inside
folds. BSDS500 validation uses the official MATLAB attachment and a
full-UDED-selection frozen exporter that never reads BSDS ground truth.
Promotion requires nonnegative UDED aggregate F1 and precision changes,
nonnegative mean fold-F1 change, at least 9/15 fold wins, BSDS ODS improvement
of at least `+0.002`, and nonnegative OIS/AP changes. The fixed preview is
documentary. The authoritative protocol is
`docs/paper/STAGE14P_PREREGISTRATION.md`.

### Stage 14p result and Stage 14q decision

Stage 14p failed its conjunctive promotion rule. On UDED selection repeated
CV, the phase field increased aggregate precision from `0.67248` to `0.72442`
but reduced recall from `0.88850` to `0.64983`, producing aggregate F1
`0.68510` versus `0.76555` (delta `-0.08044`). Mean fold F1 changed from
`0.76472` to `0.68229` (delta `-0.08243`), with `0/15` fold wins. On official BSDS500 validation,
ODS changed by `+0.00522`, while OIS changed by `-0.00286` and AP by
`-0.04888`. Thus the candidate failed the UDED F1 conditions and the required
nonnegative BSDS OIS/AP conditions. It is not promoted, and its fixed
coefficients must not be tuned from this outcome.

Stage 14q advances to the preregistered fallback family: a fixed small
anisotropic directional atom bank for multiscale singularity
localization. It changes only the localizer; the compact five-feature Choquet
context gate is retained. The bank has two normal scales, four fixed
orientations, and a fixed 2:1 tangent elongation. UDED 5x3 leakage-free CV and
official BSDS500-validation ODS/OIS/AP remain conjunctive development axes.
The deterministic preview and native-resolution exporter are mandatory. The
authoritative protocol is `docs/paper/STAGE14Q_PREREGISTRATION.md`.

### Stage 14q result

Stage 14q failed the UDED portion of its conjunctive promotion rule. The fixed
anisotropic localizer increased aggregate precision from `0.67248` to
`0.69227`, but reduced recall from `0.88850` to `0.78195`. Aggregate F1 fell
from `0.76555` to `0.73438` (delta `-0.03116`), mean fold F1 changed by
`-0.03135`, and the candidate won only `1/15` folds. This fixed bank is not
promoted and must not be tuned from the result; the outcome does not disprove
continuous shearlet edge theory.

The first required official BSDS500-validation attachment failed during
incumbent native matching after 10/100 images because MATLAB exited with
Windows heap corruption (`0xc0000374`). The attachment-only retry preserved
the manifest, cached frozen predictions, candidate, preview, pinned vendor
sources, and completed UDED result. It completed all 100 images. Relative to
the incumbent, the fixed anisotropic localizer changed official BSDS-val ODS
by `+0.00334`, OIS by `-0.00089`, and AP by `-0.01526`. Thus it passed only
the ODS-margin condition and failed the required nonnegative OIS/AP conditions,
in addition to its decisive UDED failure. Stage 14q is closed without
promotion. The result is a cross-dataset sharpening trade-off, not evidence
against continuous shearlet theory. The compact Choquet-gated grayscale
Scharr+NMS controller remains incumbent; the next action is a live-literature
checkpoint selecting one mechanistically distinct falsification without using
protected test feedback.

### Post-Stage-14q literature checkpoint and Stage 14r decision

The live primary-literature checkpoint selected orientation-lifted geometry
on `SE(2)` rather than tuning the failed singularity bank. Duits and Franken
(2010, DOI `10.1090/S0033-569X-10-01172-0`) establish linear left-invariant
contour enhancement in position-orientation space; Franken and Duits (2009,
DOI `10.1007/s11263-009-0213-5`) establish the crossing-preserving rationale;
and Zhang et al. (2016, DOI `10.4208/nmtma.2015.m1411`) document numerical
realizations of the linear process. This geometry is distinct from Stage 14i's
image-plane endpoint linking and Stages 14p-q's replacement localizers.

Stage 14r therefore retains the complete compact Choquet-gated Scharr score,
lifts it into 32 unoriented tangent bins, applies one fixed confidence-stopped
linear tangent/angular diffusion, projects by maximum, and applies the
unchanged gradient-normal NMS. UDED-selection 5x3 leakage-free CV and official
BSDS500-validation ODS/OIS/AP are conjunctive development axes. A
largest-component GT-coverage condition is included because the mechanism
specifically claims continuity. No diffusion, lift, projection, or fusion
sweep is permitted. The deterministic preview and frozen native-resolution
exporter are mandatory. The authoritative protocol is
`docs/paper/STAGE14R_PREREGISTRATION.md`.

### Stage 14r result — mixed cross-dataset signal, no promotion

Stage 14r failed its preregistered conjunctive promotion rule. On UDED
selection, the fixed SE(2) candidate changed aggregate F1 by `-0.002762`,
aggregate precision by `-0.006990`, and mean fold F1 by `-0.002026`, with only
`5/15` fold-F1 wins. Its claimed continuity endpoint also failed: mean paired
largest-component GT coverage changed by `-0.002008`, with only `4/15` fold
wins, versus required values of at least `+0.005` and `9/15`.

Official BSDS500-validation evaluation completed and was directionally
positive: ODS/OIS/AP changed by `+0.003807/+0.001687/+0.007795`. Those gains
satisfy the BSDS portion but cannot override the explicitly conjunctive UDED
and continuity failures. The compact Choquet-gated grayscale Scharr+NMS
controller remains incumbent. The result rejects this fixed hard-lift,
five-step diffusion, max-projection realization only; it does not reject
invertible orientation-score or SE(2) contour theory. No Stage-14r parameter
may be tuned from this outcome. The deterministic preview is
`results/local_dev/stage14r_se2_contour_enhancement/best_method_preview.png`,
with conditioned input, ground truth, incumbent prediction, candidate
prediction, soft projection, and retained incumbent; it is documentary only.
A live-literature checkpoint is next before selecting a distinct mechanism.

### Post-Stage-14r literature checkpoint and Stage 14s decision

The live primary-literature checkpoint moved to fractional-order localization
rather than tuning the failed SE(2) realization. Mathieu et al. (2003, DOI
`10.1016/S0165-1684(03)00194-4`) establish the noninteger
selectivity/noise-immunity trade-off; Zhang et al. (2020, DOI
`10.1016/j.dsp.2019.102639`) place fractional Gaussian derivatives in a
Canny-like NMS pipeline; and Belhadi et al. (2025, DOI
`10.5269/bspm.78430`) provide a recent non-neural fractional-gradient method.
No inspected external/test outcome was used. The SOTA ledger was reviewed but
not changed because this mechanism search did not reveal a newer verified
matched-protocol neural target than the 2026-10-06 refresh.

Stage 14s tests exactly one fixed half-order isotropic spectral Riesz gradient
as a replacement for Scharr+NMS. Median conditioning, the retained compact
five-feature context, distorted-Choquet gamma, gate strength/floor, outer-fold
fitting, and threshold fitting are unchanged. UDED-selection repeated CV and
official BSDS500-validation ODS/OIS/AP are conjunctive development axes. No
fractional-order or implementation sweep is permitted. The authoritative
protocol is `docs/paper/STAGE14S_PREREGISTRATION.md`; a deterministic preview
and frozen native-resolution exporter are required.

### Stage 14s result — BSDS benefit with decisive UDED failure, no promotion

Stage 14s failed its preregistered conjunctive promotion rule. On UDED
selection, the fixed half-order Riesz candidate changed aggregate F1 by
`-0.035994`, aggregate precision by `-0.022856`, and mean fold F1 by
`-0.035832`, with `0/15` fold-F1 wins. Thus every UDED non-collapse/stability
condition failed.

Official BSDS500-validation evaluation completed and was strongly positive
relative to the incumbent: ODS/OIS/AP changed by
`+0.011613/+0.005046/+0.018042`. These gains satisfy the BSDS portion but do
not override the predeclared conjunction. The compact Choquet-gated grayscale
Scharr+NMS controller remains incumbent. The result rejects this fixed
half-order spectral Riesz realization only; no fractional-order, padding,
normalization, orientation, or fusion tuning is authorized. The deterministic
preview is
`results/local_dev/stage14s_fractional_riesz_localizer/best_method_preview.png`,
with conditioned input, ground truth, incumbent prediction, candidate
prediction, fractional magnitude, and retained incumbent; it is documentary
only. The sharp UDED/BSDS discrepancy routes next to a live-literature and
mechanism checkpoint rather than directly choosing a nearby derivative.

### Post-Stage-14s literature checkpoint and Stage 14t decision

The live primary-literature checkpoint compared three non-neural trust
mechanisms: Dempster–Shafer explicit ignorance, component-tree persistence, and
a-contrario statistical meaningfulness. It selected the a-contrario direction
because it directly controls expected accidental detections under an
image-internal null, whereas a first Dempster–Shafer test would require more
arbitrary mass assignments and persistence alone lacks a false-alarm scale.

Desolneux, Moisan, and Morel (2001, DOI
`10.1023/A:1011290230196`) establish edge detection by the Helmholtz principle.
Tepper, Musé, and Almansa (2013, DOI
`10.1007/s10851-012-0411-6`) extend meaningful-boundary analysis to partially
salient level lines and combined gestalts. Stage 14t tests a much narrower,
clearly labeled connected-component surrogate: a fixed 8-bit upper-level
filtration of the retained compact Choquet-gated Scharr score, conservative
Bonferroni test count, two-pixel independent sampling, `epsilon=1`, and an NFA
reliability gate with the existing `0.10` floor. It does not replace Scharr,
link components, route by dataset, or reproduce the full level-line method.

UDED-selection 5×3 leakage-free CV and official BSDS500-validation ODS/OIS/AP
are conjunctive. No NFA, null, quantization, connectivity, sampling, floor, or
fusion sweep is permitted. The authoritative protocol is
`docs/paper/STAGE14T_PREREGISTRATION.md`; the runner includes a frozen native-
resolution exporter and deterministic preview. The SOTA ledger was reviewed
but not changed because this mechanism search found no newer verified matched-
protocol neural target than the 2026-10-06 refresh.

### Stage 14t result — rejected on UDED and official BSDS500 validation

Stage 14t failed every preregistered UDED condition. The fixed a-contrario
candidate changed aggregate F1 by `-0.017248`, aggregate precision by
`-0.020834`, and mean fold F1 by `-0.016024`, with only `1/15` fold-F1 wins.
The reliability attenuation reduced both precision and recall, so the fixed
connected-support NFA surrogate did not deliver the claimed trust benefit.

The deterministic preview was emitted at
`results/local_dev/stage14t_acontrario_meaningfulness/best_method_preview.png`
with conditioned input, ground truth, incumbent prediction, candidate
prediction, meaningfulness reliability, and retained incumbent; it remains
documentary only. The attachment-only retry completed on the frozen maps.
Relative to the incumbent, official BSDS500-validation ODS/OIS/AP changed by
`-0.012569/-0.017611/-0.028297`. Thus the candidate also failed every official
metric condition, and the preregistered conjunction rejects it on both
development axes. This closes Stage 14t without promotion. The compact
Choquet-gated grayscale Scharr+NMS controller remains incumbent; no NFA, null,
quantization, connectivity, sampling, floor, or fusion tuning is authorized.
Because another trust-calibration mechanism failed, the next action is a live
primary-literature/mechanism checkpoint rather than automatically advancing a
deferred family.

### Post-Stage-14t literature checkpoint and Stage 14u decision

The live primary-literature checkpoint compared explicit evidential ignorance,
threshold-filtration persistence, and uncertainty-controlled PDE conditioning.
It selected evidential ignorance because Stage 14t already showed that another
connected upper-level-set attenuation is poorly motivated, while earlier
conditioning screens and Stage 14h caution against immediately returning to a
smoother. The selected mechanism instead changes how the incumbent's existing
sources represent disagreement.

Seo, Sivakumar, and Kwon (2011, DOI
`10.5391/IJFIS.2011.11.1.019`) establish an edge-detection precedent for
Dempster-Shafer evidence. Yager (1987, DOI
`10.1016/0020-0255(87)90007-7`) motivates preserving conjunctive conflict as
ignorance rather than normalizing it away, and Smets and Kennes (1994, DOI
`10.1016/0004-3702(94)90026-4`) provide the pignistic decision transform.

Stage 14u therefore uses three non-overlapping sources: Scharr+NMS strength,
the four non-persistence compact memberships aggregated by the retained
gamma-0.55 Choquet capacity, and the scale-persistence membership. Each scalar
cue receives the fixed maximally ignorant binary mass assignment that preserves
its pignistic probability. Three-way conjunctive fusion assigns all conflict
to the universal hypothesis by Yager's rule; the pignistic edge probability
then enters the unchanged strength-2.0, floor-0.10 gate. No mass coefficient,
source weight, or conflict rule is fit or swept. The authoritative protocol is
`docs/paper/STAGE14U_PREREGISTRATION.md`; UDED-selection repeated CV and
official BSDS500 validation remain conjunctive, and the runner includes the
required frozen exporter and deterministic preview. The SOTA ledger was
reviewed but not changed because this mechanism checkpoint found no newer
verified matched-protocol neural target than the 2026-10-06 refresh.

### Stage 14u UDED result and pending official attachment

Stage 14u failed its preregistered UDED-selection gate. Relative to the compact
Choquet controller, aggregate F1 changed by `-0.002450`, aggregate precision by
`+0.000720`, and mean fold F1 by `-0.001708`; recall changed by `-0.007806`, and
the candidate won only `3/15` folds. Thus the small precision increase did not
offset the recall loss, and the candidate failed the aggregate-F1, mean-fold,
and fold-win requirements. This fixed three-source least-committed Yager
realization is not promoted, and its masses, source partition, conflict rule,
decision transform, gamma, and gate must not be tuned from this result.

The deterministic preview used the preregistered first validation image of the
first split with columns conditioned input, ground truth, incumbent prediction,
candidate prediction, fused ignorance, and fused conflict; it remains
documentary only. The required official BSDS500-validation attachment stopped
during incumbent native matching after 37/100 images with the known intermittent
Windows MATLAB heap-corruption exit (`0xc0000374`). This is an attachment failure,
not a scientific rerun condition. A frozen attachment-only retry is registered;
it preserves CV, predictions, candidate parameters, and vendored evaluator
sources. The compact controller remains incumbent regardless of the attachment
because the conjunctive UDED conditions already failed. After documentary
closure, the next scientific action is a live literature/mechanism checkpoint.

The first attachment-only retry again encountered the native Windows MATLAB
heap-corruption exit, this time after writing 12/100 incumbent per-image match
files. Because successful prefixes survive the fault, the evaluator plumbing
now checkpoints nonempty per-image Berkeley outputs and resumes the remaining
images in a fresh MATLAB process before running aggregation separately. A
second frozen attachment-only retry is registered. This changes neither the
matcher nor any scientific artifact and does not reopen Stage 14u's failed
UDED decision.

### Stage 15 transition and Stage 15a registration

After the Stage-14 sequence of bounded failures and mixed UDED/BSDS behavior,
the research mode is now reproduction, matched-protocol audit, and error
diagnosis before any new architecture. Live verification of the official
Berkeley benchmark description and the pinned BIDS mirror confirmed that the
local path should operate on soft boundary maps, sweep thresholds, and match
against every human annotation. The pinned checkout also contains a stronger
local reference than configuration inspection alone: five example PNG maps
with shipped aggregate boundary-evaluation outputs.

Stage 15a is therefore registered to reproduce that fixture within `1e-4` on
ODS/OIS/AP through the same Windows/MATLAB wrapper, audit all 100 BSDS500
validation image/GT pairs and evaluator source hashes, then attach official
validation ODS/OIS/AP for fixed full Canny, ungated repository Scharr+NMS, and
the unchanged compact incumbent. These values establish a measurement floor;
they cannot promote a method or tune a parameter. The deterministic preview
uses sorted validation positions 1, 50, and 100 with input, mean-annotator GT,
Canny, Scharr, and incumbent columns. The authoritative frozen protocol is
`docs/paper/STAGE15A_PREREGISTRATION.md`.

The first controller launch did not complete because the controller's system
Python lacked scikit-image. Inspection of the already generated frozen audit
artifacts also exposed a separate protocol issue: AP reproduced within the
registered `1e-4` bound, but ODS and OIS differed from the shipped five-image
table by `0.000171` and `0.000259`. This is not grounds to relax a
preregistered tolerance. Stage 15a remains open while an architecture-free
fixture diagnostic records exact table/source hashes and localizes the
Windows-MEX or evaluator-path drift. The full validation attachment and Stage
15b remain downstream of that fidelity decision.

The first fixture diagnostic confirmed that the discrepancy is systematic:
all three shipped aggregate tables differ from their local regenerations, with
maximum numeric deltas of `0.000287` (aggregate), `0.001068` (per-image), and
`0.000260` (per-threshold). The pinned evaluator and matcher hashes were
preserved, but those deltas alone do not distinguish a repository wrapper
defect from compiled-platform variation. A second fixture-only diagnostic is
therefore registered. It compares raw and aggregate results from the wrapper
against Piotr Dollár's independently written `edgesEvalImg`, which documents
BSDS compatibility, using the same pinned Windows MEX, then repeats that path
in a fresh MATLAB process. Exact agreement will rule out the compatibility
transform, aggregation, and process nondeterminism without relaxing the
registered tolerance or scoring BSDS500 validation.

The first launch of that path-equivalence diagnostic stopped before matching:
the pinned `edgesEvalImg` source depends on `getPrmDflt` from Piotr Dollár's
separate MATLAB toolbox, while only the pinned `edges` repository was on the
MATLAB path. No fixture result was produced. An attachment-only retry is
registered with a strict repository-local name/value parser covering the
explicit `out`, `thrs`, `maxDist`, and `thin` arguments. Vendored evaluator
code, matcher binaries, fixture inputs, aggregation, and the `1e-4` decision
tolerance remain unchanged; full validation scoring remains deferred.

The parser-repaired retry also stopped before matching, now because the local
diagnostic harness passed the fixture's RGB source photographs to
`edgesEvalImg` instead of the shipped single-channel PNG boundary predictions.
The resulting three-dimensional threshold map was rejected by `bwmorph`.
This is a harness input-selection defect, not evaluator evidence. A second
attachment-only retry is registered with the PNG prediction directory; it
does not alter the pinned evaluator, matcher, fixture artifacts, aggregation,
or tolerance, and still does not score BSDS500 validation.

The corrected path-equivalence retry completed, but it did not meet its exact
agreement condition. Wrapper-versus-`edgesEvalImg` aggregate-table differences
reached `0.000757`, and two fresh runs of the identical Piotr Dollar path
differed by as much as `0.000507`; raw integer match counts changed by up to
eight between paths and up to seven between repeats. Because the two evaluator
paths use the byte-identical pinned Windows matcher, repeat drift rules out a
simple wrapper-only explanation and demonstrates that this binary/path is not
deterministic enough to certify the `1e-4` fixture tolerance on this platform.

Stage 15a remains open. A fixture-only source-build diagnostic is registered:
compile `correspondPixels` from the exact pinned BSDS500 C++ sources into the
result directory with the selected MATLAB compiler and repeat the unchanged
fixture in fresh processes. No vendored file, tolerance, validation result, or
detector architecture is changed. Stage 15b remains deferred.

The first source-build launch stopped before producing a matcher because the
pinned Unix-era code includes POSIX timing headers unavailable to MSVC. This
is a compiler-portability failure, not fixture or detector evidence. An
attachment-only retry is registered with a repository-local compatibility
include layer for the missing timing declarations, legacy integer aliases,
MATLAB API rename, IEEE-754 layout, and legacy macros. A compile smoke test
completed with Microsoft Visual C++ 2022. The vendored source files remain
byte-unchanged, compatibility-header hashes are recorded, and the matcher
algorithm, fixture, `1e-4` tolerance, and deferred-validation policy are
unchanged.

The compatibility-layer retry successfully built the matcher but stopped
before fixture matching because the repository-local resolution assertion
compared MATLAB's backslash-form resolved path against the harness's
forward-slash-form matcher directory. This is a diagnostic-harness defect and
provides no fixture, evaluator, or detector feedback. A second attachment-only
retry is registered after separator normalization in that assertion. The
rebuilt source, vendored bytes, matching logic, fixture, tolerance, validation
policy, and architecture remain unchanged.

The separator-normalized retry again stopped before matching. Its fixture-only
harness called the pinned `evaluation_bdry_image.m` without applying the
repository's audited MATLAB R2023a syntax mirror, so MATLAB rejected the legacy
`groundTruth{i}.Boundaries` expression at parse time. This is a harness
compatibility omission and supplies no fixture or detector evidence. A third
attachment-only retry is registered with the same syntax-only run-local
transform used by the official repository wrapper. Vendored bytes, rebuilt
matcher logic, fixture inputs, tolerance, validation deferral, and architecture
remain unchanged.

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

### Stage 15a source rebuild result and clock-seed diagnostic

The syntax-repaired source-build retry completed and rejected the hoped-for
platform repair. The exact pinned source rebuilt with MSVC still varied across
fresh processes: maximum repeat deltas were `0.000104` for `eval_bdry.txt`,
`0.000433` for `eval_bdry_img.txt`, and `0.000180` for
`eval_bdry_thr.txt`. Differences from the shipped tables reached `0.001083`.
Thus neither the shipped binary nor a source-pinned Windows rebuild can certify
the registered `1e-4` fixture requirement.

Source inspection supplies a bounded causal hypothesis: the pinned matcher
constructs its global random stream with `reseed(0)`, which seeds from the
clock, and `kofn.cc` consumes that stream for randomized sampling. One final
fixture-only diagnostic is registered with a predeclared seed of `1` in a
run-local source copy. It tests exact fresh-process repeatability only; the
controlled binary cannot score a dataset, the shipped target is not tuned to,
and the Stage-15a tolerance remains unchanged. Exact repetition will close
Stage 15a as a failed reference certification rather than convert the control
into an official evaluator.

### Stage 15a closure — clock-seeded matcher sampling confirmed

The preregistered fixed-seed causal diagnostic completed successfully. With
the pinned matcher sources copied into the result directory and only the
global default seed changed from the clock request `reseed(0)` to fixed seed
`1`, two fresh MATLAB processes produced identical `eval_bdry.txt`,
`eval_bdry_img.txt`, and `eval_bdry_thr.txt` tables. Every repeat maximum
absolute delta was exactly zero and the paired table hashes were identical.
This isolates clock-seeded randomized sampling in `kofn.cc` as the cause of
the fresh-process fixture drift observed with the unmodified matcher.

The control does not reproduce the shipped reference: maximum table
differences were `0.000287`, `0.000866`, and `0.000344`, respectively. Per the
registered rule, Stage 15a therefore closes **without** reference reproduction
verification. The fixed-seed binary is a diagnostic artifact only and may not
score any dataset; official Windows-path results remain stochastic and
uncertified for final claims. No detector prediction, BSDS validation image,
protected split, or MFI architecture was involved in this diagnostic.

The next registered action is a high-reasoning/live-literature Stage-15b
checkpoint for the exact or explicitly fidelity-labeled reproduction of SED.
It must resolve author code, published parameters, training classification,
and evaluation conventions before registering a detector run.

### Stage 15b literature/provenance checkpoint — exact SED run registered

The checkpoint verified the primary IJCV paper and the authors' public
`BoundaryDetection` repository. The method is strictly untrained: its
physiological parameters are fixed across datasets and it uses no supervised
large-dataset fitting. The paper reports colour BSDS500-test ODS/OIS/AP
`0.71/0.74/0.74`; those literature values remain separate from our development
validation score.

The official repository is pinned at commit
`11514b80162e5cd93fd244515189649656105a14`. It states that the manuscript
F-measures were generated by the MATLAB implementation and that the C++ path
was used only for timing. The unmodified MATLAB full-model entry point passed
a one-image MATLAB R2023a compatibility smoke test with a finite native-size
response spanning `[0,1]`. All reachable author MATLAB files are
hash-registered. No explicit repository license was found, so the source will
remain an ignored local dependency and will not be redistributed.

`stage15b_sed_exact_reproduction` is registered as an exact author-code
BSDS500-validation reproduction, not a surrogate or MFI candidate. Only batch
I/O and direct 8-bit serialization are supplied by the repository. It will
emit per-image maps, runtimes and hashes, a fixed-position preview, and the
default official attachment against the unchanged incumbent. Stage 15a's
evaluator caveat remains explicit: the unmodified Windows matcher is
stochastic and reference-uncertified, and the fixed-seed diagnostic binary is
forbidden for dataset scoring. No MFI architecture work or SED tuning is
authorized from this stage.

The first exact-run launch stopped before SED execution because Git rejected
the ignored author checkout as dubious ownership: it had been materialized by
the sandbox account and was read by the interactive account. This is a harness
failure and supplies no detector or evaluator evidence. A repository-local
repair now passes a process-scoped `safe.directory` value only to Git commands
against that immutable, hash-verified checkout; it does not change global Git
configuration or author bytes. `stage15b_sed_exact_reproduction_retry1` is
registered with the detector, parameters, split, serialization, fixed preview,
and official protocol unchanged.

### Stage 15b exact SED reproduction — matched validation baseline established

The harness-only retry completed the pinned, unmodified author MATLAB full
model on all 100 native-resolution BSDS500 validation images. Under the common
repository official path, SED obtained ODS/OIS/AP
`0.678546/0.709152/0.712814`, compared with
`0.545424/0.579337/0.534296` for the unchanged compact MFI incumbent. The
corresponding deltas were `+0.133122/+0.129816/+0.178518`. Mean detector runtime
was `3.419` seconds per image (`341.876` seconds total; MATLAB export only).

This is a matched development reproduction, not an MFI promotion or a final
SOTA claim. SED remains classified as strictly untrained with fixed author
parameters, and its published BSDS500-test values remain documentary and
separate. The deterministic positions 1/50/100 preview is at
`results/local_dev/stage15b_sed_exact_reproduction/best_method_preview.png`
with panels input / mean annotation display / MFI incumbent / exact SED. The
Windows matcher remains stochastic and reference-uncertified, so these local
metrics can support Stage-15 diagnosis but cannot certify a final claim.

Stage 15b closes with SED retained as the first verified exact-code non-trained
reference baseline. No SED tuning or MFI architecture change is authorized.
The next registered action is `stage15c_vcm_reproduction_checkpoint`, a live
primary-literature and provenance audit of Lu et al.'s vector co-occurrence
morphological colour-edge detector before any implementation or scoring.

### Stage 15c literature/provenance checkpoint - fidelity preflight registered

The open-access primary paper confirms a strictly untrained HSV/HDHSV vector
morphology method with 8-level quantization, co-occurrence-weighted local
support, and adaptive dilation/erosion structuring elements. Table 5 reports
BSDS500 boundary ODS/OIS/AP `0.76/0.79/0.77`; these values remain documentary.
The paper does not bind the scored split or specify the matcher version,
distance tolerance, thinning, threshold grid, annotation treatment, or output
map convention, so metric compatibility with the repository's Berkeley path
is unverified.

No official author code or implementation supplement was located through the
publisher, DOI record, indexed web search, or GitHub search. The paper also
omits output-affecting fixed details including the local window R, spatial and
range scales, sigma terms, d/T/S/J values, hue reference, HSV coordinate
construction, padding/tie rules, vector-to-scalar map conversion, the selected
gradient variant, normalization, and postprocessing. Choosing these values
would create a repository-specific surrogate rather than reproduce the
published detector.

The single next action is therefore `stage15c_vcm_fidelity_preflight`, a
deterministic dataset-free implementation-contract audit. It generates no edge
maps and requires no official-evaluation manifest or qualitative preview. Its
registered rule forbids a detector run unless fixed primary evidence resolves
all output-affecting blockers without validation-driven choices; otherwise
Stage 15c closes as fidelity-unresolved and the campaign proceeds to the
Stage-15d Edge Drawing/EDPF checkpoint. No MFI architecture changes are made.

### Stage 15c fidelity preflight - closed unresolved; Stage 15d checkpoint registered

The deterministic preflight read no dataset and executed no detector. It
confirmed that the public VCM material does not provide author code,
supplementary implementation, or enough fixed output-affecting details to
support either an exact reproduction or a faithful reimplementation. The
unresolved contract includes the local window and kernel scales, sigma and
selection constants, HSV coordinate and hue-reference conventions,
morphological boundary rules, gradient variant, scalar-map conversion,
postprocessing, scored BSDS split, and matcher. The paper's reported
ODS/OIS/AP `0.76/0.79/0.77` therefore remain documentary and
protocol-unverified. No parameter-invented surrogate was run, and MFI is
unchanged.

Stage 15c closes as fidelity-unresolved. The next registered action is
`stage15d_ed_edpf_reproduction_checkpoint`, a high-reasoning live-primary-
literature and official-code audit of Edge Drawing and EDPF. It must separate
chain construction from EDPF's chain-level Helmholtz false-detection control,
resolve the immutable author-code lineage, fixed parameters, build and output
contract, training class, and matched-validation plan before registering one
fidelity-labeled run. Stage 14t remains only a connected-component surrogate
and does not count as an EDPF test. Architecture invention remains forbidden
through Stage 15o.

### Stage 15d literature/provenance checkpoint - exact-source build preflight registered

Live primary-source review verified the official ED_Lib repository and pinned
commit `69b8d081bd6d28192d816ec0ed02aff9186d73c1` under its MIT license. The
selected grayscale `EDPF(src)` path is strictly untrained and user-parameter-
free, while the author implementation itself is fixed: Prewitt ED with gradient
threshold 11 and anchor threshold 3, followed by chain-level Helmholtz
validation with embedded `divForTestSegment=2.25` and `EPSILON=1.0`. Its native
scalar output is the binary `CV_8UC1` edge image returned by `getEdgeImage()`.
This supports an exact-code reproduction, not a repository surrogate.

Metric compatibility is bounded but usable. The future candidate export must
preserve the native binary 0/255 map without normalization or softening, and
the common official BSDS500-validation path may report ODS/OIS/AP. Because a
binary map provides only one nontrivial operating point, the resulting AP must
carry that limitation and cannot be interpreted as a soft-map ranking curve.
The local matcher also retains Stage 15a's stochastic/reference-uncertified
caveat. No BSDS or protected data were inspected at this checkpoint.

The workstation currently exposes Python OpenCV 5.0 without `ximgproc` and no
resolved C++ `OpenCV_DIR`, so a detector run is not yet registered. The single
next action is `stage15d_edpf_build_preflight`: clone and hash-verify the pinned
author source in ignored vendor storage, compile the unmodified sources through
an external repository-local harness, and run a deterministic synthetic binary-
output smoke test. Only a passing preflight may advance to one exact native-
resolution BSDS500-validation reproduction. Failure permits dependency/harness
repair only, not an algorithm substitution or EDPF tuning. Stage 14t remains a
different connected-component surrogate, and MFI architecture stays unchanged.

### Stage 15d build preflight - pinned OpenCV dependency repair registered

The dataset-free preflight verified the immutable ED_Lib checkout, source
hashes, and MIT license, but CMake stopped before compilation because no C++
OpenCV package configuration was installed (`OpenCV_DIR` was unset). No dataset
or detector benchmark ran, so this is dependency feedback only and does not
change the EDPF fidelity claim or MFI architecture.

The single next action is `stage15d_edpf_build_preflight_retry1`. It resolves
only the missing author-documented dependency by building OpenCV 3.4.20 from
upstream tag object `404ca455aeed9d26946e281b0383829bd0c533b1` with a minimal
core/imgproc configuration, then repeats the unchanged exact-source compile and
deterministic synthetic binary-output smoke test. It remains dataset-free and
may advance to validation only if the smoke test passes.

### Stage 15d dependency retry 1 - annotated-tag provenance repair registered

The retry stopped before OpenCV configuration because the harness compared
Git `HEAD` with the object ID of the annotated `3.4.20` tag. Git correctly
peeled tag object `404ca455aeed9d26946e281b0383829bd0c533b1` to release commit
`1eb1d4c3708f2bd95562cedd58d28461505c2d37`; the checkout was therefore the
registered release, and the failure was solely a provenance-assertion defect.
No dataset, detector, compiler, or benchmark ran.

`stage15d_edpf_build_preflight_retry2` is registered as an attachment-only
harness repair. It verifies both immutable Git object IDs separately and then
repeats the unchanged minimal OpenCV build and exact EDPF synthetic smoke test.
No dependency version, author source, detector parameter, data role, or MFI
architecture changes.

### Stage 15d dependency retry 2 - direct static config repair registered

Retry 2 verified both immutable OpenCV objects and successfully built and
installed the pinned OpenCV 3.4.20 `core`/`imgproc` static libraries. The EDPF
harness then stopped at CMake configuration because it selected OpenCV 3.4's
top-level Windows-pack dispatcher. That legacy dispatcher does not recognize
MSVC version 19.42 and therefore could not choose a runtime directory, although
the exact installed `staticlib/OpenCVConfig.cmake` package was present. No EDPF
source compiled, and no dataset or detector benchmark ran.

`stage15d_edpf_build_preflight_retry3` is registered as an attachment-only
config-selection repair. It selects the direct static package generated by the
same pinned build, bypassing only the obsolete runtime dispatcher, and repeats
the unchanged exact-source synthetic smoke test. Dependency/source versions,
detector parameters, dataset deferral, and MFI architecture remain unchanged.

### Stage 15d dependency retry 3 - stale unused-codec imports

Retry 3 correctly selected the installed static-package configuration, but
that OpenCV 3.4 export table also declared unused codec targets such as
`libjpeg-turbo` that were not built by the preregistered minimal
`core`/`imgproc` dependency build. CMake therefore stopped before compiling
EDPF. No dataset or detector benchmark ran, so this is only a build-harness
defect and supplies no scientific feedback.

`stage15d_edpf_build_preflight_retry4` is registered as an attachment-only
repair. The harness directly imports the exact installed `opencv_core3420`,
`opencv_imgproc3420`, and `zlib` artifacts and repeats the unchanged synthetic
smoke test. It does not alter author source, OpenCV version, EDPF parameters,
data roles, or MFI architecture.

### Stage 15d dependency retry 4 - irrelevant color source in grayscale build

Retry 4 successfully configured the direct imports and reached author-source
compilation. It then stopped because the external grayscale harness included
`EDColor.cpp`, whose unused diagnostic `imwrite` statement requires OpenCV's
imgcodecs declaration and library. The preregistered detector is the grayscale
`EDPF(Mat)` constructor, whose compiled implementation requires `ED.cpp` and
`EDPF.cpp`; the `EDPF(EDColor)` overload needs the class definition but does not
require linking the color detector implementation unless it is called. No
dataset, detector benchmark, or smoke executable ran, so this is build-harness
feedback only.

`stage15d_edpf_build_preflight_retry5` is registered as an attachment-only
source-surface repair. It compiles the unmodified pinned `ED.cpp` and
`EDPF.cpp`, retains the same pinned OpenCV `core`/`imgproc`/`zlib` artifacts,
and repeats the unchanged deterministic grayscale smoke test. It does not add
imgcodecs, modify author bytes or parameters, run BSDS, or change MFI.

### Stage 15d dependency retry 5 - link contract exposed

Retry 5 compiled the selected pinned author sources and reached final linking,
but did not produce the smoke executable. The repository harness used MSVC's
dynamic `/MD` runtime while the pinned static OpenCV build used `/MT`.
Separately, `ED.cpp` defines `ED(EDColor&)` in the same object file as the
selected grayscale constructor, so the linker requires the author `EDColor`
member definitions even though the grayscale smoke path never invokes that
overload. No dataset was read and no detector output or benchmark was produced.

`stage15d_edpf_build_preflight_retry6` is registered as an attachment-only
link-contract repair. It keeps the immutable author and OpenCV revisions,
matches the external harness to OpenCV's `/MT` runtime, builds pinned OpenCV
`core`/`imgproc`/`imgcodecs` plus generated dependencies, and compiles the
unmodified `ED.cpp`, `EDColor.cpp`, and `EDPF.cpp` translation units. The
synthetic grayscale smoke test and all EDPF parameters remain unchanged.
Validation and MFI architecture work remain deferred.

### Stage 15d dependency retry 6 - stale unused OpenCV exports

Retry 6 rebuilt and installed the pinned OpenCV libraries but stopped during
harness configuration. OpenCV 3.4's generated static export table validates
`libprotobuf` and `quirc` archives even though the registered minimal build did
not build any consuming modules and did not install those archives. The exact
required `core`, `imgproc`, `imgcodecs`, and codec artifacts are present. No
author source was compiled, no smoke executable ran, and no dataset was read.

`stage15d_edpf_build_preflight_retry7` is registered as an attachment-only
CMake import repair. It directly imports only the exact installed artifacts
required by the unchanged `ED.cpp`/`EDColor.cpp`/`EDPF.cpp` surface, retains
the `/MT` runtime and immutable source revisions, and repeats the unchanged
synthetic smoke test. Validation and MFI architecture work remain deferred.

### Stage 15d dependency preflight passed; exact reproduction registered

Retry 7 completed the preregistered source/build gate. The immutable ED_Lib
commit `69b8d081bd6d28192d816ec0ed02aff9186d73c1` compiled from unmodified
`ED.cpp`, `EDColor.cpp`, and `EDPF.cpp` against the pinned OpenCV 3.4.20 peeled
commit `1eb1d4c3708f2bd95562cedd58d28461505c2d37`. The fixed synthetic input was
processed twice and produced identical native `CV_8UC1` binary output with 122
edge pixels and range `0/255`. No dataset or benchmark was read, so this is
build-fidelity evidence rather than detector-performance evidence.

The single next action is `stage15d_edpf_exact_reproduction`. It runs the exact
grayscale author `EDPF(Mat)` path over all 100 native-resolution BSDS500
validation images, serializes the binary output unchanged, records per-image
runtime and map hashes, and emits `best_method_preview.png` from sorted
positions 1, 50, and 100 with panel order input / mean-GT display / incumbent /
exact EDPF. Its manifest attaches the default official evaluator against the
unchanged incumbent. Native binary output provides only one nontrivial
operating point, so AP will be reported with that limitation. The Stage-15a
stochastic/reference-uncertified matcher caveat remains. This is a reproduction
baseline and cannot tune EDPF or modify MFI.

### Stage 15d exact EDPF reproduction result

The exact hash-verified author implementation completed on all 100
native-resolution BSDS500 validation images. The executed path was the fixed
grayscale `EDPF(Mat)` constructor from ED_Lib commit
`69b8d081bd6d28192d816ec0ed02aff9186d73c1`, compiled without source changes
against pinned OpenCV 3.4.20. It is strictly untrained and emitted the native
binary `CV_8UC1` maps unchanged. Total detector time was `0.4847363` seconds,
or about `0.00485` seconds per image; batch export wall time was `0.8308333`
seconds.

Under the common local official BSDS500-validation path, EDPF obtained
ODS/OIS/AP `0.548048/0.548596/0.000000`. Relative to the unchanged compact
MFI controller (`0.545470/0.579328/0.534289`), the deltas were
`+0.002577/-0.030732/-0.534289`. The native detector has only one nontrivial
binary operating point, so AP is retained for protocol completeness but must
not be interpreted as a dense-ranking comparison. The local matcher remains
stochastic and reference-uncertified under the Stage-15a caveat, so this is
development reproduction evidence and not a final SOTA claim.

The deterministic qualitative panel is
`results/local_dev/stage15d_edpf_exact_reproduction/best_method_preview.png`
for sorted validation positions 1, 50, and 100. Its columns are input, mean
annotator boundary for display, retained MFI incumbent, and exact EDPF. All
100 maps, hashes, and per-image runtimes are preserved. EDPF is retained as an
exact chain-first, chain-level Helmholtz baseline; it is not promoted into MFI
and will not be tuned. Stage 14t remains a non-equivalent connected-component
surrogate.

The next action is `stage15e_co_sco_reproduction_checkpoint`, a high-reasoning
live-primary-source and official-code audit of Yang et al.'s CO/SCO contextual
color baselines. It must resolve provenance, license, fixed variants and
parameters, training class, output/evaluator conventions, and the matched
validation plan before exactly one fidelity-labeled action is registered. MFI
architecture invention remains prohibited through Stage 15o.

### Stage 15e CO/SCO checkpoint: exact paired reproduction registered

Live primary-source and official-code review resolved both author releases on
the UESTC project page. The institutional CO code-v1 and SCO code-v2 archives
are pinned respectively by SHA-256
`a8563d595d6db78698ece7c30ac0a31d8e7298e424e187cdcf84658c9a4bcb39`
and `01f928da7c9ecacfd3b0ebc0ce5a095fb561d2366745eee6e72e56234a6c9071`;
all reachable MATLAB sources have separate registered hashes. Both exact
native-size R2023a smoke tests returned finite soft maps in `[0,1]`.

The methods are not learned, but they are classified more precisely as
**parameter-fixed but author-tuned**: the 2015 paper selected sigma `1.1`, cone
weight `-0.7`, and SSC window `5` on the 200-image BSDS300 training set. The
registered `stage15e_co_sco_exact_reproduction` therefore runs the unmodified
CO and SCO author functions at that common published setting on all 100
BSDS500-validation images. This paired design isolates the published modified
spatial-sparseness constraint while preserving intrinsic author normalization
and NMS. It emits both map sets, per-image runtimes and hashes, a positions
1/50/100 five-column preview, and one common official-evaluation attachment.

The archives state research-purpose use but provide no open-source license, so
they remain ignored local dependencies and are not redistributed. Literature
BSDS300/500 test numbers remain documentary because archive-era evaluator
equivalence is not assumed. No CO/SCO tuning and no MFI architecture change are
authorized from the validation result; architecture invention remains deferred
through Stage 15o.

### Stage 15e exact CO/SCO reproduction result

Both hash-verified institutional author implementations completed on all 100
native-resolution BSDS500 validation images at the fixed published setting.
CO obtained local official-path ODS/OIS/AP
`0.635925/0.665489/0.651767`; SCO obtained
`0.656582/0.682564/0.694939`. Relative to the unchanged compact MFI
incumbent (`0.545462/0.579027/0.534288`), the CO deltas were
`+0.090463/+0.086462/+0.117478` and the SCO deltas were
`+0.111120/+0.103538/+0.160651`. The paired SCO-minus-CO changes were
`+0.020656/+0.017076/+0.043173`, providing matched reproduction evidence
that the published modified spatial-sparseness step adds material value to
this color-opponent baseline. This is mechanism decomposition, not permission
to integrate or tune SCO before the diagnostic program finishes.

Mean detector time was about `0.2522` seconds per image for CO and `0.3424`
seconds per image for SCO. All maps, hashes, runtimes, and the deterministic
positions 1/50/100 five-column preview are preserved. Both methods remain
parameter-fixed but author-tuned external references, not MFI components.
Their paper test metrics remain protocol-separated, and the Stage-15a local
matcher remains stochastic and reference-uncertified, so these validation
results do not support a final SOTA claim. The unchanged MFI controller remains
the incumbent.

The next action is `stage15f_compass_reproduction_checkpoint`, a
high-reasoning live-primary-source and code audit of Ruzon and Tomasi's Compass
distribution-gradient detector. It must resolve code availability, immutable
provenance, training class, all output-affecting half-disc/distribution
parameters, scalar-map conventions, and protocol compatibility before exactly
one fidelity-labeled action is registered. Stage 14l's failed fixed LBP context
feature is not treated as a Compass reproduction. Architecture invention
remains prohibited through Stage 15o.

### Stage 15f Compass checkpoint: exact-code build preflight registered

Live primary-source review recovered the complete official author MATLAB/C
archive from the Stanford Compass page. The archive is pinned by SHA-256
`43e2ab843af620f5b6405843be0c5478b6953039c36b1e32b2a3ac725ddce7ea`,
and all 26 contained files have separately registered hashes. The source
implements the published adaptive CIE-Lab color signatures, binary-split
vector quantization, bounded perceptual ground distance, EMD comparison of
oriented half-windows, and maximum-EMD strength. No explicit software license
was located, so the ignored local dependency will not be redistributed.

Compass is classified as strictly untrained. The fixed prospective path uses
the CVPR paper's full-image sigma `4` comparison (radius `12`) with author
defaults: spacing `1`, edge angle `180`, six wedges per quadrant (15-degree
sampling), and 10 clusters. The dense strength `S` in `[0,1]` is the future
scalar response; the author-trimmed radius border will be zero-padded to native
size and serialized directly to 8-bit without per-image normalization. The
papers did not report Berkeley ODS/OIS/AP, so their qualitative results remain
protocol-separated.

The registered next action is `stage15f_compass_build_preflight`. It downloads
and hash-verifies the archive, compiles only the unmodified author MEX surface
under R2023a, and runs a fixed synthetic RGB smoke test twice. This is needed
because the 2004 build predates the current MEX API and `compass.c` calls
`srand(clock())` before randomized clustering. The preflight records response
repeatability but may not fix the seed. No benchmark dataset, official
evaluation, or qualitative benchmark preview is involved. Only a passing
exact-source smoke test may advance to one fixed BSDS500-validation
reproduction; a harness failure permits harness-only repair, not author-code
editing, scale search, a surrogate, or MFI architecture work.

The first build preflight compiled the hash-verified author source under the
default R2018a MEX API, then failed at the first `compassmex` output allocation
with MATLAB's maximum-variable-size error. Inspection localized the failure to
the unchanged 2004 gateway's `int dims[3]` passed to `mxCreateNumericArray`:
the modern default ABI expects a 64-bit dimension vector and therefore reads a
spurious enormous extent. This is an external build-compatibility failure, not
Compass output or benchmark evidence; no dataset was read and no response map
was produced.

The single registered next action is
`stage15f_compass_build_preflight_retry1`. It rebuilds the same immutable
author bytes with MATLAB's documented compatible array-dimensions mode and
repeats the unchanged synthetic smoke/repeatability test. No source byte,
Compass parameter, RNG behavior, dataset role, or MFI architecture changes.

### Stage 15f Compass dependency preflight passed; exact reproduction registered

The compatible-array-dimensions retry passed the preregistered source/build
gate. The unchanged, hash-verified 2004 author MEX emitted a finite bounded
maximum-EMD response on the fixed synthetic RGB input (`41 x 57`, range
`0` to `0.9959797263`). The two calls in that process were identical, while
the source's `srand(clock())` behavior remains unchanged and is recorded as a
repeatability caveat rather than patched. No dataset or benchmark was read.

The single next action is `stage15f_compass_exact_reproduction`. It runs the
unmodified author detector at the preregistered sigma `4`, spacing `1`,
180-degree, six-wedge, ten-cluster setting over all 100 native-resolution
BSDS500 validation images. Author-valid centers are restored to native image
coordinates with a zero radius-12 border, then the response is serialized
directly to 8-bit without per-image normalization. The run retains maps,
runtimes, hashes, and the fixed positions 1/50/100 four-column preview, and
attaches the common official evaluator against the unchanged incumbent. This
is a reproduction baseline only; neither Compass nor MFI may be tuned from it.

### Stage 15f exact-run finalization failure and frozen-map retry

The exact Compass detector completed all 100 validation images and wrote all
100 native-resolution maps and ordered runtime rows. MATLAB printed the
registered completion marker, then exited during process teardown with Windows
heap corruption (`0xc0000374`). Because Python correctly treated the nonzero
exit as failure, hashes, provenance, preview, and the official-evaluation
manifest were not emitted; consequently no score was attached. This is an
environment/harness finalization failure after detector completion, not a
Compass result and not permission for a second randomized detector draw.

`stage15f_compass_exact_reproduction_retry1` is registered as an
attachment-only recovery. It validates and hashes the exact frozen maps and
runtime rows, emits the preregistered fixed preview and manifest, and invokes
only the unchanged evaluator. Compass parameters, RNG behavior, predictions,
dataset role, and MFI architecture remain unchanged.

### Stage 15f exact Compass reproduction result

The attachment-only recovery validated the exact 100 frozen maps and runtime
rows, wrote their hashes and provenance, emitted the deterministic sorted
positions 1/50/100 preview, and attached the unchanged official evaluator
without rerunning Compass. The exact author maximum-EMD response obtained
local official-path ODS/OIS/AP `0.630841/0.656565/0.518359`. Relative to the
unchanged compact MFI incumbent (`0.545423/0.579478/0.534295`), the deltas
were `+0.085418/+0.077086/-0.015936`. Thus Compass gives materially stronger
best-threshold and per-image-optimal F-measures but a lower full precision-
recall ranking area. This mixed profile is retained for later Stage-15
complementarity diagnosis and is not an MFI architecture decision.

The detector accumulated `978.256` seconds across 100 images, about `9.783`
seconds per image. Compass remains a strictly untrained exact-code baseline;
its clock-seeded author clustering was not modified or repeated for selection.
The fixed preview panel order is input, mean annotator boundary for display,
retained MFI incumbent, and exact Compass maximum-EMD strength. All validation
evidence remains subject to the Stage-15a stochastic/reference-uncertified
Windows matcher caveat and cannot support a final SOTA claim.

The next action is `stage15g_texture_surround_reproduction_checkpoint`, a
high-reasoning live-primary-literature and official-code audit of Yang, Peng
and Wu's 2025 texture-gradient plus surround-modulation method (DOI
`10.1007/s11760-025-04339-6`). It must resolve fidelity, immutable provenance,
fixed parameters, training class, output and evaluator conventions before one
fidelity-labeled run or preflight. Stage 14l and Compass do not substitute for
this method, and MFI architecture invention remains prohibited before Stage
15p.

### Stage 15g checkpoint: related sources do not establish executable fidelity

The live audit verified the target peer-reviewed article as a strictly
untrained analytic hierarchy, but found no article-specific author code or
supplement. A same-inventor Southwest Jiaotong University patent
(`CN115830051A/B`) describes the same square-root retinal encoding, oriented
Gaussian responses, three-part surround modulation, texture gradients,
endpoint cells, and channel fusion. The author's public BESD repository at
commit `eeb1f7eddcff0c998d8a96083f0579c7f1644b61` contains closely related
Python code.

Those sources are not interchangeable with the target article. The patent and
BESD code conflict on Gaussian and surround parameters, the patent leaves
several weights, texture scales, nonlinearities, and output conventions
unfixed, and BESD accompanies a different paper and adds segment construction
plus feedback. The paper reports BSDS500/MBDD while the patent reports a
separate BSDS/NYUDv2 evaluation, so their metrics also remain documentary and
protocol-separated.

The single registered next action is
`stage15g_texture_surround_fidelity_preflight`. It records the discrepancies in
a deterministic, dataset-free implementation contract. It may not score a
hybrid surrogate or read any benchmark. If article-specific primary material
does not resolve every output-affecting item, Stage 15g will close
fidelity-unresolved and advance to Stage 15h without changing MFI.

### Stage 15g closure: fidelity unresolved

The deterministic preflight confirmed that the public primary-source contract
is incomplete. No article-specific code or supplement was found, the related
patent is not proven equivalent, and the BESD repository implements a different
paper. Output-affecting conflicts remain in Gaussian and surround construction,
weights, texture scales, nonlinearities, endpoint modulation, fusion,
postprocessing, and evaluation protocol. No detector or dataset was run, and no
hybrid surrogate was scored. Stage 15g therefore closes fidelity-unresolved;
its reported and patent metrics remain documentary and protocol-unverified.

The single registered next action is
`stage15h_adaptive_surround_reproduction_checkpoint`, a high-reasoning live
primary-literature and official-code audit of Zhang et al.'s adaptive
multiscale V1 surround-modulation model. It must resolve executable fidelity,
fixed parameters, training class, output conventions, and metric compatibility
before one fidelity-labeled run or preflight. MFI remains unchanged, and no
architecture invention is authorized before Stage 15p.

### Stage 15h checkpoint: public contract is insufficient for a detector run

The live primary-source audit verified the target as a strictly untrained
analytic adaptive/multiscale surround detector, but found no article-specific
author code, supplement, or executable archive. The publisher record is
subscription-only. Its public abstract and figures establish contrast-dependent
suppression/facilitation, multiscale surround modulation, and four butterfly
orientations, but do not fix the complete receptive-field kernels, local
contrast statistic and adaptive transfer, scale schedule and fusion, scalar
output/postprocessing, or native map convention.

The paper's BSDS500 average optimal F-score `0.703` and NYUD follow-up remain
documentary: the public record does not resolve the scored split, per-image
versus dataset-wide optimization, matcher, tolerance, thinning, threshold grid,
annotation handling, or output convention. A same-group contrast-adaptive
predecessor (`10.1007/s11042-024-19666-y`) is not an implementation substitute;
it adds retinal color antagonism, LGN gain control, and LIF processing and is
not stated to be equivalent to the target.

The single registered next action is
`stage15h_adaptive_surround_fidelity_preflight`. It records each unresolved
output-affecting item in a deterministic dataset-free contract and may not run
a detector, read a benchmark, borrow parameters from the related predecessor,
or synthesize a surrogate. If the blockers remain, Stage 15h closes
fidelity-unresolved and advances to the Stage-15i fractional-reference
checkpoint without changing MFI.

### Stage 15h closure: fidelity unresolved

The deterministic preflight confirmed that public primary material does not
resolve the target article's executable contract. Article-specific code and a
supplement remain unavailable, while the complete receptive-field filters,
contrast statistic and adaptive transfer, multiscale/orientation fusion,
scalar output and postprocessing, and matched evaluation protocol remain
output-affecting blockers. The related same-group predecessor is not proven
equivalent and cannot supply those choices. No detector or dataset was run,
and no surrogate was scored. Stage 15h therefore closes fidelity-unresolved;
its reported metrics remain documentary and protocol-unverified.

The single registered next action is
`stage15i_fractional_reference_reproduction_checkpoint`, a high-reasoning
live-primary-literature and official-code audit of *Fractional Dirac Operators
for Edge Detection* (DOI `10.3390/fractalfract10060412`). It must resolve
executable fidelity, fixed parameters, training class, output conventions,
the exact reported evaluator, and the method's distinction from the failed
Stage-14s spectral Riesz realization before one fidelity-labeled run or
preflight. This is a reference audit, not permission to tune fractional
operators or alter MFI before Stage 15p.

### Stage 15i checkpoint: official QFrD code found; runtime preflight registered

The CC BY primary paper identifies the public author repository, now pinned at
its sole commit `8dcc8d846e6dcbe1bc4b931b89f1c814f5f9a245`. The proposed
detector is non-learned but is classified as parameter-fixed and author-tuned:
the paper selects fractional order `alpha=0.8` after comparing several orders
and reports BSDS500-test ODS checks supporting `theta=pi/2`; the symmetric
quaternion axis is fixed as `(0,1,1,1)/sqrt(3)`. The fixed author path also uses
64-pixel replicate padding, Gaussian sigma `2.0`, fixed-range response scaling,
bilinear NMS at radius `1.5`, and absolute hysteresis defaults `0.8/2.5`.

The paper's BSDS500-test QFrD ODS/OIS/AP `0.6145/0.6361/0.5996` remain
documentary. It names Piotr's Structured Edge Toolbox but not an immutable
evaluator commit or binary, and Stage 15a's local Windows matcher remains
stochastic and reference-uncertified. The code has no explicit license or
requirements file. A further fidelity caveat is recorded rather than silently
repaired: the manuscript describes left multiplication `M(alpha,theta)Q`, while
the pinned implementation computes `q_mul(Q, M_full)`. A later run can be an
exact author-code reproduction, but cannot claim independent algebraic
equivalence between paper and code.

This target is mechanistically different from Stage 14s: it processes native
RGB jointly in a quaternion QFT at order `0.8` with a Hilbert rotation, whereas
Stage 14s tested a grayscale half-order isotropic spectral Riesz-gradient
localizer. The present audit does not reopen fractional tuning.

The single registered next action is `stage15i_qfrd_runtime_preflight`. It will
hash-verify the immutable author checkout, record the paper/code caveat and
runtime dependencies, and attempt a fixed-default deterministic synthetic
smoke test only. The repository environment currently lacks PyTorch and
torchvision, so a failure permits a dependency-only retry; it may not read
BSDS, alter author bytes or parameters, or change MFI. Only a passing preflight
may register one exact native-resolution BSDS500-validation reproduction with
the required fixed positions 1/50/100 preview and common official evaluator.

### Stage 15i runtime preflight 1: checkout/runtime repair registered

The first dataset-free preflight stopped before source-contract verification
or synthetic execution. The harness cloned with `--no-checkout` and then
applied its cleanliness guard before populating the pinned tree, so Git
reported every tracked file as deleted. The dependency inventory separately
confirmed that PyTorch and torchvision were absent. No benchmark image was
read, no detector output was produced, and this failure supplies no fractional
or MFI performance evidence.

The single registered next action is
`stage15i_qfrd_runtime_preflight_retry1`. This attachment-only harness repair
uses a separate ignored checkout, populates the immutable commit before the
cleanliness audit, installs pinned CPU `torch==2.9.0` and
`torchvision==0.24.0`, and repeats the unchanged fixed synthetic smoke test.
It may not read BSDS, change author bytes or detector parameters, tune the
fractional family, or modify MFI. Only a pass may register the exact validation
reproduction.

### Stage 15i runtime preflight passed; exact reproduction registered

The repaired dataset-free preflight passed. The ignored author checkout is at
the pinned commit, its 59 tracked files reproduce the registered aggregate
manifest hash, all fixed source-contract checks passed, and pinned CPU
PyTorch/torchvision are available. Two executions on the fixed synthetic RGB
input were bitwise identical, finite, and native-size. No benchmark image or
ground truth was read, so this result contains no detector-performance
feedback.

The single registered next action is `stage15i_qfrd_exact_reproduction`. It
runs the unchanged author QFrD path at alpha `0.8`, full Hilbert rotation,
symmetric RGB quaternion axis, sigma `2.0`, 64-pixel replicate padding, and
the fixed author NMS/hysteresis defaults over all 100 native-resolution
BSDS500-validation images. It preserves direct-clipped soft maps, runtimes and
hashes, emits the preregistered positions 1/50/100 preview, and attaches the
unchanged official evaluator against the incumbent. This is a reproduction
baseline only; the paper/code multiplication-order caveat remains, and neither
fractional tuning nor MFI architecture work is authorized.

### Stage 15i exact QFrD reproduction complete; Stage 15j audit registered

The exact pinned-author-code QFrD reproduction completed for all 100
native-resolution BSDS500 validation images at the published fixed defaults.
The common local evaluator produced ODS/OIS/AP
`0.587261/0.618621/0.583650`, versus
`0.545412/0.579356/0.534277` for the unchanged compact MFI incumbent. The
paired deltas were therefore `+0.041849/+0.039265/+0.049373`. Mean detector
runtime was `1.168` seconds per image. The frozen maps, hashes, per-image
runtimes, and deterministic positions 1/50/100 preview are complete.

This establishes QFrD as a useful parameter-fixed but author-tuned fractional
reference under the common validation path; it does not establish paper/code
algebraic equivalence, promote QFrD into MFI, or reopen fractional tuning. The
Windows matcher remains stochastic and reference-uncertified, so these are
development/reproduction metrics rather than a final protocol-certified claim.

The single registered next action is
`stage15j_high_number_protocol_audit_checkpoint`. It uses live primary-source
research to determine whether unusually high reported non-trained F/F1 values
are Berkeley ODS or instead use average-optimal, per-image, multi-output, or
otherwise incompatible protocols. It may select at most one exact reproduction
or fidelity preflight, or close Stage 15j and advance to Stage 15k. It may not
score protected data, tune reproduced methods, or change MFI architecture.

### Stage 15j high-number protocol audit closed; Stage 15k registered

Live primary-source review found no additional non-trained detector with both a
high matched Berkeley result and a complete immutable implementation contract.
The 2026 multiscale-Gabor/directional-Sobel paper reports BSDS500 precision,
recall and F1 `0.913/0.865/0.888`, but defines neither ODS/OIS nor a Berkeley
matcher, tolerance, split, annotator aggregation, threshold scope or thinning
contract; its direct-pixel metric and empirically optimal settings are not a
Berkeley ODS result. BPAED likewise reports generic accuracy/F1/Pratt metrics
without a matched Berkeley contract or public implementation. As a useful
source-internal control, the FACAFCV paper reports noisy-image optimal F up to
`0.8910` separately from BSDS500 ODS/OIS/AP `0.589/0.608/0.533`.

Stage 15j therefore closes without another reproduction or any change to the
non-trained matched frontier. The single registered next action is
`stage15k_per_image_oracle_matrix`. It analyzes only already frozen MFI, SED,
EDPF, CO, SCO, Compass and QFrD validation maps and their existing official
per-image count tables. It will emit fixed-threshold and per-image-best
precision/recall/F1, pairwise win/loss tables, a descriptive ground-truth
method-oracle upper bound, and the fixed positions 1/50/100 qualitative panel.
No detector or matcher is rerun, no router is authorized, and MFI remains
unchanged through Stage 15o.

### Stage 15k per-image oracle diagnosis complete; Stage 15l registered

Stage 15k parsed the existing official per-image count tables for the seven
frozen methods without rerunning a detector or matcher. At each method's
nearest raw ODS threshold, exact SED was the best single method with aggregate
F1 `0.678500`. A ground-truth-informed per-image method oracle reached
`0.697054`, a descriptive gain of `+0.018554`; its 100 winners were SED 52,
SCO 18, CO 14, Compass 9, MFI 4, EDPF 3, and QFrD 0. Under per-image-best raw
thresholds, the analogous oracle gain over SED was `+0.015459`. These are
upper-bound diagnostics, not ODS/OIS results or a deployable router. The fixed
positions 1/50/100 preview is complete, and the Stage-15a matcher caveat
continues to apply.

The single registered next action is
`stage15l_image_regime_characterization`. It measures a fixed set of
image-internal texture, contrast, density, fragmentation, orientation,
curvature, scale, and annotation properties, then reports preregistered
Spearman and quartile associations with frozen-method F1 deltas. It may not
fit a router, select a threshold, rerun a detector/matcher, or change MFI.

### Stage 15l image-regime diagnosis complete; Stage 15m registered

Stage 15l completed over the 100 frozen BSDS500-validation outputs. Its
strongest globally corrected associations were structural: EDPF's delta over
MFI increased with incumbent fragmentation (`rho=0.451`, BH `q=0.000164`) and
edge density (`rho=0.382`, `q=0.00228`), and decreased with mean incumbent
component size (`rho=-0.451`). SED's advantage over MFI also increased with
incumbent fragmentation (`rho=0.325`, `q=0.0130`) and edge density
(`rho=0.318`, `q=0.0139`). These are descriptive associations over frozen
development outputs, not evidence for a deployable router or a feature choice.
The deterministic positions 1/50/100 preview is complete. No detector or
matcher was rerun; the Stage-15a evaluator caveat remains.

The single registered next action is
`stage15m_pixel_segment_complementarity`. At each method's already reported
ODS threshold it uses a fixed spatial-support contract to quantify unique
GT-supported response, shared unsupported response, weak-gradient recovery,
and connected-component continuity. The proximity analysis is explicitly not
Berkeley one-to-one matching. A required official attachment reuses frozen MFI
and SED maps only. No router, threshold selection, detector regeneration, or
MFI architecture change is authorized.

### Stage 15m pixel/segment complementarity complete; Stage 15n registered

Stage 15m completed the preregistered spatial diagnosis over all seven frozen
BSDS500-validation methods. Under the diagnostic proximity contract, exact SED
had `383,993` GT-supported and `182,413` unsupported pixels, versus `380,970`
and `353,416` for MFI. Its supported-pixel and supported-component fractions
were `0.678` and `0.607`, versus `0.519` and `0.430` for MFI, and its mean
supported component was larger (`8.71` versus `6.15` pixels). Relative to one
another, `35.6%` of MFI's supported pixels and `32.0%` of SED's were unique
outside the fixed two-pixel overlap radius. This establishes descriptive
spatial complementarity and stronger SED support/precision, but the counts are
not Berkeley one-to-one matches and cannot define a router or feature choice.
The deterministic positions 1/50/100 preview is complete.

The default-on official attachment failed while redundantly matching the
unchanged incumbent, after MATLAB reported the previously documented Windows
heap corruption. Because Stage 15m consumed frozen maps and does not make a new
ODS/OIS/AP claim, this attachment failure does not invalidate its diagnostic
outputs and is not retried.

The single registered next action is
`stage15n_uded_bsds_discrepancy_audit`. It compares fixed image-internal regime
distributions for UDED selection and BSDS500 validation and relates them to
the already frozen per-image Stage-14r SE(2) and Stage-14s Riesz deltas. UDED
deltas are averaged across the existing repeated-CV validation appearances;
BSDS deltas are reconstructed at the already reported raw ODS thresholds from
existing official count tables. No detector or matcher is rerun, no router is
fit, and MFI remains frozen through Stage 15o.

### Stage 15n UDED/BSDS discrepancy audit complete; Stage 15o registered

The frozen-result audit confirms that the Stage-14r/14s reversal accompanies
large dataset-regime differences rather than a uniform mechanism effect.
BSDS validation has far fewer GT components per megapixel than UDED selection
(standardized mean difference `-3.251`, BH `q=4.57e-12`) and much larger mean
GT components (`+1.080`, the same `q`). BSDS also has lower global intensity
variation, but higher mean gradient and texture-residual activity. Within
BSDS, Riesz delta increases with gradient mean (`rho=0.341`, BH `q=0.00840`),
gradient density (`rho=0.342`, `q=0.00840`), texture residual (`rho=0.319`,
`q=0.0131`), and gradient q90 (`rho=0.294`, `q=0.0242`); SE(2) shows weaker
positive gradient-density and mean-gradient associations. UDED contains only
15 images, so its within-dataset associations are underpowered and remain
descriptive. These findings do not authorize a dataset router or feature
choice.

The final registered diagnostic is
`stage15o_texture_evidence_decomposition`. It separates fixed analytic maps
for interior texture activity, cross-boundary texture contrast, local Scharr
strength, existing multiscale persistence, and a fixed high-gradient
component-support surrogate. Deterministic boundary and hard-interior samples
from UDED selection and BSDS validation feed image-blocked diagnostic logistic
models with fold-fitted scaling. The models are association probes, not
detectors or routers. Stage 15p is justified only if cross-boundary texture
contrast adds directionally consistent held-out AUC/AP on both development
datasets beyond gradient+persistence and beyond all other fixed cues. The
incumbent remains frozen through this decision.

The first Stage-15o launch stopped before reading either dataset because the
runner imported scikit-learn, which is not part of the repository environment.
No cue, sample, model, preview, or scientific result was produced. A single
harness-only dependency retry is registered after expressing the unchanged
fold-fitted standardization, class-balanced L2 logistic probe, ROC AUC, and
average precision contract with the repository-supported SciPy/NumPy stack.
The cue definitions, deterministic samples, folds, decision rule, dataset
roles, and architecture freeze are unchanged.

### Stage 15o texture-evidence decomposition complete; Stage 15p not justified

The dependency-repaired diagnostic completed on the preregistered deterministic
samples and image-blocked folds. On BSDS500 validation, cross-boundary texture
contrast was strongly incremental: relative to gradient plus persistence,
mean AUC/AP changed from `0.588330/0.577389` to
`0.653711/0.655504` (`+0.065381/+0.078115`), with both metrics positive in
`5/5` folds. Relative to the four-cue model without cross-boundary texture,
the all-five model changed AUC/AP from `0.587147/0.576627` to
`0.653283/0.654730` (`+0.066136/+0.078103`), again positive in `5/5` folds.

The UDED-selection result reversed. Relative to gradient plus persistence,
the cross-texture model changed AUC/AP from `0.814649/0.816702` to
`0.806495/0.805110` (`-0.008154/-0.011592`); relative to all cues except
cross-texture, the all-five model changed them from `0.820745/0.815340` to
`0.804159/0.800043` (`-0.016586/-0.015297`). Only `2/5` UDED folds were
positive in either contrast. The registered rule required directionally
consistent incremental AUC and AP on both datasets, so Stage 15p is not
authorized. This is evidence against integrating this fixed analytic cue, not
against all texture-distribution boundaries. The deterministic positions
1/50/100 cue preview is complete. The official attachment re-evaluated only
the unchanged incumbent (`0.545424/0.579469/0.534295` ODS/OIS/AP) and therefore
does not provide candidate evidence; the reference-reproduction caveat remains.

The single registered next action is
`stage16a_generation2_mechanism_checkpoint`. It is a live-primary-literature
synthesis of the complete Stage-15 evidence and must select exactly one
bounded, interpretable, non-neural generation-2 falsification with a
preregistered conjunctive UDED-selection and BSDS-validation rule. The compact
Choquet-gated grayscale Scharr+NMS controller remains incumbent meanwhile.

### Stage-16a checkpoint closure; Stage-16b fixed expert mean registered

The live primary-literature synthesis selected one fixed detector-level
combination rather than another isolated cue or localizer. Exact SED is the
strongest matched non-trained Stage-15 reference, its primary component
analysis attributes benefit to contour continuation and texture suppression,
and Stage 15m found substantial two-way unique GT-supported response between
SED and MFI (`32.0%` and `35.6%`). Kittler et al.'s primary classifier-
combination analysis supports the sum rule as a conservative robust fixed
combiner. This rationale does not imply calibrated posterior maps.

The registered next action is `stage16b_fixed_sed_mfi_fusion`. It tests only
the equal arithmetic mean `0.5*MFI + 0.5*SED`, after common 8-bit score
serialization, against both constituents. UDED selection uses 5x3 outer CV
with fold-fitted compact memberships and per-variant thresholds. Official
BSDS500 validation evaluates incumbent, frozen exact SED, and fusion under the
unchanged path. Promotion is conjunctive and requires the fusion to exceed
both constituents on UDED stability/F1 and the better constituent on all three
BSDS metrics, including at least `+0.002` ODS. No weight search, learned
router, dataset identity, Stage-15p texture cue, protected split, or
architecture promotion occurs at registration.

### Stage 16b fixed SED/MFI expert mean rejected; Stage 16c registered

Stage 16b completed with its deterministic fixed-position preview and official
BSDS500-validation attachment. On UDED selection, the equal mean reached
aggregate precision/recall/F1 `0.662510/0.895195/0.761474`, versus compact
MFI `0.669124/0.873332/0.757710` and exact SED
`0.631376/0.721516/0.673443`. Relative to compact MFI, aggregate F1 improved
by `+0.003764` and mean fold F1 by `+0.000781`, but precision changed by
`-0.006614` and the candidate won only `5/15` folds. It won all 15 folds and
improved aggregate F1 by `+0.088031` against SED. The UDED conjunction thus
failed its precision and MFI fold-win conditions.

Under the common official BSDS500-validation path, the fusion obtained
ODS/OIS/AP `0.629371/0.653496/0.645995`; exact SED obtained
`0.678549/0.708811/0.712810`. The fusion therefore trailed the better
constituent by `-0.049178/-0.055314/-0.066815`, failing all three BSDS
conditions, even though it exceeded the compact MFI incumbent by
`+0.083945/+0.074019/+0.111705`. The local matcher remains stochastic and
reference-uncertified, so these are development metrics rather than final
claim evidence.

The fixed mean is rejected and no architecture is promoted. This result is
evidence that fixed SED/MFI averaging can recover UDED recall and improve over
MFI on both datasets, but it does not provide a single combination that
dominates both heterogeneous constituents. The preregistration closes
outcome-driven searches over weights, normalizations, nonlinear means, routers,
and constituent parameters.

The single registered next action is
`stage16c_generation2_mechanism_checkpoint`, a high-reasoning live-primary-
literature escalation that must select one mechanistically distinct bounded
generation-2 falsification with a preregistered conjunctive UDED-selection and
BSDS500-validation rule. The compact Choquet-gated grayscale Scharr+NMS
controller remains incumbent.

### Stage 16c checkpoint closure; Stage 16d stable-region-boundary gate registered

The live primary-literature checkpoint selected one mid-level structural
mechanism rather than another detector average or localizer replacement.
Donoser, Riemenschneider, and Bischof (CVPR 2010, DOI
`10.1109/CVPR.2010.5539833`) analyze the shape stability of region boundaries
across levels of an inverted gradient component tree. Their fixed settings
are minimum region area `400`, level displacement `5`, maximum chamfer
distance `10`, and minimum retained fragment length `70`. Their evaluation is
not matched BSDS500 ODS/OIS/AP and no public exact node-selection code was
established, so Stage 16d is explicitly a repository-specific mechanism
surrogate rather than a reproduction claim.

The registered next action is `stage16d_stable_region_boundary_gate`. It
constructs a fixed stability-support map from the serialized compact-MFI
score's lower-level adjacent regions and applies that map through the retained
gate exponent `2.0` and floor `0.10`. This is distinct from Stage 14t's NFA on
upper-level edge-response components, Stage 14i endpoint linking, and Stage
16b detector averaging. UDED selection uses 5x3 leakage-free CV and BSDS500
validation uses the official attachment. Promotion requires all preregistered
UDED F1/precision/recall/stability conditions plus BSDS ODS/OIS/AP benefit.
No stability parameter, gate, serialization, or threshold-grid choice may be
tuned from the result; the incumbent remains unchanged pending the outcome.

### Stage 16d stable-region-boundary gate rejected; Stage 16e registered

Stage 16d completed its deterministic fixed-position preview and official
BSDS500-validation attachment, but failed its preregistered conjunctive rule.
On UDED selection, the candidate obtained aggregate precision/recall/F1
`0.661605/0.862135/0.748675`, versus `0.669124/0.873332/0.757710` for the
compact incumbent. Precision, recall, and F1 changed by `-0.007519`,
`-0.011196`, and `-0.009035`; mean fold F1 changed by `-0.008272`, and the
candidate won only
`4/15` folds. It therefore failed every registered UDED performance and
stability condition.

Under the common official BSDS500-validation path, the stable-region candidate
changed ODS/OIS/AP by `-0.000319/-0.000637/-0.001587`. Thus the candidate also
failed every BSDS benefit condition. The local matcher remains stochastic and
reference-uncertified, so these remain development metrics rather than final
claim evidence.

The fixed repository-specific component-tree surrogate is rejected and no
architecture is promoted. This bounded result does not falsify the published
region-boundary-stability method, but it closes outcome-driven tuning of the
surrogate's quantization, connectivity, region area, level displacement,
chamfer distance, fragment length, gate exponent, floor, and threshold grid.

The single registered next action is
`stage16e_generation2_mechanism_checkpoint`, a high-reasoning live-primary-
literature escalation that must select exactly one mechanistically distinct
bounded generation-2 falsification with a preregistered conjunctive UDED-
selection/BSDS500-validation rule. The compact Choquet-gated grayscale
Scharr+NMS controller remains incumbent.

### Stage 16e checkpoint closure; Stage 16f rolling-guidance conditioning registered

The live primary-literature checkpoint selected one fixed image-domain,
scale-aware conditioning test. Zhang, Shen, Xu, and Jia's *Rolling Guidance
Filter* (ECCV 2014, DOI `10.1007/978-3-319-10578-9_53`) explicitly separates
structure scale from edge magnitude: Gaussian-scale removal suppresses small
structures, then iterative joint guidance restores the sharpness of surviving
larger boundaries. The primary paper and official author project page also
demonstrate the mechanism before classical edge detection.

The registered next action is `stage16f_rolling_guidance_localizer`. It is an
equation-level repository reimplementation, not an exact author-code
reproduction. It fixes grayscale spatial sigma `3`, range sigma `0.1`, four
iterations, and three-sigma numerical support between the retained median
conditioning and unchanged Scharr+NMS localizer. The compact five-feature
Choquet context, gamma, gate, outer-fold fitting, and threshold fitting remain
unchanged. This tests whether scale-aware suppression addresses the incumbent's
documented unsupported/fragmented response without revisiting Stage 16d's
response gate, Stage 16b's fusion, or Stage 14h's gravitational parameters.

Promotion is conjunctive. UDED selection requires at least `+0.002` aggregate
F1, at least `+0.002` precision, recall no worse than `-0.01`, nonnegative mean
paired fold-F1, and at least `9/15` fold wins. The official BSDS500-validation
attachment must complete with ODS at least `+0.002` and nonnegative OIS/AP.
No rolling-guidance, conditioning-order, color, localizer, context, gate, or
threshold parameter may be tuned from the outcome. The compact controller
remains incumbent pending the result.

### Stage 16f rolling-guidance localizer rejected; Stage 16g registered

Stage 16f completed its fixed-position preview and official attachment but
failed the preregistered conjunctive rule. On UDED selection, rolling guidance
obtained aggregate precision/recall/F1 `0.623991/0.681130/0.651310`, versus
`0.662514/0.876181/0.754512` for compact MFI. The corresponding changes were
`-0.038523/-0.195051/-0.103203`; mean fold F1 changed by `-0.102773`, and the
candidate won `0/15` folds. It therefore failed every UDED requirement.

Under the common official BSDS500-validation path, the candidate improved
ODS/OIS/AP by `+0.035113/+0.028126/+0.009010`. These gains are development
evidence, but the rule required both datasets to pass and the local matcher
remains stochastic and reference-uncertified. The candidate is rejected, the
incumbent is unchanged, and no RGF, conditioning-order, color, localizer-
fusion, context, gate, or threshold parameter may be tuned from the outcome.
This bounded result does not falsify rolling-guidance filtering generally.

The single registered next action is
`stage16g_generation2_mechanism_checkpoint`, a high-reasoning live-primary-
literature escalation. It must select exactly one mechanistically distinct,
interpretable non-neural falsification and preregister a conjunctive UDED-
selection/BSDS500-validation rule. It must account for the repeated BSDS-
positive/UDED-negative localizer pattern without using dataset identity or
protected feedback.

### Stage 16g checkpoint closure; Stage 16h hysteresis persistence registered

The live primary-literature checkpoint selected a fixed connected-threshold
mechanism that preserves the incumbent localizer. Canny's original hysteresis
uses strong seeds to retain connected weak contour responses, and its Figure 7
demonstrates the fixed `T1`/`2*T1` relation used here. Salembier, Oliveras, and
Garrido's connected-operator theory provides the upper-level-component view
and the contour-support preservation rationale.

The registered next action is `stage16h_hysteresis_persistence_boost`. It
serializes the unchanged compact-MFI score to the common 8-bit lattice and,
over all 255 high levels, assigns each supported pixel the greatest high level
for which it is 8-connected through pixels above half that level to a strong
seed. The candidate is pointwise no smaller than the serialized incumbent and
has exactly the same nonzero support. Thus median conditioning, the compact
Choquet context, grayscale Scharr+NMS localization, and fold fitting are all
unchanged.

Stage 16h is a repository-specific soft hysteresis extension, not an exact
Canny or max-tree reproduction. It is distinct from Stage 14i endpoint
creation, Stage 14t NFA attenuation, Stage 16d region-shape stability, Stage
16f image conditioning, and Stage 16b expert averaging. Promotion is
conjunctive across UDED repeated CV and official BSDS500 validation, including
a registered UDED recall gain and asserted support/floor invariants. No
high/low ratio, connectivity, quantization, propagation, threshold, context,
or localizer parameter may be tuned from the outcome. The compact controller
remains incumbent pending the result.

### Stage 16h hysteresis persistence rejected; Stage 16i registered

Stage 16h completed its deterministic fixed-position preview and official
attachment but failed the preregistered conjunctive rule. On UDED selection,
the candidate obtained aggregate precision/recall/F1
`0.658916/0.870800/0.750184`, versus
`0.662514/0.876181/0.754512` for compact MFI. The corresponding deltas were
`-0.003598/-0.005380/-0.004328`; mean fold F1 changed by `-0.004378`, and the
candidate won only `3/15` folds. The pointwise-floor and exact-support
invariants held, so this is a mechanism failure rather than an invariant or
export failure.

Under the common official BSDS500-validation path, ODS/OIS/AP changed by
`-0.000783/+0.002205/-0.020691`. The isolated OIS gain cannot satisfy the
required joint rule because ODS and AP regressed and every UDED requirement
failed. The local matcher remains stochastic and reference-uncertified, so
these metrics are development evidence rather than final-claim evidence.

The fixed repository-specific soft hysteresis transform is rejected and no
architecture is promoted. This does not falsify classical Canny hysteresis or
connected filtering generally, but it closes outcome-driven tuning of the
ratio, connectivity, quantization, propagation, threshold grid, context,
gate, and localizer.

The single registered next action is
`stage16i_generation2_mechanism_checkpoint`, a high-reasoning live-primary-
literature escalation that must select exactly one mechanistically distinct,
interpretable non-neural falsification and preregister a conjunctive UDED-
selection/BSDS500-validation rule. The compact Choquet-gated grayscale
Scharr+NMS controller remains incumbent.

### Stage 16i checkpoint closure; Stage 16j step-profile context registered

The live primary-literature checkpoint selected one local profile-model test
that preserves the incumbent localizer. Nalwa and Binford's one-dimensional
surface-fitting formulation identifies a hyperbolic tangent as an adequate
step-edge basis and distinguishes discontinuities from smoother surface
explanations. Elder and Zucker establish that natural edges span varying blur
scales. Together they motivate a fixed multiscale profile-shape reliability
cue rather than another response-component operation or localizer replacement.

The registered next action is `stage16j_step_profile_context`. Along the
incumbent Scharr normal it samples seven fixed positions and measures the
normalized least-squares advantage of the best of three fixed centered tanh
step templates over a smooth linear template. Its training-fold-fitted
positive membership is appended to the retained five-feature distorted-
Choquet context only when it passes the pre-existing AUC eligibility rule.
Median conditioning, grayscale Scharr+NMS, gamma, gate, and fold-threshold
fitting remain unchanged.

Stage 16j is a repository-specific bounded surrogate, not an exact Nalwa-
Binford or Elder-Zucker reproduction. Promotion is conjunctive across UDED-
selection repeated CV and official BSDS500 validation, with a cue-eligibility
endpoint and deterministic fixed-position preview. No profile geometry,
template width, interpolation, calibration, Choquet, gate, localizer, or
threshold parameter may be tuned from the result. The compact controller
remains incumbent pending the outcome.

### Stage 16j step-profile context rejected; Stage 16k registered

Stage 16j completed its fixed positions 1/8/15 preview and official
attachment. On UDED selection, compact-plus-profile obtained aggregate
precision/recall/F1 `0.662442/0.880593/0.756096`, versus
`0.662514/0.876181/0.754512` for compact MFI. The deltas were
`-0.000072/+0.004412/+0.001584`; mean fold F1 improved by `+0.001563`, the
candidate won `12/15` folds, and the cue was eligible in `14/15` folds.
Although all other UDED conditions passed, the aggregate gain missed the
registered `+0.002` requirement.

Under the common official BSDS500-validation path, ODS/OIS/AP changed by
`-0.001980/-0.001964/+0.001585`. The AP gain does not compensate for the ODS
and OIS regressions because all conditions were required. The Windows matcher
remains stochastic and reference-uncertified, so these are development rather
than final-claim metrics.

The fixed repository-specific profile cue is rejected and the incumbent is
unchanged. The result shows that this cue was locally discriminative and
stable on UDED, but it does not establish jointly transferable incremental
context value. Its geometry, template widths, interpolation, eligibility,
calibration, Choquet context, gate, localizer, and thresholds are closed to
outcome-driven tuning. This does not falsify parametric edge modeling or local
scale control generally.

The single registered next action is
`stage16k_generation2_mechanism_checkpoint`, a high-reasoning live-primary-
literature escalation that must choose exactly one mechanistically distinct,
interpretable non-neural falsification with a preregistered joint UDED/BSDS
rule and no protected feedback.

### Stage 16k checkpoint closure; Stage 16l exact EDPF chain context registered

The live primary-literature checkpoint selected one chain-first structural
evidence test. Topal and Akinlar's Edge Drawing constructs contiguous,
one-pixel-wide chains directly from anchors, and Akinlar and Topal's EDPF runs
that detector at its fixed extreme settings before rejecting statistically
meaningless chain segments with the author Helmholtz/NFA test. The immutable
MIT-licensed author implementation at commit
`69b8d081bd6d28192d816ec0ed02aff9186d73c1` has already passed exact build,
synthetic repeatability, and BSDS-validation reproduction checks. Stage-15l
also found that EDPF's relative advantage increases with incumbent
fragmentation and edge density. This supplies a development-grounded reason to
test chain support without using dataset identity or the earlier binary EDPF
benchmark score as a fusion weight.

The authoritative preregistration is
`docs/paper/STAGE16L_PREREGISTRATION.md`. The registered next action is
`stage16l_edpf_chain_context`. It executes the
unchanged exact grayscale author EDPF on each image, expands its binary chain
map by exactly one 8-neighbourhood pixel to accommodate raster alignment with
Scharr NMS, and exposes that support as one positive membership. The
membership receives a weight only when it passes the existing `0.56`
training-AUC eligibility rule inside the outer UDED fold. The retained five
memberships, distorted-Choquet gamma `0.55`, gate strength `2.0`, floor `0.10`,
median conditioning, grayscale Scharr+NMS localization, and threshold fitting
remain unchanged.

This experiment is mechanistically distinct from Stage 14t's post-hoc
upper-level connected-component NFA, Stage 14i's endpoint linking, Stage 14r's
SE(2) diffusion, Stage 16d's region-boundary stability gate, and Stage 16h's
connected-threshold score persistence. It is also not a promotion of binary
EDPF as the detector. Promotion is conjunctive: UDED requires aggregate F1
delta at least `+0.002`, precision at least `-0.002`, recall at least `-0.003`,
nonnegative mean fold-F1 delta, at least `9/15` F1 wins, eligibility in at
least `12/15` folds, nonnegative mean largest-component GT-coverage delta, and
at least `8/15` coverage wins. The official BSDS500-validation attachment must
complete with ODS delta at least `+0.002` and nonnegative OIS/AP deltas. Fixed
positions 1/8/15 produce the mandatory preview. EDPF parameters, the one-pixel
alignment adapter, eligibility, integration, context, gate, localizer, and
threshold grid may not be tuned from the result. The compact controller
remains incumbent pending the outcome.

### Stage 16l exact EDPF chain context rejected; Stage 16m registered

Stage 16l completed exact-author source/hash checks, finite-map checks, its
fixed positions 1/8/15 preview, and the official attachment. The EDPF chain
cue was training-eligible in all `15/15` folds, but it did not add stable UDED
value. Relative to compact MFI, aggregate precision/recall/F1 changed by
`-0.000244/-0.000090/-0.000191`; mean fold F1 changed by `-0.000013`, and the
candidate won only `8/15` fold-F1 comparisons. Mean paired largest-component
GT coverage changed by `+0.000030`, but only `3/15` coverage comparisons were
wins. It therefore failed the aggregate-F1, mean-fold, fold-win, and coverage-
win conditions.

Under the common official BSDS500-validation path, ODS/OIS/AP improved by
`+0.013847/+0.005044/+0.014949`. Those substantial gains satisfy every BSDS
condition but cannot override the UDED failures because the rule was explicitly
conjunctive. The Windows matcher remains stochastic and reference-uncertified,
so these are development rather than final-claim metrics.

The fixed chain-support membership is rejected and the compact Choquet-gated
grayscale Scharr+NMS controller remains incumbent. This is evidence that exact
EDPF chain support is individually discriminative and useful on BSDS validation
but does not establish stable cross-dataset incremental context value in this
fixed integration. It does not falsify EDPF chain construction or chain-level
Helmholtz validation generally. Author parameters, the one-pixel alignment
dilation, eligibility, membership weighting, Choquet context, gate, localizer,
and thresholds are closed to result-driven tuning.

The single registered next action is
`stage16m_generation2_mechanism_checkpoint`, a high-reasoning live-primary-
literature escalation that must choose exactly one mechanistically distinct,
interpretable non-neural falsification with a preregistered joint UDED/BSDS
rule and no protected feedback.

### Stage 16m checkpoint closure; Stage 16n SUSAN context registered

The live primary-literature checkpoint selected one fixed local-self-
similarity test. Smith and Brady's SUSAN principle measures the size of the
neighbourhood whose brightness is similar to its nucleus, producing an initial
edge response without image derivatives. The official Oxford material fixes a
radius-3.4, 37-pixel circular mask, a smooth sixth-power brightness comparison,
and a geometric threshold at three quarters of the maximum USAN area; a
published edge example supplies the fixed 8-bit brightness threshold `20`.

The authoritative preregistration is
`docs/paper/STAGE16N_PREREGISTRATION.md`. The registered next action is
`stage16n_susan_context`. It computes the normalized initial USAN-area deficit
on the unchanged median-conditioned grayscale image and, only when eligible
inside an outer UDED training fold, appends it as one positive membership to
the compact distorted-Choquet context. It does not import SUSAN direction,
NMS, thinning, or linking and does not replace the Scharr+NMS localizer. This
centre-referenced self-similarity representation is distinct from failed
detector averaging, component/region support, conditioning, connected-
threshold persistence, normal-profile fitting, half-disc texture contrast,
and exact EDPF chain support.

Promotion is conjunctive. UDED selection requires aggregate F1 delta at least
`+0.002`, precision at least `-0.002`, recall at least `-0.003`, nonnegative
mean fold-F1 delta, at least `9/15` fold wins, and eligibility in at least
`12/15` folds. The official BSDS500-validation attachment must complete with
ODS delta at least `+0.002` and nonnegative OIS/AP deltas. Fixed positions
1/8/15 provide the required preview. Mask geometry, brightness threshold,
similarity exponent, geometric threshold, boundary handling, calibration,
context, gate, localizer, and threshold grid are frozen before results. The
compact controller remains incumbent pending the outcome.

### Stage 16n SUSAN context rejected; Stage 16o registered

Stage 16n completed the fixed positions 1/8/15 preview, finite/bounded checks,
and official attachment. The SUSAN cue was training-eligible in all `15/15`
folds. Relative to compact MFI on UDED selection, aggregate
precision/recall/F1 changed by `-0.000463/+0.001628/+0.000302`; mean fold F1
changed by `+0.000185`, and the candidate won only `7/15` fold comparisons.
It therefore failed the preregistered `+0.002` aggregate-F1 margin and `9/15`
fold-win conditions, while passing the precision, recall, mean-fold, and
eligibility conditions.

Under the common official BSDS500-validation path, ODS/OIS/AP improved by
`+0.004674/+0.002200/+0.006049`, satisfying every BSDS condition. Those gains
cannot override the UDED failures because the rule was explicitly conjunctive.
The Windows matcher remains stochastic and reference-uncertified, so these are
development rather than final-claim metrics.

The fixed initial-response membership is rejected and the compact
Choquet-gated grayscale Scharr+NMS controller remains incumbent. This result
shows that the fixed centre-referenced USAN deficit is individually
discriminative and mildly beneficial, including on BSDS validation, but does
not establish stable cross-dataset incremental value in the retained context.
It does not falsify the full SUSAN detector. Its parameters and integration
are closed to result-driven tuning.

The single registered next action is
`stage16o_generation2_mechanism_checkpoint`, a high-reasoning live-primary-
literature escalation that must choose exactly one mechanistically distinct,
interpretable non-neural falsification with a preregistered joint UDED/BSDS
rule and no protected feedback.

### Stage 16o checkpoint closure; Stage 16p empirical-copula context registered

The live checkpoint first rejected local structure-tensor coherence as the
next mechanism because coherence and cross-scale orientation consistency are
already represented in the historical feature bank; relabeling them would not
be a distinct falsification. The checkpoint instead targets the recurring
calibration pattern itself. Several fixed Stage-16 additions were individually
eligible and improved BSDS validation but failed to add stable UDED value,
which is consistent with image/dataset-dependent membership marginals
distorting a fixed nonlinear aggregation even when spatial cue ordering remains
useful.

Zabih and Woodfill's ECCV 1994 non-parametric rank transform (DOI
`10.1007/BFb0028345`) establishes relative ordering as a robust alternative to
raw photometric values. Empirical-copula work separately motivates mapping
variables through their marginal CDFs to isolate dependence from marginal
shift. These sources motivate, but are not claimed to be reproduced by, one
fixed repository test.

The authoritative preregistration is
`docs/paper/STAGE16P_PREREGISTRATION.md`. The registered next action is
`stage16p_copula_context`. Within each image, each of the five retained
fold-calibrated membership maps is replaced by its deterministic empirical-CDF
midrank `(average_rank - 0.5) / N` before the unchanged distorted-Choquet
integral. Ties receive average ranks. Singleton weights, gamma `0.55`, gate
strength `2.0`, floor `0.10`, median conditioning, grayscale Scharr+NMS, and
fold-fitted thresholds are unchanged. The transform uses only the current
unlabelled image; it does not fit an adapter, use dataset identity, or inspect
another target image.

Promotion is conjunctive. UDED selection requires aggregate F1 delta at least
`+0.002`, precision at least `-0.002`, recall at least `-0.003`, nonnegative
mean fold-F1 delta, and at least `9/15` fold wins. The official BSDS500-
validation attachment must complete with ODS delta at least `+0.002` and
nonnegative OIS/AP deltas. Deterministic rank-contract checks and the fixed
positions 1/8/15 preview are mandatory. No rank definition, tie rule,
normalization scope, feature subset, weight, gamma, gate, localizer, or
threshold may be tuned from the result. The compact controller remains
incumbent pending the outcome.

### Stage 16p first launch stopped before scientific output

The first Stage-16p launch stopped during repeated CV before writing metrics,
the deterministic preview, or the official-evaluation manifest. Its launcher
used seed `20261010`, unlike the established generation-2 repeated-CV seed
`20261009` used by Stages 16j, 16l, and 16n. Under that inconsistent seed, the
stochastic training-fold bank preselector omitted the preregistered retained
`gabor4_scale_persistence` feature in repeat 2/fold 2, so the compact-controller
contract correctly raised an error. This provides no candidate-performance or
official-evaluator feedback.

One harness-only retry is registered as
`stage16p_copula_context_retry1` with explicit seed `20261009`. The retry
restores the established folds and fold-fitted compact-controller contract; it
does not change the empirical-rank transform, retained features, weights,
Choquet/gate/localizer settings, thresholds, promotion rule, dataset roles, or
official BSDS500-validation attachment.

### Stage 16p empirical-copula context rejected; Stage 16q registered

The seed-corrected retry completed all rank-contract checks, the fixed
positions 1/8/15 preview, repeated CV, and official attachment. Relative to
compact MFI on UDED selection, aggregate precision/recall/F1 changed by
`-0.004462/-0.016471/-0.009028`; mean fold F1 changed by `-0.007685`, and the
candidate won only `2/15` fold comparisons. It failed every preregistered UDED
performance and stability condition.

Under the common official BSDS500-validation path, ODS/OIS/AP changed by
`+0.008482/-0.000650/+0.001349`. The ODS gain and small AP gain do not satisfy
the conjunctive official axis because OIS was required to be nonnegative. The
Windows matcher remains stochastic and reference-uncertified, so these remain
development metrics rather than final-claim evidence.

The fixed image-internal empirical-copula realization is rejected. This result
is evidence that discarding absolute membership marginals harms UDED transfer
in the retained nonlinear context; it is not a general rejection of copula or
rank-based methods. Rank definition, tie handling, normalization scope,
feature subset, weights, aggregation, gate, localizer, and thresholds are
closed to result-driven tuning. The compact controller remains incumbent.

The single registered next action is
`stage16q_generation2_mechanism_checkpoint`, a high-reasoning live-primary-
literature escalation that must choose exactly one mechanistically distinct,
interpretable non-neural falsification with a preregistered joint UDED/BSDS
rule and no protected feedback.

### Stage 16q checkpoint closure; Stage 16r Sugeno context registered

The live primary-literature checkpoint selected one fixed aggregation-semantic
test rather than another cue, localizer, conditioning operator, structural
gate, or marginal transform. De Campos and Bolaños (1992, DOI
`10.1016/0165-0114(92)90037-5`) distinguish Choquet's quantitative arithmetic
accumulation from Sugeno's qualitative max-min aggregation over a shared fuzzy
measure. Marco-Detchart et al. (2023, DOI
`10.1007/978-3-031-39965-7_28`) compare both families for edge detection and
report broadly similar structures with differences around texture and external
boundaries. This supports a bounded test of whether arithmetic compensation
among moderate memberships contributes to the recurring cross-dataset
instability.

The authoritative preregistration is
`docs/paper/STAGE16R_PREREGISTRATION.md`. The registered next action is
`stage16r_sugeno_context`. It replaces only the incumbent distorted-Choquet
functional with the discrete Sugeno integral
`max_i min(x_(i), mu(A_i))`, using the same five fold-calibrated memberships,
outer-fold singleton weights, and capacity
`mu(A)=(sum_{j in A} w_j)^0.55`. Median conditioning, grayscale Scharr+NMS,
gate strength `2.0`, floor `0.10`, and threshold fitting are unchanged. This
is distinct from Stage 14f's RDF increments and Stage 16p's empirical marginal
normalization, and it has no mixing or searched parameter.

Promotion remains conjunctive. UDED selection requires aggregate F1 delta at
least `+0.002`, precision at least `-0.002`, recall at least `-0.003`,
nonnegative mean fold-F1 delta, and at least `9/15` fold wins. The official
BSDS500-validation attachment must complete with ODS delta at least `+0.002`
and nonnegative OIS/AP deltas. Fixed positions 1/8/15 supply the deterministic
preview, and algebraic contract checks are mandatory. No Sugeno operator,
capacity, gamma, weight, membership, gate, localizer, threshold, or
Choquet/Sugeno mixture may be tuned from the result. The compact Choquet
controller remains incumbent pending the outcome.

The first Stage-16r launch stopped before dataset access or result creation
because the controller's Python environment did not contain the runner's
undeclared `scikit-image` JPEG reader. This is harness/dependency evidence only
and provides no Sugeno or detector feedback. A harness-only retry is registered
after replacing that reader with the already-supported Pillow RGB path. The
candidate, folds, seed, parameters, preview, exporter, official attachment, and
conjunctive promotion rule are unchanged.

The Pillow-reader retry also stopped before dataset access or result creation.
Although the Stage-16r file no longer used scikit-image for JPEG reading, its
unchanged legacy UDED and incumbent-feature imports require the repository's
declared scikit-image dependency. The controller had invoked system Python,
while the existing repository `.venv` contains that dependency. A second
harness-only retry is registered through an experiment-local batch launcher
that selects `.venv` without changing detector code, data, parameters,
artifacts, or the conjunctive decision rule.

That batch retry stopped before its launcher or any dataset access because the
controller's Windows `cmd /s /c` path passed the launcher's surrounding quotes
literally; Windows consequently treated the quoted path as an unknown command.
This is harness evidence only and supplies no detector or Sugeno feedback. A
third unchanged harness retry is registered through a repository-local Python
delegator that selects the same `.venv` interpreter. Detector code, data,
folds, seed, aggregation, artifacts, official attachment, and the conjunctive
promotion rule remain unchanged.

### Stage 16r Sugeno context rejected; Stage 16s registered

The environment-repaired fixed Sugeno aggregation completed its repeated CV,
algebraic checks, deterministic preview, and official attachment. Relative to
compact Choquet MFI on UDED selection, aggregate F1/precision/recall and mean
fold F1 changed by `+0.000378/+0.000300/+0.000497/+0.000393`; the candidate
won `8/15` fold comparisons. It therefore missed the preregistered `+0.002`
aggregate-F1 margin and `9/15` fold-win requirement.

Under the common official BSDS500-validation path, ODS/OIS/AP changed by
`+0.001498/+0.000473/-0.013481`. The candidate missed the required `+0.002`
ODS gain and materially reduced AP. Algebraic contracts and the fixed preview
passed, but all promotion conditions were conjunctive. The candidate is
rejected; its Sugeno operators, capacity, gamma, weights, memberships, gate,
localizer, thresholds, and any Choquet/Sugeno mixture are closed to tuning.
The compact Choquet controller remains incumbent.

The single registered next action is
`stage16s_generation2_mechanism_checkpoint`, a high-reasoning live-primary-
literature escalation that must select exactly one mechanistically distinct,
interpretable non-neural falsification with a preregistered joint UDED/BSDS
rule and no protected feedback.

### Stage 16s checkpoint closure; Stage 16t automatic scale selection registered

The live primary-literature checkpoint selected one fixed localization-scale
test rather than another context cue, aggregation operator, conditioning
filter, structural gate, or detector mixture. Lindeberg (1998, DOI
`10.1023/A:1008097225773`) defines a scale-space edge by the conjunction of a
gradient-direction spatial maximum and a maximum of gamma-normalized edge
strength over scale. With first-order normalization gamma `1/2`, sharp edges
select fine scales while diffuse or noisy edge structure can select coarser
scales. This supplies an image-internal response to boundary-width variation
without dataset identity.

The authoritative preregistration is
`docs/paper/STAGE16T_PREREGISTRATION.md`. The registered next action is
`stage16t_scale_space_localizer`. It evaluates fixed variance levels
`t={1,4,16}` (`sigma={1,2,4}`), selects the largest
`sigma^0.5 * |grad L|` response at every pixel, and retains the spatially
non-maximal-suppressed response at that scale. Only the localizer changes; the
median input, retained five memberships, outer-fold singleton fitting,
distorted-Choquet gamma `0.55`, gate strength `2.0`, floor `0.10`, and
threshold fitting remain unchanged.

This is a bounded repository surrogate, not a reproduction of continuous
scale-space edge curves, closed-curve construction, subscale interpolation,
or integrated saliency. Promotion remains conjunctive: UDED selection requires
aggregate F1 at least `+0.002`, precision at least `-0.002`, recall at least
`-0.003`, nonnegative mean fold-F1 delta, and at least `9/15` fold wins; the
official BSDS500-validation attachment requires ODS at least `+0.002` and
nonnegative OIS/AP. Fixed synthetic scale contracts and the positions 1/8/15
preview are also mandatory. No scale, normalization, NMS, response mapping,
context, gate, or threshold tuning is allowed from the result. The compact
Choquet-gated grayscale Scharr+NMS controller remains incumbent.

### Stage 16t automatic scale selection rejected; Stage 16u registered

The fixed scale-selected localizer completed its repeated CV, synthetic scale
contracts, deterministic preview, and official attachment. Relative to compact
MFI on UDED selection, aggregate F1/precision/recall and mean fold F1 changed
by `-0.019452/+0.001642/-0.053267/-0.020488`, and the candidate won only
`2/15` fold-F1 comparisons. It therefore failed the F1, recall, mean-fold, and
fold-win requirements despite a small precision increase.

Under the common official BSDS500-validation path, ODS/OIS/AP changed by
`+0.003808/+0.000911/-0.010464`. The ODS threshold and nonnegative OIS
condition passed, but AP declined, so this axis also failed the conjunctive
rule. The fixed positions 1/8/15 preview and all synthetic contracts passed,
but cannot override the performance failures. The candidate is rejected; its
scales, gamma normalization, derivative discretization, scale-selection/tie
rule, NMS, response mapping, conditioning, localizer integration, context,
gate, and thresholds are closed to tuning. This result does not falsify
continuous automatic scale-space edge theory. The compact Choquet-gated
grayscale Scharr+NMS controller remains incumbent.

The single registered next action is
`stage16u_generation2_mechanism_checkpoint`, a high-reasoning live-primary-
literature escalation that must select exactly one mechanistically distinct,
interpretable non-neural falsification with a preregistered joint UDED/BSDS
rule and no protected feedback.

### Stage 16u checkpoint closure; Stage 16v Structured Edge forest registered

The live primary-literature checkpoint selected the full Dollár-Zitnick
Structured Edge forest rather than another scalar cue, response transform,
conditioning operator, localizer micro-variant, or fuzzy aggregation change.
The ICCV/TPAMI method predicts structured local edge masks with a random
decision forest, thereby representing short lines, corners, and junctions at
the patch-output level. This is mechanistically distinct from Stage 14n's
shallow scalar pixel forest; the earlier result explicitly did not test the
published structured-mask system.

The exact author `pdollar/edges` repository is pinned at
`94260b5d0fc068202598312e01a37604972dcc9e`, its required official MATLAB
toolbox at `e87332637bbe8e8b92dd487c87567d9628404523`, and the shipped
`modelBsds.mat` is part of the pinned author tree (SHA-256
`9b0f2af485516c89549d4050a7d29fe789c315a4632d16cf29a07796b54c1a6b`).
The fixed synthetic R2023a smoke test passed with finite native-size output.
Source inspection confirms
that author training reads only BSDS500 `train`. The candidate is therefore
classified explicitly as a non-neural supervised detector, not as an
untrained baseline. The code's MSR-LA Full Rights license is recorded and the
author trees remain ignored external dependencies.

The authoritative protocol is `docs/paper/STAGE16V_PREREGISTRATION.md`.
`stage16v_structured_forest` freezes the shipped author model, single-scale
settings, sharpening, stride, and the NMS enabled by author `edgesEval.m`.
UDED selection uses repeated threshold-CV without forest fitting; BSDS500
validation is excluded from training and attached through the unchanged
official path. Promotion is conjunctive and requires meaningful gains on both
axes plus provenance, repeatability, runtime, hash, complexity, and fixed
positions 1/8/15 preview contracts. No forest parameter, retraining variant,
MFI fusion, score calibration, or router may be tuned from the outcome. The
compact Choquet-gated grayscale Scharr+NMS controller remains incumbent.

### Stage 16v first launch stopped before detector execution; harness retry registered

The first Stage-16v launch prepared the 15 UDED-selection inputs but stopped
before Structured Forest inference because Git's ownership guard rejected the
ignored pinned Piotr Dollár toolbox checkout during provenance verification.
No candidate map, metric, preview, manifest, or scientific result was produced.
This is a harness-only failure and supplies no detector feedback.

`stage16v_structured_forest_retry1` is registered with process-local
`safe.directory` overrides limited to the two immutable, hash-verified author
checkouts. It does not change global Git configuration, author bytes, the
shipped model, detector parameters, datasets, folds, threshold fitting,
preview positions, official evaluator, or the preregistered conjunctive rule.
The compact controller remains incumbent pending the unchanged retry.

### Stage 16v first retry stopped on a wrapper range assertion; exact-serialization retry registered

The first harness retry verified provenance and executed the pinned detector
through five UDED-selection images, then stopped before metrics because the
repository wrapper required the raw post-NMS response to be at most one. A
targeted diagnostic on the stopping image found a finite nonnegative maximum
of `1.04074215889`, with 21 samples above one. The pinned author's own
`edgesEval.m` writes `uint8(E*255)`, whose integer conversion saturates these
rare overshoots. Thus the stop was caused by a stricter wrapper contract, not
by invalid author inference, and no scientific result or official manifest was
produced.

`stage16v_structured_forest_retry2` is registered as a harness-only repair:
use the author's exact `uint8(E*255)` serialization, require finite
nonnegative raw responses, and record the raw maximum and overshoot count in
provenance. Serialized maps remain bounded 8-bit outputs. No author byte,
model, detector setting, dataset, fold, threshold, preview, evaluator, or
promotion condition changes.

### Stage 16v UDED gate failed; official attachment retry registered

The author-serialization retry completed exact Structured Forest inference,
the full UDED-selection 5x3 threshold-CV, hashes, runtimes, provenance, and the
fixed positions 1/8/15 preview. Relative to compact MFI, aggregate
F1/precision/recall and mean fold F1 changed by
`-0.035385/+0.042968/-0.142871/-0.038240`, and the forest won only `2/15`
fold comparisons. The fixed replacement therefore fails the preregistered
UDED F1, recall, mean-fold, and win-count requirements and cannot be promoted
or tuned, irrespective of its eventual BSDS500-validation result.

The mandatory official attachment failed before candidate validation
inference because the pinned sparse vendor worktree omitted the tracked
`models/forest/modelBsds.mat` file after the completed UDED run. This is an
export dependency-materialization defect, not detector feedback. The single
next action is `stage16v_structured_forest_attachment_retry`: restore the
exact model blob from the already pinned commit, verify SHA-256
`9b0f2af485516c89549d4050a7d29fe789c315a4632d16cf29a07796b54c1a6b`, and
rerun only the unchanged official BSDS500-validation export/evaluator. It may
not rerun CV, regenerate UDED predictions, change the forest, or tune/fuse it.
The compact controller remains incumbent.

### Stage 18x dual-stencil Teager-energy context rejected; Stage 18y registered

The fixed positive geometric consensus of axial and diagonal 2-D Teager-
Kaiser energy failed its conjunctive promotion rule. On UDED selection,
aggregate F1/precision/recall and mean fold F1 changed by
`+0.000813/+0.000071/+0.002072/+0.000708`, with only `3/15` fold wins and
eligibility in `3/15` folds. Official BSDS500-validation ODS/OIS/AP changed by
`+0.000002/+0.000867/+0.000088`, missing the required ODS margin. Exact
support and all synthetic, quadratic-scale, repeatability, runtime, and fixed-
preview contracts passed, but cannot override the performance failures.

The candidate is rejected; do not tune or extend its stencils, boundary
handling, rectification, consensus, normalization, calibration, eligibility,
integration, energy-operator, demodulation, contrast-enhancement, or higher-
order family. The compact Choquet-gated grayscale Scharr+NMS controller
remains incumbent. The registered next action is
`stage18y_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must choose exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule, without
combining rejected cues, relaxing the cross-dataset gate, or using protected
feedback.

## Stage 18y checkpoint closed; Stage 18z fold-fitted ICA context registered

Live primary-source review selected one fixed information-theoretic
representation test rather than another hand-designed local activity cue. Bell
and Sejnowski (Vision Research 1997, DOI
`10.1016/S0042-6989(97)00121-1`) showed that independent-component analysis of
natural-image patches yields localized oriented edge filters with sparse
responses. Hyvarinen's robust fixed-point ICA method (DOI
`10.1109/72.761722`) supplies the classical batch estimator.

Stage 18z fits a deterministic 16-component `7x7` ICA bank from 256 unlabeled
patches per outer-training image, strictly inside each UDED fold. Positive
evidence is a parameter-free affine rescaling of the maximum absolute
component response divided by response L2 energy, with zero evidence on a
constant patch. The statistic tests single-component dominance and enters only
as one outer-fold-eligible membership. It is a repository adaptation, not an
author edge detector or neural inference path.

The authoritative protocol is `docs/paper/STAGE18Z_PREREGISTRATION.md`.
`stage18z_ica_sparse_context` is registered with conjunctive UDED-selection
5x3 leakage-free CV and official BSDS500-validation criteria, deterministic
fit/algebraic contracts, exact score-support preservation, runtime/model-hash
diagnostics, and the fixed positions 1/8/15 preview. The compact bank,
distorted-Choquet gamma `0.55`, gate strength `2.0`, floor `0.10`, median
conditioning, grayscale Scharr+NMS, and threshold fitting remain unchanged.
Do not tune or extend ICA, sparse coding, learned dictionaries, component
selection, calibration, or integration from the result. Compact MFI remains
the incumbent.

### Stage 16v exact Structured Edge forest rejected; Stage 16w registered

The attachment-only retry restored and hash-verified the exact pinned author
model and completed the required official BSDS500-validation evaluation without
rerunning UDED CV. The forest scored ODS/OIS/AP
`0.712760/0.724075/0.757440`, improving over compact MFI by
`+0.167315/+0.144560/+0.223159`; all three registered BSDS margins passed.
However, the frozen UDED-selection result had already changed aggregate
F1/precision/recall and mean fold F1 by
`-0.035385/+0.042968/-0.142871/-0.038240`, with only `2/15` fold wins. Because
promotion was explicitly conjunctive, Stage 16v is rejected. The result is
strong evidence that this fixed BSDS-train structured forest is not jointly
transferable to the UDED development regime, while retaining value as a
supervised non-neural BSDS reference. It does not justify a forest sweep,
retraining, calibration, MFI fusion, or routing, and it does not falsify the
structured-forest family generally. The Stage-15a stochastic/reference-
uncertified matcher caveat remains. The compact Choquet-gated grayscale
Scharr+NMS controller remains incumbent.

The single registered next action is
`stage16w_generation2_mechanism_checkpoint`, a high-reasoning live-primary-
literature escalation that must select exactly one mechanistically distinct,
interpretable non-neural falsification with a preregistered joint UDED/BSDS
rule. It may not tune or fuse Stage 16v, revisit earlier closed families, fit
dataset identity, relax the cross-dataset rule, or use protected feedback.

### Stage 16w checkpoint closed - spectral globalization context registered

The live primary-literature checkpoint selected one fixed graph-global
context test. Arbeláez et al.'s spectral-Pb mechanism turns an intervening-
contour affinity graph into image-wide boundary evidence by differentiating
its lowest normalized-cut eigenvectors (TPAMI 2011, DOI
`10.1109/TPAMI.2010.161`). Stage 16x applies that mechanism to the unchanged
Scharr+NMS map on a fixed maximum-side-96 graph, retaining the paper's radius
`5`, affinity scale `0.1`, and `16` nontrivial eigenvectors. The resulting
soft cue is only one fold-eligible positive membership in the compact context;
the localizer and its positive support remain unchanged. This is a bounded
repository surrogate, not exact or learned gPb.

The authoritative protocol is `docs/paper/STAGE16X_PREREGISTRATION.md`.
`stage16x_spectral_globalization_context` is registered with conjunctive
UDED-selection 5x3 leakage-free CV and official BSDS500-validation criteria,
a recall non-collapse endpoint, exact score-support checks, a fixed synthetic
graph contract, runtime diagnostics, and positions 1/8/15 preview. Do not tune
the graph bound, affinities, eigensystem, cue integration, context, gate,
localizer, or thresholds from the result, and do not use it to reopen learned
gPb or forest fusion. The compact Choquet-gated grayscale Scharr+NMS
controller remains incumbent.

### Stage 16x spectral-globalization context rejected; Stage 16y registered

The fixed bounded spectral-Pb surrogate completed all numerical, support,
runtime, eligibility, and qualitative contracts. Its cue was eligible in
`15/15` UDED folds and positive score support was preserved exactly. Relative
to compact MFI, however, UDED aggregate F1/precision/recall and mean fold F1
changed by `-0.000430/-0.000190/-0.000826/-0.000364`, and the candidate won
only `6/15` folds. It therefore failed the registered F1, precision, mean-fold,
and fold-win conditions.

Official BSDS500-validation ODS/OIS/AP changed by
`+0.001975/+0.001748/+0.011216`. OIS and AP improved, but ODS missed the
preregistered `+0.002` margin by about `0.000025`; all conditions were
conjunctive. Stage 16x is rejected. The result closes this fixed coarse graph,
eigensystem, calibration, and Choquet integration to outcome-driven tuning and
does not falsify spectral clustering or exact gPb. The Stage-15a stochastic,
reference-uncertified matcher caveat remains. The compact controller is still
the incumbent.

The single registered next action is
`stage16y_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must select exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule. It may
not tune Stage 16x, advance exact/learned gPb from this outcome, revisit earlier
closed families, use dataset identity, relax the cross-dataset rule, or use
protected feedback.

### Stage 16y checkpoint closed - structure-tensor orientation context registered

Live primary-literature review selected one fixed local orientation-
organization test. Bigun, Granlund and Wiklund's second-moment formulation
(TPAMI 1991, DOI `10.1109/34.85668`) and Weickert's scalar structure-tensor
analysis (Image and Vision Computing 1999, DOI
`10.1016/S0262-8856(98)00102-4`) distinguish a locally one-dimensional edge
from flat or multidirectional structure through the tensor eigenvalues. Stage
16z retains Weickert's illustrated noise/integration scales `0.5/4.0` and uses
the continuous orientation-evidence quantity `lambda_max-lambda_min`.

The cue is appended only as one fold-calibrated, training-eligible positive
membership in the existing compact distorted-Choquet context. Median
conditioning, the five retained cues, gamma `0.55`, gate strength `2.0`, floor
`0.10`, grayscale Scharr+NMS, and threshold fitting remain unchanged. This is
not a rerun of Stage 14k: that stage replaced localization with a per-pixel
CIELAB Di Zenzo color tensor, whereas Stage 16z uses a scalar spatially
integrated tensor only for context. It also omits coherence-enhancing
diffusion.

The authoritative protocol is `docs/paper/STAGE16Z_PREREGISTRATION.md`.
`stage16z_orientation_coherence_context` is registered with conjunctive
UDED-selection 5x3 leakage-free CV and official BSDS500-validation criteria,
precision/recall non-collapse, at least 12/15 eligible folds, exact positive-
support preservation, a fixed step/flat/checkerboard numerical contract,
runtime diagnostics, and a positions 1/8/15 preview. No tensor, diffusion,
calibration, integration, context, gate, localizer, or threshold parameter may
be tuned from the outcome. The compact controller remains incumbent.

### Stage 16z structure-tensor orientation context rejected; Stage 17a registered

The fixed scalar structure-tensor cue passed the entire UDED-selection gate.
Relative to compact MFI, aggregate F1, precision, recall, and mean fold F1
changed by `+0.003263/+0.002639/+0.004184/+0.002705`; it won `14/15` folds,
was training-eligible in `15/15`, and preserved positive score support exactly.
The step/flat/checkerboard synthetic contract, repeatability, finite/bounded
checks, runtime diagnostics, and fixed positions 1/8/15 preview also completed.

Official BSDS500-validation ODS/OIS/AP changed by
`+0.001414/+0.000628/+0.010279`. OIS and AP improved, but ODS missed the
preregistered `+0.002` margin, so the conjunctive rule rejects Stage 16z. The
result is narrow positive evidence for locally integrated orientation evidence
on UDED and ranking quality on BSDS, but it does not establish the required
joint gain. No tensor scale, normalized coherence, color/multiscale variant,
diffusion, calibration, integration, context, gate, localizer, or threshold may
be tuned from this outcome. This is not a falsification of structure-tensor
analysis generally. The Stage-15a stochastic, reference-uncertified matcher
caveat remains, and the compact controller is still incumbent.

The single registered next action is
`stage17a_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must select exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule. It may
not tune Stage 16z, revisit earlier closed families, use dataset identity,
relax the cross-dataset rule, or use protected feedback.

### Stage 17a checkpoint closed - local nonparametric rank context registered

Live primary-literature review selected one fixed distribution-free local
boundary statistic. Bovik, Huang and Munson's nonparametric edge work (Pattern
Recognition 1986, DOI `10.1016/0031-3203(86)90011-7`) establishes rank-sum
testing as a robust alternative to moment-based edge evidence. Smeraldi's
ranklet construction (ICPR 2002, DOI `10.1109/ICPR.2002.1047924`) supplies a
normalized, orientation-selective Mann-Whitney interpretation with monotone
gray-level invariance.

Stage 17b uses one fixed radius-2 neighborhood and four opposed spatial
partitions. The cue is the maximum absolute tie-corrected normalized
Mann-Whitney contrast and is appended only as one outer-fold-calibrated,
training-eligible positive membership. This is a local ordering statistic, not
Stage 16p's image-wide membership ranks, Stage 16j's parametric step profile,
or Stage 14l's LBP-histogram contrast. The compact context, Choquet gamma,
gate, median conditioning, grayscale Scharr+NMS localizer, and threshold
fitting remain unchanged.

The authoritative protocol is `docs/paper/STAGE17B_PREREGISTRATION.md`.
`stage17b_ranklet_context` is registered with conjunctive UDED-selection 5x3
leakage-free CV and official BSDS500-validation criteria, precision/recall
non-collapse, eligibility, exact positive-support preservation, fixed
flat/step/monotone-invariance contracts, runtime diagnostics, and a positions
1/8/15 preview. No radius, scale, orientation, partition, rank-statistic,
calibration, integration, context, gate, localizer, or threshold parameter may
be tuned from the outcome. The compact controller remains incumbent.

### Stage 17b local Mann-Whitney rank context rejected; Stage 17c registered

The fixed local rank-contrast cue failed its conjunctive promotion rule. Its
outer-training-fold edge-versus-texture AUC was below the fixed `0.56`
eligibility threshold in all `15/15` folds, so the candidate exactly reduced
to the compact control. UDED aggregate F1, precision, recall, mean fold F1,
and fold wins therefore changed by `0/0/0/0/0`; eligibility was `0/15`.

Official BSDS500-validation ODS/OIS/AP changed by
`-0.000012/-0.000201/+0.000098`. The numerical, boundedness,
repeatability, monotone-transform invariance, positive-support, runtime, and
fixed positions 1/8/15 preview contracts completed, but the UDED eligibility
and BSDS performance requirements failed. The candidate is rejected. This is
evidence against the fixed radius-2 four-partition integration, not against
nonparametric edge statistics generally. No radius, partition, orientation,
tie, statistic, eligibility, calibration, integration, context, gate,
localizer, or threshold tuning is allowed, and the preregistration explicitly
bars multiscale, variance, color, and learned rank variants from this outcome.
The Stage-15a stochastic, reference-uncertified matcher caveat remains, and
the compact controller is still incumbent.

The single registered next action is
`stage17c_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must select exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule. It may
not tune Stage 17b, revisit earlier closed families, use dataset identity,
relax the cross-dataset rule, or use protected feedback.

### Stage 17c - GMRF Fisher-information checkpoint

The live primary-source review selected Levada's local observed-Fisher
analysis of isotropic pairwise Gaussian Markov random fields (Entropy 2014,
DOI `10.3390/e16021002`, arXiv `1108.4973`). The paper's conditional model and
maximum-pseudo-likelihood equations give a parameter-free, image-internal
measure of contextual surprise: the local type-I/type-II information ratio is
the squared conditional innovation normalized by its fitted variance. High
values represent configurations inconsistent with the image's global spatial
dependence, which the paper associates with region boundaries.

This mechanism is distinct from Stage 17b's local ordering statistic and from
the closed tensor, spectral-graph, localizer, conditioning, persistence,
topology, profile, and self-similarity tests. Stage 17d fixes the paper's
second-order eight-neighbour system, reflection at the finite raster boundary,
analytic per-image pseudo-likelihood fit, and no evidence clipping or per-image
normalization. One outer-fold-eligible positive membership is appended to the
unchanged five-cue Choquet context. The authoritative preregistration is
`docs/paper/STAGE17D_PREREGISTRATION.md`; promotion is conjunctive across UDED
selection and official BSDS500 validation. No result has yet been inspected.

### Stage 17d local GMRF Fisher-information context rejected; Stage 17e registered

The fixed local GMRF cue was eligible in all `15/15` UDED-selection folds and
produced a small recall gain, but it failed the preregistered joint rule. UDED
aggregate F1, precision, recall, and mean fold F1 changed by
`+0.000719/-0.000108/+0.002133/+0.000715`, with `10/15` fold wins. The
aggregate F1 gain missed `+0.002`, and precision was negative rather than
nonnegative. Official BSDS500-validation ODS/OIS/AP changed by
`+0.000312/-0.002259/-0.003687`, failing the ODS margin and both nonnegative
OIS/AP conditions.

The synthetic step/flat, finite/nonnegative, affine-intensity invariance,
repeatability, exact positive-support, runtime, and fixed positions 1/8/15
preview contracts completed. They do not override the failed performance
conditions. The candidate is rejected. This closes only the fixed isotropic
eight-neighbour conditional-innovation integration, not GMRF information
geometry generally; no neighbourhood, estimator, scale, anisotropy, color,
mixture, learned-field, calibration, or integration variant may be tuned from
the result. The Stage-15a stochastic, reference-uncertified matcher caveat
remains, and compact Choquet-gated grayscale Scharr+NMS remains incumbent.

The single registered next action is
`stage17e_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must select exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule. It may
not tune Stage 17d, revisit earlier closed families, use dataset identity,
relax the cross-dataset rule, or use protected feedback.

### Stage 17e checkpoint closed - photometric quasi-invariant context registered

Live primary-literature review selected one fixed physics-based color-context
test. Van de Weijer, Gevers, and Geusebroek's photometric quasi-invariants
(TPAMI 2005, DOI `10.1109/TPAMI.2005.75`) decompose an RGB spatial derivative
under the dichromatic reflection model. Stage 17f removes the component of
each sigma-1 horizontal/vertical RGB derivative parallel to the local RGB
direction and uses the combined residual energy as positive evidence. The
projection suppresses the derivative component attributable to achromatic
shadow/shading changes without the low-intensity division of a full color
invariant.

The cue is computed after the incumbent `3x3` median conditioning is applied
independently to RGB channels and is appended only as one outer-training-fold-
eligible membership. Grayscale Scharr+NMS localization, the five retained
memberships, gamma `0.55`, gate strength `2.0`, floor `0.10`, and threshold
fitting remain unchanged. This differs from Stage 14k's CIELAB Di Zenzo tensor
localizer replacement: it is a photometric projection used only for context,
with no color-gradient localizer or grayscale/color mixture.

The authoritative protocol is `docs/paper/STAGE17F_PREREGISTRATION.md`.
`stage17f_photometric_quasi_invariant_context` is registered with conjunctive
UDED-selection repeated CV and official BSDS500-validation criteria, exact
score-support preservation, fixed chromatic/achromatic/flat synthetic
contracts, runtime diagnostics, and positions 1/8/15 preview. Do not tune the
RGB conditioning, derivative scale, projection, energy, invariant family,
eligibility, calibration, integration, context, gate, localizer, or thresholds
from the result. The compact Choquet-gated grayscale Scharr+NMS controller
remains incumbent.

### Stage 17f photometric quasi-invariant context rejected; Stage 17g registered

The fixed sigma-1 shadow-shading photometric quasi-invariant membership passed
the official BSDS axis but failed the preregistered UDED aggregate-F1 margin
and fold-win requirements. UDED aggregate F1, precision, recall, and mean fold
F1 changed by `+0.000756/+0.000826/+0.000594/+0.000509`; the cue was eligible
in `12/15` folds but won only `7/15`. Official BSDS500-validation ODS/OIS/AP
changed by `+0.003855/+0.002520/+0.008468`, satisfying that development axis.
The synthetic chromatic/achromatic/flat, projection-orthogonality,
repeatability, finite/nonnegative, exact-support, runtime, and fixed positions
1/8/15 preview contracts also passed. Because every condition was required,
the candidate is rejected. This closes only the fixed shadow-shading
quasi-invariant integration; it does not falsify photometric invariance theory.
No photometric parameter, variant, calibration, integration, context,
localizer, or threshold may be tuned from the mixed result. The Stage-15a
stochastic, reference-uncertified matcher caveat remains, and compact
Choquet-gated grayscale Scharr+NMS remains incumbent.

The single registered next action is
`stage17g_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must choose exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule. It may
not tune Stage 17f, revisit earlier closed families, use dataset identity,
relax the cross-dataset rule, or use protected feedback.

### Stage 17g checkpoint closed - local fractal-scaling context registered

Live primary-literature review selected one fixed stochastic-scaling test.
Tönnies and Schnabel (IEEE CBMS 1994, DOI `10.1109/38.55153`) model local
gray-level change through fractional Brownian behavior and use the deterministic
component introduced by edges to distinguish boundaries from region interiors
and noise. Stage 17h is a bounded repository surrogate: on the unchanged
median-conditioned grayscale image, it estimates a local first-order
structure-function law at dyadic lags `1/2/4` over the minimal centered `9x9`
support and forms positive evidence as the clipped Hölder slope times clipped
log-log `R2` times the largest-lag variation amplitude.

The cue is appended only as one outer-training-fold-eligible membership.
Grayscale Scharr+NMS localization, the five retained memberships, gamma `0.55`,
gate strength `2.0`, floor `0.10`, and threshold fitting remain unchanged. The
authoritative protocol is `docs/paper/STAGE17H_PREREGISTRATION.md`.
`stage17h_local_fractal_context` is registered with conjunctive UDED-selection
repeated CV and official BSDS500-validation criteria, exact score-support
preservation, fixed flat/step/checker/noise synthetic contracts, runtime
diagnostics, and positions 1/8/15 preview. Do not tune the fractal estimator,
lags, support, directions, evidence factors, calibration, integration, context,
gate, localizer, or thresholds from the result. The compact controller remains
incumbent.

### Stage 17h local fractal-scaling context rejected; Stage 17i registered

The fixed local fractional-Brownian scaling membership failed its conjunctive
promotion rule. On UDED selection, aggregate F1/precision/recall and mean fold
F1 changed by `+0.000164/+0.000385/-0.000232/+0.000073`; the candidate won
`11/15` folds and the cue was eligible in `15/15`, but aggregate F1 missed the
required `+0.002` margin. Official BSDS500-validation ODS/OIS/AP changed by
`+0.001978/+0.000972/+0.011064`; ODS narrowly missed its required `+0.002`
margin. Exact support preservation and the synthetic, finite/bounded,
repeatability, runtime, and fixed-preview contracts passed, but cannot override
the two margin failures. The candidate is rejected. This closes only the fixed
repository surrogate, not local fractal analysis generally; no fractal or
integration variant may be tuned from the result. The Stage-15a stochastic,
reference-uncertified matcher caveat remains, and compact Choquet-gated
grayscale Scharr+NMS remains incumbent.

The single registered next action is
`stage17i_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must choose exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule. It may
not tune Stage 17h, revisit earlier closed families, use dataset identity,
relax the cross-dataset rule, or use protected feedback.

### Stage 17i mechanism checkpoint - local brightness entropy registered

The live primary-literature checkpoint selected one fixed information-
concentration cue rather than another stochastic-scaling, rank, random-field,
tensor, graph, structural, aggregation, conditioning, or localizer variant.
Shiozaki's 1986 entropy operator normalizes brightness inside a `3x3` region
as `p_i=I_i/sum I` and uses the resulting entropy decrease at severe local
brightness changes. Stage 17j uses the bounded deficit `1-H(p)/log(9)` on the
unchanged median-conditioned grayscale image as one outer-training-fold-
eligible positive membership. It adds no histogram bins, opposed regions,
orientation, scale selection, or per-image normalization.

The authoritative protocol is `docs/paper/STAGE17J_PREREGISTRATION.md`.
`stage17j_brightness_entropy_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, exact score-
support preservation, fixed synthetic and multiplicative-scale contracts,
runtime diagnostics, and positions 1/8/15 preview. Do not tune the window,
probability definition, entropy family, zero-sum rule, boundary handling,
eligibility, calibration, integration, context, gate, localizer, or thresholds,
and do not advance to multiscale, clustered, Renyi/Tsallis, color, spatial,
histogram-binned, or cross-half entropy variants from the result. Compact
Choquet-gated grayscale Scharr+NMS remains incumbent.

### Stage 17j brightness-entropy context rejected; Stage 17k registered

The fixed Shiozaki-style `3x3` brightness-entropy membership failed its
conjunctive promotion rule. On UDED selection, aggregate F1/precision/recall
and mean fold F1 changed by
`+0.001106/+0.000175/+0.002682/+0.001305`; the candidate won `12/15` folds,
the cue was eligible in `15/15`, and score support was exactly preserved. The
aggregate-F1 gain nevertheless missed the preregistered `+0.002` margin.
Official BSDS500-validation ODS/OIS/AP improved by
`+0.007561/+0.003648/+0.012971`, satisfying that axis. The synthetic,
multiplicative-scale, repeatability, support, runtime, and fixed-preview
contracts also passed, but all promotion conditions were required. The
candidate is rejected. This closes only the fixed brightness-entropy
integration, not entropy-based edge analysis generally; no entropy or
integration variant may be tuned from the result. The Stage-15a stochastic,
reference-uncertified matcher caveat remains, and compact Choquet-gated
grayscale Scharr+NMS remains incumbent.

The single registered next action is
`stage17k_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must choose exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule. It may
not tune Stage 17j, revisit earlier closed families, use dataset identity,
relax the cross-dataset rule, or use protected feedback.

### Stage 17k checkpoint closed - isotropic surround-isolation context registered

Live primary-literature review selected one fixed annular feature-density test.
Grigorescu, Petkov, and Westenberg (Image and Vision Computing 2004, DOI
`10.1016/j.imavis.2003.12.004`) define isotropic non-CRF suppression from the
positive part of a difference of Gaussians at `sigma` and `4*sigma`, and a
parameter-free suppression slope `atan(surround/local_energy)`. Stage 17l uses
the complementary bounded evidence `1-(2/pi)atan(t/M)` over the unchanged
median-conditioned pre-NMS Scharr magnitude. `sigma=1` is anchored to the
incumbent's local `3x3` Scharr footprint; radius `12` is the fixed three-outer-sigma numerical
support. No suppression factor, hysteresis, orientation term, image adapter,
or parameter search is introduced.

The cue is appended only as one outer-training-fold-eligible positive
membership. The retained compact bank, distorted-Choquet gamma `0.55`, gate
strength `2.0`, floor `0.10`, median conditioning, grayscale Scharr+NMS
localizer, and threshold fitting remain unchanged. The authoritative protocol
is `docs/paper/STAGE17L_PREREGISTRATION.md`.
`stage17l_surround_isolation_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, exact score-
support preservation, fixed synthetic isolation/dense-edge contracts, runtime
diagnostics, and positions 1/8/15 preview. Do not tune the surround geometry,
energy, slope mapping, orientation dependence, calibration, integration,
context, gate, localizer, or thresholds, and do not advance to adaptive,
anisotropic, multiscale, color, end-stopped, facilitated, or learned surround
variants from the result. The compact controller remains incumbent.

### Stage 17l isotropic surround-isolation context rejected; Stage 17m registered

The fixed surround-isolation membership failed the conjunctive rule. UDED
aggregate F1/precision/recall and mean fold F1 changed by
`-0.000046/-0.000767/+0.001221/+0.000010`, with `5/15` fold wins and only
`10/15` eligible folds. Official BSDS500-validation ODS/OIS/AP changed by
`+0.001673/+0.001578/+0.007118`; ODS missed the registered `+0.002` margin.
The numerical, synthetic, scale-invariance, support, runtime, and fixed-preview
contracts passed, but cannot override these failures. This closes only the
fixed repository integration, not surround-suppression theory generally; no
surround or integration variant may be tuned from the result. The Stage-15a
stochastic, reference-uncertified matcher caveat remains, and compact Choquet-
gated grayscale Scharr+NMS remains incumbent.

The single registered next action is
`stage17m_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must choose exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule. It may
not tune Stage 17l, revisit earlier closed families, use dataset identity,
relax the cross-dataset rule, or use protected feedback.

### Stage 17m checkpoint - two-scale topological-sensitivity context registered

Live primary-source review selected Amstutz and Fehrenbach's parabolic
topological-gradient construction (JMIV 2015, DOI
`10.1007/s10851-015-0558-z`; HAL `hal-01025706`). The paper interprets an
edge as a location where inserting an infinitesimal insulating crack improves
a variational image criterion. Its variance-maximization `h3` indicator
couples gradients across heat scales, and its analytic one-point quadrature
fixes `beta=1-sqrt(1-4/pi^2)`. Stage 17n uses the paper's illustrated `T=2`
and the positive extremal eigenvalue of the resulting two-scale `h4`
quadratic form.

The candidate is one fold-calibrated, training-eligible positive context
membership. It does not change median conditioning, the five retained
memberships, distorted-Choquet gamma `0.55`, gate strength `2.0`, floor
`0.10`, grayscale Scharr+NMS localization, or threshold fitting. Unlike Stage
16t, it does not choose among scales or replace the localizer; unlike Stage
14p, it does not evolve a phase field. The implementation is an equation-level
repository realization, not the paper's full NMS/hysteresis or finite-element
pipeline.

The authoritative preregistration is
`docs/paper/STAGE17N_PREREGISTRATION.md`. Promotion is conjunctive across
UDED-selection 5x3 leakage-free CV and official BSDS500 validation, with fixed
synthetic, support, runtime, and positions 1/8/15 preview contracts. No
protected split is used. No heat time, quadrature, derivative, PDE/cost,
calibration, integration, gate, localizer, or threshold variant may be tuned
from the result. The compact Choquet-gated grayscale Scharr+NMS controller
remains incumbent pending execution.

### Stage 17n two-scale topological-sensitivity context rejected; Stage 17o registered

The fixed `h4` topological-sensitivity membership failed the conjunctive rule.
UDED aggregate F1/precision/recall and mean fold F1 changed by
`-0.000350/-0.000556/+0.000028/-0.000330`, with only `3/15` fold wins despite
`14/15` eligibility. Official BSDS500-validation ODS/OIS/AP improved by
`+0.006420/+0.004441/+0.014245`, satisfying that development axis. The
synthetic, quadratic-scaling, finite/nonnegative, repeatability, support,
runtime, and fixed-preview contracts passed, but all promotion conditions were
required. This closes only the fixed equation-level `h4` integration, not
topological-gradient edge theory generally; no heat-time, quadrature,
topological cost/PDE, color, multiscale, anisotropic, restoration, calibration,
or integration variant may be tuned from the result. The Stage-15a stochastic,
reference-uncertified matcher caveat remains, and compact Choquet-gated
grayscale Scharr+NMS remains incumbent.

The single registered next action is
`stage17o_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must choose exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule. It may
not tune Stage 17n, revisit earlier closed families, use dataset identity,
relax the cross-dataset rule, or use protected feedback.

### Stage 17o checkpoint - local robust-gradient outlier context registered

Live primary-source review selected Black and Sapiro's local robust-gradient
scale principle (Scale-Space 1999, DOI `10.1007/3-540-48236-9_23`). Their
method treats a gradient as edge evidence relative to robust local gradient
variation, allowing weak structure to be significant in smooth regions while
requiring larger deviations in texture. Stage 17p isolates that representation
from their anisotropic-diffusion pipeline.

On the unchanged median-conditioned grayscale image, the candidate computes
Scharr magnitude and, in one fixed reflected `9x9` window, its local median and
`1.4826`-normalized MAD. Positive gradient excess is mapped to the bounded
ratio `d/(d+s)` and enters only as one fold-calibrated, training-eligible
positive membership. The image, retained five-cue bank, distorted-Choquet
gamma `0.55`, gate strength `2.0`, floor `0.10`, grayscale Scharr+NMS
localizer, and fold-fitted thresholds remain unchanged. This is a bounded
repository surrogate, not Black-Sapiro diffusion or a detector reproduction.

The authoritative preregistration is
`docs/paper/STAGE17P_PREREGISTRATION.md`. Promotion is conjunctive across
UDED-selection 5x3 leakage-free CV and official BSDS500 validation, with
finite/bounded, flat/step/texture, positive-scale-invariance, exact support,
runtime, and fixed positions 1/8/15 preview contracts. No window, gradient,
robust estimator, mapping, diffusion, calibration, integration, gate,
localizer, or threshold variant may be tuned from the result. The compact
Choquet-gated grayscale Scharr+NMS controller remains incumbent pending
execution.

### Stage 17p local robust-gradient outlier context rejected; Stage 17q registered

The fixed robust local-significance cue was training-ineligible in every UDED
outer fold: its edge-versus-texture AUC never reached the preregistered `0.56`
threshold. The candidate therefore reduced exactly to the compact control on
UDED selection, producing zero deltas in aggregate F1, precision, recall, and
mean fold F1, with `0/15` candidate wins and `0/15` eligible folds. Official
BSDS500-validation ODS/OIS/AP changed by
`+0.000035/-0.000086/+0.000100`; the ODS margin and nonnegative OIS condition
failed. Synthetic, positive-scale, repeatability, score-support, runtime, and
fixed positions 1/8/15 preview contracts passed, but all promotion conditions
were conjunctive. This rejects only the fixed `9x9` median/MAD positive-excess
integration, not robust statistics or the complete Black-Sapiro method. No
outlier-statistic or integration variant may be tuned from the result. The
Stage-15a stochastic, reference-uncertified matcher caveat remains, and compact
Choquet-gated grayscale Scharr+NMS remains incumbent.

The single registered next action is
`stage17q_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must choose exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule. It may
not tune Stage 17p, revisit earlier closed families, use dataset identity,
relax the cross-dataset rule, or use protected feedback.

## Stage 17q - generation-2 mechanism checkpoint

The live primary-source review selected directional nonlocal patch recurrence
as a mechanistically distinct test. Xu, Xu, and Quan (TIP 2021, DOI
`10.1109/TIP.2020.3043665`) report that recurrent patches around cartoon
contours are spatially anisotropic, whereas texture recurrence is more
isotropic. Their fixed directional matching uses `5x5` patches, a `51x51`
search region, four width-8 bands, 16 matches per direction, and similarity
bandwidth `0.3`.

Stage 17r isolates the normalized directional nonlocal residual from their Eq.
6 as one positive fold-eligible membership. It is a bounded repository cue,
not a reproduction of the paper's complete wavelet/DCT morphology-component
decomposition. Median conditioning, the retained five memberships, distorted-
Choquet gamma `0.55`, gate strength `2.0`, floor `0.10`, grayscale Scharr+NMS,
and leakage-free fold fitting are unchanged. This mechanism differs from the
closed SUSAN centre-similarity, local-rank, half-disc histogram, spectral-
graph, structural-support, conditioning, and localizer families because it
tests the directional organization of nonlocal recurrent patches.

The authoritative protocol is `docs/paper/STAGE17R_PREREGISTRATION.md`.
Promotion is conjunctive across UDED-selection repeated CV and official
BSDS500 validation, with flat/step/checkerboard, repeatability, exact-support,
runtime, and fixed positions 1/8/15 preview contracts. No protected split was
used at the checkpoint. The compact controller remains incumbent pending the
result, and no patch/search, band, match, similarity, decomposition, or
integration parameter may be tuned afterward.

### Stage 17r directional patch-recurrence context rejected; Stage 17s registered

The fixed directional nonlocal-residual membership was eligible in every
outer fold and won `14/15` fold-F1 comparisons. UDED aggregate
F1/precision/recall and mean fold F1 changed by
`+0.001396/+0.000554/+0.002800/+0.001231`, but the aggregate F1 gain missed
the preregistered `+0.002` margin. Official BSDS500-validation ODS/OIS/AP
changed by `+0.001872/+0.000782/+0.003748`; ODS independently missed its
`+0.002` margin. The synthetic, finite/bounded, repeatability, exact-support,
runtime, and fixed positions 1/8/15 preview contracts passed. Because all
conditions were conjunctive, the candidate is rejected. This closes only the
fixed repository residual integration, not patch-recurrence theory or the
complete Xu-Xu-Quan decomposition. The Stage-15a matcher caveat remains, and
the compact controller stays incumbent.

The single registered next action is
`stage17s_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must choose exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule. It may
not tune Stage 17r, revisit earlier closed families, use dataset identity,
relax the cross-dataset rule, or use protected feedback.

### Stage 17s checkpoint - Frei-Chen patch-subspace context registered

Live primary-source review selected Frei and Chen's fixed orthogonal patch
representation (IEEE Transactions on Computers 1977, DOI
`10.1109/TC.1977.1674733`). Their nine normalized `3x3` masks decompose a
local image patch into four edge, four line, and one average basis component;
the cosine of the angle to the edge-subspace projection is a bounded measure
of edge-like patch geometry.

Stage 17t uses exactly that soft projection occupancy as one fold-calibrated,
training-eligible positive context membership. It does not threshold the
response or run the paper's sequential binary detector. Median conditioning,
the retained five memberships, distorted-Choquet gamma `0.55`, gate strength
`2.0`, floor `0.10`, grayscale Scharr+NMS, and leakage-free fold fitting are
unchanged. This tests a complete analytic local patch basis rather than
nonlocal recurrence, a derivative tensor, a normal-profile template, a
texture histogram, or a localizer replacement.

The authoritative protocol is `docs/paper/STAGE17T_PREREGISTRATION.md`.
Promotion is conjunctive across UDED-selection repeated CV and official
BSDS500 validation, with basis-orthonormality, flat/step/checkerboard/noise,
positive-scale, repeatability, exact-support, runtime, and fixed positions
1/8/15 preview contracts. No protected split was used at the checkpoint. The
compact controller remains incumbent pending the result, and no basis,
subspace, normalization, scale, color, sequential-detector, calibration, or
integration variant may be tuned afterward.

### Stage 17t Frei-Chen patch-subspace context rejected; Stage 17u registered

The fixed Frei-Chen edge-subspace membership was eligible in all `15/15`
outer folds and won `10/15` fold-F1 comparisons. UDED aggregate
F1/precision/recall and mean fold F1 changed by
`+0.000590/+0.000108/+0.001404/+0.000790`, but the aggregate F1 gain missed
the preregistered `+0.002` margin. Official BSDS500-validation ODS/OIS/AP
improved by `+0.005624/+0.002471/+0.013006`, so that axis passed. The
orthonormality, synthetic, finite/bounded, repeatability, positive-scale,
exact-support, runtime, and fixed positions 1/8/15 preview contracts also
passed. Because every condition was required, the candidate is rejected.
This closes only the fixed soft edge-subspace integration, not Frei-Chen
patch analysis or the complete sequential detector. The Stage-15a matcher
caveat remains, and the compact controller stays incumbent.

The single registered next action is
`stage17u_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must choose exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule. It may
not tune Stage 17t, combine rejected cues, revisit earlier closed families,
use dataset identity, relax the cross-dataset rule, or use protected feedback.

### Stage 17u checkpoint closed; Stage 17v morphological blur-minimum context registered

The live primary-literature checkpoint selected one fixed nonlinear
order-statistic context test. Van Vliet, Young, and Beckers (1989, DOI
`10.1016/0734-189X(89)90131-X`) write Lee's blur-minimum morphological edge
strength as `min(gradmax,-gradmin)`. With the fixed smallest `3x3` unit-square
support, this becomes the smaller distance from the center intensity to the
local maximum and minimum. It is positive only when the center has both
brighter and darker support, unlike the previously available local range or a
one-sided gradient.

Stage 17v appends that raw statistic only as one outer-training-fold-eligible
positive membership. It does not run nonlinear-Laplacian zero crossings,
Gaussian smoothing, distance transforms, contour extraction, or thresholding.
The compact bank, gamma `0.55`, gate strength `2.0`, floor `0.10`, median
conditioning, grayscale Scharr+NMS, and threshold fitting remain unchanged.

The authoritative protocol is `docs/paper/STAGE17V_PREREGISTRATION.md`.
`stage17v_morphological_blur_minimum_context` is registered with conjunctive
UDED-selection repeated CV and official BSDS500-validation criteria, exact
score-support preservation, fixed ramp/step/checkerboard/impulse and
photometric contracts, runtime diagnostics, and positions 1/8/15 preview. No
protected split was inspected. Do not tune or extend the morphology, support,
shape, smoothing, zero-crossing, calibration, or integration family from the
result. The compact Choquet-gated grayscale Scharr+NMS controller remains the
incumbent.

### Stage 17v morphological blur-minimum context rejected; Stage 17w registered

The fixed `3x3` two-sided morphological blur-minimum membership failed its
conjunctive promotion rule despite passing the BSDS500-validation axis. On
UDED selection, aggregate F1/precision/recall and mean fold F1 changed by
`-0.000167/-0.000396/+0.000244/-0.000150`; the cue was eligible in only
`9/15` folds and won only `3/15`. Official BSDS500-validation ODS/OIS/AP
improved by `+0.002346/+0.001524/+0.005760`. The synthetic, photometric,
repeatability, support, runtime, and fixed-preview contracts passed, but
cannot override the UDED failures. The candidate is rejected; do not tune or
extend its support, shape, morphology, smoothing, zero-crossing, calibration,
integration, context, gate, localizer, or thresholds, and do not advance to
larger, circular, weighted, multiscale, color, adaptive-SNR, hierarchical,
contour-extraction, or complete nonlinear-Laplacian variants from this result.
The compact Choquet-gated grayscale Scharr+NMS controller remains incumbent.

The single registered next action is
`stage17w_generation2_mechanism_checkpoint`, a high-reasoning live-primary-
literature escalation that must select exactly one mechanistically distinct
bounded generation-2 falsification with a preregistered joint UDED-selection/
BSDS500-validation rule. It may not tune morphology or earlier closed
families, combine rejected cues, use dataset identity, relax the cross-dataset
rule, or use protected feedback.

## Stage 17w checkpoint closed; Stage 17x semi-global change-point context registered

Live primary-source review selected Jevnisek and Avidan's semi-global
scanline-segmentation principle (CVIU 2016, DOI
`10.1016/j.cviu.2016.07.004`) as a mid-level alternative to the exhausted
local patch/activity sequence. Their method optimally segments one-dimensional
scanlines and merges boundary evidence across directions. Bellman's dynamic-
programming construction (DOI `10.1145/366573.366611`) and Schwarz's fixed
model-dimension penalty (DOI `10.1214/aos/1176344136`) provide the deterministic
optimization and complexity-control basis.

Stage 17x is explicitly a bounded repository surrogate, not exact SGBD. On a
fixed maximum-side-256 working grid it fits piecewise-constant rows and columns
by exact dynamic programming with a first-difference-noise-scaled `log(N)`
penalty, assigns adjacent-segment contrast symmetrically to each selected
between-sample change point, and merges directions by maximum. It omits SGBD's
textons, semi-global smoothing, fitted MDL temperature, segment-count
marginalization, and optional UCM. The cue enters only as one fold-calibrated,
training-eligible positive membership; compact Choquet context and grayscale
Scharr+NMS localization remain unchanged.

The authoritative protocol is `docs/paper/STAGE17X_PREREGISTRATION.md`.
Promotion is conjunctive across UDED-selection repeated CV and official
BSDS500 validation, with finite/bounded, flat/step/checkerboard, photometric,
repeatability, exact-support, runtime, and fixed positions 1/8/15 preview
contracts. No protected split was used. No working-grid, direction, segment,
penalty, noise-scale, rasterization, merge, calibration, integration, or full-
SGBD variant may be tuned afterward.

### Stage 17x semi-global scanline change-point context rejected; Stage 17y registered

The fixed row/column change-point membership improved UDED-selection aggregate
F1/precision/recall and mean fold F1 by
`+0.001916/+0.000546/+0.004221/+0.001692`, with `13/15` fold wins,
eligibility in `15/15` folds, and exact score-support preservation. The
aggregate F1 gain nevertheless missed the preregistered `+0.002` margin.
Official BSDS500-validation ODS/OIS/AP improved by
`+0.004943/+0.002056/+0.011994`, so that axis passed. The synthetic,
photometric, repeatability, runtime, and fixed-preview contracts also passed,
but every promotion condition was required. The candidate is rejected; do not
tune or extend the working grid, directions, segment model, noise estimator,
BIC penalty, raster support, merging, calibration, integration, scanline-DP,
change-point, or full-SGBD family from this result. The compact controller
remains incumbent.

The single registered next action is
`stage17y_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must choose exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule. It may
not tune Stage 17x, combine rejected cues, revisit earlier closed families,
use dataset identity, relax the cross-dataset rule, or use protected feedback.

## Stage 17y checkpoint closed; Stage 17z adaptive polynomial residual registered

Live primary-source review selected De Simone, Kenne, and Zullo's 2026
PolyEdge representation-failure mechanism (DOI
`10.1007/s11075-026-02497-3`). The official MIT repository is pinned at
commit `53277503faae02514cc9249bccd2083210c00138`. Its adaptive quadtree and
bivariate polynomial reconstructions produce residual evidence where a smooth
local representation fails, a mechanism distinct from Stage 17x's complete-
scanline piecewise-constant partitions and the earlier fixed local-patch,
texture, graph, topology, conditioning, aggregation, and localizer tests.

Stage 17z calls the unmodified author pipeline on the unchanged median-
conditioned grayscale image with the paper's Section-7 settings: degree `6`,
Chebyshev admissible meshes, continuous sampling, depth `8`, minimum cell size
`4`, RMSE tolerance `1e-3`, Gaussian sigma `1`, and equal averaging of the
four author-normalized residuals. It appends only that continuous residual as
one outer-fold-eligible positive membership and does not run percentile
thresholding or alter the retained localizer.

The authoritative protocol is `docs/paper/STAGE17Z_PREREGISTRATION.md`.
`stage17z_adaptive_polynomial_residual_context` is registered with conjunctive
UDED-selection repeated CV and official BSDS500-validation criteria, pinned-
source provenance, exact score-support preservation, fixed synthetic and
photometric contracts, runtime diagnostics, and positions 1/8/15 preview.
Do not tune or extend the polynomial, node, subdivision, residual,
normalization, fusion, threshold, calibration, or integration family from the
result. The compact Choquet-gated grayscale Scharr+NMS controller remains
incumbent.

### Stage 17z adaptive polynomial residual context rejected; Stage 18a registered

The fixed pinned-author PolyEdge residual failed its conjunctive promotion
rule. UDED-selection aggregate F1/precision/recall and mean fold F1 changed by
`+0.001554/+0.000345/+0.003594/+0.001405`; the cue was eligible in `15/15`
folds and won `14/15`, but aggregate F1 missed the required `+0.002` margin.
Official BSDS500-validation ODS/OIS/AP changed by
`+0.001034/-0.000566/+0.006465`, failing both the ODS margin and OIS
non-collapse condition. The pinned-source, synthetic, affine-photometric,
repeatability, exact-support, runtime, and fixed-preview contracts passed, but
could not override the performance failures. The candidate is rejected; do
not tune or extend its polynomial, node, subdivision, smoothing, residual,
normalization, combination, threshold, coefficient-analysis, calibration, or
integration family. The compact controller remains incumbent.

The single registered next action is
`stage18a_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must choose exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule. It may
not tune Stage 17z or earlier closed families, combine rejected cues, use
dataset identity, relax the cross-dataset rule, or use protected feedback.

## Stage 18a checkpoint closed; Stage 18b FH region-boundary context registered

Live primary-source review selected Felzenszwalb and Huttenlocher's adaptive
internal-variation segmentation predicate (IJCV 2004, author-hosted paper and
official code page). Unlike the earlier spectral-Pb surrogate, response
component stability gate, scanline partitions, or polynomial reconstruction,
the new mechanism builds image regions by accepting a graph transition only
when it is small relative to variation already accepted inside both adjacent
components.

Stage 18b fixes the paper's grayscale natural-image grid setting: Gaussian
sigma `0.8`, eight-neighbour absolute-difference edges, and
`tau(C)=300/|C|`. It disables implementation-level minimum-component
postprocessing and marks both raster endpoints of every between-component
adjacency. That binary support enters only as one outer-training-fold-
eligible positive membership; the compact Choquet context and grayscale
Scharr+NMS localization remain unchanged. The scikit-image 0.26.0 realization
is equation-level and is not claimed as exact author-code reproduction.

The authoritative protocol is `docs/paper/STAGE18B_PREREGISTRATION.md`.
`stage18b_fh_region_boundary_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, exact score-
support preservation, fixed flat/step/checkerboard/noise contracts, runtime
diagnostics, and positions 1/8/15 preview. No graph, smoothing, observation
scale, connectivity, minimum-size, boundary rasterization, color,
feature-space, hierarchy, calibration, or integration variant may be tuned
from the result. No protected split was used and the compact controller
remains incumbent.

The first Stage-18b launch stopped before dataset access or result creation.
Its strict FH synthetic contract passed, but the reused Stage-17h experiment
harness then requested legacy `bounded`, `step_exceeds_checker`, and
`step_exceeds_noise` keys that the FH contract had not exposed. This is a
pre-result harness-interface defect and supplies no detector or benchmark
feedback. `stage18b_fh_region_boundary_context_retry1` is registered with
direct FH compatibility diagnostics; the candidate, fixed parameters, data,
folds, preview, official attachment, and conjunctive promotion rule are
unchanged.

### Stage 18b FH adaptive-region boundary context rejected; Stage 18c registered

The harness-repaired fixed FH cue failed its conjunctive promotion rule. On
UDED selection, aggregate F1/precision/recall and mean fold F1 changed by
`-0.000307/-0.000632/+0.000277/-0.000248`; the cue was eligible in `14/15`
folds but won only `6/15`. Official BSDS500-validation ODS/OIS/AP improved by
`+0.002858/+0.002241/+0.009290`, passing that development axis. The UDED F1,
precision, mean-fold, and fold-win failures nevertheless reject the candidate.
Synthetic, repeatability, exact-support, runtime, and fixed-preview contracts
passed. Do not tune or extend FH smoothing, graph scale/connectivity/weights,
component processing, boundary rasterization, color, feature-space, hierarchy,
calibration, eligibility, or integration. The compact controller remains
incumbent.

The single registered next action is
`stage18c_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must choose exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule. It may
not tune Stage 18b or earlier closed families, combine rejected cues, use
dataset identity, relax the cross-dataset rule, or use protected feedback.

## Stage 18c checkpoint closed; Stage 18d active micro-drift variance context registered

Live primary-source review selected Schmittwilken and Maertens' active edge
model (Journal of Vision 2022, DOI `10.1167/jov.22.8.5`) and its official code
at pinned commit `cb35f82f8c0064f346f689dbc49a34eb9d694972`. The paper's
`S-V-N` control makes a static edge temporally informative by sampling it
along small Brownian fixation shifts, taking multiscale isotropic DoG response
variance, and normalizing within scale. This supplies a temporal active-
sampling hypothesis rather than another static patch cue, region partition,
graph, localizer, conditioning filter, aggregation, or detector fusion.

Stage 18d fixes all published simulation constants: 40 pixels/degree,
diffusion `20 arcmin^2/s`, 0.2 seconds, 10 Hz variance sampling, ten trials,
and five octave-spaced DoG center sigmas `0.016` through `0.256` degrees with
2:1 surround ratio. One preregistered seed (`20261017`) freezes the ten
otherwise random integer drift paths. The repository adaptation uses reflected
native-raster shifts, averages trial variance, applies published scale-mean
normalization, and maps the mean response by `E/(1+E)`. That cue enters only as
one outer-training-fold-eligible positive membership; the compact context and
grayscale Scharr+NMS localizer remain unchanged. It is equation-level, not an
exact author simulation or evaluation reproduction.

The authoritative protocol is `docs/paper/STAGE18D_PREREGISTRATION.md`.
`stage18d_active_drift_variance_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, exact score-
support preservation, fixed flat/step/checkerboard/noise, repeatability and
positive-affine contracts, runtime diagnostics, and positions 1/8/15 preview.
No drift, filter, temporal, normalization, calibration, integration, context,
gate, localizer, or threshold parameter may be tuned or extended from the
result. No protected split was used and the compact controller remains
incumbent.

### Stage 18d active micro-drift variance context rejected; Stage 18e registered

The fixed active micro-drift variance cue failed its conjunctive promotion
rule. On UDED selection, aggregate F1/precision/recall and mean fold F1 changed
by `-0.000845/-0.000523/-0.001363/-0.000724`, with only `4/15` fold wins. The
cue was eligible in `15/15` folds and preserved exact score support. Official
BSDS500-validation ODS/OIS/AP improved by
`+0.002372/+0.001440/+0.009916`, passing that axis. The UDED F1, precision,
mean-fold, and fold-win failures nevertheless reject the candidate. Synthetic,
positive-affine, repeatability, runtime, and fixed-preview contracts passed.
Do not tune or extend the active-drift, filter, temporal, normalization,
calibration, eligibility, or integration family. The compact controller
remains incumbent.

The single registered next action is
`stage18e_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must choose exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule. It may
not tune Stage 18d or earlier closed families, combine rejected cues, use
dataset identity, relax the cross-dataset rule, or use protected feedback.

## Stage 18e checkpoint closed; Stage 18f triangle-partition context registered

Live primary-source review selected Ofir, Galun, Nadler, and Basri's
hierarchical faint-curve search (CVPR 2016, DOI
`10.1109/CVPR.2016.30`). The official author MATLAB repository is pinned at
commit `19dc4845b26f81b68f40bc2e3e36bfe1c59d01d2`, tree
`fa9866f16e8679e77123a2a807978886a9a83595`; its immutable Windows source/MEX
surface passed a deterministic R2023a flat/step smoke test. The mechanism
accumulates statistical contrast and shape evidence over a combinatorial
family of curves through a triangle-partition tree, rather than altering the
incumbent's local filters, response graph, region partition, aggregation, or
localization.

Stage 18f uses one fixed whole-image author block. The unchanged median-
conditioned grayscale image is isotropically fitted into a reflected
`129x129` square, passed to `runIm(block,false,0)` with parameter index zero,
unletterboxed, and bilinearly projected back to native support. The author
defaults are frozen, including filter width `2`, minimum contrast `8`, minimum
curve length `5`, NMS threshold `0.5`, maximum turn angle `48`, tree level
`3`, assumed noise sigma `0.1`, and the shipped statistical/shape weights.
The response enters only as one outer-training-fold-eligible positive
membership. This is an immutable-author-code integration with a disclosed
raster adapter, not exact native-resolution detector reproduction; no explicit
source license was found, so the ignored checkout is not redistributed.

The authoritative protocol is `docs/paper/STAGE18F_PREREGISTRATION.md`.
`stage18f_triangle_partition_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, source,
synthetic, repeatability, exact-support, runtime, and fixed positions 1/8/15
preview contracts. Do not tune or extend the tree, curve family, statistical
or shape scores, author parameters, NMS, block geometry, resampling,
projection, calibration, integration, context, gate, localizer, or thresholds
from the result. The compact controller remains incumbent.

The first Stage-18f launch passed source provenance and the preregistered
four-map synthetic author batch, then stopped before UDED access because the
reused Stage-17h harness requested legacy `step_exceeds_checker` and
`step_exceeds_noise` keys absent from the Stage-18f contract. No candidate
metric, preview, manifest, or official score was produced. A harness-only
`stage18f_triangle_partition_context_retry1` is registered with those keys as
truthful aliases of the already registered orthogonal-step positivity and
16-pixel localization checks. The candidate, author bytes and parameters,
datasets, folds, artifacts, evaluator, and promotion rule are unchanged.

### Stage 18f triangle-partition context rejected; Stage 18g registered

The harness-repaired fixed author triangle-partition cue completed all
registered artifacts and passed source, synthetic, finite/bounded,
repeatability, exact-support, runtime, and fixed positions 1/8/15 preview
contracts. On UDED selection, aggregate F1/precision/recall and mean fold F1
changed by `-0.000864/-0.000920/-0.000720/-0.000786`; the candidate won
`0/15` folds and the cue was eligible in only `11/15`. It therefore failed
the aggregate-F1, precision, mean-fold, fold-win, and eligibility conditions.

Official BSDS500-validation ODS/OIS/AP improved by
`+0.006363/+0.004455/+0.020200`, passing that development axis. Because the
promotion rule was conjunctive, the candidate is rejected. This closes only
the fixed one-block author-response integration, not the published detector,
and does not authorize tree, curve, score, author-parameter, block, tiling,
scale, projection, calibration, eligibility, or integration tuning. The
Windows matcher remains stochastic and reference-uncertified. Compact
Choquet-gated grayscale Scharr+NMS remains incumbent.

The single registered next action is
`stage18g_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must choose exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule. It may
not tune Stage 18f or earlier closed families, combine rejected cues, use
dataset identity, relax the cross-dataset rule, or use protected feedback.

## Stage 18g checkpoint closed; Stage 18h spectral-residual context registered

Live primary-source review selected Hou and Zhang's global spectral-residual
saliency model (CVPR 2007, DOI `10.1109/CVPR.2007.383267`). The paper removes
a local average from the image log-amplitude spectrum, retains Fourier phase,
and reconstructs image-specific statistical innovation. Its fixed experimental
contract uses a 64-pixel visual scale, a `3x3` log-spectrum average, and
Gaussian saliency smoothing at sigma `8`. Unlike the recently closed local,
region, graph, curve, recurrence, and structural mechanisms, the new signal is
global Fourier-domain surprise relative to the image's own spectral statistics.

Stage 18h uses an equation-level grayscale realization rather than an exact
author-code reproduction. The unchanged median-conditioned image is resized
isotropically to maximum side `64`; the squared residual-spectrum
reconstruction is smoothed, maximum-scaled when nonzero, and bilinearly
returned to native support. A constant input has an exact-zero cue. The map is
not used as a boundary detector: it enters only as one outer-training-fold-
eligible positive context membership while compact Choquet aggregation and
grayscale Scharr+NMS localization remain unchanged.

The authoritative protocol is `docs/paper/STAGE18H_PREREGISTRATION.md`.
`stage18h_spectral_residual_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, exact score-
support preservation, fixed flat/rare-object/periodic/noise, multiplicative-
scale and repeatability contracts, runtime diagnostics, and positions 1/8/15
preview. Do not tune or extend its working scale, spectrum, averaging,
smoothing, normalization, saliency variant, calibration, eligibility, or
integration family. The compact controller remains incumbent.

### Stage 18h spectral-residual context rejected; Stage 18i registered

The fixed spectral-residual proto-object membership failed its conjunctive
promotion rule on both development axes. On UDED selection, aggregate
F1/precision/recall and mean fold F1 changed by
`-0.000192/-0.000029/-0.000468/-0.000195`, with only `1/15` fold wins and
`5/15` eligible folds. Official BSDS500-validation ODS/OIS/AP changed by
`-0.000023/-0.000360/+0.000103`, failing the ODS margin and OIS non-collapse
condition. Exact support and all synthetic, multiplicative-scale,
repeatability, runtime, and fixed-preview contracts passed, but cannot
override the performance failures. The candidate is rejected; do not tune or
extend its working scale, spectrum, phase handling, spectral averaging,
smoothing, normalization, raster projection, saliency variants, calibration,
eligibility, or integration family. The compact controller remains incumbent.

The registered next action is `stage18i_generation2_mechanism_checkpoint`, a
live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
Stage 18h or earlier closed families, combine rejected cues, use dataset
identity, relax the cross-dataset rule, or use protected feedback.

## Stage 18i checkpoint closed; Stage 18j PMI dependency context registered

Live primary-source review selected Isola, Zoran, Krishnan, and Adelson's
image-internal pointwise-mutual-information boundary principle (ECCV 2014,
DOI `10.1007/978-3-319-10578-9_52`). Their central distinction is statistical
dependency rather than amplitude contrast: frequently co-occurring texture
pairs can remain strongly associated, whereas a rarer pair spanning an object
boundary has low PMI after correction for its marginals. The official
BSD-licensed source is pinned at commit
`ee2d76e98340313a8f92e1b65064a9b4ea90ac77`.

Stage 18j deliberately isolates the affinity principle before the author's
spectral clustering, avoiding a revisit of the closed Stage-16x globalization
family. The unchanged median-conditioned grayscale raster is serialized to
256 levels; one symmetric image-internal co-occurrence table is formed from
four centered pair axes with Laplace-one regularization. Density-corrected
`PMI_rho` uses the author-code exponent `1.25`, and bounded negative PMI is
the positive cue. The result enters only as one outer-training-fold-eligible
membership; compact Choquet aggregation and grayscale Scharr+NMS remain
unchanged. This is an equation-level repository surrogate, not an exact PMI
detector reproduction or a half-disc histogram contrast.

The authoritative protocol is `docs/paper/STAGE18J_PREREGISTRATION.md`.
`stage18j_pmi_dependency_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, exact score-
support preservation, fixed flat/step/checkerboard/noise, label-reassignment
and repeatability contracts, runtime diagnostics, and positions 1/8/15
preview. Do not tune or extend the intensity alphabet, pair geometry,
co-occurrence model, pseudocount, PMI, density convention, deficit mapping,
KDE, graph/spectral, calibration, or integration family. The compact
controller remains incumbent.

### Stage 18j PMI dependency context rejected; Stage 18k registered

The fixed image-internal PMI dependency-deficit cue passed its BSDS500-
validation criteria but failed the conjunctive UDED aggregate-F1 margin. UDED
aggregate F1/precision/recall and mean fold F1 changed by
`+0.000534/+0.002268/-0.002507/+0.000636`; it won `9/15` folds, was eligible
in `15/15`, and preserved exact score support, but the F1 gain remained below
the preregistered `+0.002`. Official BSDS500-validation ODS/OIS/AP improved by
`+0.005537/+0.002090/+0.009347`. Synthetic, statistical-invariance,
repeatability, runtime, and fixed-preview contracts passed, but all promotion
conditions were required. The fixed realization is rejected and compact
Choquet-gated grayscale Scharr+NMS remains incumbent.

The single registered next action is
`stage18k_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must choose exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule. It may
not tune Stage 18j or earlier closed families, combine rejected cues, use
dataset identity, relax the cross-dataset rule, or use protected feedback.

## Stage 18k checkpoint closed; Stage 18l image-torque context registered

Live primary-source review selected Nishigaki, Fermuller, and DeMenthon's
image-torque operator (CVPR 2012, DOI `10.1109/CVPR.2012.6247714`). Its
mid-level statistic is the signed moment of oriented edge tangents about a
patch center: random texture contributions tend to cancel, whereas extended
closed contours accumulate coherently. This supplies closure participation
rather than another intensity dependency, local activity, region partition,
graph, response-connection, or detector-fusion mechanism.

Stage 18l computes continuous Scharr-tangent torque at the paper's illustrated
`5x5`, `21x21`, and `45x45` square supports. Signed patch torque is divided by
its radial triangle-inequality bound, coherently backprojected to participating
edge samples, bounded analytically, and appended only as one outer-training-
fold-eligible membership. The paper's learned logistic boundary-strengthening
coefficients are excluded. Compact Choquet aggregation and grayscale
Scharr+NMS localization remain unchanged.

The authoritative protocol is `docs/paper/STAGE18L_PREREGISTRATION.md`.
`stage18l_image_torque_context` is registered with conjunctive UDED-selection
repeated CV and official BSDS500-validation criteria, exact score-support
preservation, fixed flat/closed-circle/open-step/checkerboard, polarity and
repeatability contracts, runtime diagnostics, and positions 1/8/15 preview.
Do not tune or extend the torque support, patch shape, oriented edge measure,
coherence, backprojection, learning, attention/segmentation, calibration, or
integration family. The compact controller remains incumbent.

### Stage 18l image-torque context rejected; Stage 18m registered

The fixed image-torque closure-support cue passed its official BSDS500-
validation criteria but failed the conjunctive UDED conditions. UDED aggregate
F1/precision/recall and mean fold F1 changed by
`+0.000573/-0.000342/+0.002149/+0.000483`, with `9/15` fold wins,
`15/15` eligibility, and exact score-support preservation. The aggregate-F1
gain remained below `+0.002`, and precision was negative. Official
BSDS500-validation ODS/OIS/AP improved by
`+0.003934/+0.001900/+0.012284`. Synthetic closure, polarity, repeatability,
runtime, support, and fixed-preview contracts passed, but all promotion
conditions were required. The fixed realization is rejected and compact
Choquet-gated grayscale Scharr+NMS remains incumbent.

The single registered next action is
`stage18m_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must choose exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule. It may
not tune Stage 18l or earlier closed families, combine rejected cues, use
dataset identity, relax the cross-dataset rule, or use protected feedback.

## Stage 18m checkpoint closed; Stage 18n sloped-facet break context registered

Live primary-source review selected Haralick's local sloped-facet statistical
edge principle (Computer Graphics and Image Processing 1980, DOI
`10.1016/0146-664X(80)90004-0`), with the fixed nested-regression statistic
from Chow (Econometrica 1960, DOI `10.2307/1910133`). Haralick's key
distinction is not raw gradient activity but whether opposing best-fitting
local planes differ beyond their within-region residual variation.

Stage 18n fits two disjoint `3x3` planar neighborhoods centered two pixels to
either side of each candidate under four fixed axes, compares them with one
pooled plane, maps the resulting F statistic by `F/(1+F)`, and takes the
maximum axis response. The bounded cue enters only as one outer-training-fold-
eligible membership. It is a fixed repository surrogate rather than an exact
reproduction of Haralick's iterative facet procedure; compact Choquet
aggregation and grayscale Scharr+NMS localization remain unchanged.

The authoritative protocol is `docs/paper/STAGE18N_PREREGISTRATION.md`.
`stage18n_facet_break_context` is registered with conjunctive UDED-selection
repeated CV and official BSDS500-validation criteria, exact score-support
preservation, flat/ramp/step/checkerboard/noise, photometric-invariance and
repeatability contracts, runtime diagnostics, and positions 1/8/15 preview.
Do not tune or extend its neighborhoods, axes, plane model, regression,
structural-break statistic, mapping, calibration, eligibility, or integration
family. The compact controller remains incumbent.

### Stage 18n sloped-facet structural-break context rejected; Stage 18o registered

The fixed facet-break cue failed its conjunctive promotion rule on both
development axes. UDED aggregate F1/precision/recall and mean fold F1 changed
by `-0.000162/-0.000171/-0.000138/-0.000130`; it won only `1/15` folds and
was eligible in only `2/15`. Official BSDS500-validation ODS/OIS/AP changed by
`-0.000021/+0.000078/+0.000098`, so the required ODS gain also failed. The
synthetic, photometric, repeatability, exact-support, runtime, and fixed-preview
contracts passed, but all promotion conditions were required. The fixed
realization is rejected and compact Choquet-gated grayscale Scharr+NMS remains
incumbent.

The single registered next action is
`stage18o_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must choose exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule. It may
not tune Stage 18n or earlier closed families, combine rejected cues, use
dataset identity, relax the cross-dataset rule, or use protected feedback.

## Stage 18o checkpoint closed; Stage 18p median OWA context registered

Live primary-source review selected Ronald Yager's ordered weighted averaging
framework (IEEE Transactions on Systems, Man, and Cybernetics 1988, DOI
`10.1109/21.87068`). The median is the fixed OWA whose sole nonzero ordered
weight selects the central input. This offers a bounded response to the recent
pattern of weak or ineligible single-cue additions: it adds no descriptor and
instead tests whether explicit majority support transfers better than the
incumbent Choquet context's arithmetic compensation.

Stage 18p sorts the unchanged five retained fold-calibrated memberships and
sets context to `x_(3)`. It deliberately omits singleton weights and the gamma
capacity only in the candidate aggregation, while the control remains the
unchanged distorted-Choquet controller. The fixed median differs from Stage
16r's capacity-limited Sugeno max-min integral and introduces no weight search,
quantifier, trim fraction, mixture, dataset identity, or rejected cue.

The authoritative protocol is `docs/paper/STAGE18P_PREREGISTRATION.md`.
`stage18p_median_owa_context` is registered with conjunctive UDED-selection
repeated CV and official BSDS500-validation criteria, exact algebraic and
score-support contracts, and a fixed positions 1/8/15 preview. Do not tune or
extend its OWA vector, order statistic, quantifier, trimming, weighting,
capacity, mixture, calibration, context gate, localizer, or thresholds. The
compact Choquet-gated grayscale Scharr+NMS controller remains incumbent.

### Stage 18p median OWA context rejected; Stage 18q registered

The fixed median OWA failed its conjunctive promotion rule on both development
axes. On UDED selection, aggregate F1/precision/recall and mean fold F1 changed
by `-0.001998/-0.001055/-0.003541/-0.001747`, with only `1/15` fold wins.
On official BSDS500 validation, ODS/OIS/AP changed by
`+0.000666/-0.000988/-0.012906`. The ODS change missed the required `+0.002`
margin and both OIS and AP violated their non-collapse conditions. The
finite/bounded, repeatability, monotonicity, idempotence, permutation,
central-order-statistic, exact-support, and fixed-preview contracts passed,
but all promotion conditions were required.

The candidate is rejected; do not tune or extend its OWA vector, quantifier,
order statistic, trimming, weighting, capacity, mixture, calibration, gate,
localizer, or thresholds, and do not advance to adaptive, weighted, learned,
spatial, image-conditioned, or cue-selected OWA variants. The compact Choquet-
gated grayscale Scharr+NMS controller remains incumbent. The local Windows
Berkeley matcher remains stochastic and reference-reproduction-unverified.

The registered next action is `stage18q_generation2_mechanism_checkpoint`, a
live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification under a
preregistered joint UDED/BSDS rule. It may not tune Stage 18p or earlier closed
families, combine rejected cues, use dataset identity, relax the cross-dataset
rule, or use protected feedback.

## Stage 18q checkpoint closed; Stage 18r polarity-continuation context registered

Live primary-source review selected one fixed contrast-sign grouping test from
Geisler and Perry's natural-contour statistics (Visual Neuroscience 2009, DOI
`10.1017/S0952523808080875`). Their measurements and ideal-observer analysis
show that edge-element geometry and contrast polarity jointly inform contour
grouping. Stage 18r isolates that mechanism without reproducing their learned
statistics: signed unit Scharr gradients are sampled symmetrically along the
local tangent at fixed offsets `1/2/4`, and each offset requires positive
polarity/orientation alignment on both tangent sides. The three bilateral
supports are averaged into one bounded positive membership.

This is distinct from signless tensor coherence, the Stage-14r unoriented-
polarity SE(2) lift, binary EDPF chains, patch torque/closure, and Stage 14b's
placement of anti-texture evidence. It does not link or diffuse contours, add a
graph, replace localization, or combine rejected cues. The compact bank,
Choquet gamma `0.55`, gate strength `2.0`, floor `0.10`, median conditioning,
grayscale Scharr+NMS, and fold fitting remain unchanged.

The authoritative protocol is `docs/paper/STAGE18R_PREREGISTRATION.md`.
`stage18r_polarity_continuation_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, exact score-
support preservation, fixed synthetic polarity/photometric/rotation contracts,
runtime diagnostics, and positions 1/8/15 preview. Do not tune or extend its
offsets, gradients, sign convention, interpolation, bilateral rule, scale
fusion, calibration, integration, grouping, completion, graph, context, gate,
localizer, or thresholds. The compact controller remains incumbent.

### Stage 18r polarity-continuation context rejected; Stage 18s registered

The fixed signed-gradient contrast-polarity continuation membership was
training-ineligible in all `15/15` UDED-selection folds: its training
edge-versus-texture AUC remained below the preregistered `0.56` threshold, so
the candidate exactly reduced to compact MFI and all UDED aggregate and fold
metrics were unchanged. Official BSDS500-validation ODS/OIS/AP changed by
`-0.000044/-0.000018/+0.000101`, failing the required ODS gain and OIS
non-collapse condition. The synthetic polarity, photometric, rotation,
repeatability, exact-support, runtime, and fixed-preview contracts passed, but
all promotion conditions were required.

The candidate is rejected; do not tune or extend its tangent offsets,
gradients, sign convention, interpolation, bilateral support, scale fusion,
calibration, eligibility, integration, context, gate, localizer, or thresholds,
and do not advance to association-field, completion, diffusion, graph, color,
multiscale, or learned-polarity variants from this result. The compact Choquet-
gated grayscale Scharr+NMS controller remains incumbent.

The single registered next action is
`stage18s_generation2_mechanism_checkpoint`, a live-primary-literature
escalation that must choose exactly one mechanistically distinct bounded
generation-2 falsification under a preregistered joint UDED/BSDS rule. It may
not tune Stage 18r or earlier closed families, combine rejected cues, use
dataset identity, relax the cross-dataset rule, or use protected feedback.

## Stage 18s checkpoint closed; Stage 18t isotonic membership calibration registered

The checkpoint added neither another descriptor nor another localizer. The
repeated weakness or complete training ineligibility of isolated positive cues
instead motivated a direct test of the retained membership semantics. Zadrozny
and Elkan (KDD 2002, DOI `10.1145/775047.775151`) showed that an ordered score
can be calibrated by isotonic regression without assuming a sigmoid, while
Niculescu-Mizil and Caruana (ICML 2005, DOI
`10.1145/1102351.1102430`) emphasized leakage-separated calibration and the
different distortions addressed by sigmoid and isotonic maps.

Stage 18t computes the unchanged five sigmoid memberships, then fits one
class-balanced weighted pool-adjacent-violators map per membership using only
the current outer UDED training fold's edge-versus-texture samples. Exact score
ties are aggregated, the fitted map is piecewise constant and nondecreasing,
and out-of-range values use the nearest terminal block. The calibrated values
replace only the five membership marginals before unchanged distorted-Choquet
aggregation. This is not Stage 14m's multivariate logistic fusion and is not
Stage 16p's label-free within-image rank normalization.

The authoritative preregistration is
`docs/paper/STAGE18T_PREREGISTRATION.md`. The registered experiment is
`stage18t_isotonic_membership_calibration`, with UDED-selection 5x3
leakage-free CV, official BSDS500-validation attachment, exact positive-score
support preservation, deterministic PAV contracts, and the fixed positions
1/8/15 preview. Promotion remains conjunctive. No calibration form, class
weight, label, feature, capacity, aggregation, gate, localizer, or threshold
may be tuned from the result. The compact controller remains incumbent.

### Stage 18t isotonic membership calibration rejected; Stage 18u registered

The fixed per-membership weighted isotonic calibration failed its conjunctive
promotion rule. On UDED selection, aggregate F1/precision/recall and mean fold
F1 changed by `+0.000574/+0.000822/+0.000110/+0.000676`, with `11/15` fold
wins. The precision, recall, mean-fold, and fold-win conditions passed, but the
aggregate F1 gain missed the required `+0.002` margin. Official BSDS500-
validation ODS/OIS/AP changed by `+0.001623/+0.000700/+0.003573`; OIS and AP
were nonnegative, but ODS missed its required `+0.002` margin. All
non-performance contracts passed, but every condition was required.

The candidate is rejected. Do not tune or extend its class weights, labels,
samples, PAV loss, ties, extrapolation, smoothing, shrinkage, splines,
calibration family, feature selection, weights, capacity, aggregation, gate,
localizer, or thresholds, and do not combine it with rejected cues. The compact
Choquet-gated grayscale Scharr+NMS controller remains incumbent. The local
Windows Berkeley matcher remains stochastic and reference-reproduction-
unverified.

The registered next action is `stage18u_generation2_mechanism_checkpoint`, a
live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification under a
preregistered joint UDED/BSDS rule. It may not tune Stage 18t or earlier closed
families, combine rejected cues, use dataset identity, relax the cross-dataset
rule, or use protected feedback.

### Stage 18u checkpoint closed; Stage 18v relative-variation context registered

Live primary-source review selected Xu et al.'s windowed inherent-versus-total
variation principle (ACM TOG 2012, DOI `10.1145/2366145.2366158`). Signed
gradients reinforce through one coherent structural transition but cancel in
oscillatory texture, unlike signless tensor energy or the closed bilateral
polarity-continuation test. The public author implementation fixes sigma `3`
and a 15-sample Gaussian support.

Stage 18v computes horizontal/vertical forward differences on the unchanged
median-conditioned grayscale image and forms the bounded ratio
`(|G*dx|+|G*dy|)/(G*|dx|+G*|dy|)`, with zero at zero total variation. The cue
enters only as one outer-training-fold-eligible positive membership. It does
not run RTV smoothing or change the compact bank, distorted-Choquet capacity,
gate, Scharr+NMS localizer, or threshold fitting.

The authoritative preregistration is
`docs/paper/STAGE18V_PREREGISTRATION.md`. The registered experiment is
`stage18v_relative_variation_context`, with conjunctive UDED-selection 5x3
leakage-free CV and official BSDS500-validation criteria, exact score-support
preservation, fixed synthetic/photometric contracts, runtime diagnostics, and
the positions 1/8/15 preview. No derivative, window, scale, ratio, smoothing,
calibration, or integration variant may be tuned from the result. The compact
Choquet-gated grayscale Scharr+NMS controller remains incumbent.

### Stage 18v relative-variation context rejected; Stage 18w registered

The fixed signed-gradient coherence ratio was training-ineligible in all
`15/15` UDED-selection folds (training AUC remained below `0.56`), so the
candidate exactly reduced to compact MFI and all UDED metrics were unchanged.
Official BSDS500-validation ODS/OIS/AP changed by
`+0.000016/+0.000554/+0.000107`; the ODS gain missed the required `+0.002`
margin. Synthetic, photometric-invariance, repeatability, exact-support,
runtime, and fixed-preview contracts passed, but every promotion condition was
required.

The candidate is rejected. No derivative, window, scale/support, boundary,
ratio, zero rule, calibration, eligibility, integration, RTV smoothing, or
total-variation variant may be tuned or combined from this result. Compact
Choquet-gated grayscale Scharr+NMS remains incumbent. The single registered
next action is `stage18w_generation2_mechanism_checkpoint`, a live-primary-
literature escalation that must choose exactly one mechanistically distinct
bounded generation-2 falsification under a preregistered joint UDED/BSDS rule,
without protected feedback or relaxation of the cross-dataset gate.

## Stage 18w checkpoint closed; Stage 18x Teager-energy context registered

Live primary-source review selected Boudraa and Diop's 2-D Teager-Kaiser
quadratic energy formulation (ICIP 2008, DOI
`10.1109/ICIP.2008.4712471`) as one mechanistically distinct local nonlinear-
activity test. Its axial Type-1A and diagonal Type-1B stencils compare squared
center intensity with symmetric-neighbor products. Stage 18x rectifies their
positive responses and uses a fixed geometric consensus divided by the
analytic bound. Requiring both stencils suppresses one-stencil lattice
activity without adding smoothing, a learned parameter, or a rejected cue.

The authoritative protocol is `docs/paper/STAGE18X_PREREGISTRATION.md`.
`stage18x_teager_energy_context` is registered with conjunctive UDED-selection
5x3 leakage-free CV and official BSDS500-validation criteria, exact score-
support preservation, fixed synthetic and quadratic-scale contracts, runtime
diagnostics, and positions 1/8/15 preview. The compact bank, distorted-
Choquet gamma `0.55`, gate strength `2.0`, floor `0.10`, median conditioning,
grayscale Scharr+NMS, and threshold fitting remain unchanged. This is an
equation-level repository adaptation, not the paper's contrast-enhancement
pipeline. Do not tune or extend TKEO stencils, fusion, higher-order energy,
demodulation, contrast enhancement, calibration, or integration from the
result. The compact controller remains incumbent.

### Stage 18z fold-fitted ICA sparse context rejected; Stage 19a registered

The fixed unlabeled FastICA response-concentration membership was training-
ineligible in all `15/15` UDED-selection folds: training AUC remained below
the preregistered `0.56` threshold. The candidate therefore reduced exactly
to compact MFI, with zero change in aggregate F1, precision, recall, mean fold
F1, and fold wins. Official BSDS500-validation ODS/OIS/AP changed by
`-0.000056/+0.000027/+0.000074`, failing the required `+0.002` ODS margin.
The deterministic fit, convergence, whitening, orthogonality, synthetic,
positive-affine, exact-support, runtime, model-hash, and fixed-preview
contracts passed, but cannot override the performance failures.

The candidate is rejected. Do not tune or extend ICA patch sampling,
whitening, component count, solver, nonlinearity, response concentration,
calibration, eligibility, or integration, and do not advance to sparse coding,
overcomplete dictionaries, independent subspaces, color/multiscale ICA,
supervised atom selection, classifiers, or neural implementations from this
result. Compact Choquet-gated grayscale Scharr+NMS remains incumbent. The
single registered next action is `stage19a_generation2_mechanism_checkpoint`,
a live-primary-literature escalation that must choose exactly one
mechanistically distinct bounded generation-2 falsification under a
preregistered joint UDED/BSDS rule without protected feedback or relaxation
of the cross-dataset gate.

### Stage 19a transition closed; Stage 19b descriptor atlas registered

The user-directed policies `automation/STAGE19_GT_GUIDED_POLICY.md` and
`docs/paper/STAGE19_GT_GUIDED_PROGRAM.md` supersede the generic open-ended
mechanism fallback for this bounded phase. The remaining budget is exactly
three Stage-19 analysis experiments and at most four Stage-20 candidate
experiments. Stage 19E must freeze the full ordered Stage-20 queue before any
candidate outcome is inspected; the queue cannot be expanded or replaced
after failures. Four failed candidates stop the campaign for synthesis.

`stage19b_descriptor_relevance_atlas` is registered as analysis experiment 1
of 3. It reconstructs the frozen pool of the five incumbent raw cues plus
structure tensor, brightness entropy, patch recurrence, semi-global
change-point, Frei-Chen, PMI, and image-torque evidence. It reads only pinned
BSDS500-train image/GT blobs and preserves individual annotators. UDED
selection is screened against pinned BSDS tree identifiers before GT-guided
analysis; `03-35028` is excluded because it names BSDS-test image `35028`.
Only filenames, not protected BSDS val/test image or GT bytes, are used for
that screen.

The atlas preregisters deterministic uniform within-image sampling, exact and
fixed `0.0075`-diagonal tolerant target views, per-image AUC/AP/nonparametric
dependence/effect statistics, a 1000-replicate image bootstrap, empirical
monotone probability curves, annotator-consensus strata, and runtime records.
The qualitative artifact uses sorted BSDS-train positions 1, 100, and 200 with
panel order input, mean human GT, then the twelve frozen descriptor maps. The
official manifest is train-only and incumbent-only because Stage 19B creates
no candidate detector map. No cue selection, detector promotion, BSDS-
validation read, architecture change, or thirteenth descriptor is permitted.

### Stage 19b descriptor atlas complete; Stage 19c registered

Stage 19B completed on the preregistered 200 pinned BSDS500-train images and
14 overlap-clean UDED-selection images. The overlap manifest again excluded
`03-35028` by filename lineage without reading protected BSDS image or GT
bytes. All twelve frozen cues had positive mean tolerant-union rank-biserial
association in both domains. Structure-tensor coherence had the highest mean
tolerant-union ROC-AUC in both BSDS train (`0.774285`, 95% image-bootstrap CI
`0.760020--0.788168`) and overlap-clean UDED (`0.910701`, CI
`0.887902--0.932764`). This univariate ranking is descriptive only: the
registered Stage-19B rule forbids cue selection, promotion, or architecture
change.

The incumbent-only official BSDS-train attachment completed with ODS/OIS/AP
`0.535481/0.574794/0.514450`. There was no candidate comparison; the score is
development provenance and retains the Stage-15a stochastic/reference-
unverified evaluator caveat.

`stage19c_pairwise_complementarity` is registered as analysis experiment 2 of
3 under `docs/paper/STAGE19C_PREREGISTRATION.md`. It preserves the twelve-cue
pool, Stage-19B sampling/overlap firewall, and image grouping. It measures
per-image Spearman redundancy, conditional information against incumbent
cues, and additive-versus-bilinear pairwise logistic gains. The fixed
same-direction, chance-floor, bilateral-correlation, and bilateral-conditional-
gain rules produce a shortlist capped at six for Stage 19D. BSDS validation,
protected blobs, higher-order searches, detector promotion, and MFI changes
remain forbidden.

### Stage 19c pairwise complementarity complete; Stage 19d registered

Stage 19C completed its pairwise-only analysis on the preregistered 200
BSDS500-train images and 14 overlap-clean UDED-selection images. The frozen
shared-relevance/redundancy rule retained, in order, structure-tensor
coherence, `gabor4_s13`, semi-global change-point evidence, `hessian_s13`,
brightness entropy, and `gabor4_s5`. Frei-Chen edge-subspace evidence was the
only rule-pruned descriptor, because it was bilaterally redundant with the
higher-ranked brightness-entropy cue without the required bilateral additive
gain. These results freeze an analysis shortlist only and do not change the
detector.

The incumbent-only official BSDS-train attachment recorded ODS/OIS/AP
`0.535462/0.574704/0.514451`. It supplies development provenance but no
candidate comparison and retains the stochastic/reference-reproduction caveat.

`stage19d_aggregation_identification` is registered under
`docs/paper/STAGE19D_PREREGISTRATION.md` as experiment 3 of 3. Using the frozen
six-cue shortlist, it compares exactly the fixed incumbent distorted-Choquet
context, monotone nonnegative additive/logistic aggregation, and a constrained
monotone 2-additive Choquet model. BSDS validation, protected blobs, family
expansion, descriptor replacement, detector promotion and architecture change
remain forbidden.

### Stage 19d aggregation identification complete; Stage 19e registered

Stage 19D completed on 200 BSDS500-train images and the identical 14-image
overlap-clean UDED-selection manifest, with image-grouped fitting and no
BSDS500-validation or protected-blob read. The monotone 2-additive Choquet
family was the preregistered winner: its weaker-domain mean class-balanced log
loss was `0.540647`, weaker-domain ROC-AUC was `0.822024`, and it did not meet
the transfer-collapse definition. The fixed distorted-Choquet control ranked
second among non-collapsed families. The additive/logistic family had strong
within-domain ranking but was classified as transfer-collapsed by the frozen
rule. These are family-identification results only; no detector was promoted.

The incumbent-only official BSDS500-train attachment recorded ODS/OIS/AP
`0.535458/0.574768/0.514449`. It provides development provenance, not a
candidate comparison, and retains the stochastic/reference-reproduction
caveat.

`stage19e_stage20_queue_freeze` is registered as the required planning-only
synthesis checkpoint. It must use only the completed Stage-19B-D artifacts to
freeze the full ordered Stage-20 queue, capped at four candidates, and fully
preregister every candidate before Stage 20A executes. No later failure may
replace a queued candidate, no fifth candidate may be added, and exhausting
the queue without promotion ends in synthesis rather than open-ended
literature escalation. Compact MFI remains unchanged.

### Stage 19e closure - complete Stage-20 queue frozen; Stage 20a registered

Stage 19E completed without reading BSDS500 validation or any protected
image/GT blob. The complete four-entry queue is frozen in
`automation/stage20_frozen_queue.json` and fully specified by
`docs/paper/STAGE20_QUEUE_PREREGISTRATION.md`. Every entry uses the Stage-19D
winning monotone 2-additive Choquet family. In order, the descriptor sets are:
the complete six-cue Stage-19C shortlist; the four-cue shared-interaction core;
the dominant `gabor4_s13`/semi-global-change-point pair; and the retained
compact five-member bank as an aggregation-only fallback. The transfer-
collapsed additive/logistic family is excluded.

All candidates share one immutable fitting and evaluation contract. Membership
maps and the constrained capacity are fitted inside each outer overlap-clean
UDED fold; the known `03-35028`/BSDS-test-35028 lineage item is not read. The
official BSDS500-validation exporter fits once on all 14 overlap-clean UDED
selection images and reads no BSDS GT. Promotion remains conjunctive across
UDED repeated CV, completed official BSDS validation, fit/support contracts,
and the deterministic positions 1/7/14 preview. No outcome may change the
remaining queue. `stage20a_full_shortlist_2additive_choquet` is the sole next
action; compact distorted-Choquet MFI remains incumbent.

### Stage 20a closure - full shortlist rejected; Stage 20b registered

Stage 20A completed under the frozen queue contract. The full six-cue
2-additive Choquet candidate passed the complete overlap-clean UDED gate:
aggregate F1 changed by `+0.007589`, precision by `+0.013213`, recall by
`-0.002227`, and mean fold F1 by `+0.006121`, with `13/15` fold wins. All 15
capacity fits converged and the candidate preserved incumbent score support.

The official BSDS500-validation attachment improved ODS from `0.545428` to
`0.552830` (`+0.007402`) and OIS from `0.579569` to `0.583281`
(`+0.003711`), but AP fell from `0.534292` to `0.490363` (`-0.043929`). The
preregistered rule required nonnegative AP as part of a conjunction, so the
candidate is rejected despite its strong UDED and ODS/OIS results. The fixed
positions 1/7/14 preview and all runtime, capacity, per-fold, and per-image
artifacts are complete. The Windows matcher remains stochastic and reference-
reproduction-unverified, as previously documented.

No Stage-20 entry or parameter changes from this result. Compact MFI remains
incumbent, and `stage20b_interaction_core_2additive_choquet`, the already-
frozen four-cue interaction-core candidate, is the sole next action.

### Stage 20b closure - interaction core rejected; Stage 20c registered

Stage 20B completed under the immutable queue contract. The four-cue
2-additive Choquet candidate passed the full overlap-clean UDED gate:
aggregate F1 changed by `+0.007539`, precision by `+0.013211`, recall by
`-0.002354`, and mean fold F1 by `+0.006079`, with `13/15` fold wins. All
15 capacity fits converged, predictions were finite and bounded, and score
support exactly matched the incumbent. The fixed positions 1/7/14 preview and
the registered capacity, runtime, fold, and per-image artifacts are complete.

The official BSDS500-validation attachment improved ODS from `0.545448` to
`0.552777` (`+0.007330`) and OIS from `0.579486` to `0.583664`
(`+0.004178`), but AP fell from `0.534298` to `0.490359` (`-0.043939`).
Because nonnegative AP is mandatory in the preregistered conjunction, the
candidate is rejected. The Windows matcher remains stochastic and reference-
reproduction-unverified, as already documented.

This second consecutive Stage-20 candidate shows the same strong UDED and
ODS/OIS movement with a large AP loss, but the frozen campaign forbids using
that outcome to alter calibration, capacity fitting, descriptors, or queue
order. Compact MFI remains incumbent. The sole next action is the already-
frozen candidate 3/4, `stage20c_dominant_pair_2additive_choquet`; Stage 20D
remains unchanged and no replacement or fifth candidate is permitted.

### Stage 20c closure - dominant pair rejected; Stage 20d registered

Stage 20C completed under the immutable queue contract. The two-cue
`gabor4_s13`/semi-global-change-point 2-additive Choquet candidate passed the
full overlap-clean UDED gate: aggregate F1 changed by `+0.008839`, precision
by `+0.011107`, recall by `+0.004564`, and mean fold F1 by `+0.006457`, with
`12/15` fold wins. All 15 capacity fits converged, predictions were finite and
bounded, and score support exactly matched the incumbent. The fixed positions
1/7/14 preview and registered capacity, runtime, fold, and per-image artifacts
are complete.

The official BSDS500-validation attachment improved ODS from `0.545407` to
`0.559712` (`+0.014305`) and OIS from `0.579200` to `0.588014`
(`+0.008814`), but AP fell from `0.534293` to `0.508071` (`-0.026222`).
Because nonnegative AP is mandatory in the preregistered conjunction, the
candidate is rejected. The Windows matcher remains stochastic and reference-
reproduction-unverified, as already documented.

Compact MFI remains incumbent, and no Stage-20 parameter or queue entry may
change from this result. The sole next action is the already-frozen final
candidate, `stage20d_incumbent_bank_2additive_choquet`. If it fails, the
bounded four-candidate program ends in synthesis without automatic literature
escalation, replacement, or a fifth candidate.

### Stage 20d closure - incumbent-bank 2-additive candidate rejected; bounded program complete

Stage 20D completed under the immutable queue contract. The retained five-cue
bank with fold-fitted monotone 2-additive Choquet aggregation passed the full
overlap-clean UDED gate: aggregate F1 changed by `+0.008531`, precision by
`+0.014096`, recall by `-0.001226`, and mean fold F1 by `+0.007238`, with
`15/15` fold wins. All 15 capacity fits converged, predictions were finite and
bounded, and score support exactly matched the incumbent. The fixed positions
1/7/14 preview and registered capacity, runtime, fold, and per-image artifacts
are complete.

The official BSDS500-validation attachment changed ODS from `0.545424` to
`0.543849` (`-0.001575`), OIS from `0.579470` to `0.575774`
(`-0.003695`), and AP from `0.534298` to `0.530463` (`-0.003835`). It
therefore failed the registered ODS, OIS, and AP requirements and is rejected.
The Windows matcher remains stochastic and reference-reproduction-unverified,
as already documented.

The complete four-entry queue is exhausted without promotion. All four
2-additive candidates improved overlap-clean UDED aggregate F1 by more than the
registered margin. The three pruned Stage-19 cue sets improved official
BSDS500-validation ODS/OIS but lost AP; the aggregation-only compact-bank
fallback regressed ODS/OIS/AP. This supports a narrow conclusion: the
Stage-19D-identified 2-additive family fitted under this frozen contract is
useful for the UDED operating-point objective but does not satisfy joint
cross-domain ranking transfer. It does not justify post-hoc calibration,
capacity, descriptor, or threshold changes. Compact distorted-Choquet MFI
remains incumbent. In accordance with Stage 19E, there is no Stage 20E,
replacement candidate, or automatic literature escalation; the bounded
program ends in synthesis without reaching the long-horizon SOTA goal.

### Stage 21 activation and Stage 21A protocol certification registered

The user-directed Stage-21 bounded program supersedes the Stage-20 synthesis
stop without reopening its queue. Stages 21A--21G are protocol-certification
and frozen-output diagnostics; only Stage 21H may preregister at most one new
causally justified mechanism after those diagnostics. Compact distorted-
Choquet MFI remains the incumbent.

Live primary-source review separated three evaluation endpoints. The primary
Berkeley path remains all-annotation one-to-one `correspondPixels` with 99
thresholds, `maxDist=0.0075`, and thinning. Berkeley `maxDist=0.025` is only a
parameter-matched sensitivity track. Estrada--Jepson `0.025` is a distinct
directional matcher used by the target fuzzy literature and must not be called
Berkeley matching or used for promotion.

Stage 21A is preregistered in
`docs/paper/STAGE21A_PROTOCOL_CERTIFICATION_PREREGISTRATION.md`. It audits the
pinned Berkeley sources and reuses, without rerunning, Stage-15a's fixture and
causal RNG evidence. Reference reproduction remains false because the official
matcher requests a clock seed, consumes randomized sampling, and the shipped
fixture omits RNG provenance; the fixed-seed binary remains forbidden for
dataset scoring. A committed Berkeley `0.025` config must differ from standard
only in `max_dist`.

For the fuzzy track, the target paper points to KITT. The public pinned KITT
v1.01 matcher calls an absent helper beyond its one-pixel bootstrap, while the
same immutable tree ships the complete v1.00 implementation as a backup.
Stage 21A therefore hash-verifies the tree and executes a byte-identical,
filename-compatible runtime copy of that complete backup on fixed exact,
offset, competition, crossing, tolerance-boundary, and multi-annotator
micro-cases. This is best-public-source fidelity, not a claim of identity with
an unpublished paper-private copy. No dataset or detector is run. Only a pass
of the complete Stage-21A stop rule may advance to Stage 21B.

The first Stage-21A execution failed before creating a result artifact. The
MATLAB micro-case harness initialized `cases` as fieldless `struct([])` and
then attempted to assign the first populated `runCase` record into it, causing
MATLAB's dissimilar-structure assignment error. No BSDS split or detector was
read or scored, and the failure supplies no evaluator evidence. A harness-only
retry is registered after initializing `cases` directly from that unchanged
first record; sources, hashes, cases, tolerances, protocol interpretations,
and stop rules are unchanged. Stage 21B remains deferred.

### Stage 21A closure and Stage 21B registration

The harness-only retry completed the full Stage-21A stop rule without reading
a BSDS split or scoring a detector. The standard Berkeley source audit
confirmed `nthresh=99`, `maxDist=0.0075`, thinning, all-annotation
accumulation, and one-to-one matching. Reference reproduction remains
unverified for the exact causal reason established in Stage 15A: the pinned
matcher clock-seeds random k-of-n sampling, the shipped fixture records no RNG
state, and the unmodified Windows path misses the registered `1e-4` bound. A
fixed-seed diagnostic is repeatable but neither reproduces the shipped tables
nor is permitted for dataset scoring.

The Berkeley `0.025` configuration differs only in `max_dist`. The distinct
Estrada--Jepson `0.025` track passed every registered micro-case using the
byte-identical complete KITT v1.00 backup at pinned commit
`d70bb66ef9ab6f5cea8ead528fe5ac15ac096baf`. Its status is explicitly
best-public-source fidelity, not equivalence to an unpublished private copy.

The registered next action is
`stage21b_three_protocol_retrospective_benchmark`, governed by
`docs/paper/STAGE21B_PREREGISTRATION.md`. It hashes and rescores only the
frozen incumbent and Stage-20A--D validation maps under three separately
reported tracks. Neither loose-tolerance track may promote a model or be
conflated with the other; Stage 21B fits no detector and cannot alter MFI.

### Stage 21B first launch timed out; resumable continuation registered

The first Stage-21B launch exhausted the six-hour controller limit after
completing all five Berkeley-standard methods and preserving the Berkeley
`0.025` incumbent plus all 100 per-image match tables for Stage 20A. It did
not produce the Berkeley `0.025` aggregate table, the Estrada--Jepson track,
cross-protocol deltas, or a final summary, so no Stage-21B scientific
interpretation is made from the partial output. The separate default official
attachment also timed out and supplies no additional conclusion.

`stage21b_three_protocol_retrospective_retry1` is an attachment-only
continuation. The harness now reuses completed aggregate files, collects
complete per-image match sets without rematching them, resumes only missing
Berkeley matches, and checkpoints Estrada--Jepson results per frozen method.
Frozen PNG bytes, matcher sources, thresholds, tolerances, ground truth,
protocol definitions, preview positions, and non-promotional interpretation
are unchanged. Stage 21C remains deferred until Stage 21B fully completes.

### Stage 21B retry 1 timed out after completing Stage-20B match tables

The first resumable continuation again reached the controller limit, but it
made durable progress: all 100 nonempty Berkeley-`0.025` per-image match tables
for Stage 20B now exist. Its aggregate summary and the remaining loose-
Berkeley/Estrada--Jepson outputs are still absent, so there is still no complete
Stage-21B scientific result and the partial metrics are not interpreted.

`stage21b_three_protocol_retrospective_retry2` is registered as the same
attachment-only continuation. It will collect the complete Stage-20B tables
without rematching them and resume only missing later work. Frozen map bytes,
protocols, matcher code, thresholds, tolerances, fidelity caveats, preview, and
non-promotional rules remain unchanged. Stage 21C remains deferred.

### Stage 21B retry 2 timed out after completing Stage-20C match tables

The second resumable continuation again reached its execution limit, but all
100 nonempty Berkeley-`0.025` per-image match tables for Stage 20C are now
preserved. The Stage-20C aggregate collection, Stage-20D loose matching, the
Estrada--Jepson track, cross-protocol deltas, and final summary are still
absent. Therefore no partial metric is interpreted as a Stage-21B result.

`stage21b_three_protocol_retrospective_retry3` is registered as the unchanged
attachment-only continuation. It collects complete Stage-20C tables without
rematching and resumes only missing later frozen-method work. Frozen maps,
protocol definitions, matcher code, thresholds, tolerances, fidelity caveats,
preview, and non-promotional rules remain unchanged. Stage 21C stays deferred.

### Stage 21B retry 3 timed out after completing Stage-20D match tables

The third resumable continuation again reached its execution limit, but all
100 nonempty Berkeley-`0.025` per-image match tables for Stage 20D are now
preserved. The complete loose-Berkeley aggregate table, Estrada--Jepson track,
cross-protocol deltas, and final summary are still absent. No partial metric is
therefore interpreted as a Stage-21B result.

`stage21b_three_protocol_retrospective_retry4` is registered as the unchanged
attachment-only continuation. It collects the now-complete loose-Berkeley
track without rematching and resumes only missing Estrada--Jepson frozen-method
work. Frozen maps, protocols, matcher code, thresholds, tolerances, fidelity
caveats, preview, and non-promotional rules remain unchanged. Stage 21C stays
deferred.

### Stage 21B retry 4 timed out after two Estrada--Jepson methods

The fourth continuation completed and preserved the full five-method
Berkeley-`0.025` table and complete 99-threshold Estrada--Jepson grids for the
incumbent and Stage 20A. It timed out while processing Stage 20B, before the
remaining three grids or any final Stage-21B summary existed. The partial
protocol result is still not interpreted scientifically.

`stage21b_three_protocol_retrospective_retry5` is registered as an unchanged
attachment-only continuation. A harness-only repair now atomically checkpoints
each completed Estrada--Jepson threshold so controller timeouts cannot discard
hours of identical frozen-map matching. Existing complete grids are reused;
maps, matcher, thresholds, tolerance, annotation handling, aggregation,
fidelity caveats, and non-promotional rules are unchanged. Stage 21C remains
deferred until all registered Stage-21B outputs exist.

### Stage 21B retry 5 timed out after completing Stage-20B and Stage-20C fuzzy grids

The fifth continuation reached the controller limit, but its atomic threshold
checkpoints preserved complete 99-threshold Estrada--Jepson grids for Stage 20B
and Stage 20C. Together with the earlier incumbent and Stage-20A grids, only
the frozen Stage-20D fuzzy grid remains. The fuzzy-comparison table,
cross-protocol table, and final summary are still absent, so the partial
protocol outputs receive no standalone scientific interpretation.

`stage21b_three_protocol_retrospective_retry6` is registered as the unchanged
attachment-only continuation. It reuses all completed Berkeley and
Estrada--Jepson outputs and resumes only Stage 20D, retaining threshold-level
checkpoints. Frozen maps, matcher code, thresholds, tolerance, annotation
handling, aggregation, fidelity caveats, and non-promotional rules are
unchanged. Stage 21C remains deferred until Stage 21B completes.

### Stage 21B three-protocol retrospective complete; Stage 21C registered

The sixth continuation completed the final Stage-20D Estrada--Jepson grid and
wrote every registered Stage-21B table, full PR artifact, map-hash record,
summary, and fixed positions 1/50/100 preview. The outer official-evaluation
wrapper timed out only after the runner emitted its success marker; the
experiment's own summary is complete, so no further attachment retry is
scientifically required.

Under standard Berkeley `maxDist=0.0075`, Stage 20C was the strongest frozen
candidate by ODS/OIS (`0.559695/0.587638`) but remained below the incumbent in
AP (`0.508080` versus `0.534292`). Increasing Berkeley tolerance to `0.025`
raised every method substantially; Stage 20C reached ODS/OIS/AP
`0.695163/0.738162/0.661288`, while the incumbent reached
`0.681956/0.729451/0.700661`. The tolerance gain therefore does not remove the
candidate's AP deficit. Under the separate best-public-KITT
Estrada--Jepson-`0.025` track, Stage 20C had the highest best-threshold F
(`0.688486`) versus incumbent `0.674182`. These fuzzy-protocol numbers are
non-promotional and not numerically interchangeable with Berkeley metrics.
Berkeley reference reproduction remains unverified because the shipped
fixture's clock-seeded RNG state is unavailable.

The registered next action is `stage21c_pr_ap_anatomy`. It consumes only the
frozen Stage-21B Berkeley-standard counts and exact map bytes to quantify PR
crossings, precision at fixed recall, AP area by recall band, predicted-edge
density by threshold, and per-image operating-point/AP changes. It fits no
detector, reruns no matcher, reads no protected split, and cannot promote a
model.

### Stage 21C first launch stopped on NumPy API compatibility

The first Stage-21C launch stopped before writing any result artifact because
the installed NumPy no longer exposes the legacy `trapz` alias used for the
registered trapezoidal PR integrations. No detector, map, matcher, benchmark,
or protected split was run or read, so this supplies no scientific feedback.
`stage21c_pr_ap_anatomy_retry1` is registered as a harness-only retry using
NumPy's current `trapezoid` spelling for the identical calculation. Inputs,
diagnostic endpoints, maps, protocol, preview, and reference-unverified status
remain unchanged; Stage 21D stays deferred until Stage 21C completes.

### Stage 21C PR/AP anatomy complete; Stage 21D registered

The dependency-compatible retry completed every frozen-map diagnostic and the
fixed positions 1/50/100 preview without fitting a detector or rerunning a
matcher. Stage 20C's precision envelope exceeded the incumbent at recall
`0.25/0.50/0.75/0.90` by about
`+0.01277/+0.01695/+0.02271/+0.02230`. Its common-range envelope-area contrast
was also positive (`+0.00643`), but its lowest-recall `[0,0.25]` contribution
was lower by about `-0.00688`, and official raw-curve AP remained lower by
about `-0.02620`. Thus the operating-point gain is not simply a uniformly
worse envelope: the AP loss is especially sensitive to the earliest ranking
region and to raw threshold-curve ordering that an optimistic monotone envelope
can hide. Diagnostic per-image envelope area improved on 85/100 images for
Stage 20C, reinforcing that this quantity is not interchangeable with official
aggregate AP.

The required official attachment independently rescored the incumbent and
Stage 20C under the same standard configuration and reproduced the qualitative
contrast: Stage 20C changed ODS/OIS/AP by
`+0.01431/+0.00849/-0.02620`. Its small numeric drift from the earlier frozen
table is consistent with the already documented clock-seeded Windows matcher;
`reference_reproduction_verified=false` remains mandatory.

The registered next action is `stage21d_ranking_localization_diagnosis`. It
uses only exact frozen PNGs, the already reported ODS thresholds, and BSDS500
validation annotations to measure descriptive pixel ranking, bidirectional
GT/prediction distances, support at the two fixed tolerances, and a clearly
labeled near-GT multiplicity surrogate. It does not rerun the matcher, refit a
model, read a protected split, or promote a candidate. The authoritative
contract is `docs/paper/STAGE21D_PREREGISTRATION.md`.

### Stage 21D ranking/localization diagnosis complete; Stage 21E registered

The frozen-map diagnosis found that Stage 20C improved both score association
and spatial support relative to compact MFI under its descriptive union-distance
contract. Pixel-tolerance AUC/AP increased from about `0.51193/0.33933` to
`0.51607/0.34281`; mean GT-to-prediction distance decreased from `4.94` to
`4.47` pixels and prediction-to-GT distance from `13.75` to `13.28` pixels.
At the frozen standard-ODS thresholds, mean GT support within `0.0075` rose
from `0.75357` to `0.77315`, and prediction support from `0.56589` to
`0.57012`. Stage 20C also had a higher near-GT multiplicity surrogate
(`6.74` versus `6.62` predictions per GT pixel; `0.735` versus `0.715` of GT
pixels with at least two nearby predictions), so the diagnosis supports a
mixed interpretation: modestly better ranking/local coverage coexists with
more duplicate/broadened local response. These quantities are not Berkeley
one-to-one metrics and do not rescue Stage 20C's official AP loss.

The required official attachment preserved the frozen contrast:
Stage 20C changed ODS/OIS/AP by `+0.01427/+0.00872/-0.02622`. Compact MFI
remains the incumbent, and Berkeley reference reproduction remains unverified.

The registered next action is `stage21e_spatial_tolerance_response_curve`.
It evaluates all five exact frozen map sets with Berkeley matching at
`0.00375/0.0075/0.015/0.025`, reusing the complete Stage-21B `0.0075` and
`0.025` tables and resumably matching only the two missing distances. The
curves are diagnostic and non-promotional; `0.0075` remains the sole primary
endpoint and no row is an Estrada--Jepson result. The authoritative contract
is `docs/paper/STAGE21E_PREREGISTRATION.md`.

### Stage 21E spatial-tolerance response complete; Stage 21F registered

All five frozen methods were evaluated at Berkeley distance fractions
`0.00375/0.0075/0.015/0.025`, reusing the two complete Stage-21B tracks.
Stage 20C exceeded compact MFI in ODS at every distance by approximately
`+0.01104/+0.01427/+0.01436/+0.01321`, but its AP deficit also persisted and
grew from about `-0.01882` to `-0.03937`. Relaxing correspondence tolerance
therefore does not rescue the candidate or support a simple constant-offset
explanation. Only `0.0075` remains primary; other rows are non-promotional
Berkeley sensitivity results, not Estrada--Jepson scores. Reference
reproduction remains unverified.

The registered next action is
`stage21f_context_localizer_nms_decomposition`, under
`docs/paper/STAGE21F_PREREGISTRATION.md`. It reconstructs the frozen incumbent
and Stage-20C computations and requires exact final PNG agreement while
reporting descriptive rank and spatial diagnostics for context, pre-NMS local
evidence, pre-NMS coupling, and the final post-NMS score. It fits or promotes
nothing and advances only to Stage 21G.

### Stage 21F context/localizer/NMS decomposition complete; Stage 21G registered

The frozen reconstruction matched all 100 incumbent and all 100 Stage-20C PNG
maps byte for byte. Stage 20C context had higher descriptive tolerant-union
AUC/AP than incumbent context (`0.72895/0.50745` versus `0.68663/0.47882`).
After multiplication by shared pre-NMS Scharr evidence it retained a smaller
advantage (`0.67432/0.45757` versus `0.65491/0.44567`) and improved
density-matched GT coverage (`0.60716` versus `0.56111`). Final NMS reduced
both methods' diagnostic AUC/AP sharply, while Stage 20C retained a small
advantage (`0.51607/0.34281` versus `0.51193/0.33933`) and better GT support.
Thus the AP loss is not explained by wholesale contextual ranking or spatial-
support failure; coupling and NMS compress the context advantage, leaving raw-
curve and consensus ordering as the remaining diagnosis. These union metrics
are not official Berkeley scores. The official attachment retained Stage
20C's `+0.01424/+0.00813/-0.02622` ODS/OIS/AP contrast, with reference
reproduction still unverified.

The registered next action is `stage21g_human_consensus_ranking_analysis`, the
final Stage-21 diagnostic under `docs/paper/STAGE21G_PREREGISTRATION.md`. It
uses the five exact frozen map sets and a fixed multi-annotator consensus
signal to report rank correlations, higher-versus-lower consensus pairwise
accuracy, consensus strata, and weak-over-strong failure cases. It fits and
promotes nothing and completion advances only to the single-mechanism Stage-
21H synthesis.

### Stage 21G human-consensus ranking complete; Stage 21H registered

All five frozen methods showed weak ordering by human annotation consensus.
Compact MFI obtained pooled Spearman `0.07877`, Kendall tau-b `0.06363`, and
higher-versus-lower consensus pairwise accuracy `0.52275`; Stage 20C changed
these only to `0.07994/0.06462/0.52307`. The 2-additive variants therefore did
not materially solve consensus ordering even where Stage 20C improved ODS and
descriptive local support. The required official attachment preserved the
known Stage-20C contrast, `+0.01426/+0.00897/-0.02621` ODS/OIS/AP, with
reference reproduction still unverified.

The finite program authorizes exactly one causally justified candidate:
`stage21h_consensus_pairwise_choquet`, preregistered in
`docs/paper/STAGE21H_PREREGISTRATION.md`. It keeps Stage 20C's two cues and the
entire inference pipeline fixed, replacing only capacity fitting with an
equal-domain pairwise logistic ranking objective over leakage-free UDED
boundary/background pairs and BSDS500-train annotator-consensus pairs. It must
pass the existing conjunctive UDED and standard-Berkeley validation margins,
including nonnegative AP. Failure ends Stage 21 without replacement.

### Stage 21H first launch - harness-only seed coupling failure

The first launch completed fixed BSDS500-train preparation and reached the
fourth UDED split, then stopped before producing any result artifact. The
reused Stage-20 harness had propagated Stage 21H's preregistered ranking seed
`20261028` into the legacy compact-control bank preselector; under that
unintended stream the preselector omitted frozen
`gabor4_scale_persistence`. This is not candidate feedback and does not alter
the single-candidate budget. A harness-only retry is registered with the
Stage-21H seed unchanged for folds, memberships, and ranking pairs, while the
fixed compact control uses its established bank-sampling base seed
`20261009` with the same per-fold offsets. Candidate objective, data,
parameters, promotion rule, preview, and official attachment are unchanged.

### Stage 21H retry 1 - fixed-control preselection failure persisted

Retry 1 again stopped in the fourth UDED split before producing a result
artifact. The restored legacy sampling stream was applied as intended, but
Stage 21H's preregistered fold partition changes the training images and hence
the correlation-based selector still omitted frozen
`gabor4_scale_persistence`. This is a control-harness defect, not candidate
feedback. `stage21h_consensus_pairwise_choquet_retry2` calibrates exactly the
already-frozen five compact-control features inside each outer training fold,
bypassing eligibility/correlation selection only for that fixed incumbent
control. It preserves the Stage-21H folds, ranking seed, candidate objective,
data, parameters, promotion rule, preview, and official attachment.

### Stage 21H complete - consensus-pairwise capacity fitting rejected

The second harness-only retry completed the one authorized Stage-21H
candidate. Relative to compact MFI on the 14-image overlap-clean UDED
selection set, the consensus-pairwise two-cue 2-additive Choquet candidate
changed aggregate F1, precision, recall, and mean fold F1 by
`+0.004628`, `+0.012625`, `-0.009200`, and `+0.004584`. It won `12/15`
folds, all `15/15` constrained fits converged, and score support was preserved,
but recall crossed the preregistered `-0.003` non-collapse boundary.

The required standard-Berkeley BSDS500-validation attachment changed
ODS/OIS/AP by `+0.014168/+0.008702/-0.033638`. Thus the candidate also
failed the independently required nonnegative AP condition despite its clear
ODS/OIS gains. Both axes were conjunctive, so the candidate is rejected and
compact distorted-Choquet MFI remains the incumbent. The fixed positions
1/7/14 preview is complete. The local Windows matcher remains stochastic and
reference reproduction remains unverified, so these development scores do not
support a final SOTA claim.

This closes the finite Stage-21 program. Its contract permits no second
Stage-21H candidate, replacement, tuning, or automatic literature escalation.
The generalized non-neural SOTA objective remains unmet.

### Stage 22A first launch - thesis-source materialization failure

The first Stage-22A certification launch read no dataset and scored no
detector. Its exact and one-pixel-shift ejBCM-F synthetic cases passed, but
the historical `getBoundaries` smoke test could not run because eight helper
sources named by the earlier provenance manifest had never been materialized
in the repository. The launch also exposed incorrect LF-normalized expected
hashes for the four already-vendored sources. These are provenance/harness
defects and supply no protocol or detector feedback.

The original helper files were retrieved from the user-provided thesis Drive
folder using their previously recorded Drive hashes, and the manifest now
records their Drive file IDs plus repository LF-normalized hashes. The
registered next action is the harness-only
`stage22a_thesis_legacy_protocol_certification_retry1`. It reruns the
unchanged source checks and synthetic MATLAB microcases, consumes no new
scientific-stage slot, and leaves Stage 22B deferred until certification
passes.

### Stage 22A retry 1 - transitive KITT dependency exposed

Retry 1 verified every recorded thesis/Drive source hash and passed the exact
and shifted ejBCM-F microcases without reading a dataset or scoring a detector.
The `getBoundaries` smoke test then reached the recovered thresholding code and
stopped because `rosinUnimodalThr.m` explicitly calls `gaussianSmooth`, an
unrecorded transitive KITT dependency. The pinned public KITT tree at commit
`d70bb66ef9ab6f5cea8ead528fe5ac15ac096baf` supplies that function and its
`createGaussianFilter` dependency under GPL; their normalized source hashes
are now fixed in the provenance manifest.

The registered next action is the single Stage-22A compatibility diagnosis
allowed by the program,
`stage22a_thesis_legacy_protocol_certification_retry2`. It exposes those two
byte-verified public sources only through an ignored immutable runtime checkout
and reruns the unchanged synthetic certification. It changes no thesis source
or mathematical operation, consumes no additional scientific-stage slot, and
keeps Stage 22B deferred.

### Stage 22A closure - thesis legacy protocol certified; Stage 22B registered

The final harness-only compatibility diagnosis verified every recorded thesis,
Drive, and pinned public-KITT source hash. The exact and shifted ejBCM-F
microcases passed, and the unchanged `getBoundaries(map, inf)` ridge smoke case
produced a nonempty 60-pixel binary map. No dataset or detector was read or
scored. This satisfies the Stage-22A authorization gate without consuming an
additional scientific-stage slot.

The registered next action is
`stage22b_thesis_legacy_retrospective_benchmark`, scientific stage 2/5. It
uses only the frozen compact-MFI and Stage-20C BSDS500-validation maps, applies
the certified thesis transform, preserves every per-human-GT ejBCM-F value,
and reports the historical per-image-best summary plus transparent all-GT
variants. The optional rejected Stage-21H diagnostic comparator is included
because its exact retry-2 cache contains all 100 frozen maps. The aggregate
KITT Stage-21B score remains in a separate table for the incumbent and Stage
20C methods previously covered by that certified track. No legacy metric may
promote or tune a detector.

### Stage 22B complete - thesis-legacy comparison recorded; Stage 22C registered

The certified historical path completed on the frozen compact-MFI, Stage-20C,
and rejected Stage-21H validation maps. Across 100 images and 546 per-GT rows
per method, mean per-image best legacy F0.5 was `0.571790` for compact MFI,
`0.602663` for Stage 20C, and `0.602248` for Stage 21H. Stage 20C changed the
all-per-GT mean from `0.497851` to `0.525383`. Bootstrap intervals, per-GT
rows, best-annotation distributions, frozen-map hashes, and the fixed positions
1/50/100 preview are complete.

This does not reverse the modern-protocol rejection. Thesis best-match,
aggregate KITT, loose Berkeley, and standard Berkeley are distinct endpoints;
none of the legacy/loose tracks is promotional. The documentary standard-
Berkeley attachment again changed Stage-20C ODS/OIS/AP by
`+0.014309/+0.008472/-0.026222`, and reference reproduction remains
unverified. Compact distorted-Choquet MFI remains incumbent.

Scientific stage 3/5 is now registered as
`stage22c_inter_image_score_calibration_diagnosis`, with its immutable contract
in `docs/paper/STAGE22C_PREREGISTRATION.md`. It freezes the calibration-
dominance statistic before analysis, uses exact frozen maps and existing
standard-Berkeley counts, and cannot fit, select, or promote a detector.

The first Stage-22C launch computed its diagnostic tables but failed before
emitting the required summary, preview, and manifest because the harness
supplied an unsupported third positional argument to `write_panel_grid`. No
complete Stage-22C result is interpreted. The registered harness-only retry
changes only that call to the established two-argument API and does not consume
another scientific-stage slot; Stage 22D remains deferred.

### Stage 22C closure — calibration dominance passes; Stage 22D registered

The preview-API retry completed the frozen-map diagnosis. Stage 20C's
per-image best-threshold IQR was `0.16`. The GT-derived isotonic upper bound
showed `+0.11617` diagnostic pooled tolerant-union AP recoverability, whereas
mean within-image versus pooled AUC differed by only `0.00107`. The frozen
components were therefore `0.80`, `1.00`, and `0.02137`, for a calibration-
dominance score of `0.60712`; two components exceeded `0.50`, so the registered
calibration-dominance rule passes. This is causal-diagnostic evidence, not a
selection of any simulated normalization or a promotion. The official
attachment preserved Stage 20C's `+0.01427/+0.00824/-0.02623` ODS/OIS/AP
pattern, and compact MFI remains incumbent.

Stage 22D is now preregistered as the independent frozen-pipeline local-
competition/NMS diagnosis. Its score was fixed before output inspection and
Stage 22E remains unavailable until both dominance scores can be compared
mechanically.

### Stage 22D closure — local competition rejected as dominant; Stage 22E registered

The byte-verified frozen-pipeline diagnosis reconstructed all 100 compact-MFI
and all 100 Stage-20C final maps exactly. Stage 20C's high-consensus demotion
rate was `0.62524` versus `0.62306` for compact MFI, yielding a demotion
component of only `0.02180`. No early false positive was attributed to the
fixed local-competition condition, and Stage 20C's near-GT multiplicity was
slightly lower (`5.36689` versus `5.40864`), so the other two components were
zero. The frozen competition-dominance score is therefore `0.00727`, with
zero components above `0.50`; local competition is not dominant. The official
attachment retained Stage 20C's ODS/OIS/AP contrast of
`+0.01430/+0.00777/-0.02622`. These diagnostics do not promote either method,
and compact MFI remains incumbent.

The mechanical Stage-22 rule compares that result with Stage 22C's passing
calibration score (`0.60712`, two qualifying components) and selects Branch C.
The single final candidate is
`stage22e_positive_support_quantile_calibration`, preregistered in
`docs/paper/STAGE22E_PREREGISTRATION.md`. It leaves the frozen Stage-20C
detector unchanged and maps each image's positive-score empirical midranks to
a 255-point median reference quantile curve fitted strictly within the outer
UDED training fold; zeros, support, ties, and within-image ordering are
preserved. The family and constants were frozen without using Stage-22C's
normalization-simulation outcomes. Stage 22 ends after this candidate's
conjunctive UDED/standard-Berkeley decision, with no second candidate or
tuning pass.

### Stage 22E complete - quantile calibration rejected; bounded program closed

The sole Stage-22E candidate completed all registered artifacts and
implementation checks. Relative to compact MFI on the 14-image overlap-clean
UDED selection set, its aggregate F1, precision, recall, and mean fold F1
changed by `-0.117803`, `-0.116321`, `-0.113429`, and `-0.112746`. It won
`0/15` folds. All `15/15` capacity fits converged, with zero support,
within-image-ordering, or repeatability violations. The failure is therefore
scientific rather than a broken transform or fit.

The required standard-Berkeley BSDS500-validation attachment changed
ODS/OIS/AP by `+0.014451/+0.008171/-0.040971`. The positive operating-point
movement does not rescue the material AP regression, and the UDED gate had
already failed decisively. The fixed positive-support empirical-midrank to
outer-training median-quantile-reference calibration is rejected. Compact
distorted-Choquet MFI remains the incumbent; reference reproduction remains
unverified and the generalized SOTA goal remains unmet.

The fixed preview uses overlap-clean UDED positions 1, 7, and 14 with columns
input, ground truth, compact-MFI out-of-fold prediction, calibrated Stage-20C
out-of-fold prediction, and calibrated continuous score. It is documentary
only.

| hypothesis | evidence for | evidence against | falsified? | implication |
|---|---|---|---|---|
| Fixed spatial offset explains the AP deficit | Stage 20C improved tolerant localization and ODS | Its AP deficit persisted and widened across Berkeley distances `0.00375` to `0.025` | Yes, as the dominant explanation | Do not repair the ranking problem by loosening tolerance or applying a fixed displacement |
| Weak context is the primary failure | Contextual aggregation is compressed by later pipeline stages | Stage 21F found substantially better Stage-20C context AUC/AP and byte-matched final reconstruction | Yes, as a wholesale explanation | The issue lies in transfer/ranking behavior, not absence of useful context |
| NMS/local competition dominates | NMS compresses both methods' diagnostic discrimination | Stage 22D score was `0.00727`; no qualifying component and no excess multiplicity | Yes, under the fixed attribution contract | No NMS branch or parameter sweep is justified |
| Inter-image calibration dominates | Stage 22C score was `0.60712`, with threshold dispersion and large GT-oracle headroom | Cross-image versus within-image AUC discrepancy was only `0.00107`; Stage 22E then collapsed UDED and lost BSDS AP | Mixed; the fixed quantile remedy is falsified | Calibration remains a diagnostic association, not an established repair mechanism |
| Human-consensus ordering is adequate | Stage 20C was marginally above compact MFI | All methods had weak correlations and near-chance pairwise accuracy; Stage 21H did not repair AP | Yes | Consensus weakness remains descriptive and cannot motivate another candidate in this program |
| Thesis-legacy protocol is compatible | Stage 22A passed hashes and microcases; Stage 22B scored all frozen maps and GTs | Best-public-source and historical-protocol caveats remain | No, compatibility was established with caveats | Use legacy results only as a separate longitudinal bridge, never for promotion |
| Positive-support quantile calibration repairs global ranking | It preserved support/order and improved BSDS ODS/OIS | UDED F1 `-0.117803`, `0/15` wins, and BSDS AP `-0.040971` | Yes | Reject the fixed mechanism; no tuning, replacement, or sixth Stage-22 experiment |

Stage 22 closes at scientific stage 5/5. Its contract permits no second
candidate, replacement, post-hoc tuning, sixth experiment, or automatic
literature escalation. The next action is human synthesis and planning, not a
registered autonomous experiment.

### Stage 23A complete - evidence x aggregation landscape frozen; cache certification registered

The user-directed Stage-23 campaign changes the unit of study from serial
incumbent modification to a reproducible evidence-family by aggregation-family
landscape. Stage 23A accessed no dataset and scored no detector. Live primary-
source and official-code review produced the descriptor census, aggregation
census, detector/protocol matrix, and populated Stage-23 literature ledger.

The first UDED landscape is bounded to 13 raw evidence maps: the five retained
Gabor/Hessian/persistence anchors plus Scharr magnitude, CIELAB Di Zenzo vector
gradient, structure-tensor coherence, phase congruency, half-disc distribution
contrast, image-internal PMI deficit, semi-global changepoint support, and FH
region boundaries. Stage 23D may forward no more than eight cross-family pairs,
four triples, the incumbent five-map anchor, and two necessary single controls.
The Stage-23E aggregation shortlist is exactly eight families: equal mean,
nonnegative logistic additive, max, min, median OWA, Sugeno, fixed-gamma
distorted Choquet, and monotone 2-additive Choquet. Algebraic duplicate cells
must be labeled rather than counted as independent wins.

Complete detectors such as SED, SCO, Compass, EDPF, gPb, PMI spectral
boundaries, and Structured Forest remain later fidelity/gap-guided targets;
their outputs do not enter the raw descriptor pool. Literature test metrics are
documentary and protected splits remain outside model selection.

The registered next action is `stage23b_cache_certification`, a synthetic-only
conjunctive certification of content keys, exact reuse, artifact and manifest
hashes, atomic writes, parameter/preprocessing key separation, fail-closed
corruption, and GT-isolated inference extraction. No benchmark descriptor may
be extracted until Stage 23B passes.

### Stage 23B closure - cache certified; Stage 23C registered

The synthetic-only cache certification passed every conjunctive condition.
Exact requests reused artifacts without extractor calls; parameter and
preprocessing changes made new keys; transform reuse, sidecars, hashes and
atomic JSONL manifests agreed; deliberate corruption failed closed with zero
repair calls; GT-declared inference was rejected before computation; and no
temporary file remained. No benchmark or GT was read.

The registered next action is
`stage23c_cached_uded_descriptor_baselines` under
`docs/paper/STAGE23C_PREREGISTRATION.md`. It extracts all 13 frozen evidence
maps once on the 14-image overlap-clean UDED selection set, validates all 182
cache identities, and reports individual-map 5x3 threshold-CV baselines and a
fixed positions 1/7/14 atlas. It cannot prune or promote a descriptor; Stage
23D must analyze complementarity over every cached map. Compact MFI remains
incumbent.

### Stage 23C closure - cached descriptor atlas complete; Stage 23D registered

Stage 23C completed on all 14 overlap-clean UDED-selection images after
excluding known protected BSDS-test lineage item `03-35028` before byte access.
The frozen 13-map pool produced 182 cache misses on its one authorized
extraction pass, followed by 182 exact reload/manifest validations. All maps
were finite and shape-correct; every individual-map 5x3 threshold-CV baseline,
per-image row, score-distribution summary, and the fixed positions 1/7/14
preview completed. These individual results are non-selective and do not alter
the compact-MFI incumbent. The incumbent-only BSDS500-validation attachment
contains no descriptor comparison and retains the reference-unverified caveat.

The registered next action is `stage23d_cached_complementarity_map`. It consumes
all thirteen exact cached maps and, under the prospective rule in
`docs/paper/STAGE23D_PREREGISTRATION.md`, measures all 78 pair relationships and
may freeze at most eight cross-family pairs, four triples, the unchanged
incumbent anchor, and two necessary single controls for Stage 23E. No descriptor
extractor, aggregator fit, detector promotion, or protected split is permitted.

### Stage 23D closure - bounded input sets frozen; Stage 23E registered

The cached complementarity map completed with all 182 exact Stage-23C maps
loaded and no extraction, repair, or protected-lineage byte access. All 78
unordered pairs were reported. The prospective rule froze eight cross-family
pairs, four triples, the five-cue incumbent anchor, and the two single controls
`semiglobal_changepoint` and `halfdisc_distribution_contrast`. These selections
define a bounded factorial screen and do not alter compact MFI. The official
BSDS500-validation attachment scored only the unchanged incumbent and contains
no candidate comparison.

The registered next action is
`stage23e_cached_descriptor_aggregator_landscape`. Under
`docs/paper/STAGE23E_PREREGISTRATION.md`, it compares exactly equal mean,
nonnegative logistic additive, maximum, minimum, median OWA, shared-capacity
Sugeno, gamma-0.55 distorted Choquet, and monotone 2-additive Choquet on the
frozen sets with common outer-fold memberships. Its fixed rule may forward at
most three primary cells and their equal-mean controls to Stage 23F. It cannot
promote a detector or read a candidate BSDS validation result.

### Stage 23E closure - descriptor-aggregator validation frontier frozen

Stage 23E completed the bounded 15-set by eight-family landscape using exactly
182 Stage-23C cache hits and zero descriptor computations. All 120 nominal
cells, 1,800 fold rows, fitted-parameter records, negative cells, aliases, and
the fixed positions 1/7/14 preview are complete. The preregistered rule froze
minimum conjunction for `gabor4_scale_persistence` plus
`structure_tensor_coherence`; nonnegative logistic additive fusion for
`gabor4_scale_persistence` plus `halfdisc_distribution_contrast`; and median
OWA for `fh_region_boundary`, `halfdisc_distribution_contrast`, and
`structure_tensor_coherence`. Each advances with its matched equal-mean
control. The incumbent-only official attachment supplied no candidate result.

The registered next action is `stage23f_literature_validation_frontier` under
`docs/paper/STAGE23F_PREREGISTRATION.md`. It fits only on the 14 overlap-clean
UDED images, caches the four required native BSDS500-validation evidence maps
and all six aggregated map sets, and attaches standard Berkeley scoring. Its
fixed transfer rule compares each primary only with its matched mean; Stage 23F
cannot promote a detector or backfill the frontier. Compact MFI remains
incumbent and reference reproduction remains unverified.

### Stage 23F inference complete; official attachment continuation registered

Stage 23F completed all non-evaluator requirements on 100 native-resolution
BSDS500-validation images. It made exactly 400 one-time descriptor-cache
computations and 600 aggregate-cache computations, froze all six score-map
sets, retained hashes/provenance, and emitted the fixed positions 1/50/100
preview. Inference did not read validation ground truth and compact MFI remains
unchanged.

The required standard-Berkeley attachment reached its six-hour controller
limit after preserving complete nonempty per-image match tables for the
incumbent, both `pair_03` cells, and the `pair_04` logistic cell, plus 19
nonempty tables for the paired equal-mean control. The triple cells had not
started. Partial metrics have no standalone interpretation, so the frozen
transfer rule has not been applied.

The registered next action is
`stage23f_literature_validation_frontier_retry1`. This attachment-only
continuation targets the original evaluator directory, whose audited resume
path skips nonempty per-image tables. It may finish only missing matches and
aggregate the unchanged six frozen methods; it cannot extract a descriptor,
refit an aggregator, regenerate a map, backfill a frontier cell, promote a
detector, or advance to Stage 23G before completion. Berkeley reference
reproduction remains unverified.

### Stage 23F retry 1 timeout - second attachment continuation registered

The first resumable continuation also reached the six-hour controller limit.
It completed the fifth method, `stage23f_pair_04_equal_arithmetic_mean`, and
preserved the first nonempty per-image match table for
`stage23f_triple_04_median_owa`. The matched triple control has not started.
Without all six frontier cells there is no transfer classification, and no
partial metric is interpreted.

The registered next action is
`stage23f_literature_validation_frontier_retry2`. It is the same attachment-only
resume in the original evaluator directory: all frozen maps and all complete or
nonempty match tables are reused, only missing matches may run, and the frozen
primary-versus-mean rule is applied only after completion. Stage 23G remains
deferred, compact MFI remains incumbent, and Berkeley reference reproduction
remains unverified.

### Stage 23F retry 3 harness failure - fourth attachment continuation registered

Retry 3 stopped before evaluator work because the checkpoint-preserving runner
could not resolve its sibling `run_official_bsds` module. No matcher, dataset
score, descriptor extraction, fit, or map generation ran, so the failure has no
scientific interpretation. The runner now adds its own directory to the module
search path explicitly.

The registered next action is
`stage23f_literature_validation_frontier_retry4`. It is the unchanged
attachment-only continuation: all six frozen map sets and every complete or
nonempty match table are preserved, only missing standard-Berkeley matching may
run, and the primary-versus-mean transfer rule remains frozen until completion.
Stage 23G remains deferred and compact MFI remains incumbent.

### Stage 23F closure - no jointly transferable primary; Stage 23G checkpoint registered

The checkpoint-preserving fourth continuation completed the full frozen
standard-Berkeley frontier without descriptor extraction, refitting, aggregate
map regeneration, or loss of valid per-image tables. Minimum conjunction on
Gabor persistence plus structure-tensor coherence exceeded its matched equal
mean by `+0.05909/+0.03196` ODS/OIS but lost `-0.04275` AP. Nonnegative
logistic addition on Gabor persistence plus half-disc contrast changed the
same metrics by `+0.02954/+0.00925/-0.00793`. Median OWA on the
FH/half-disc/tensor triple changed them by
`-0.01403/-0.03972/-0.10468`. Because the frozen rule required ODS at least
`+0.002` and nonnegative OIS and AP jointly, none of the three UDED-selected
aggregation advantages transferred. No cell is promoted or backfilled and
compact MFI remains incumbent. The local Berkeley evaluator remains
reference-unverified.

The registered next action is `stage23g_gap_guided_detector_checkpoint`. It
scores no dataset. High-reasoning live primary-source and official-code review
must select exactly one reproducible strong non-neural detector target,
characterize its existing evidence, and register one bounded gap-guided next
action using the completed Stage-23 map prospectively. Failed Stage-23F
relationships cannot be presented as validated or tuned.

### Stage 23G checkpoint - exact SED and opposed-distribution gap selected

Live primary-source and official-code review retained exact full SED as the
single target. It is the strongest exact strictly untrained detector already
reproduced under the common BSDS500-validation path and already has frozen maps
on both BSDS validation and UDED selection. Its published and pinned-author
architecture contains color opponency, oriented Gaussian derivatives,
multiscale V1 surround, V2 texture suppression, feedback, and NMS, but it has
no explicit opposed-region distribution comparison.

The one missing-family hypothesis is therefore the cached half-disc
distribution contrast. Stage 23D showed that this weak individual map had low
rank redundancy and stable unique GT support across multiple families; this is
not a reinterpretation of Stage 23F, where its nonnegative-logistic pairing
improved ODS/OIS but lost AP and failed the joint rule. No nontrivial
aggregation relationship transferred. The only possible downstream
aggregation is prospectively fixed to the matched equal-mean control, and only
if a target-specific cross-domain gap diagnosis passes.

`stage23g1_sed_halfdisc_gap_diagnosis` is registered under
`docs/paper/STAGE23G1_PREREGISTRATION.md`. It performs no detector or descriptor
computation, validates all frozen SED/hash and Stage-23 cache provenance, and
measures cue-only GT rescue, conditional correctness, image stability, and
rank nonredundancy on overlap-clean UDED selection and BSDS500 validation. It
cannot promote a detector or alter compact MFI.

### Stage 23G1 closure - SED/half-disc gap unsupported cross-domain

The frozen-map diagnosis completed with zero detector runs, zero descriptor
computations, 114 exact cache hits, and no protected-lineage byte read. The
half-disc cue passed all four preregistered conditions on overlap-clean UDED:
mean cue-only GT fraction `0.25667`, conditional correctness `0.60109`, unique
GT support on `92.86%` of images, and mean SED/cue Spearman `0.04418`. On
BSDS500 validation it retained cue-only GT fraction `0.17233`, unique support
on every image, and mean Spearman `-0.01521`, but mean
`P(cue correct | SED wrong)` was only `0.38056`, below the frozen `0.50`
requirement. The conjunctive cross-domain gap rule therefore failed.

The SED/half-disc route closes without the conditional equal-mean intervention,
cue or target substitution, detector promotion, or incumbent change. The
incumbent-only official attachment contains no candidate comparison. Compact
distorted-Choquet MFI remains incumbent and Berkeley reference reproduction
remains unverified. The registered next action is the planning-only
`stage23_literature_escalation`; it must preserve this negative result, score no
dataset, and select at most one prospectively justified next Stage-23 action or
close the campaign path if none exists.

### Stage 23 literature escalation — complete PMI detector preflight registered

The live primary-source and official-code checkpoint preserves the Stage-23F
and Stage-23G1 negative results and selects a distinct strong-detector target:
Isola et al.'s complete PMI-affinity plus spectral-clustering boundary
detector. The official code is pinned at commit
`ee2d76e98340313a8f92e1b65064a9b4ea90ac77` under its shipped three-clause
BSD-style license. The author source exposes an explicit
`MS_algorithm_from_paper` path with color/local-variance features, per-image
KDE dependency estimation, three scales, fixed `rho=1.25`, and spectral
globalization. This is materially different from the bounded Stage-18j/
Stage-23 grayscale PMI-deficit evidence map.

The registered next action is `stage23g2_pmi_exact_runtime_preflight` under
`docs/paper/STAGE23G2_PREREGISTRATION.md`. It is dataset-free and verifies
immutable source, source contracts, MEX/runtime compatibility, and one fixed
synthetic execution of the exact paper path. It cannot read a benchmark, score
a detector, run an intervention, reopen SED/half-disc, or alter compact MFI.
Only a pass may lead to a separately registered exact development reproduction
before any missing-family diagnosis.
