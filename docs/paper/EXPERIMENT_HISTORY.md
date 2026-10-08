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
