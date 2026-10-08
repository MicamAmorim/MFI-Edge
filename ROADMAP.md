# MFI-Edge research roadmap

Last updated: **2026-10-07**

Legend: 🟢 completed/implemented · 🟡 active/partial · 🔴 planned · ⚪ parked.

## Branch responsibilities

| Branch | Role |
|---|---|
| `main` | stable/promoted models only |
| `mfi-edge-local-dev` | active workstation research |
| `mfi-edge-webui` | qualitative inference/comparison UI |
| `experiment/uded-railway` | server experiment/infrastructure history |

---

# Scientific trajectory

1. **MFI-Classic** — multiscale fuzzy evidence + classical localizer + NMS/linking.
2. **MFI-Fuzzy++ / Stages 5–7** — broad fuzzy-measure/operator competition and UDED generalization.
3. **CH-MFI-v2 / Stage 10** — context/hierarchy/uncertainty controlling localization; ultimately below Scharr on UDED.
4. **Edge Signature / Stages 11–12** — use GT to discover stable properties that distinguish true boundaries from high-gradient texture, then translate those properties into an interpretable analytical/fuzzy controller while keeping precise localization separate.
5. **External transfer / Stage 13** — freeze the UDED-development representatives and test whether the learned structural signature transfers unchanged to other edge datasets.

Guiding question:

> **Can stable multiscale structural evidence tell a precise edge localizer where to trust or distrust its response, and can that controller transfer across datasets without re-fitting?**

---

# Latest evidence

## CH-MFI-v2

Best 519-config winner remained below Scharr on UDED held-out:

- CH-MFI-v2 F1: **0.71325**
- Scharr F1: **0.76204**
- delta: **-0.04879**

Later scale-bank/regime-Shapley variants did not replace it.

## Stage 11 / 11b — edge-signature discovery

`oriented_ms` fixed a real implementation artifact:

- historical `oriented`: **22/80** exact duplicate scale/descriptor pairs;
- `oriented_ms`: **0/80**.

Held-out diagnostic discrimination:

| score | AUC | AP |
|---|---:|---:|
| analytical signature | 0.6606 | 0.4257 |
| logistic diagnostic | **0.6992** | **0.5029** |

Main interpretation: the descriptor space contains real information, but exact localization and context/texture rejection are different tasks.

## Stage 12a — fixed Scharr + analytical gate

The large CH-MFI degradation disappeared when Scharr+NMS remained the fixed localizer.

- Scharr held-out F1: **0.76204**
- Stage-12a: **0.76225**
- delta: +0.00020, CI crosses zero.

Conclusion: context should **control** localization, not compete with it.

## Stage 12b / 12c — fuzzy positive and anti-texture evidence

Stage 12b suggested that explicit anti-texture evidence could help. Stage 12c repaired feature-bank leakage by rebuilding positive/negative banks inside each outer fold. Several dual models looked promising on the already-inspected UDED held-out half, but that split is now development confirmation only.

## Stage 12d — repeated leakage-free bipolar CV

Stage 12d used only the 15 UDED selection images, with **5 repeats × 3 folds = 15 outer validations**. UDED held-out was not used.

| candidate | repeated CV F1 | delta vs Scharr |
|---|---:|---:|
| Scharr | 0.75095 | — |
| positive distorted-Choquet | **0.75889** | **+0.00794** |
| separable bi-capacity | 0.75811 | +0.00715 |
| ratio control | 0.75669 | +0.00573 |

## Stage 14b â€” spatial polarity mechanism ablation

On UDED selection only (5 repeats × 3 folds), the spatial negative-evidence ratio
scored CV F1 0.75669, below positive-only (0.75889) and marginally below the
image-mean-negative control (0.75922). Its mean fold delta against the image-mean
control was −0.00213; the preregistered criterion for spatial anti-texture support
was not met. This does not establish that negative evidence is universally
useless, but it removes spatial negative localization as a supported mechanism
for the current candidate. The next Stage-14 step prunes the positive feature
bank before any conditional combination is considered.

The positive-only controller narrowly wins. The separable bi-capacity remains very close and occupies **12 of the global top 20** configurations, versus 8 positive controls, but current repeated-CV evidence does not support claiming that negative evidence adds performance beyond the positive bank.

The positive bank is very stable: `gabor4_s5`, `hessian_s7`, `gabor4_s13`, `hessian_s13`, and `gabor4_scale_persistence` appeared in all 15 splits. The strongest anti-texture feature, `steered_hessian_scale_centroid`, also appeared in all 15 splits.

### Stage 14a/14c research checkpoint

The Stage-14 checkpoint compared three directions: RDF aggregation under
controlled corruption (retained as a later robustness question because prior
UDED inner-CV did not beat the standard family), positive-bank pruning
(selected now based on Stage-12d feature stability and Stage-14b results), and
conditional expert routing (deferred until development ablations show
complementary regimes). The registered Stage-14c test compares the full and
five-feature stable positive banks under identical repeated leakage-free CV on
UDED selection. External test results and UDED held-out are excluded.

Stage 14d tested the compact bank without `gabor4_scale_persistence`. The
four-feature variant scored CV F1 0.75473 versus 0.75889 for the five-feature
bank, with mean paired fold delta -0.00322 (3 wins, 12 losses). Retain
persistence and the five-feature compact bank under the predeclared pruning
rule. Fold events are descriptive only.

Stage 14f is registered as a synthetic-validation-only robustness
falsification: standard positive distorted-Choquet versus d-CC/FBPC/absolute
RDF, with identical frozen compact features, Scharr+NMS, gate, and clean-fit
threshold procedure. It reports absolute F1 and clean-referenced degradation
by Gaussian-noise, blur, texture, and compound family at three predeclared
severities. The comparison changes only the aggregation layer; external sets
and UDED held-out remain unavailable for design or feedback.

Stage 14f completed and did not support d-CC promotion. Its absolute mean
corrupted-F1 advantage was -0.00191; clean mean-image F1 changed by -0.00280;
there were zero corruption families with positive absolute advantage. The
descriptive clean-referenced degradation advantage was +0.00088 (positive in
three families), below the +0.01 threshold in the history. The runner summary
instead labels absolute corrupted F1 with a +0.005 threshold as primary. This
preregistration/reporting mismatch is recorded in `docs/paper/EXPERIMENT_HISTORY.md`;
both criteria failed, so d-CC is not retained. RDF robustness remains an
unsupported hypothesis on this protocol. No external or UDED held-out result
informed the interpretation.

Stage 14g compared three mechanistically distinct follow-ups. Further RDF
operator tuning is deferred; conditional experts remain blocked pending
development-only complementary errors; the d-CC paper's gravitational
preprocessing result motivates one isolated test of that conditioning step.
Stage 14h is registered on synthetic validation only: replace the median
prefilter with the fixed grayscale gravitational smoother before both the
feature and Scharr branches, with the compact positive controller frozen. The
source result is a hypothesis for this different multiscale system, not
evidence of transfer. The experiment must pass its preregistered criteria and
then receive a separate development confirmation before any retention.

Stage 14h completed without promotion. Gravitational smoothing produced mean
corrupted-F1 advantage `+0.00534`, but clean F1 fell by `-0.27231` and only
the texture family improved (`1/4` families), so two mandatory criteria failed.
Median conditioning remains incumbent. The texture-only benefit is a useful
complementarity observation but does not yet define a valid observable router;
known synthetic corruption labels cannot be used at inference. Further
gravitational/RDF tuning is deferred, and the repeatable autonomous literature
checkpoint is next to select one mechanistically distinct development test.

The literature checkpoint selected Stage 14i as that distinct test. Current
crisp-edge work makes contour continuity an explicit concern, and this
repository already has independent Stage-4 synthetic evidence for fixed
MFI-guided geodesic linking. Stage 14i transfers exactly that linker
(`max_gap=8`, `max_mean_cost=0.60`) to UDED-selection repeated leakage-free CV,
with no parameter sweep and no score-model change. Promotion requires
predeclared F1/precision noninferiority and natural-image connectivity gains.

Stage 14i completed without promotion. Fixed geodesic linking changed
aggregate F1 by `-0.01519` and mean fold F1 by `-0.01134` with no fold wins.
Its mean paired largest-component GT-coverage gain was only `+0.00156`, far
below the predeclared `+0.03`, even though precision remained within its
noninferiority margin and coverage improved in 12/15 fold means. The no-link
compact positive controller remains incumbent. Linker micro-tuning is blocked;
the autonomous literature/mechanism escalation was used to choose a distinct
representation test.

That checkpoint selected Stage 14j: append one fixed-default Kovesi PC2 maximum
phase-congruency moment to the retained positive context bank. The mechanism is
cross-scale phase alignment normalized by local response energy, rather than a
new smoother, fuzzy increment, or topology rule. Stage 14j keeps median
conditioning, distorted-Choquet gamma 0.55, the gate, and Scharr+NMS fixed. It
uses UDED-selection 5x3 repeated leakage-free CV, fits phase membership and
weight only within training folds, and permits no phase-parameter sweep. A
conditional phase/gradient localizer is deferred until this single-feature
test establishes complementarity.

Stage 14j completed without promotion. Compact-plus-phase changed aggregate F1
by `-0.000361` and mean fold F1 by `-0.000251`, with 6/15 fold wins. The phase
feature was training-eligible in every fold and precision remained within its
allowed margin, but the three F1 criteria failed. The compact five-feature
controller remains incumbent. Phase-parameter tuning and the conditional
phase/gradient router are not justified by this result; the repeatable
autonomous literature escalation is next and must select a mechanistically
distinct development-only test.

The live checkpoint selected Stage 14k as a direct localizer-information test.
The incumbent converts RGB to grayscale before Scharr, so it cannot detect a
chromatic discontinuity with little luminance contrast. Stage 14k changes only
the localizer to a fixed CIELAB Di Zenzo tensor built from channel-wise Scharr
derivatives; the compact fuzzy context, gate, conditioning footprint, repeated
CV splits, and fold-fitted threshold policy remain fixed. The candidate is a
replacement, not a tuned grayscale/color fusion or router. Promotion requires
the preregistered aggregate F1 and precision margins, positive mean fold delta,
and at least 9/15 fold wins on UDED selection only.

Stage 14k completed without promotion. The fixed Lab tensor replacement
changed aggregate F1 by `-0.011544`, precision by `-0.013249`, and mean fold F1
by `-0.012055`, with 1/15 fold wins. All four promotion conditions failed, so
grayscale Scharr+NMS remains incumbent. Do not tune color weights, fusion,
routing, or tensor parameters from this outcome. The next action is the
repeatable autonomous literature escalation, which must select a
mechanistically distinct development-only test.

The post-color checkpoint selected Stage 14l: a fixed oriented half-disc
texture-distribution feature appended to the compact context bank. This is
distinct from Stage 14k's pointwise color tensor and from the failed topology,
phase, smoothing, and RDF mechanisms. It compares uniform-LBP occurrence
histograms on opposite sides of a putative boundary using chi-square distance,
while Scharr+NMS remains the localizer. All feature calibration and thresholds
are fold-fitted on UDED selection only; no external feedback or parameter
sweep is allowed. The deterministic preview has columns conditioned input,
GT, incumbent, candidate, and retained best.

Stage 14l completed without promotion. Aggregate F1 improved by only
`+0.000310` (below the preregistered `+0.001` margin), mean fold F1 by
`+0.000370`, and precision changed by `-0.000040`; however, the candidate won
only 6/15 folds and the feature was eligible in only 7/15 folds. The compact
five-feature controller remains incumbent. Do not tune this texture feature
from the outcome. A mechanistically distinct autonomous literature escalation
is next.

That escalation selected Stage 14m, a detector-level aggregation/calibration
test. Rather than adding another descriptor, it fits one fixed-form,
class-balanced L2 logistic probability-of-boundary model inside each outer
training fold from Scharr+NMS, compact Choquet context, their product, and the
five retained memberships. Candidate predictions are restricted to
Scharr+NMS support, so the context/localizer role separation is preserved.
The incumbent and candidate each receive an independently fold-fitted
threshold. No regularization, feature, interaction, or classifier sweep is
allowed. This tests whether the Stage-11 linear diagnostic signal can improve
the actual detector and whether the fixed multiplicative gate, rather than the
representation, is now the bottleneck.

Stage 14m completed without promotion. The linear candidate improved
precision by `+0.005232`, but aggregate F1 fell by `-0.004972`, mean fold F1
fell by `-0.006046`, and it won only 4/15 folds. All 15 models converged. The
compact five-feature Choquet controller remains incumbent, and no logistic
regularization, sampling, interaction, or classifier micro-tuning is allowed
from this result.

The following autonomous live-literature escalation selected Stage 14n, a
bounded non-neural learned-localizer test motivated by Structured Forests and
Oriented Edge Forests. The candidate fits a fixed shallow randomized forest
inside every UDED-selection training fold from dense raw Scharr, Scharr+NMS,
the retained compact context/memberships, and two localizer-context products.
It produces a dense posterior that is localized by the existing fixed
gradient-direction NMS. This isolates nonlinear cue interaction plus dense
scoring without introducing the full patch-label, offset, sharpening, and
compositing machinery of a structured forest. Parameters and the conjunction
promotion rule are frozen in `docs/paper/STAGE14N_PREREGISTRATION.md`; no
forest sweep is allowed from the outcome.

Stage 14n completed without promotion. The shallow forest changed aggregate
F1 by `-0.024925`, aggregate precision by `-0.038556`, and mean fold F1 by
`-0.025724`, with only 2/15 fold wins. All 15 models were finite and recall
was nearly unchanged, isolating a large precision deficit. The compact
five-feature Choquet controller with grayscale Scharr+NMS remains incumbent.
Do not tune forest capacity, sampling, channels, or calibration from this
result; a mechanistically distinct live-literature escalation is next.

The post-forest escalation selected Stage 14o: interval uncertainty plus a
reliability-conditioned capacity field. The five compact memberships remain
fixed, but their pixelwise disagreement defines an interval width and a convex
interpolation from the retained gamma-0.55 capacity toward the additive
capacity. Interval-envelope width explicitly attenuates the powered context
once;
Scharr+NMS and the incumbent gate remain unchanged. The experiment is a single
fixed point, not an interval/capacity sweep, and is registered for UDED
selection repeated CV plus the default-on official BSDS500-validation MATLAB
attachment. Promotion requires the preregistered conjunction across both
development axes.

Stage 14o failed every UDED non-collapse condition: aggregate F1 changed by
`-0.009801`, precision by `-0.015321`, and mean fold F1 by `-0.007976`, with
`0/15` wins. It cannot be promoted regardless of the pending official metrics.
The first three BSDS-val attachment attempts exposed, in sequence, absolute-
path exporter imports, MEX existence semantics, and MATLAB R2023a's inability
to parse chained cell/field indexing in the pinned evaluator. No attempt
reached scoring. The fourth retry reached its run-local compatibility mirror
but exposed an unused four-output `fileparts` call that MATLAB R2023a rejects.
A fifth plumbing-only retry completed matching and read all 100 incumbent
result files, then MATLAB terminated with Windows heap corruption before it
could write the summary. The sixth retry isolated native matching and
pure-MATLAB aggregation in fresh processes and completed all 100 images. The
candidate changed ODS/OIS/AP by `+0.00225/+0.00182/-0.00100`; the negative AP
change failed the official criterion, while the UDED conjunction had already
failed decisively. Stage 14o is closed without promotion.

Stage 14p completed without promotion. Its precision gain was overwhelmed by
a UDED recall collapse: aggregate F1 changed by `-0.08044` and mean fold F1 by
`-0.08243`. Official BSDS500-validation ODS rose by `+0.00522`, but OIS fell
by `-0.00286` and AP by `-0.04888`; the conjunctive cross-dataset rule failed.
Do not tune the phase-field coefficients from this outcome.

Stage 14q is registered as the distinct next mechanism: a fixed eight-atom
anisotropic directional bank replaces Scharr localization while
the retained compact Choquet gate remains unchanged. This is a bounded
shearlet-motivated singularity test with two fixed scales and four fixed
orientations, not a continuous-shearlet reproduction. It uses UDED repeated
leakage-free CV plus the default official BSDS500-validation attachment, with
no bank sweep and a deterministic preview.

Stage 14q then failed its UDED gate: aggregate F1 fell by `0.03116`, mean fold
F1 by `0.03135`, recall by `0.10655`, and the candidate won only `1/15` folds,
despite a `0.01979` precision increase. The fixed atom bank is not promoted or
tuned, and grayscale Scharr+NMS remains incumbent. Its first official
BSDS500-validation attachment ended after 10/100 incumbent images with an
intermittent MATLAB heap-corruption exit. A frozen attachment-only retry then
completed all 100 images: ODS changed by `+0.00334`, but OIS by `-0.00089` and
AP by `-0.01526`. The cross-dataset conjunctive rule therefore failed, and
Stage 14q is closed. A live-literature checkpoint is next to select one
mechanistically distinct falsification rather than tune this atom bank.

Stage 14r is closed without promotion. The fixed `SE(2)` enhancement improved
official BSDS-val ODS/OIS/AP by `+0.00381/+0.00169/+0.00779`, but reduced UDED
aggregate F1 by `0.00276`, reduced precision by `0.00699`, won only `5/15`
folds, and reduced rather than improved largest-component GT coverage. The
preregistered conjunction therefore failed. Do not tune the 32-bin hard lift,
diffusion, projection, or fusion from this mixed result. The compact
Choquet-gated grayscale Scharr+NMS controller remains incumbent. Route next to
a live-literature checkpoint for one mechanistically distinct falsification.

The post-Stage-14r live-literature checkpoint selected Stage 14s: one fixed
half-order isotropic spectral Riesz-gradient localizer, with the retained
compact Choquet context and all fitting semantics unchanged. This tests the
nonlocal selectivity/noise-immunity rationale of fractional differentiation
without tuning an order or revisiting SE(2). UDED repeated leakage-free CV and
official BSDS500-validation ODS/OIS/AP are conjunctive, and the runner includes
the required deterministic preview and frozen exporter.

Stage 14s is closed without promotion. The candidate improved official
BSDS500-validation ODS/OIS/AP by `+0.01161/+0.00505/+0.01804`, but reduced
UDED aggregate F1 by `0.03599`, precision by `0.02286`, and mean fold F1 by
`0.03583`, with `0/15` wins. The conjunctive rule failed decisively. Do not
tune the fractional implementation from this mixed result; retain grayscale
Scharr+NMS and route to a live-literature/mechanism checkpoint.

The post-Stage-14s checkpoint selected Stage 14t: one fixed a-contrario
connected-support meaningfulness gate over the unchanged compact Choquet-gated
Scharr score. The test asks whether an image-internal number-of-false-alarms
model can reject accidental strong responses without another localizer or a
learned domain router. It uses a fixed 8-bit upper-level filtration,
conservative test-count bound, two-pixel effective sampling, `epsilon=1`, and
the retained `0.10` attenuation floor. UDED repeated CV and official BSDS-val
remain conjunctive; the runner includes the required preview and frozen
exporter. Dempster–Shafer ignorance and pure threshold persistence are deferred.

Stage 14t is closed without promotion after reducing both UDED and official
BSDS500-validation performance. Stage 14u then tested a fixed three-source
Yager-rule evidential fusion. It failed the UDED gate: aggregate F1 changed by
`-0.00245`, mean fold F1 by `-0.00171`, recall by `-0.00781`, and only `3/15`
folds won, despite a `+0.00072` precision change. The candidate is not promoted
or tunable. Its official BSDS-val attachment encountered the known intermittent
MATLAB heap-corruption exit after 37/100 incumbent images; a frozen
attachment-only retry then exited after 12/100. A resumable second retry now
checkpoints completed per-image Berkeley matches across fresh MATLAB processes
without changing the evaluator, predictions, or candidate. After documentary closure, run a live
literature/mechanism checkpoint. Threshold persistence and
uncertainty-controlled PDE conditioning remain deferred, not automatically
selected.

Stage 15 is now active and temporarily forbids new MFI architecture through
Stage 15o. Stage 15a is registered first: reproduce the pinned BSDS five-image
boundary-evaluator fixture, audit all validation pairs/annotations and protocol
invariants, and score fixed Canny, repository Scharr+NMS, and the unchanged
incumbent through one matched official path. On successful closure, continue
the preregistered reproduction campaign with Stage 15b SED rather than resume
one-shot mechanism invention.

Stage 15a is currently pending evaluator diagnosis. The initial controller
launch used a Python interpreter without scikit-image, and the frozen
five-image fixture artifacts miss the preregistered `1e-4` agreement bound on
ODS/OIS while passing it on AP. Route evaluator/export scripts through the
repository environment, quantify the fixture drift without changing tolerance,
and defer full validation scoring and Stage 15b until fidelity is resolved.
The first diagnostic found systematic table-level drift but did not localize
it. The next registered fixture-only test compares the repository wrapper with
the documented BSDS-compatible `edgesEvalImg` path under the identical Windows
matcher and repeats it in a fresh MATLAB process; no validation images or new
detector maps are involved.
The first launch stopped before matching because the pinned `edgesEvalImg`
requires `getPrmDflt` from Piotr Dollár's separate MATLAB toolbox. A strict
repository-local parser for the diagnostic's explicit name/value arguments is
now registered for one attachment-only retry. This changes neither evaluator
math nor the frozen fixture tolerance; Stage 15a, full validation, and Stage
15b remain pending that result.
The parser-repaired retry exposed a separate local harness error before
matching: it supplied the RGB fixture photographs rather than the shipped
single-channel PNG boundary predictions, so `bwmorph` correctly rejected the
three-dimensional threshold map. A second attachment-only retry now supplies
the PNG predictions. This changes no evaluator semantics, fixture tolerance,
validation result, or architecture.

The corrected retry then exposed genuine repeat instability in the pinned
Windows matcher path: identical fresh-process runs differed by up to
`0.000507` in aggregate tables and seven raw matched-count units, while the two
nominally compatible evaluator wrappers differed by up to `0.000757`. This
fails the exact-agreement branch and is too large for the registered `1e-4`
fixture certification. The next and only registered action rebuilds the exact
pinned Berkeley C++ matcher sources outside the vendor tree, records compiler
provenance, and repeats only the five-image fixture. Full validation and Stage
15b remain deferred.

That first build stopped before matching because MSVC lacks the POSIX and
legacy GNU declarations used by the pinned sources. The registered
attachment-only retry supplies a hashed repository-local compatibility include
layer while leaving the vendored source bytes and matching logic unchanged; a
Microsoft Visual C++ 2022 compile smoke test now succeeds. The retry still
scores only the five-image fixture, and full validation and Stage 15b remain
deferred.

That retry built the matcher but stopped before matching because the local
resolution assertion compared MATLAB's backslash-form path with the harness's
forward-slash-form directory. One second attachment-only retry is registered
after separator normalization. This repair changes no source bytes, matcher
logic, fixture, tolerance, validation policy, or detector architecture; full
validation and Stage 15b remain deferred.

The separator-normalized retry stopped before matching because the local
fixture harness omitted the audited MATLAB R2023a syntax mirror used by the
main evaluator. A third attachment-only retry now applies that run-local
syntax transform without changing vendored bytes, matcher logic, fixture
inputs, tolerance, validation policy, or architecture. Stage 15a and Stage 15b
remain pending.

Scientific conclusion:

> **Positive multiscale edge-signature evidence is reproducibly useful on UDED development. Anti-texture evidence is stable and interpretable, but its incremental value is unresolved. External transfer must decide whether either mechanism generalizes.**

Full note: `docs/paper/STAGE12D_REPEATED_BIPOLAR_RESULTS.md`.

### Validation policy

- **do not use UDED held-out for further architecture selection**;
- Stage-12d candidates are frozen from UDED selection only;
- Stage 13 must apply them unchanged to external datasets;
- official paper claims still require official dataset-specific evaluation protocols.

---

# Track A — active workstation campaign

| Milestone | Status | Latest decision |
|---|:---:|---|
| CH-MFI-v2 standard screen | 🟢 | negative vs Scharr |
| learned scale-bank / regime-Shapley | 🟢 | no winner replacement |
| Stage 11 signature discovery | 🟢 | reproducible structural signal |
| `oriented_ms` | 🟢 | scale collapse fixed |
| cross-scale relational descriptors | 🟢 | balance/delta/persistence/entropy/centroid/peak |
| Stage 12a fixed-Scharr gate | 🟢 | near-null vs Scharr |
| Stage 12b fuzzy signature | 🟢 | dual family became promising |
| Stage 12c leakage-free bank CV | 🟢 | leakage fixed; UDED held-out retired |
| Stage 12d repeated bipolar CV | 🟢 | positive wins narrowly; bi-capacity remains close |
| freeze external candidates | 🟢 | exact banks/configs/thresholds frozen on UDED selection |
| **Stage 13a BSDS frozen transfer** | 🟡 **RUN NOW** | no BSDS tuning; first external check |
| BIPEDv2 external replication | 🟡 preflight registered | test split frozen; author-provided download requires human license acceptance |
| official BSDS500 evaluation | 🟢 integrated | default-on MATLAB validation attachment; final claims still require reference reproduction verification |
| topology/linking revisit | 🟢 Stage 14i completed | fixed linker not promoted; F1 and coverage-effect criteria failed |
| post-topology mechanism search | 🟢 completed | selected phase congruency as a distinct representation mechanism |
| Stage 14j phase context | 🟢 completed | eligible in 15/15 folds but no incremental F1; not promoted |
| post-phase mechanism search | 🟢 completed | selected fixed CIELAB vector-gradient localization |
| Stage 14k color-tensor localizer | 🟢 completed | fixed Lab tensor replacement failed all promotion criteria; grayscale Scharr retained |
| post-color mechanism search | 🟢 completed | selected explicit two-sided texture-distribution contrast |
| Stage 14l texture-distribution context | 🟢 completed | small sub-margin gain; 6/15 wins and 7/15 eligible; not promoted |
| post-texture mechanism search | 🟢 completed | selected fixed-form linear probability-of-boundary cue fusion |
| Stage 14m linear cue fusion | 🟢 completed | converged in 15/15 folds but reduced aggregate F1; compact Choquet controller retained |
| post-linear-fusion mechanism search | 🟢 completed | selected a bounded shallow edge-forest localizer from primary Structured Forest/OEF literature |
| Stage 14n shallow edge forest | 🟢 completed | finite in 15/15 folds but large F1/precision loss and only 2/15 wins; not promoted |
| post-forest mechanism search | 🟢 completed | selected explicit interval ignorance plus convex reliability-conditioned capacity |
| Stage 14o interval-capacity uncertainty | 🟢 completed; not promoted | UDED failed all criteria; BSDS ODS/OIS rose slightly but AP fell, so the conjunctive rule failed |
| Stage 14p Ambrosio–Tortorelli phase field | 🟢 completed; not promoted | large UDED F1/recall and BSDS AP losses despite a small BSDS ODS gain |
| Stage 14q anisotropic singularity localizer | 🟢 completed; not promoted | UDED F1/recall collapsed; BSDS ODS rose slightly but OIS/AP fell, so the conjunctive rule failed |
| post-singularity mechanism search | 🟢 completed | selected fixed SE(2) orientation-lifted contour enhancement from primary literature |
| Stage 14r SE(2) contour enhancement | 🟢 completed; not promoted | BSDS ODS/OIS/AP rose, but UDED F1/precision and preregistered continuity coverage fell |
| post-SE(2) mechanism search | 🟢 completed | selected one fixed half-order Riesz-gradient localizer from primary fractional-edge literature |
| Stage 14s fractional Riesz localizer | 🟢 completed; not promoted | BSDS ODS/OIS/AP improved strongly, but UDED F1/precision collapsed and the candidate won 0/15 folds |
| post-fractional mechanism search | 🟢 completed | selected fixed a-contrario connected-support meaningfulness rather than another localizer |
| Stage 14t a-contrario meaningfulness | 🟢 completed; not promoted | Failed all UDED criteria and reduced official BSDS-val ODS/OIS/AP by 0.01257/0.01761/0.02830; compact controller retained |
| post-a-contrario mechanism search | 🟢 completed | selected fixed Yager-rule evidential ignorance over disjoint incumbent sources |
| Stage 14u Yager evidential ignorance | 🟡 UDED failed; official attachment retry pending | F1/mean-fold/3-of-15 win criteria failed despite a tiny precision gain; no mass-rule tuning |
| Stage 14u official BSDS-val retry | 🟡 retry 2 registered | resumable frozen attachment after two intermittent MATLAB heap-corruption exits; no CV, prediction, matcher, or vendor changes |
| dynamic localizer revisit | ⚪ | learned/routed localizers remain parked; Stage 14k does not justify a color router |
| wide sweep | 🔴 blocked | no brute-force expansion before external evidence |

### Run now

```powershell
git fetch
git switch mfi-edge-local-dev
git pull
.\run_stage13_bsds_transfer.bat
```

By default this attempts the complete BSDS500 **test** split at max side 256. Do not pass `--limit` for the real frozen transfer run. The script downloads missing BSDS files automatically.

Send:

```text
results\external\stage13a_bsds_transfer\summary.json
results\external\stage13a_bsds_transfer\external_metrics.csv
results\external\stage13a_bsds_transfer\per_image_metrics.csv
results\external\stage13a_bsds_transfer\preview_positive_control.png
results\external\stage13a_bsds_transfer\preview_separable_bicapacity.png
results\external\stage13a_bsds_transfer\preview_ratio_control.png
```

---

# Track B — current candidate architecture

```text
image
  -> oriented_ms descriptors + cross-scale relations
  -> positive boundary memberships -------> C_plus
  -> texture / anti-boundary memberships -> C_minus

image -> median conditioning -> Scharr -> NMS

positive control:
  C_plus -> context gate -> frozen threshold -> edge map

separable bi-capacity control:
  B(x) = normalize(C_plus - lambda*C_minus)
  -> context gate -> frozen threshold -> edge map
```

Stage 12d froze three unique representatives for transfer:

1. `positive__gp0.55__a2__floor0.1`;
2. `bicap__gp0.55__gm1.75__l0.35__a2__floor0.1`;
3. `ratioctl__gp0.55__gm1__l1__a2__floor0.1`.

The logistic model remains an upper-bound diagnostic only, not the proposed detector.

---

# Track C — model-family coverage

| Research idea | Status |
|---|:---:|
| context analyzer | 🟢 |
| hierarchical coarse/fine MFI | 🟢 tested |
| conditional fuzzy operators | 🟢 tested |
| distorted-probability capacities | 🟢 |
| scale-specific capacities | 🟢 tested |
| global/regime Shapley | 🟡 utility redesign needed |
| SWAFED | 🟢 tested |
| d-CF / d-CC / d-XC / d-Choquet | 🟢 tested |
| Choquet-inspired aggregation | 🟢 experimental |
| partition-conditioned aggregation | 🟢 experimental |
| `oriented_ms` descriptors | 🟢 |
| cross-scale relational signature | 🟢 |
| positive fuzzy signature | 🟢 stable development signal |
| explicit anti-texture bank | 🟢 stable features, incremental value unresolved |
| separable bipolar / bi-capacity model | 🟢 implemented/tested |
| general non-separable bi-capacity | 🔴 conditional future |
| formal k-interactive learning | 🔴 |
| Fourier/multiband branch | 🔴 |
| dynamic localizer | ⚪ parked |
| uncertainty controller | ⚪ parked/redesign |
| learned router/dynamic convolution | 🔴 v3 |
| annotator uncertainty / ranking loss | 🔴 |
| TEED/PiDiNet fuzzy ensemble | 🔴 hybrid generation |

---

# Track D — datasets and validation

| Dataset/protocol | Status | Role |
|---|:---:|---|
| synthetic v2 | 🟢 | mechanism diagnosis |
| UDED selection 15 | 🟢 | completed development/calibration source |
| UDED held-out 15 | ⚪ exhausted for final testing | development confirmation only |
| BSDS500 consensus transfer proxy | 🟡 **Stage 13a** | external frozen generalization check |
| BIPED | 🔴 next | cross-dataset replication |
| official Berkeley matching | 🔴 | publication-grade evaluation |
| multi-annotator BSDS uncertainty | 🔴 | preserve individual annotations |
| higher-resolution rerun | 🔴 | finalist sensitivity check |

Stage 13a intentionally reports a **consensus-thresholded BSDS + tolerant-dilation proxy**, not official Berkeley bipartite matching. ODS/OIS on BSDS are descriptive only; the primary external transfer metric uses thresholds frozen before BSDS.

Stage 13c targets author-designated BIPEDv2: 250 outdoor RGB/edge-map pairs at 1280×720, with 200 train and 50 test. Train is not used for fitting or calibration; test is a frozen replication. The author distribution carries terms that must be accepted by a human, so the registered read-only preflight validates the locally supplied canonical layout before any inference. Preserve native resolution and frozen Stage-12d settings. The Berkeley project recommends submitting soft, thinned score maps to its official benchmark code; that code uses multi-annotator matching through CSA++ and requires MATLAB, so it should be run as a separate publication-grade evaluation when the compatible toolchain is available.

---

# Track E — research automation

Planned `automation/research_controller.py`:

- local Python executes long experiments;
- Codex is called only after a result is ready;
- Git is the scientific memory;
- explicit budget / stop file / max-iteration limits;
- no held-out/test feedback inside iterative optimization;
- only allow-listed experiment commands may execute automatically.

Implement after the Stage-13 external-validation runners are stable.

---

# Track F — promotion

No Stage-12/13 model is promoted to `main` yet.

Promotion requires:

1. exact frozen config;
2. documented calibration source;
3. untouched external validation/test;
4. reproducible threshold/evaluation protocol;
5. qualitative inspection;
6. runtime/resolution report;
7. external evidence that the controller improves or robustly matches the fixed localizer.

```text
mfi-edge-local-dev -> validated candidate -> main -> mfi-edge-webui
```

---

# Paper/research record

Maintain together:

- `ARCHITECTURE_MAP.md`
- `BIBLIOGRAPHY_MATRIX.md`
- `LEGACY_REVIEW_CORPUS.md`
- `EXPERIMENT_HISTORY.md`
- `STAGE11_EDGE_SIGNATURE.md`
- `STAGE11_EDGE_SIGNATURE_RESULTS.md`
- `STAGE11B_SCALE_SENSITIVE_RESULTS.md`
- `STAGE12A_SIGNATURE_GATE_RESULTS.md`
- `STAGE12B_FUZZY_SIGNATURE_RESULTS.md`
- `STAGE12C_LEAKFREE_RESULTS.md`
- `STAGE12D_REPEATED_BIPOLAR_RESULTS.md`
- `PAPER_WRITING_PLAN.md`
- `references.bib`

Update this roadmap whenever a result changes the scientific direction.

## Current Stage-15a diagnostic

The syntax-repaired source-build retry completed, but the exact pinned source
rebuilt under MSVC remained non-repeatable (`0.000104`, `0.000433`, and
`0.000180` maximum deltas across the three fixture tables) and differed from
the shipped fixture by as much as `0.001083`. The registered `1e-4`
certification therefore still fails.

The final Stage-15a diagnostic fixed only the clock-seeded global random stream
to preregistered seed `1` in a result-local source copy. Two fresh processes
then produced byte-identical fixture tables, establishing clock-seeded matcher
sampling as the cause of the observed repeat drift. Stage 15a is closed without
reference reproduction verification: the controlled matcher is diagnostic-only
and must never score datasets, while the unmodified official Windows path
remains stochastic and uncertified for final claims.

The Stage-15b checkpoint recovered and smoke-tested the unmodified author
MATLAB SED implementation at pinned commit
`11514b80162e5cd93fd244515189649656105a14`. It is classified as strictly
untrained with fixed author parameters; the paper's BSDS500-test
`0.71/0.74/0.74` remains documentary and separate from local validation.

The active next action is `stage15b_sed_exact_reproduction`. It runs the exact
author full model on native-resolution BSDS500 validation, writes per-image
maps/runtime/hashes and the fixed positions 1/50/100 qualitative panel, then
attaches the unchanged official validation path against the incumbent. The
author source remains an ignored local dependency because no explicit license
was found. This is a reproduction baseline only; no MFI architecture work or
post-result SED tuning is authorized.

The initial launch failed before detector execution because Git's ownership
guard rejected the ignored author checkout created by a different local
account. The active action is now
`stage15b_sed_exact_reproduction_retry1`, using a process-local trust override
only for the immutable, hash-verified checkout. No author source, detector
parameter, dataset role, output convention, preview position, or evaluation
protocol changes.

Stage 15b is now complete. The exact author MATLAB SED full model scored
BSDS500-validation ODS/OIS/AP `0.678546/0.709152/0.712814`, improving over the
unchanged MFI incumbent by `+0.133122/+0.129816/+0.178518` under the same local
official path. It is retained as a strictly untrained external baseline, not
integrated into MFI. The fixed positions 1/50/100 preview and per-image maps,
runtimes, and hashes are complete. The Stage-15a caveat remains: the Windows
matcher is stochastic and not reference-certified, so no final claim may rely
on this result alone.

The active next action is `stage15c_vcm_reproduction_checkpoint`. It will use
live primary-source research to resolve author code, fixed parameters,
training class, output convention, and Berkeley-protocol compatibility for Lu
et al.'s 2021 vector co-occurrence morphological colour-edge method before one
fidelity-labeled reproduction is registered. Architecture invention remains
forbidden through Stage 15o.

The Stage-15c primary-source checkpoint found the method strictly untrained but
not reproducible exactly or faithfully from public material. No author code or
supplement was located, and the paper omits multiple fixed parameters, the
vector-to-scalar output convention, gradient selection/postprocessing, and the
exact BSDS evaluation path. Its reported ODS/OIS/AP `0.76/0.79/0.77` remain
documentary and protocol-unverified. The active next action is
`stage15c_vcm_fidelity_preflight`, a dataset-free implementation-contract audit
that will not invent parameters, emit maps, or score a surrogate. If the
contract remains unresolved, Stage 15c closes and the reproduction sequence
advances to Stage 15d; architecture invention remains forbidden.

The Stage-15c preflight confirmed the unresolved implementation contract. No
dataset was read, no detector was executed, and no VCM surrogate was scored;
the reported `0.76/0.79/0.77` remains documentary and protocol-unverified.
Stage 15c is closed as non-reproducible from the available public material.

The active next action is `stage15d_ed_edpf_reproduction_checkpoint`. It will
use live primary literature and the official ED_Lib repository to establish an
immutable code lineage, license/build contract, fixed published variant and
parameters, training class, scalar output convention, and matched BSDS500-
validation plan before one exact or explicitly fidelity-labeled run is
registered. Stage 14t is not treated as EDPF, and MFI architecture invention
remains forbidden through Stage 15o.

The Stage-15d checkpoint verified a reproducible exact-code target: official
MIT-licensed ED_Lib commit `69b8d081bd6d28192d816ec0ed02aff9186d73c1`,
using its fixed grayscale EDPF constructor and native binary edge image. The
paper/code distinction between ED chain construction and EDPF chain-level
Helmholtz validation is resolved; Stage 14t remains a non-equivalent surrogate.
The binary output can be evaluated on the common official validation path, but
AP will have a documented single-operating-point limitation and the Stage-15a
matcher caveat remains.

The active next action is `stage15d_edpf_build_preflight`, a dataset-free,
hash-verified build and deterministic synthetic-output smoke test. It is needed
because the current Python OpenCV lacks the Edge Drawing binding and no C++
OpenCV development configuration is yet resolved. A pass advances to one exact
BSDS500-validation reproduction; a failure permits build/dependency repair
only. No dataset is read, no official-evaluation manifest or preview is needed,
and architecture invention remains forbidden through Stage 15o.

That preflight stopped before compilation because the workstation has no C++
OpenCV package configuration. Source identity and license checks passed; no
dataset was read and no detector result was produced. The active action is now
`stage15d_edpf_build_preflight_retry1`, an attachment-only harness repair that
builds pinned upstream OpenCV 3.4.20 core/imgproc and repeats the unchanged
EDPF compile/smoke test. No reimplementation, parameter change, benchmark run,
or MFI architecture work is authorized by this retry.

Retry 1 stopped before dependency configuration because the immutable OpenCV
3.4.20 identifier had been recorded as an annotated-tag object while the
harness compared it directly with the peeled commit in `HEAD`. The source is
the intended release; no dataset or detector ran. The active action is now
`stage15d_edpf_build_preflight_retry2`, which verifies tag object `404ca455`
and peeled commit `1eb1d4c` separately before repeating the unchanged build
and synthetic smoke test. This is provenance/harness repair only.

Retry 2 built and installed pinned OpenCV 3.4.20 successfully, but the EDPF
CMake step selected OpenCV's legacy top-level Windows-pack dispatcher, which
cannot classify the workstation's MSVC 19.42 runtime. The direct installed
static-package config exists and is the exact output of that build. The active
action is `stage15d_edpf_build_preflight_retry3`, an attachment-only repair
that selects that direct config and repeats the unchanged dataset-free compile
and smoke test. Validation and architecture work remain deferred.

Retry 3 reached the direct static package, but OpenCV 3.4's generated import
table referenced unused codec libraries excluded by the registered minimal
`core`/`imgproc` build. No EDPF source compiled and no dataset ran. The active
action is `stage15d_edpf_build_preflight_retry4`, an attachment-only harness
repair that imports the exact installed `core`, `imgproc`, and `zlib` artifacts
directly and repeats the unchanged synthetic smoke test. Dependency/source
versions, detector parameters, validation deferral, and architecture remain
unchanged.

Retry 4 configured successfully and began compiling the pinned author source,
but the grayscale-only harness unnecessarily included `EDColor.cpp`. Its unused
diagnostic `imwrite` call depends on the deliberately excluded OpenCV imgcodecs
module, so compilation stopped before linking or smoke execution. The selected
grayscale `EDPF(Mat)` path uses only `ED.cpp` and `EDPF.cpp`; author bytes and
detector behavior remain unchanged. The active action is
`stage15d_edpf_build_preflight_retry5`, an attachment-only source-surface repair
that compiles those exact required translation units and repeats the unchanged
synthetic smoke test. No dataset was read; validation and architecture work
remain deferred.

Retry 5 reached final linking but exposed two harness contracts: its default
`/MD` runtime did not match the pinned static OpenCV `/MT` build, and the
`ED(EDColor&)` overload compiled into `ED.cpp` requires author `EDColor`
definitions even when the selected grayscale constructor is the only executed
path. No smoke executable or dataset result was produced. The active action is
`stage15d_edpf_build_preflight_retry6`, an attachment-only repair that matches
the static runtime and compiles the complete required author surface against a
pinned OpenCV build including imgcodecs. Detector code, fixed parameters,
synthetic input, validation deferral, and MFI architecture are unchanged.

Retry 6 installed the required pinned OpenCV artifacts but its generated
static export table rejected absent `libprotobuf` and `quirc` archives for
unused modules before compiling the author source. The active action is
`stage15d_edpf_build_preflight_retry7`, an attachment-only CMake repair that
imports only the installed core/imgproc/imgcodecs and codec artifacts required
by the unchanged author source surface. The matched `/MT` runtime, synthetic
smoke input, detector parameters, validation deferral, and architecture remain
unchanged.

Retry 7 passed the complete dependency gate. The hash-verified, unmodified
author EDPF sources compiled against the pinned OpenCV 3.4.20 artifacts, and
the unchanged deterministic smoke test returned the same binary map in both
executions (`122` edge pixels; only `0/255`). The active action is now
`stage15d_edpf_exact_reproduction`, the single registered native-resolution
BSDS500-validation run. It preserves the author binary output, records
per-image runtime and hashes, emits the preregistered positions 1/50/100
qualitative panel, and attaches the common official evaluator. This is a
matched-protocol reproduction baseline only; MFI architecture work remains
deferred.

The exact Stage-15d EDPF reproduction completed on all 100 BSDS500 validation
images. It obtained local official-path ODS/OIS/AP
`0.548048/0.548596/0.000000`, versus incumbent
`0.545470/0.579328/0.534289`; the binary author output makes AP a documented
single-operating-point limitation. EDPF is retained as an exact, strictly
untrained chain-first reference baseline and does not change MFI. Its maps,
runtime/hashes, and fixed positions 1/50/100 preview are complete, while the
Stage-15a matcher-certification caveat remains.

The active next action is `stage15e_co_sco_reproduction_checkpoint`. It will
use live primary literature and official/author-designated code to audit the
CO and SCO color-opponent contextual methods, resolve immutable provenance,
fixed variants and parameters, training class, output conventions, and metric
compatibility, then register exactly one exact reproduction or fidelity
preflight. No dataset result may select parameters or variants, and MFI
architecture invention remains forbidden through Stage 15o.

The Stage-15e checkpoint resolved complete official institutional author-code
contracts for both CO and SCO. The active next action is now
`stage15e_co_sco_exact_reproduction`, a single paired native-resolution
BSDS500-validation run at the 2015 paper's BSDS300-train-fitted setting
(`sigma=1.1`, eight orientations, cone weight `-0.7`, SSC window `5`). Exact
CO provides the no-SSC control and exact SCO adds only the published modified
spatial-sparseness weighting. Both archives and every reachable source file are
hash-pinned; the research-only code remains ignored and unredistributed. The
run must preserve separate maps/runtime/hashes, emit the fixed positions
1/50/100 preview, and attach the common official evaluator. It is reproduction
and mechanism diagnosis only: no CO/SCO tuning or MFI change is authorized.

The exact Stage-15e paired run is complete. CO scored local official-path
ODS/OIS/AP `0.635925/0.665489/0.651767`, while SCO scored
`0.656582/0.682564/0.694939`; SCO therefore improved over its paired no-SSC
control by `+0.020656/+0.017076/+0.043173`. Both substantially exceeded the
unchanged MFI incumbent on this development validation split, but remain
parameter-fixed, author-tuned reference baselines. They are not integrated or
tuned, and the Stage-15a matcher-certification caveat still prevents a final
claim.

The active next action is `stage15f_compass_reproduction_checkpoint`. It will
use live primary literature and official/author-designated code to determine
whether Ruzon and Tomasi's Compass operator can be reproduced exactly or
faithfully under the common validation protocol. It must resolve the full
half-disc distribution-gradient contract before registering one run or one
fidelity preflight. Stage 14l is not a Compass reproduction, and MFI
architecture invention remains forbidden through Stage 15o.

The Stage-15f checkpoint recovered the complete official author MATLAB/C
archive and pinned it at SHA-256
`43e2ab843af620f5b6405843be0c5478b6953039c36b1e32b2a3ac725ddce7ea`.
The method is strictly untrained, and the prospective fixed path is the
published full-image sigma `4` setting with author defaults (spacing `1`,
180-degree edge model, six wedges per quadrant, 10 clusters). The papers do
not provide Berkeley metrics, and no validation result has been inspected.

The active next action is `stage15f_compass_build_preflight`, a dataset-free
compile and synthetic repeatability test of the unmodified 2004 MEX source.
It must characterize the source's clock-seeded randomized clustering without
patching the seed. A pass may register one exact-response validation run; a
build failure permits only external harness repair. No scale sweep, surrogate,
benchmark scoring, or MFI architecture change is authorized.

The initial preflight compiled but could not allocate its first output because
the 2004 gateway supplies a 32-bit `int` dimension vector to a modern default
MEX ABI expecting 64-bit dimensions. No dataset was read and no Compass map was
generated. The active next action is the attachment-only
`stage15f_compass_build_preflight_retry1`, which selects MATLAB's compatible
array-dimensions build mode for the unchanged author sources and repeats the
same synthetic smoke test. BSDS validation and MFI architecture work remain
deferred.

The compatible-array-dimensions retry passed: unchanged author code produced a
finite bounded synthetic maximum-EMD map, and no dataset was read. The active
next action is `stage15f_compass_exact_reproduction`, the single fixed
native-resolution BSDS500-validation run at published sigma `4` and author
defaults. It preserves maps/runtime/hashes, emits the preregistered positions
1/50/100 preview, and attaches the common official evaluator. The author's
clock-seeded clustering remains untouched and documented; no Compass tuning or
MFI architecture change is authorized.

The fixed Compass run generated all 100 validation maps and runtime rows, but
MATLAB exited with heap corruption only after printing its 100-image completion
marker. The active next action is the attachment-only
`stage15f_compass_exact_reproduction_retry1`: validate and hash those frozen
maps, emit the missing preview/provenance/official manifest, and attach the
unchanged evaluator without rerunning the randomized author detector. No
Compass tuning or MFI architecture change is authorized.

The Compass attachment is complete. Exact author-code Compass scored local
official-path ODS/OIS/AP `0.630841/0.656565/0.518359`, changing the unchanged
MFI incumbent by `+0.085418/+0.077086/-0.015936`. It is retained as a strictly
untrained external reference with a mixed best-F/full-ranking profile, not as
an MFI component; the fixed preview, hashes, maps and runtimes are complete.

The active next action is `stage15g_texture_surround_reproduction_checkpoint`.
It will use live primary literature and official/author code to audit the 2025
texture-gradient plus surround-modulation detector, resolve its fidelity and
complete fixed implementation contract, and register exactly one reproduction
or fidelity preflight. No MFI architecture invention is authorized before
Stage 15p.

The Stage-15g checkpoint found no article-specific author code or supplement.
A same-inventor patent (`CN115830051A/B`) strongly corroborates the published
retina/V1 texture-gradient/V2 endpoint/V4 mechanism, and the official BESD
repository at `eeb1f7e...` exposes related code, but neither is an exact
implementation contract for the target article. They conflict on Gaussian and
surround geometry, the patent leaves weights and output conventions unresolved,
and BESD accompanies a different paper with segment linking and feedback.

The active next action is therefore
`stage15g_texture_surround_fidelity_preflight`, a deterministic dataset-free
contract audit. It may not execute a detector, read a benchmark, or combine the
patent and BESD code into a surrogate. If the recorded conflicts remain, Stage
15g closes fidelity-unresolved and advances to the Stage-15h checkpoint. MFI
architecture remains unchanged and frozen through Stage 15o.

The preflight confirmed those conflicts and closed Stage 15g as
fidelity-unresolved without executing a detector or reading a dataset. The
patent and BESD implementation remain related evidence, not an executable
contract for the target article, and no surrogate may be synthesized from
them.

The active next action is
`stage15h_adaptive_surround_reproduction_checkpoint`, a high-reasoning live
primary-source and official-code audit of Zhang et al.'s adaptive multiscale V1
surround-modulation detector. It must settle implementation fidelity, fixed
parameters, training class, output conventions, and matched-validation
feasibility before registering one detector run or dataset-free fidelity
preflight. MFI remains frozen through Stage 15o.

The Stage-15h live audit found no article-specific code or supplement and no
complete public executable contract. Public primary material establishes a
strictly untrained contrast-adaptive, multiscale V1 surround mechanism and four
butterfly orientations, but leaves the full filters, adaptation law, scale and
orientation fusion, output/postprocessing, and matched evaluator unresolved.
The reported BSDS500 average optimal F-score `0.703` and NYUD follow-up remain
documentary and protocol-unverified. A related same-group contrast-adaptive
paper is not proven equivalent and may not supply missing choices.

The active next action is therefore
`stage15h_adaptive_surround_fidelity_preflight`, a deterministic dataset-free
implementation-contract audit. It may not run a detector or benchmark, invent
parameters, or combine related methods into a surrogate. If fidelity remains
blocked, Stage 15h closes unresolved and advances to the Stage-15i modern
fractional-reference checkpoint. MFI architecture remains frozen through Stage
15o.

The Stage-15h preflight confirmed the missing executable contract without
running a detector or reading a dataset. Complete filters, adaptation,
multiscale/orientation fusion, scalar output/postprocessing, and matched metric
conventions remain unresolved, and the non-equivalent predecessor cannot fill
them. Stage 15h is closed fidelity-unresolved; its reported metrics remain
documentary only.

The active next action is
`stage15i_fractional_reference_reproduction_checkpoint`. It will use live
primary literature and official/author code to audit the 2026 Fractional Dirac
detector, distinguish it from Stage 14s, and register exactly one exact
reproduction, faithful fixed reimplementation, or dataset-free fidelity
preflight. Fractional tuning and MFI architecture invention remain prohibited.

The Stage-15i audit found the official one-commit QFrD repository at
`8dcc8d846e6dcbe1bc4b931b89f1c814f5f9a245` and a complete code-defined
fixed detector path. QFrD is parameter-fixed but author-tuned, not learned. Its
paper reports BSDS500-test ODS/OIS/AP `0.6145/0.6361/0.5996`, which remain
documentary and protocol-separated from our future validation run. The audit
also records that the paper specifies left multiplier application while the
author code applies it on the right; exact-code reproduction is still possible,
but paper/code algebraic equivalence is not assumed. No code license or
requirements file is present, and the current project environment lacks
PyTorch/torchvision.

The active next action is `stage15i_qfrd_runtime_preflight`, a dataset-free
immutable-source/dependency audit and fixed synthetic repeatability smoke test.
It may repair runtime dependencies only after a recorded failure and may not
read BSDS, alter the author source, tune fractional parameters, or change MFI.
Only a pass may advance to one exact author-code BSDS500-validation
reproduction with maps, runtimes, hashes, the fixed positions 1/50/100 preview,
and the unchanged official evaluation attachment.

The first preflight produced no scientific feedback: a fresh `--no-checkout`
clone appeared dirty to the subsequent guard because all tracked files were
intentionally absent, and the runtime inventory confirmed missing
PyTorch/torchvision. The active next action is the harness-only
`stage15i_qfrd_runtime_preflight_retry1`. It uses a separate ignored checkout,
populates the pinned commit before the cleanliness check, installs pinned CPU
`torch==2.9.0` and `torchvision==0.24.0`, and repeats the identical dataset-free
source/synthetic preflight. BSDS access, QFrD parameter changes, author-source
changes, and MFI architecture work remain prohibited.

The repaired Stage-15i preflight passed immutable-source verification,
dependency checks, and bitwise-repeatable native-shape synthetic execution.
No benchmark was read. The active next action is
`stage15i_qfrd_exact_reproduction`: run the pinned exact author code once at
the frozen published defaults over BSDS500 validation, retain maps, runtimes
and hashes, emit the fixed positions 1/50/100 preview, and attach the common
official evaluator against the unchanged incumbent. This remains a baseline
reproduction; QFrD/fractional tuning and MFI redesign remain prohibited.

The exact Stage-15i QFrD reproduction is complete. On BSDS500 validation it
obtained ODS/OIS/AP `0.587261/0.618621/0.583650`, improving the unchanged MFI
incumbent by `+0.041849/+0.039265/+0.049373`; mean runtime was about `1.168`
seconds per image. QFrD remains a parameter-fixed, author-tuned reference only.
Its paper/code multiplication-order caveat and the local evaluator's
reference-uncertified status remain explicit, and no fractional or MFI tuning
is permitted from this result.

The active next action is `stage15j_high_number_protocol_audit_checkpoint`.
This live-primary-literature checkpoint will classify unusually high reported
non-trained edge F/F1 values by split, threshold scope, matcher/tolerance,
annotation protocol, thinning/NMS, resizing, and output multiplicity. It will
register at most one fidelity-labeled reproduction/preflight, or close the
audit and transition to Stage 15k. Architecture invention remains prohibited.

Stage 15j closed without a new reproduction target. Primary sources showed
that the Gao Gabor-Sobel `0.888` F1 and BPAED headline F1 use incompletely
specified direct/generic metrics rather than a verified Berkeley ODS contract.
FACAFCV independently illustrates the mismatch: its noisy-image optimal F can
reach `0.8910`, while its separate BSDS500 ODS is `0.589`. These numbers do not
alter the matched non-trained frontier or justify a surrogate implementation.

The active next action is `stage15k_per_image_oracle_matrix`. It parses the
existing official per-image count tables for frozen MFI, SED, EDPF, CO, SCO,
Compass and QFrD outputs, produces pairwise win/loss and descriptive oracle
complementarity artifacts, and emits the fixed positions 1/50/100 preview. It
does not rerun detectors or the stochastic matcher and cannot authorize a
router or MFI architecture change. Stage 15l follows after this diagnosis.

Stage 15k is complete. Exact SED was the strongest frozen single reference at
the nearest raw ODS threshold (aggregate F1 `0.678500`), while the descriptive
ground-truth per-image method oracle reached `0.697054` (`+0.018554`). The
oracle selected non-SED methods on 48/100 images, but it is not deployable and
does not authorize routing or MFI redesign.

The active next action is `stage15l_image_regime_characterization`. It uses
only frozen validation outputs and existing per-image counts to test
predeclared image-regime associations. No detector/matcher rerun, fitted
router, architecture change, or protected-split access is permitted. Stage
15m follows after this diagnostic.

Stage 15l is complete. Structural regime measures carried the clearest
associations: SED and especially EDPF improved relative to MFI as incumbent
fragmentation and edge density rose, while larger incumbent components showed
the reverse pattern. These descriptive validation associations cannot define
a router or alter MFI.

The active next action is `stage15m_pixel_segment_complementarity`. It analyzes
the seven frozen methods at their previously reported thresholds using fixed
pixel-support and connected-component definitions, with a deterministic
positions 1/50/100 preview and an official attachment over frozen maps. It may
characterize localization, weak-boundary recovery, texture/unsupported
response, and continuity, but it may not fit a router or change MFI before the
Stage-15 diagnostic sequence reaches its preregistered redesign gate.

Stage 15m is complete. The frozen-map proximity diagnosis found that SED has a
much lower unsupported response and stronger supported-component profile than
MFI, while both preserve substantial unique GT-supported pixels. The result is
descriptive complementarity, not a routing or architecture decision. The
redundant official attachment failed under the known intermittent Windows
MATLAB matcher corruption and will not be retried because no new detector or
official metric was required by the diagnosis.

The active next action is `stage15n_uded_bsds_discrepancy_audit`. It uses
existing UDED-selection repeated-CV tables and existing BSDS500-validation
official count tables for the fixed Stage-14r SE(2) and Stage-14s Riesz
mechanisms, together with fixed image-internal regime measures. It tests the
dataset/error-regime explanation for their opposite cross-dataset deltas
without rerunning detectors or matching, fitting a router, or changing MFI.
Stage 15o remains the next and final diagnostic gate before any conditional
generation-2 architecture experiment.
