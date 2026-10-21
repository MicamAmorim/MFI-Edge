# MFI-Edge persistent scientific context

This file is the compact scientific memory injected into every autonomous Codex decision. Keep it current whenever the interpretation, incumbent architecture, dataset roles, or long-horizon goal changes. It is not a substitute for experiment-specific preregistrations or `docs/paper/EXPERIMENT_HISTORY.md`; it is the high-signal context needed so fresh agent invocations do not reason from an isolated benchmark result.

## Long-horizon objective

Develop an **interpretable, non-neural edge/boundary detector** that can surpass the strongest verified neural-network methods in the literature **under matched official protocols and across multiple datasets**, not by overfitting a single benchmark. The agent is authorized to prune, combine, redesign, and promote new classical/fuzzy/non-neural models and methodologies as development evidence justifies them.

The target is generalization, not a one-dataset leaderboard trick. A final `goal_reached=true` requires the current SOTA ledger in `docs/paper/SOTA_TARGETS.md` to be refreshed from primary sources and the frozen MFI-Edge generation to satisfy its multi-benchmark gate under official or author-designated evaluation without test-driven tuning.

No neural network, pretrained neural feature extractor, learned deep embedding, or neural postprocessor may be part of the final MFI-Edge inference path. Classical optimization, fuzzy measures/integrals, analytical descriptors, statistical estimation, hand-designed multiscale features, non-neural learned parameters on development data, and interpretable routing are allowed.

## Core architectural thesis

The strongest surviving thesis is separation of roles:

- **MFI / multiscale signature = context:** is this structure boundary-like, persistent, and trustworthy rather than texture/noise?
- **Scharr + NMS = precise localization:** where is the local boundary response?
- Do not force the fuzzy contextual score itself to be the final edge map unless development evidence overturns this separation.

Current incumbent lineage:

`image -> conditioning -> oriented multiscale descriptors -> compact positive fuzzy context -> context gate -> Scharr+NMS localizer -> frozen/fold-fitted threshold -> edge map`

After Stage 14d, the provisionally retained compact positive bank is:

- `gabor4_s5`
- `hessian_s7`
- `gabor4_s13`
- `hessian_s13`
- `gabor4_scale_persistence`

Current positive aggregation parameters inherited from Stage 12d development: distorted-Choquet gamma `0.55`, context-gate strength `2.0`, floor `0.10`. Scale persistence is retained because removing it in Stage 14d reduced repeated-CV F1.

## Key experimental history

### Stage 10 — CH-MFI-v2

Broad contextual/hierarchical architecture, 519 configurations. Best held-out F1 `0.71325` versus Scharr `0.76204` (delta `-0.04879`). This motivated stronger separation of contextual discrimination and local pixel localization. Earlier broad d-family variants were weaker in that architecture/protocol; this is evidence against blind broad RDF sweeps, not a universal rejection of d-Choquet-like operators.

### Stage 11/11b — edge signature

`oriented_ms` removed duplicate descriptor-scale artifacts present in the earlier schedule. A logistic diagnostic achieved held-out AUC about `0.6992`, AP `0.5029`; it was diagnostic evidence, not a detector. Stable positive evidence concentrated in Gabor/Hessian responses and cross-scale persistence. Stable anti-texture evidence concentrated in scale-location/distribution properties of curvature-like responses.

### Stage 12a — fixed localizer signature gate

A contextual signature multiplicatively gating fixed Scharr+NMS avoided the large degradation of Stage 10. Gain was tiny (`+0.00020` held-out F1) and not a strong performance claim, but it validated the context/localizer separation.

### Stage 12b/12c

Initial fuzzy signature experiments revealed a CV leakage issue in feature-bank selection. Stage 12c corrected it by fitting bank selection, memberships, and thresholds inside folds. Historical held-out observations after this point are development history only and must not drive Stage 14 optimization.

### Stage 12d — repeated leakage-free bipolar CV

5 repeats x 3 folds on UDED selection.

- positive control: CV F1 about `0.758894`, development delta vs Scharr `+0.00794`
- separable bicapacity: about `0.758105`
- ratio control: about `0.756688`

Correct conclusion: positive fuzzy signature was the robust development winner; bicapacity was close but did not establish incremental negative-evidence benefit; ratio was a control, not the selected winner.

Positive-feature stability included `gabor4_s5`, `hessian_s7`, `gabor4_s13`, `hessian_s13`, and `gabor4_scale_persistence` in every Stage-12d split.

### Stage 13 — frozen external transfer

External results are documentation only and cannot choose Stage 14 architectures or parameters.

BSDS proxy fixed operating point: Scharr about `0.19104`; positive `+0.00205`, bicap `+0.00248`, ratio `+0.00333` over Scharr. This used a local tolerant matcher, not the official Berkeley evaluator.

BIPEDv2 frozen fixed-threshold diagnostics: Scharr `0.73702`, positive `0.72541`, bicap `0.73385`, ratio `0.74607`. Ratio won 49/50 images in that external diagnostic, but this **must not** retroactively make it the development winner or guide Stage 14 optimization.

### Stage 14b — polarity mechanism ablation

UDED-selection repeated leakage-free CV. Spatially aligned negative evidence did not beat an image-mean-negative control. Primary contrast mean fold delta about `-0.00213` with 6 wins / 9 losses. Conclusion: no development support for spatial anti-texture alignment in that mechanism. This does not prove all negative information is useless.

### Stage 14c — positive-bank pruning

Five universally stable positive features matched/slightly exceeded the fold-trained full bank (`0.75905` vs `0.75889` aggregate F1). Difference was tiny and not a performance claim; value was simplification and stability. Compact five-feature bank retained provisionally.

### Stage 14d — persistence ablation

Removing `gabor4_scale_persistence` reduced aggregate F1 to about `0.75473` versus `0.75889`, mean paired fold delta about `-0.00322`, 3 wins / 12 losses. Persistence is therefore retained.

### Stage 14f — targeted RDF robustness falsification

Compared retained standard positive distorted-Choquet against d-CC with FBPC and absolute RDF on paired synthetic corruption conditions, clean-calibrated thresholds frozen across corruption. The authoritative preregistration is `docs/paper/STAGE14F_PREREGISTRATION.md`.

Result: d-CC was **not promoted**. Mean absolute corrupted-F1 advantage about `-0.00191`, clean delta about `-0.00280`, and positive absolute advantage in `0/4` corruption families. Descriptive clean-referenced degradation advantage was only about `+0.00088`. Conclusion applies to this isolated d-CC/FBPC/abs test; do not claim RDF operators are universally disproven.

### Stage 14g/14h — gravitational conditioning falsification

Post-RDF high-reasoning literature review selected a targeted gravitational-conditioning ablation as a mechanistically distinct test. Stage 14h did **not** promote gravitational smoothing: mean corrupted-F1 advantage was about `+0.00534`, but clean F1 fell by about `-0.27231` and only the texture family improved (`1/4` families positive). The candidate therefore failed two required criteria and median conditioning remains incumbent. The texture-specific gain is descriptive evidence of regime complementarity, not permission to route on known corruption labels or to tune the smoother. The next step is a literature/mechanism escalation rather than further gravitational or RDF micro-tuning.

### Stage 14i — topology-repair falsification

Stage 14i did **not** promote fixed MFI/context-guided geodesic endpoint
linking on UDED-selection repeated leakage-free CV. Relative to the no-link
control, aggregate F1 changed by `-0.01519`, mean fold F1 by `-0.01134` with
`0/15` fold wins, and mean paired largest-component GT coverage by only
`+0.00156` versus the preregistered `+0.03` requirement. Precision changed by
`-0.00304`, and coverage improved in 12/15 folds, but all four criteria were
required. The no-link compact positive controller remains incumbent. Do not
micro-tune this linker from Stage-14i outcomes; proceed to a mechanistically
distinct literature escalation.

### Stage 14j — phase-congruency context falsification

Appending one fixed-default Kovesi PC2 maximum phase-congruency covariance
moment to the retained five-feature positive bank did **not** pass the
preregistered UDED-selection repeated-CV promotion rule. The phase feature was
training-eligible in 15/15 folds, but aggregate F1 changed by `-0.000361`, mean
fold F1 by `-0.000251`, and the candidate won only 6/15 folds. Aggregate
precision changed by `-0.000589`. This shows that the fixed phase moment is
individually discriminative under the training eligibility test but does not
establish incremental context value in the current distorted-Choquet gate.
The compact five-feature controller remains incumbent. Do not tune phase
parameters or advance the deferred phase/gradient router from this result;
proceed to a mechanistically distinct literature escalation.

### Stage 14k — vector-color localization falsification

Stage 14k did **not** promote the fixed CIELAB Di Zenzo tensor localizer on
UDED-selection repeated leakage-free CV. Relative to grayscale Scharr+NMS,
aggregate F1 changed by `-0.01154`, aggregate precision by `-0.01325`, and mean
fold F1 by `-0.01205`, with only 1/15 fold wins. All preregistered criteria
failed. Grayscale Scharr+NMS remains incumbent. Do not tune color weights,
grayscale/color mixtures, routers, or tensor parameters from this result. The
next step is a mechanistically distinct literature escalation rather than
vector-color micro-tuning.

### Stage 14l — texture-distribution context falsification

Stage 14l did **not** promote the fixed oriented half-disc uniform-LBP
histogram chi-square feature on UDED-selection repeated leakage-free CV. The
candidate changed aggregate F1 by only `+0.000310` and mean fold F1 by
`+0.000370`, with 6/15 fold wins; the feature was training-eligible in only
7/15 folds. Although precision was effectively unchanged (`-0.000040`), the
candidate failed the preregistered aggregate-gain, fold-win, and eligibility
requirements. The compact five-feature positive controller remains incumbent.
Do not tune the LBP descriptor, half-disc geometry, eligibility threshold, or
fusion from this result. Proceed to a mechanistically distinct live-literature
escalation without held-out or external-test feedback.

### Stage 14m — linear cue-fusion falsification

Stage 14m did **not** promote the fold-fitted, class-balanced L2 logistic
probability-of-boundary fusion on UDED-selection repeated leakage-free CV.
Relative to the compact Choquet controller, aggregate F1 changed by
`-0.004972`, mean fold F1 by `-0.006046`, and the candidate won only 4/15
folds. All 15 models converged and precision increased by `+0.005232`, but
recall fell enough to fail the aggregate-gain, mean-fold, and fold-win
requirements. The compact five-feature controller remains incumbent. Do not
tune regularization, sampling, interactions, or classifier variants from this
result. Proceed to a mechanistically distinct live-literature escalation
without held-out or external-test feedback.

### Stage 14n — shallow edge-forest localizer falsification

Stage 14n did **not** promote the fixed shallow randomized forest on UDED-
selection repeated leakage-free CV. Relative to the compact Choquet
controller, aggregate F1 changed by `-0.024925`, aggregate precision by
`-0.038556`, and mean fold F1 by `-0.025724`, with only 2/15 fold wins. All
15 models produced finite predictions and the forest nearly preserved recall
(`+0.000993`), but its precision loss defeated every performance requirement.
The compact five-feature positive controller with grayscale Scharr+NMS remains
incumbent. Do not sweep forest size, depth, leaves, sampling, channels, or
calibration from this result, and do not infer that full structured-patch
forests were tested. Proceed to a mechanistically distinct live-literature
escalation without held-out or external-test feedback.

### Stage 14o — registered interval-uncertainty capacity falsification

The post-forest literature escalation selected one fixed interval-valued
uncertainty mechanism. Cue disagreement across the retained five memberships,
normalized by outer-training-fold statistics, defines interval width; the same
uncertainty convexly interpolates the retained gamma-0.55 capacity toward its
additive counterpart, and Choquet-envelope width attenuates unreliable
context. The compact bank, grayscale Scharr+NMS, gate strength, and floor are
unchanged. Stage 14o is registered on UDED-selection 5x3 leakage-free CV and
must attach official BSDS500-validation MATLAB ODS/OIS/AP through its frozen
native-resolution exporter. Promotion is conjunctive across the preregistered
UDED non-collapse and BSDS-val benefit criteria. Do not tune interval width,
normalization quantile, capacity endpoints, gamma, or gate from the result.

The UDED portion failed all non-collapse criteria: aggregate F1 delta
`-0.00980`, precision delta `-0.01532`, mean fold-F1 delta `-0.00798`, and
`0/15` fold wins. The sixth attachment-only retry then completed official
BSDS500-validation scoring. The candidate improved ODS by `+0.00225` and OIS
by `+0.00182`, but reduced AP by `-0.00100`, failing the required AP
condition. Together with the decisive UDED failure, Stage 14o is closed
without promotion. The evaluator now completes through isolated native
matching and pure-MATLAB aggregation processes, but reference-detector
reproduction remains unverified and no final SOTA claim may rely on it. Do not
rerun the CV or tune the interval mechanism.

### Stage 14p — MFI-coupled Ambrosio–Tortorelli falsification

Stage 14p did **not** promote the fixed MFI-coupled Ambrosio–Tortorelli phase
field. Relative to the compact controller, UDED aggregate F1 changed by
`-0.08044`, aggregate precision by `+0.05194`, and mean fold F1 by `-0.08243`,
with `0/15` fold wins. The recall collapse defeated the UDED F1 and fold-win
conditions despite higher precision. On official
BSDS500 validation, ODS improved by `+0.00522`, but OIS changed by `-0.00286`
and AP by `-0.04888`. The conjunction therefore failed decisively. The
compact positive Choquet gate with grayscale Scharr+NMS remains incumbent.
Do not tune the phase-field coefficients or discretization from this result.

### Stage 14q — anisotropic singularity localizer falsification

The fixed eight-atom shearlet-motivated localizer failed the UDED portion of
its conjunctive rule. Relative to compact Choquet-gated Scharr+NMS, aggregate
F1 changed by `-0.03116`, mean fold F1 by `-0.03135`, and recall by
`-0.10655`, with only `1/15` fold wins; precision increased by `+0.01979`.
This is a recall-collapse falsification of this fixed discrete atom bank, not
of continuous shearlet theory. On official BSDS500 validation, ODS improved by
`+0.00334`, but OIS changed by `-0.00089` and AP by `-0.01526`. The conjunctive
rule therefore failed on both development axes. The candidate cannot be
promoted or tuned; grayscale Scharr+NMS remains the incumbent. This triggered
the live-literature/mechanism checkpoint documented below.

### Stage 14r — SE(2) contour-enhancement falsification

Stage 14r did **not** promote the fixed confidence-stopped SE(2) contour
enhancement. It improved official BSDS500-validation ODS/OIS/AP by
`+0.00381/+0.00169/+0.00779`, respectively, but failed every preregistered
UDED/continuity condition: aggregate F1 `-0.00276`, precision `-0.00699`, mean
fold F1 `-0.00203`, only `5/15` fold-F1 wins, mean largest-component GT
coverage `-0.00201`, and only `4/15` coverage wins. The conjunctive rule
therefore rejects the candidate. This is evidence against this fixed hard
lift, diffusion, and max-projection realization, not against SE(2) theory.
Do not tune its discretization or fusion from the mixed result. The compact
Choquet-gated grayscale Scharr+NMS controller remains incumbent; proceed to a
live-literature checkpoint for a mechanistically distinct falsification.

### Stage 14s — fractional Riesz localizer falsification

Stage 14s did **not** promote the fixed half-order isotropic spectral
Riesz-gradient localizer. It improved official BSDS500-validation ODS/OIS/AP
by `+0.01161/+0.00505/+0.01804`, but failed every preregistered UDED condition:
aggregate F1 `-0.03599`, precision `-0.02286`, mean fold F1 `-0.03583`, and
`0/15` fold wins. The explicitly conjunctive rule therefore rejects the
candidate. This is a mixed cross-dataset result against this fixed spectral
realization, not against fractional differentiation generally. Do not tune
fractional order, padding, normalization, orientation, or fusion from the
result. Grayscale Scharr+NMS remains incumbent. The discrepancy triggers a
live-literature/mechanism checkpoint before the next bounded falsification.

### Post-Stage-14s checkpoint — Stage 14t registered

The live primary-literature checkpoint did not select another localizer. The
repeated BSDS-positive/UDED-negative pattern in Stages 14r–14s instead motivates
one fixed a-contrario reliability test over the unchanged incumbent score.
Stage 14t uses a conservative number-of-false-alarms model over connected upper
level components to attenuate responses without statistically meaningful
support. It is explicitly a repository-specific connected-component surrogate,
not a reproduction of the full level-line meaningful-boundaries algorithms of
Desolneux et al. or Tepper et al. UDED-selection repeated CV and official
BSDS500 validation remain conjunctive, and no NFA, quantization, connectivity,
sampling, or attenuation parameter may be tuned from the result. Dempster–
Shafer ignorance and pure threshold-persistence remain deferred alternatives.

### Stage 14t — a-contrario meaningfulness falsification

The fixed connected-support NFA surrogate failed every preregistered UDED
condition. Relative to the unchanged compact controller, aggregate F1 changed
by `-0.01725`, aggregate precision by `-0.02083`, and mean fold F1 by
`-0.01602`, with only `1/15` fold wins. The frozen official BSDS500-validation
attachment also changed ODS/OIS/AP by `-0.01257/-0.01761/-0.02830`. The
candidate therefore failed both development axes and is not promoted. Do not
tune the NFA, null, quantization, connectivity, sampling, floor, or fusion from
this result. The compact Choquet-gated grayscale Scharr+NMS controller remains
incumbent. Route next to a live-literature/mechanism checkpoint before choosing
among deferred Dempster–Shafer ignorance, threshold persistence, PDE
conditioning, or a mechanistically different alternative.

### Stage 14u - Yager evidential-ignorance falsification pending attachment

The fixed three-source Yager-rule fusion failed the preregistered UDED gate.
Relative to the compact controller, aggregate F1 changed by `-0.00245`, mean
fold F1 by `-0.00171`, and recall by `-0.00781`; precision increased only
`+0.00072`, and the candidate won `3/15` folds. The fixed realization therefore
cannot be promoted or tuned. The required official BSDS500-validation
attachment failed during incumbent native matching after 37/100 images with
intermittent Windows MATLAB heap corruption, and its first frozen retry failed
after 12/100. A second attachment-only retry is registered with resumable
per-image matching across fresh MATLAB processes; it does not rerun CV, alter
predictions or vendor matching code, or change the scientific decision from
UDED. The compact Choquet-gated grayscale Scharr+NMS controller
remains incumbent. After the frozen attachment completes, route to a live
literature/mechanism checkpoint rather than tuning masses, sources, conflict
handling, the decision transform, gamma, or the gate.

### Stage 15 transition — reproduction and diagnosis program active

The project has paused architecture invention through Stage 15o. Stage 15a is
registered as the first action: reproduce the five-image evaluator fixture
shipped with the pinned BSDS500 code, audit native validation images and all
annotations, and establish fixed Canny, ungated repository Scharr+NMS, and the
unchanged incumbent under the same official BSDS500-validation path. This is a
measurement/reproduction stage, not a promotion experiment. Its deterministic
preview uses sorted validation positions 1, 50, and 100. After Stage 15a is
closed, follow the preregistered Stage-15 reproduction sequence beginning with
the SED baseline; do not design a new MFI architecture before Stage 15p.

The first Stage-15a controller attempt failed because it launched under a
system Python without scikit-image. A repository-environment repair is now in
place, but an existing frozen fixture run also missed the preregistered `1e-4`
agreement bound on ODS and OIS (`0.000171` and `0.000259`; AP error
`0.000059`). Stage 15a therefore remains open. Diagnose the fixture/platform
drift without relaxing the registered tolerance or running the full validation
attachment; this is evaluator fidelity work, not detector feedback.

The first fixture diagnostic preserved hashes and found systematic differences
in aggregate, per-image, and per-threshold tables, but could not yet separate a
wrapper defect from compiled-platform variation. A fixture-only equivalence
test is registered between the repository compatibility path and Piotr
Dollár's documented BSDS-compatible `edgesEvalImg`, using the same pinned
Windows matcher and fresh-process repetition. Its first launch stopped before
matching because the pinned `edgesEvalImg` depends on `getPrmDflt` from
Dollár's separate MATLAB toolbox. An attachment-only retry is registered with
a strict repository-local parser for the explicit diagnostic arguments; no
vendored evaluator code, tolerance, fixture, or detector is changed. Full
validation and Stage 15b remain deferred; no architecture work is authorized.

That parser-repaired retry stopped before matching because the local harness
passed RGB fixture photographs instead of the shipped single-channel PNG
boundary predictions to `edgesEvalImg`; `bwmorph` rejected the resulting 3-D
map. This is a diagnostic-harness defect and provides no evaluator or detector
feedback. A second attachment-only retry is registered with the correct PNG
inputs, leaving evaluator code, matcher, tolerance, and architecture unchanged.

The corrected retry completed but failed its equivalence condition. The two
fresh runs of the identical Piotr Dollar path differed by up to `0.000507` in
aggregate tables and seven raw match-count units; wrapper-versus-Piotr-Dollar
differences reached `0.000757`. Thus the pinned Windows binary/path is not
repeatable enough to certify the registered `1e-4` fixture tolerance, and the
drift cannot be assigned solely to the repository wrapper. Stage 15a remains
open. One fixture-only diagnostic is registered to compile the exact pinned
BSDS500 C++ matcher sources outside the vendor tree, record build provenance,
and repeat the unchanged fixture. Full validation, Stage 15b, and architecture
work remain deferred.

The first source-build launch failed before matching because the pinned
Unix-era sources require POSIX/legacy declarations absent under MSVC. A hashed
repository-local compatibility include layer now permits an MSVC 2022 compile
smoke test without changing vendored source bytes or matching logic. One
attachment-only fixture retry is registered; validation scoring, Stage 15b,
and architecture work remain deferred.

That retry built the matcher but stopped before fixture matching because a
repository-local assertion compared equivalent Windows paths with different
slash conventions. A second attachment-only retry is registered after path
separator normalization. This is harness-only repair: matcher sources and
logic, fixture, tolerance, validation deferral, and architecture are unchanged.

The separator-normalized retry stopped at MATLAB parse time because its local
fixture harness omitted the audited R2023a syntax mirror already used by the
repository evaluator for pinned `evaluation_bdry_image.m`. A third
attachment-only retry is registered with that syntax-only run-local transform;
vendored bytes, rebuilt matching logic, fixture, `1e-4` tolerance, validation
deferral, and architecture remain unchanged.

## d-Choquet terminology

Do not conflate these:

- **distorted-capacity Choquet:** gamma changes capacity weighting; ordinary Choquet increments remain.
- **d-Choquet / d-CF / d-XC / d-CC:** a restricted dissimilarity function changes the increment/difference construction.

Repository `src/advanced_fuzzy_v2.py` implements RDFs including abs, square, sqrt, x2 and sqrt2 plus an exploratory sine variant. Relevant primary paper: Amorim et al. (2025), *Generalizations of Choquet-like Integrals by Restricted Dissimilarity Functions Applied to Multi-Channel Edge Detection Problems*, Applied Sciences 15(24):13273, DOI 10.3390/app152413273.

## Dataset and feedback firewall

Allowed optimization/development feedback:

- synthetic development/validation sets explicitly designated development before inspection;
- UDED selection with leakage-free repeated CV;
- future splits explicitly predesignated as development before looking at target results.

Historically inspected / unavailable for optimization:

- UDED held-out;
- BSDS500 test;
- BIPEDv2 test;
- any future final/external split after it is inspected.

Never choose architecture, features, thresholds, operator family, experiment priority, hyperparameters, or routing rules from those inspected external/final outcomes.

A redesigned generation must be developed on allowed data, frozen, and then evaluated on a genuinely untouched external dataset/protocol if a new generalization claim is needed.

## Research behavior

The agent may autonomously:

- prune redundant features, branches, operators, and postprocessing;
- design and test new classical/fuzzy/non-neural descriptors and aggregation mechanisms;
- combine mechanisms only after development evidence of complementarity, or when a preregistered research checkpoint provides a clear mechanistic justification;
- create small interpretable routing/mixture-of-experts controllers using non-neural rules or non-neural statistical models;
- design robustness tests, synthetic stress tests, topology/connectivity metrics, calibration analyses, and efficiency analyses;
- search current literature at research checkpoints and update the SOTA ledger;
- freeze/promote a new model generation when repeated development evidence is stable;
- continue research automatically after a failed hypothesis by escalating to literature/mechanism search rather than stopping for ordinary scientific uncertainty.

Avoid endless micro-tuning. After repeated failures within one mechanism family, move to a mechanistically different direction. Broad sweeps are acceptable only when hypothesis-led work has justified the family and the sweep is development-only, bounded, and documented.

## Human interruption policy

Routine scientific decisions are **not** human blockers. Documentation conflicts with resolvable provenance, failed hypotheses, uncertain next mechanism, literature review, ablation design, pruning, combination design, and preregistration should be handled autonomously.

`requires_human=true` is reserved for a real external blocker such as credentials/license acceptance, a protected-lineage edit that policy forbids, a destructive/environmental action outside the allowed sandbox, or an irreducible methodological ambiguity whose resolution would change the validity of a final claim.

The user can stop at any time by creating `automation/STOP` or terminating the process.

## Visual reporting requirement

Every image-based development benchmark from this point forward should emit deterministic qualitative artifacts alongside metrics. At minimum include `best_method_preview.png`, generated from predeclared/fixed representative examples rather than result-driven cherry-picking. The report must state the panel layout and which retained/current-best method is shown. Prefer a comparison panel containing input, ground truth, incumbent prediction, candidate prediction, and a current-best-only panel when practical.

Qualitative images are for inspection and evolution tracking only; they must not silently become the optimization signal.

## Goal-state discipline

Do not declare success because one development split beats one neural number. Before setting `goal_reached=true`:

1. refresh `docs/paper/SOTA_TARGETS.md` using current primary literature and official benchmark sources;
2. freeze the candidate before final evaluation;
3. evaluate with official/author-designated protocols and matched metrics;
4. exceed the strongest verified neural result in the declared multi-benchmark generalization suite, with at least one genuinely untouched external evaluation;
5. preserve the no-neural inference constraint;
6. document runtime, parameter count/learned degrees of freedom, and qualitative outputs;
7. ensure no final/test data influenced development choices.

Until that gate is met or the user stops the process, continue autonomously within the scientific firewall.

### Stage-15a closure and Stage-15b transition

The final fixture-only causal diagnostic fixed the pinned matcher's global RNG
to preregistered seed `1` in a result-local source copy. Two fresh MATLAB
processes then produced identical aggregate, per-image, and per-threshold
fixture tables (all repeat deltas exactly zero), confirming clock-seeded random
sampling as the source of the earlier drift. Controlled-versus-shipped table
differences still reached `0.000866`. Stage 15a therefore closes without
reference reproduction verification: the fixed-seed binary is diagnostic-only
and may not score datasets, and the unmodified Windows official path remains
stochastic and uncertified for final claims.

The next registered action is a high-reasoning/live-literature Stage-15b SED
reproduction checkpoint. It must establish author-code availability, published
fixed parameters, training classification, implementation fidelity, and the
matched evaluation plan before registering one detector run. Architecture
invention remains prohibited through Stage 15o.

### Stage-15b checkpoint closure and exact reproduction registration

Primary-source review verified the authors' public MATLAB SED implementation
at commit `11514b80162e5cd93fd244515189649656105a14`. The method is strictly
untrained with fixed author parameters, and the repository states that the
MATLAB implementation produced the manuscript F-measures; the C++ path was
timing-only. The paper's colour BSDS500-test ODS/OIS/AP
`0.71/0.74/0.74` remains documentary and separate from our validation run. A
one-image R2023a smoke test passed with finite native-size output in `[0,1]`.
No explicit source license was found, so the hash-verified author code remains
an ignored local dependency and is not redistributed.

The registered next action is `stage15b_sed_exact_reproduction`: run the
unmodified author full model over native-resolution BSDS500 validation, emit
per-image maps/runtime/hashes and fixed positions 1/50/100 preview, then attach
the default official validation evaluator against the unchanged incumbent.
This is a baseline reproduction, not an MFI promotion experiment. Stage-15a's
stochastic/reference-uncertified Windows matcher caveat remains, and the
fixed-seed diagnostic matcher is forbidden for dataset scoring. No SED tuning
or MFI architecture change is authorized.

The first exact-run launch failed before SED execution because Git's ownership
guard rejected the ignored author checkout created under the sandbox account.
This provides no scientific feedback. A harness-only retry is registered with
a process-local trust override limited to the immutable, hash-verified author
checkout; no global Git setting, author byte, detector parameter, dataset role,
serialization rule, preview position, or evaluator protocol changes.

### Stage-15b exact SED reproduction complete; Stage-15c checkpoint registered

The harness-only retry completed the exact pinned author MATLAB SED full model
on all 100 native-resolution BSDS500 validation images. Under the common local
official path, SED obtained ODS/OIS/AP
`0.678546/0.709152/0.712814`, exceeding the unchanged MFI incumbent by
`+0.133122/+0.129816/+0.178518`. Mean detector export runtime was `3.419`
seconds per image. The fixed positions 1/50/100 preview, per-image maps,
runtimes, and hashes are complete.

SED is retained only as a strictly untrained exact-code reference baseline;
this reproduction does not promote or alter MFI, and the paper's BSDS500-test
numbers remain separate. The unmodified Windows matcher is still stochastic
and reference-uncertified, so no final SOTA claim may rely on the local score.
The next action is `stage15c_vcm_reproduction_checkpoint`: live primary-source
research must resolve code availability, fixed parameters, training class, and
metric compatibility for Lu et al.'s vector co-occurrence morphological colour
edge detector before registering one fidelity-labeled run. Architecture
invention remains prohibited through Stage 15o.

### Stage-15c checkpoint - VCM fidelity unresolved

The primary Lu et al. paper describes a strictly untrained HSV/HDHSV vector
morphology detector and reports BSDS500 ODS/OIS/AP `0.76/0.79/0.77`, but no
author code or supplement was located. The paper omits enough fixed parameters
and output/evaluator conventions that neither an exact reproduction nor a
faithful reimplementation is currently justified; the reported metrics remain
documentary and protocol-unverified. A single deterministic, dataset-free
`stage15c_vcm_fidelity_preflight` is registered to preserve the missing
implementation contract. Do not invent parameters or score a VCM surrogate.
If the preflight confirms the blockers, close Stage 15c as unresolved and
advance to the Stage-15d Edge Drawing/EDPF checkpoint without changing MFI.

### Stage-15c closure and Stage-15d transition

The dataset-free VCM fidelity preflight confirmed that public primary material
does not resolve the output-affecting implementation contract. No detector or
dataset was run, no surrogate was scored, and the reported BSDS500
`0.76/0.79/0.77` remains documentary and protocol-unverified. Stage 15c closes
as fidelity-unresolved without changing MFI.

The registered next action is `stage15d_ed_edpf_reproduction_checkpoint`, a
high-reasoning live-primary-literature and official-code audit of Edge Drawing
and EDPF. It must establish immutable author-code provenance, fixed parameters,
training class, build/output conventions, and a matched BSDS500-validation plan
before one fidelity-labeled run. Stage 14t's connected-component NFA surrogate
is not a reproduction or falsification of full chain-level EDPF. Architecture
invention remains prohibited through Stage 15o.

### Stage-15d checkpoint - exact EDPF source resolved; build preflight registered

Primary papers and the official ED_Lib repository support an exact grayscale
EDPF reproduction at immutable MIT-licensed commit
`69b8d081bd6d28192d816ec0ed02aff9186d73c1`. It is strictly untrained with
fixed author-code settings and returns a native binary `CV_8UC1` map. ED first
constructs contiguous pixel chains; EDPF then applies the author chain-level
Helmholtz/NFA validation. Stage 14t's connected-component attenuation is not
equivalent. A future official BSDS500-validation run must preserve the binary
0/255 output, report the single-operating-point AP limitation, and retain the
Stage-15a stochastic/reference-uncertified matcher caveat.

The current workstation has no resolved C++ OpenCV development configuration,
and its Python OpenCV lacks the Edge Drawing binding. The single registered next
action is the dataset-free `stage15d_edpf_build_preflight`: hash-verify and
compile the unmodified pinned author source through an external harness, then
run a deterministic synthetic binary-output smoke test. Only a pass may advance
to exact native-resolution BSDS500-validation reproduction. A failure permits
dependency/harness repair only, not EDPF reimplementation, parameter tuning, or
MFI architecture work.

The first build preflight passed ED_Lib source/hash/license checks but stopped
at CMake configuration because the workstation has no C++ OpenCV package. No
dataset or detector benchmark ran. One attachment-only retry is registered to
build the author-documented OpenCV 3.4 dependency from pinned upstream tag object
`404ca455aeed9d26946e281b0383829bd0c533b1`, then repeat the unchanged
dataset-free exact-source compile and binary-output smoke test. Validation and
architecture work remain deferred until that smoke test passes.

That retry stopped before configuration because `404ca455...` is the annotated
OpenCV 3.4.20 tag object, whereas Git correctly placed peeled release commit
`1eb1d4c3708f2bd95562cedd58d28461505c2d37` in `HEAD`. No dataset, detector,
compiler, or benchmark ran. A second attachment-only retry is registered with
separate immutable tag-object and peeled-commit checks; the dependency version,
EDPF source and parameters, validation deferral, and architecture are unchanged.

The second retry verified provenance and successfully built the pinned OpenCV
static libraries, but the EDPF CMake step selected OpenCV 3.4's legacy
Windows-pack dispatcher, which cannot classify MSVC 19.42 even though the
direct installed static-package config exists. No EDPF compile or dataset run
occurred. A third attachment-only retry is registered to select that exact
static config and repeat the unchanged synthetic smoke test. Validation and
architecture work remain deferred.

The third retry reached that static config but stopped before EDPF compilation
because OpenCV 3.4's generated import table referenced unused codec targets
excluded from the registered minimal `core`/`imgproc` build. A fourth
attachment-only retry is registered to import the exact installed
`core`/`imgproc`/`zlib` artifacts directly and repeat the unchanged synthetic
smoke test. No dataset was read and validation and architecture work remain
deferred.

The fourth retry configured the direct imports and reached compilation, but the
grayscale harness unnecessarily included `EDColor.cpp`; its unused diagnostic
`imwrite` call requires the deliberately excluded imgcodecs module. No linking,
smoke test, dataset read, or benchmark occurred. A fifth attachment-only retry
is registered to compile only the unmodified `ED.cpp` and `EDPF.cpp` translation
units required by the selected grayscale `EDPF(Mat)` path, using the same pinned
OpenCV artifacts and unchanged smoke test. Validation and architecture work
remain deferred.

That retry compiled the selected author sources and reached final linking, but
the harness defaulted to `/MD` against OpenCV's `/MT` static libraries and
`ED.cpp`'s same-object `ED(EDColor&)` overload left unresolved author `EDColor`
symbols. No smoke executable or dataset result was produced. A sixth
attachment-only retry is registered to match `/MT`, build pinned OpenCV
imgcodecs and its generated dependencies, compile unmodified
`ED.cpp`/`EDColor.cpp`/`EDPF.cpp`, and repeat the unchanged synthetic smoke
test. Validation and architecture work remain deferred.

The sixth retry installed the required pinned OpenCV artifacts but stopped at
CMake configuration because OpenCV 3.4's generated export table validates
absent `libprotobuf` and `quirc` archives belonging to unused modules. No
author compilation, smoke execution, or dataset read occurred. A seventh
attachment-only retry is registered to import only the exact installed
core/imgproc/imgcodecs and codec artifacts required by the unchanged author
source surface. The `/MT` runtime, immutable sources, smoke test, validation
deferral, and architecture remain unchanged.

The seventh retry passed. The immutable author `ED.cpp`/`EDColor.cpp`/`EDPF.cpp`
surface compiled against pinned OpenCV 3.4.20, and two executions on the fixed
synthetic input produced the same native binary map (`122` edge pixels, values
`0/255`). No dataset was read. The registered next action is
`stage15d_edpf_exact_reproduction`: execute the unmodified grayscale author
EDPF over all 100 native-resolution BSDS500-validation images, retain the
binary maps, per-image runtimes and hashes, emit the fixed positions 1/50/100
preview, and attach the unchanged official validation path against the
incumbent. This is a reproduction baseline, not an MFI promotion experiment;
EDPF parameters and MFI architecture remain frozen.

### Stage-15d exact EDPF reproduction complete; Stage-15e checkpoint registered

The exact unmodified-author-code grayscale EDPF run completed on all 100
native-resolution BSDS500 validation images. Under the common local official
path, EDPF obtained ODS/OIS/AP `0.548048/0.548596/0.000000`, changing the
unchanged MFI incumbent by `+0.002577/-0.030732/-0.534289`. The AP value is a
documented consequence of evaluating the native binary map, which exposes only
one nontrivial operating point; it is not evidence of a dense confidence
ranking. Mean detector runtime was about `0.00485` seconds per image. The
fixed positions 1/50/100 preview, all binary maps, runtimes, and hashes are
complete.

EDPF is retained only as an exact, strictly untrained chain-first baseline.
It does not alter or promote MFI, and no EDPF parameter may be tuned from this
result. The Stage-15a stochastic/reference-uncertified Windows matcher caveat
still applies. The registered next action is
`stage15e_co_sco_reproduction_checkpoint`: a live primary-source and code audit
of the CO/SCO color-opponent contextual baselines before any fidelity-labeled
run. Architecture invention remains prohibited through Stage 15o.

### Stage-15e checkpoint - exact paired CO/SCO reproduction registered

The official UESTC author page provides complete research-purpose-only MATLAB
archives for both CO and SCO. Their archives and reachable source files are
hash-pinned, and native-resolution R2023a smoke tests passed with finite soft
outputs in `[0,1]`. The 2015 paper establishes that sigma `1.1`, cone weight
`-0.7`, and SSC window `5` were selected on BSDS300 train, so the methods are
classified as parameter-fixed but author-tuned rather than learned.

The registered next action is `stage15e_co_sco_exact_reproduction`: run exact
CO without SSC and exact SCO with the published modified spatial-sparseness
weighting at the common fixed setting over BSDS500 validation, retain separate
maps/runtime/hashes and the fixed positions 1/50/100 preview, then attach the
unchanged official evaluator against the incumbent. This is a paired baseline
and SSC mechanism decomposition, not an MFI promotion experiment. Do not tune
CO/SCO from validation results or change MFI before Stage 15p. The author code
has no open-source license and remains ignored/unredistributed; paper test
metrics stay documentary and protocol-separated.

### Stage-15e exact CO/SCO reproduction complete; Stage-15f checkpoint registered

The exact author-code CO/SCO pair completed on all 100 native-resolution
BSDS500 validation images. CO obtained ODS/OIS/AP
`0.635925/0.665489/0.651767`; SCO obtained
`0.656582/0.682564/0.694939`. Against the unchanged MFI incumbent, SCO changed
the three metrics by `+0.111120/+0.103538/+0.160651`; against paired CO, the
published modified spatial-sparseness step changed them by
`+0.020656/+0.017076/+0.043173`. This is strong matched development evidence
for contextual sparseness within that external color-opponent method, not an
MFI architecture decision. Both methods remain parameter-fixed but
author-tuned baselines, and the incumbent is unchanged. The fixed preview,
maps, hashes, and runtimes are complete; the stochastic/reference-uncertified
Windows matcher caveat remains.

The registered next action is `stage15f_compass_reproduction_checkpoint`, a
live primary-source and code audit of the Compass half-disc distribution-
gradient detector. It must resolve fidelity, fixed parameters, training class,
output conventions, and matched validation feasibility before one detector
run or fidelity preflight. Stage 14l is not a Compass reproduction, and no MFI
architecture invention is authorized before Stage 15p.

### Stage-15f Compass checkpoint - exact source found; build preflight registered

The complete official author MATLAB/C Compass archive is available from the
Stanford project page and is pinned by SHA-256
`43e2ab843af620f5b6405843be0c5478b6953039c36b1e32b2a3ac725ddce7ea`.
Compass is strictly untrained. The prospective fixed path uses the CVPR
paper's full-image sigma `4` setting (radius `12`) with author defaults:
spacing `1`, a 180-degree edge model, six wedges per quadrant, and 10 color
clusters. The output is the maximum-EMD strength in `[0,1]`; literature
examples are qualitative and remain separate from matched validation.

The registered next action is `stage15f_compass_build_preflight`, a
dataset-free hash/build/synthetic-smoke test of the unmodified 2004 MEX code.
It must record the effect of the source's `srand(clock())` randomized
clustering without fixing its seed. Only a pass may advance to one fixed
BSDS500-validation reproduction. Harness repair is allowed if needed, but no
author-source change, scale/parameter tuning, surrogate, or MFI architecture
work is authorized.

The first build preflight compiled the hash-verified author MEX successfully
but failed on its first output allocation because the 2004 gateway's `int`
dimension vector was consumed through MATLAB's default 64-bit array-dimension
ABI, producing a spurious oversized-array request. No dataset was read and no
detector output was produced. One attachment-only retry is registered using
MATLAB's legacy compatible array-dimensions build mode with the same unmodified
author bytes, parameters, and synthetic smoke test. Validation and MFI
architecture work remain deferred.

That retry passed. The unchanged author MEX produced a finite bounded
maximum-EMD map on the fixed synthetic input under MATLAB's compatible array
dimensions mode; no dataset was read. The registered next action is
`stage15f_compass_exact_reproduction`: run the fixed published sigma-4 author
path over all 100 native-resolution BSDS500 validation images, preserve maps,
runtimes and hashes, emit the fixed positions 1/50/100 preview, and attach the
unchanged official evaluator against the incumbent. The source's clock-seeded
clustering is left untouched and recorded as provenance. This is a baseline
reproduction, not permission to tune Compass or alter MFI before Stage 15o.

The exact run generated all 100 native-resolution maps and all 100 runtime
rows, then MATLAB emitted `STAGE15F_COMPASS_EXPORT_OK images=100` before its
process exited with Windows heap corruption (`0xc0000374`). Python therefore
did not write hashes, provenance, preview, or the official-evaluation manifest,
and no score was produced. One attachment-only finalization is registered to
validate and hash those exact frozen maps, create the missing documentary
artifacts, and attach the unchanged evaluator without invoking Compass or
regenerating its clock-seeded predictions. No Compass tuning or MFI change is
authorized.

### Stage-15f exact Compass reproduction complete; Stage-15g checkpoint registered

The attachment-only finalization preserved the original 100 frozen Compass
maps and completed hashes, provenance, runtime accounting, the fixed positions
1/50/100 preview, and official validation scoring without invoking Compass.
Exact author-code Compass obtained ODS/OIS/AP
`0.630841/0.656565/0.518359`, changing the unchanged MFI incumbent by
`+0.085418/+0.077086/-0.015936`. Its stronger ODS/OIS but lower AP is a mixed
ranking profile, not permission to tune or integrate the cue. Mean detector
runtime was about `9.783` seconds per image. Compass remains a strictly
untrained exact-code reference; the source's clock-seeded clustering and the
Stage-15a stochastic/reference-uncertified evaluator caveat remain recorded.

The registered next action is
`stage15g_texture_surround_reproduction_checkpoint`, a high-reasoning live
primary-source and code audit of Yang, Peng and Wu's 2025 texture-gradient plus
surround-modulation detector. It must resolve fidelity, fixed parameters,
training class, output conventions, and matched validation feasibility before
one detector run or fidelity preflight. No MFI architecture invention is
authorized before Stage 15p.

### Stage-15g checkpoint - fidelity preflight registered

No article-specific author code or supplement was located for Yang, Peng and
Wu's 2025 texture-gradient plus surround-modulation detector. A same-inventor
patent (`CN115830051A/B`) corroborates the mechanism, and the official related
BESD repository is pinned at
`eeb1f7eddcff0c998d8a96083f0579c7f1644b61`, but neither establishes the target
article's executable contract. The sources conflict on Gaussian/surround
values; the patent leaves weights, texture scales, nonlinearities, and output
conventions unresolved; and BESD accompanies a different paper and adds
segment linking/feedback.

The registered next action is
`stage15g_texture_surround_fidelity_preflight`, a deterministic dataset-free
contract audit. Do not combine the patent and BESD implementation into a
surrogate or score a detector. If the conflicts remain, close Stage 15g as
fidelity-unresolved and proceed to the Stage-15h literature checkpoint. MFI
architecture remains unchanged through Stage 15o.

### Stage-15g closure and Stage-15h transition

The dataset-free fidelity preflight confirmed that public primary material does
not resolve the target article's output-affecting implementation contract. No
detector or dataset was run, no patent/BESD hybrid was scored, and Stage 15g
closes fidelity-unresolved without changing MFI. The reported metrics remain
documentary and protocol-unverified.

The registered next action is
`stage15h_adaptive_surround_reproduction_checkpoint`, a high-reasoning live
primary-source and official-code audit of Zhang et al.'s adaptive multiscale V1
surround-modulation detector (DOI `10.1007/s11760-024-03634-y`). It must resolve
code availability, fixed parameters, training class, output conventions, and
matched-validation feasibility before one fidelity-labeled run or preflight.
Architecture invention remains prohibited through Stage 15o.

### Stage-15h checkpoint - fidelity preflight registered

No article-specific author code, supplement, or executable archive was located
for Zhang et al.'s adaptive multiscale V1 surround-modulation detector. Public
primary material verifies a strictly untrained analytic method, contrast-
dependent suppression/facilitation, multiscale surround behavior, and four
butterfly orientations, but does not fix the complete filters, adaptation
transfer, scale/orientation fusion, scalar output/postprocessing, or matched
evaluation contract. The reported BSDS500 average optimal F-score `0.703` and
NYUD follow-up are documentary and protocol-unverified. A related same-group
contrast-adaptive paper is mechanistically distinct and not an authorized
source of missing target parameters.

The registered next action is
`stage15h_adaptive_surround_fidelity_preflight`, a deterministic dataset-free
contract audit. Do not score a hand-completed surrogate or read a benchmark. If
the blockers remain, close Stage 15h fidelity-unresolved and proceed to the
Stage-15i fractional-reference checkpoint. MFI architecture remains unchanged
through Stage 15o.

### Stage-15h closure and Stage-15i transition

The dataset-free fidelity preflight confirmed that public primary material does
not resolve the adaptive-surround detector's output-affecting implementation
contract. No detector or dataset was run, no related-paper surrogate was
scored, and the reported metrics remain documentary and protocol-unverified.
Stage 15h closes fidelity-unresolved without changing MFI.

The registered next action is
`stage15i_fractional_reference_reproduction_checkpoint`, a high-reasoning live
primary-source and official-code audit of the 2026 Fractional Dirac detector
(DOI `10.3390/fractalfract10060412`). It must resolve fidelity, fixed
parameters, training class, output/evaluator conventions, and its distinction
from the failed Stage-14s spectral Riesz realization before one run or
preflight. This does not authorize fractional tuning or MFI architecture work.

### Stage-15i checkpoint - official QFrD code found; runtime preflight registered

The primary paper's official public QFrD repository is pinned at its sole
commit `8dcc8d846e6dcbe1bc4b931b89f1c814f5f9a245`. The detector is
parameter-fixed but author-tuned: the fixed code path uses fractional order
`0.8`, full Hilbert rotation, the symmetric RGB quaternion axis, Gaussian sigma
`2.0`, 64-pixel replicate padding, bilinear NMS, and absolute hysteresis
defaults. The reported BSDS500-test ODS/OIS/AP
`0.6145/0.6361/0.5996` remain documentary and protocol-separated from a future
common validation run.

The repository has no explicit license or requirements file. The manuscript
specifies left multiplier application, while pinned code computes
`q_mul(Q, M_full)`; any future result must therefore be labeled an exact
author-code reproduction rather than proof of paper/code algebraic equivalence.
QFrD is distinct from Stage 14s because it jointly processes RGB through a
quaternion QFT at order `0.8`; Stage 14s tested a grayscale half-order isotropic
Riesz-gradient localizer. No fractional family is reopened for tuning.

The registered next action is `stage15i_qfrd_runtime_preflight`, a dataset-free
source-hash, dependency, and fixed synthetic-repeatability check. The current
project environment lacks PyTorch/torchvision; a failure permits only a
dependency repair and identical retry. Do not read BSDS, alter author bytes or
parameters, or change MFI. Only a pass may register one exact QFrD
BSDS500-validation reproduction with maps, hashes, runtimes, fixed positions
1/50/100 preview, and the unchanged official evaluator.

The first runtime preflight stopped before source verification or synthetic
execution. Its `--no-checkout` clone was correctly seen as a worktree of
deleted tracked files by the later cleanliness guard, and the project runtime
also confirmed that PyTorch/torchvision are absent. No dataset or detector ran,
so this is harness/dependency evidence only. One attachment-only retry is
registered with a fresh ignored checkout populated before cleanliness checks
and pinned CPU `torch==2.9.0`/`torchvision==0.24.0`; the author commit, source
bytes, fixed parameters, synthetic input, dataset prohibition, and MFI remain
unchanged. Only a passing retry may advance to validation reproduction.

The retry passed: the pinned 59-file author tree reproduced its registered
manifest hash, all fixed source-contract checks passed, the pinned CPU tensor
runtime is available, and the synthetic QFrD result was finite, native-size,
and bitwise repeatable. No dataset was read. The registered next action is
`stage15i_qfrd_exact_reproduction`: run the unchanged fixed-default author
path over all 100 native-resolution BSDS500-validation images, retain maps,
runtimes and hashes, emit the fixed positions 1/50/100 preview, and attach the
unchanged official evaluator against the incumbent. It is a reproduction
baseline only; the paper/code multiplication-order caveat remains, and no
QFrD/fractional tuning or MFI architecture change is authorized.

### Stage-15i exact QFrD reproduction complete; Stage-15j registered

The exact pinned-author-code QFrD run completed on all 100 native-resolution
BSDS500 validation images. Under the common local official path, QFrD obtained
ODS/OIS/AP `0.587261/0.618621/0.583650`, improving the unchanged MFI incumbent
by `+0.041849/+0.039265/+0.049373`. Mean detector runtime was about `1.168`
seconds per image. Maps, hashes, runtimes, and the fixed positions 1/50/100
preview are complete. The author-code/paper multiplication-order caveat and
the stochastic/reference-uncertified Windows matcher caveat remain.

QFrD is retained only as a parameter-fixed, author-tuned exact-code reference.
It does not alter MFI and does not reopen fractional tuning. The registered
next action is `stage15j_high_number_protocol_audit_checkpoint`, a high-
reasoning live-primary-literature audit of unusually high non-trained edge
metrics to distinguish Berkeley ODS from average-optimal, per-image,
multi-output, or otherwise incompatible F/F1 protocols. No MFI architecture
invention is authorized before Stage 15p.

### Stage-15j closure; Stage-15k per-image diagnosis registered

The live high-number audit found no additional reproducible matched-protocol
baseline. Gao and Gao's reported BSDS500 F1 `0.888` and BPAED's generic F1
claims omit the Berkeley ODS matcher/tolerance, split, annotation, threshold
and thinning contract and have no immutable author implementation. FACAFCV's
primary paper demonstrates the metric distinction directly: optimal F reaches
`0.8910` on its noisy-image experiment, while its separate BSDS500
ODS/OIS/AP are `0.589/0.608/0.533`. These headlines do not change the matched
frontier and no surrogate is authorized.

The registered next action is `stage15k_per_image_oracle_matrix`. It uses only
frozen MFI, SED, EDPF, CO, SCO, Compass and QFrD validation outputs plus their
existing official per-image count tables to build fixed-threshold and
per-image-best metrics, pairwise win/loss matrices and a descriptive
ground-truth oracle bound. No detector or matcher is rerun. The oracle is not a
deployable router, and MFI architecture remains frozen through Stage 15o.

### Stage-15k oracle diagnosis complete; Stage-15l registered

Across frozen BSDS500-validation outputs, exact SED was the strongest single
method at its nearest raw ODS threshold (aggregate F1 `0.678500`). A
ground-truth-informed per-image method oracle reached `0.697054`, a descriptive
`+0.018554` upper bound, selecting SED on 52 images, SCO 18, CO 14, Compass 9,
MFI 4, EDPF 3, and QFrD 0. At per-image-best thresholds the analogous oracle
gain was `+0.015459`. These results establish limited but real per-image
complementarity; they do not define ODS/OIS, authorize a deployable router, or
change the incumbent. The Stage-15a matcher caveat remains.

The registered next action is `stage15l_image_regime_characterization`, a
predeclared association analysis between fixed image-internal regime measures
and frozen-method F1 deltas. It may not fit a classifier/router, rerun a
detector or matcher, or alter MFI. Architecture remains frozen through Stage
15o.

### Stage-15l regime diagnosis complete; Stage-15m registered

Stage 15l found its clearest corrected associations in structural properties.
EDPF improved relative to MFI as incumbent fragmentation and edge density
increased (`rho=0.451` and `0.382`) and worsened as mean incumbent component
size increased (`rho=-0.451`). SED's advantage over MFI also increased with
fragmentation (`rho=0.325`) and edge density (`rho=0.318`). These are
descriptive BSDS-validation associations over frozen outputs, not routing or
feature-selection evidence; MFI remains unchanged.

The registered next action is `stage15m_pixel_segment_complementarity`. It
uses the seven frozen maps and already reported ODS thresholds to quantify
unique GT-supported response, shared unsupported response, weak-gradient
support, and component continuity under a fixed diagnostic spatial contract.
The proximity counts are not Berkeley ODS/OIS/AP. No router or architecture
change is authorized before the remaining Stage-15 diagnostic sequence.

### Stage-15m spatial complementarity complete; Stage-15n registered

Stage 15m completed its frozen-map diagnosis despite the redundant official
attachment failing during incumbent matching with the already documented
intermittent Windows MATLAB heap corruption. The diagnostic itself did not
need a detector or matcher rerun. At the fixed spatial contract, SED had fewer
unsupported pixels than MFI (`182,413` versus `353,416`), a higher supported
pixel fraction (`0.678` versus `0.519`), and larger supported components
(`8.71` versus `6.15` pixels). MFI and SED nevertheless retained substantial
unique GT-supported response relative to one another (`35.6%` and `32.0%`).
These proximity counts are not Berkeley ODS/OIS/AP and do not authorize a
router or architecture change.

The registered next action is `stage15n_uded_bsds_discrepancy_audit`. It uses
only existing Stage-14r/14s UDED-selection repeated-CV tables, existing
BSDS500-validation official count tables, and fixed image-internal regime
measures to test which dataset-distribution and error-regime differences
accompany the opposite SE(2)/fractional deltas. It does not rerun a detector or
matcher, fit a router, or change MFI. Architecture remains frozen through
Stage 15o.

### Stage-15n discrepancy diagnosis complete; Stage-15o registered

BSDS validation GT is much less fragmented than UDED selection
(components-per-megapixel standardized difference `-3.251`, BH
`q=4.57e-12`) and has much larger mean components (`+1.080`, same `q`).
Within BSDS, Riesz benefit rises with gradient mean/density, texture residual,
and gradient q90 after global correction; SE(2) shows weaker positive gradient
associations. UDED has only 15 images, so its association estimates are
descriptive. This explains part of the cross-dataset reversal but does not
authorize a router or feature choice.

The registered next action is `stage15o_texture_evidence_decomposition`, the
final frozen-architecture Stage-15 diagnostic. It decomposes fixed analytic
interior texture, cross-boundary texture contrast, local gradient, retained
multiscale persistence, and structural-support cues on UDED selection and
BSDS validation. Image-blocked diagnostic models are association probes only.
Stage 15p may be registered only if cross-boundary texture adds consistent
held-out AUC/AP on both datasets; MFI remains unchanged meanwhile.

The first Stage-15o launch failed before dataset access because its runner
imported undeclared scikit-learn. No scientific output was produced. A
harness-only dependency retry is registered using the repository-supported
SciPy/NumPy stack for the unchanged fold-fitted standardized, class-balanced
L2 logistic diagnostic and AUC/AP calculations. Cue maps, deterministic
sampling, folds, decision rule, dataset roles, and the architecture freeze are
unchanged.

### Stage-15o closure; Stage-16a generation-2 checkpoint registered

The dependency-repaired Stage-15o diagnostic completed, but the preregistered
cross-dataset gate for Stage 15p failed. On BSDS500 validation, adding the
cross-boundary texture cue to gradient plus persistence improved mean AUC/AP
by about `+0.06538/+0.07812`, and adding it to the other four cues improved
them by `+0.06614/+0.07810`; all five folds were positive. On UDED selection,
the same contrasts changed mean AUC/AP by about `-0.00815/-0.01159` and
`-0.01659/-0.01530`, respectively, with only `2/5` positive folds. Stage 15p
is therefore not registered, the tested analytic cross-texture cue is not
integrated, and the compact Choquet-gated grayscale Scharr+NMS controller
remains incumbent. The completed official attachment scored only that frozen
incumbent and supplies no candidate promotion evidence.

The registered next action is `stage16a_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature synthesis of the completed Stage-15
reproduction and diagnostic program. It must choose exactly one bounded,
interpretable, non-neural generation-2 falsification with a preregistered joint
UDED-selection/BSDS-validation rule. It may not revive Stage 15p, fit a
dataset-identity router, or use protected-split feedback.

### Stage-16a closure — fixed SED/MFI expert mean registered

The live checkpoint selected one fixed detector-level expert combination.
Exact SED is the strongest matched non-trained Stage-15 baseline; its primary
paper attributes gains to contour strengthening/continuation and texture
suppression. Stage 15m found substantial two-way unique GT-supported response
between MFI and SED, and Kittler et al. (1998) supplies a conservative
robustness rationale for fixed sum fusion. Stage 16b therefore tests only
`0.5 * compact_MFI + 0.5 * exact_SED` after common 8-bit score serialization.

`stage16b_fixed_sed_mfi_fusion` is registered with UDED-selection 5x3
leakage-free CV and official BSDS500-validation scoring. It compares both
constituents and the fusion under a conjunctive rule: the fusion must improve
over each constituent on UDED and over the better constituent on BSDS
ODS/OIS/AP. No weight search, router, dataset identity, Stage-15p texture cue,
or protected feedback is allowed. The compact Choquet-gated grayscale
Scharr+NMS controller remains incumbent pending the result.

### Stage 16b closure — fixed SED/MFI mean rejected; Stage 16c registered

The equal arithmetic mean did **not** pass its preregistered conjunctive rule.
On UDED selection it improved aggregate F1 over compact MFI by `+0.003764`,
but precision fell by `-0.006614`, mean fold F1 improved only `+0.000781`, and
the candidate won just `5/15` folds against MFI. It decisively exceeded SED on
UDED. On official BSDS500 validation the mean improved over MFI but remained
below the better constituent, exact SED, by `-0.049178/-0.055314/-0.066815`
ODS/OIS/AP. Therefore it is not promoted, and its weight, normalization,
nonlinear variants, and routers must not be tuned from this result. The compact
Choquet-gated grayscale Scharr+NMS controller remains incumbent.

The registered next action is `stage16c_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS-validation rule. Protected feedback,
dataset-identity routing, and outcome-driven SED/MFI fusion tuning remain
forbidden.

### Stage 16c closure — stable-region-boundary support registered

The live primary-literature checkpoint selected one fixed mid-level structural
test. Stage 16d applies a repository-specific surrogate of Donoser,
Riemenschneider, and Bischof's component-tree region-boundary shape stability
(CVPR 2010, DOI `10.1109/CVPR.2010.5539833`) to the unchanged serialized
compact-MFI score. Published fixed settings are retained: minimum region area
`400`, level delta `5`, chamfer radius `10`, and minimum fragment length `70`;
the incumbent gate exponent `2.0` and floor `0.10` are reused without search.
This is not an exact reproduction of unpublished author node selection. It is
mechanistically distinct from Stage 14t's upper-level response-component NFA,
Stage 14i endpoint linking, and Stage 16b detector averaging. Stage 16d is
registered with conjunctive UDED-selection repeated-CV and official
BSDS500-validation criteria. The compact Choquet-gated grayscale Scharr+NMS
controller remains incumbent pending the result, and no stability or gate
parameter may be tuned afterward.

### Stage 16d closure — stable-region-boundary support rejected; Stage 16e registered

The fixed component-tree-inspired support gate failed both development axes.
Relative to compact MFI on UDED selection, aggregate F1 changed by `-0.00904`,
precision by `-0.00752`, recall by `-0.01120`, and mean fold F1 by `-0.00827`,
with only `4/15` fold wins. Official BSDS500-validation ODS/OIS/AP changed by
`-0.000319/-0.000637/-0.001587`. The candidate is not promoted, and its
stability, component, gate, and threshold parameters must not be tuned from
this result. This falsifies only the fixed repository surrogate, not the full
published region-boundary-stability method. The compact Choquet-gated
grayscale Scharr+NMS controller remains incumbent.

The registered next action is `stage16e_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not revisit
the failed Stage-16d stability gate or tune the failed Stage-16b fusion family.

### Stage 16e closure — fixed rolling-guidance conditioning registered

The live primary-literature checkpoint selected one fixed image-domain
scale-aware test. Stage 16f places an equation-level grayscale Rolling Guidance
Filter (Zhang et al., ECCV 2014, DOI `10.1007/978-3-319-10578-9_53`) between
the retained median conditioning and unchanged Scharr+NMS localizer. Spatial
sigma `3`, range sigma `0.1`, four iterations, and three-sigma numerical
support are fixed before results; the compact Choquet context and all fold
fitting remain unchanged. The test targets documented unsupported small-scale
response while iterative guidance is intended to restore larger boundary
sharpness. It is distinct from Stage 14h gravitational smoothing, Stage 16d
response-derived stability gating, and Stage 16b detector averaging.

`stage16f_rolling_guidance_localizer` is registered with conjunctive UDED-
selection repeated-CV and official BSDS500-validation criteria plus a fixed
positions 1/8/15 preview. The implementation is a repository reimplementation,
not exact author code. Do not tune RGF parameters, support, color handling,
conditioning order, localizer fusion, context, gate, or threshold grid from
the result. The compact Choquet-gated median-conditioned grayscale Scharr+NMS
controller remains incumbent pending the outcome.

### Stage 16f closure — rolling-guidance conditioning rejected; Stage 16g registered

The fixed rolling-guidance localizer failed the preregistered conjunctive rule.
Relative to compact MFI on UDED selection, aggregate F1 changed by `-0.10320`,
precision by `-0.03852`, recall by `-0.19505`, and mean fold F1 by `-0.10277`,
with `0/15` fold wins. Official BSDS500-validation ODS/OIS/AP nevertheless
improved by `+0.03511/+0.02813/+0.00901`. The severe UDED recall collapse
rejects the candidate despite the clear BSDS benefit. This falsifies only the
fixed grayscale RGF realization, not scale-aware conditioning generally. Do
not tune RGF parameters, conditioning order, color handling, fusion, context,
gate, or thresholds from this result. The compact Choquet-gated median-
conditioned grayscale Scharr+NMS controller remains incumbent.

The registered next action is `stage16g_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It must account for
the repeated BSDS-positive/UDED-negative localizer pattern without fitting a
dataset-identity router or tuning the failed Stage-16b, 16d, or 16f families.

### Stage 16g closure — all-threshold hysteresis persistence registered

The live primary-literature checkpoint selected one fixed connected-threshold
test over the unchanged compact-MFI score. Stage 16h uses Canny's strong-seed/
weak-connected-response principle with the fixed Figure-7 2:1 high/low
relation, extended across all 255 serialized score levels with 8-connectivity.
Each pixel receives the greatest high threshold at which it remains connected
through half-threshold support to a strong seed. The transform is boost-only
and exactly preserves nonzero support, so median conditioning, compact Choquet
context, and grayscale Scharr+NMS localization remain unchanged.

`stage16h_hysteresis_persistence_boost` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, including a
UDED recall-gain endpoint and asserted floor/support invariants. This is a
repository-specific soft extension, not an exact Canny or max-tree
reproduction. Do not tune its ratio, connectivity, quantization, propagation,
thresholds, context, gate, or localizer from the result. The compact controller
remains incumbent pending the outcome.

### Stage 16h closure - hysteresis persistence rejected; Stage 16i registered

The fixed all-threshold hysteresis-persistence boost failed its conjunctive
rule despite preserving the registered pointwise-floor and exact-support
invariants. Relative to compact MFI on UDED selection, aggregate F1 changed by
`-0.00433`, precision by `-0.00360`, recall by `-0.00538`, and mean fold F1
by `-0.00438`, with only `3/15` fold wins. Official BSDS500-validation
ODS/OIS/AP changed by `-0.00078/+0.00220/-0.02069`. The candidate is rejected,
and the connected-threshold parameters may not be tuned from this result. The
compact Choquet-gated grayscale Scharr+NMS controller remains incumbent.

### Stage 17t closure - Frei-Chen patch-subspace context rejected; Stage 17u registered

The fixed Frei-Chen edge-subspace membership passed the official BSDS500-
validation axis but missed the conjunctive UDED aggregate-F1 margin. UDED
aggregate F1/precision/recall and mean fold F1 changed by
`+0.000590/+0.000108/+0.001404/+0.000790`; the cue was eligible in `15/15`
folds and won `10/15`, but aggregate F1 was below the required `+0.002` gain.
Official BSDS500-validation ODS/OIS/AP improved by
`+0.005624/+0.002471/+0.013006`. All non-performance contracts passed. The
candidate is rejected; do not tune or extend this basis, subspace, sequential-
detector, calibration, or integration family from the result. The compact
controller remains incumbent.

The registered next action is `stage17u_generation2_mechanism_checkpoint`, a
live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
Frei-Chen context or earlier closed families, combine rejected cues, use
dataset identity, relax the cross-dataset rule, or use protected feedback.

### Stage 17u closure - morphological blur-minimum context registered

The live primary-literature checkpoint selected one fixed nonlinear
order-statistic context test. Stage 17v computes Van Vliet, Young, and Beckers'
equation-level blur-minimum strength on the unchanged median-conditioned
grayscale image using the smallest `3x3` unit-square support:
`min(max_3x3(I)-I, I-min_3x3(I))`. The statistic is positive only when a center
pixel has both brighter and darker local support, distinguishing a two-sided
transition from a flat, local extremum, or ideal two-level oscillation. It is
appended only as one outer-training-fold-eligible positive membership and does
not run the source detector's smoothing, nonlinear-Laplacian zero crossings,
distance transforms, contour extraction, or thresholding.

The authoritative protocol is `docs/paper/STAGE17V_PREREGISTRATION.md`.
`stage17v_morphological_blur_minimum_context` is registered with conjunctive
UDED-selection repeated CV and official BSDS500-validation criteria, exact
score-support preservation, fixed synthetic/photometric contracts, runtime
diagnostics, and positions 1/8/15 preview. The compact bank, gamma `0.55`, gate
strength `2.0`, floor `0.10`, grayscale Scharr+NMS, and threshold fitting are
unchanged. Do not tune or extend the support, morphology, smoothing,
zero-crossing, calibration, integration, context, gate, localizer, or
thresholds from the result. The compact controller remains incumbent.

### Stage 17r closure - directional patch-recurrence context rejected; Stage 17s registered

The fixed Xu-Xu-Quan directional patch-recurrence membership failed its
conjunctive promotion rule despite stable positive movement. On UDED
selection, aggregate F1/precision/recall and mean fold F1 changed by
`+0.001396/+0.000554/+0.002800/+0.001231`; the cue was eligible in `15/15`
folds and won `14/15`, but aggregate F1 missed the required `+0.002` gain.
Official BSDS500-validation ODS/OIS/AP changed by
`+0.001872/+0.000782/+0.003748`; ODS also missed its required `+0.002`
margin. All non-performance contracts passed, but every promotion condition
was required. The candidate is rejected; do not tune or extend this recurrence
or integration family from the result. The compact controller remains
incumbent.

The registered next action is `stage17s_generation2_mechanism_checkpoint`, a
live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
patch recurrence or earlier closed families, use dataset identity, relax the
cross-dataset rule, or use protected feedback.

### Stage 17s closure - Frei-Chen patch-subspace context registered

The live primary-literature checkpoint selected one fixed analytic local-patch
geometry test. Stage 17t projects every `3x3` patch of the unchanged median-
conditioned grayscale image onto Frei and Chen's published normalized nine-
vector orthogonal basis. Positive evidence is the square root of the first
four edge-subspace energies divided by total basis energy, with zero evidence
for a zero-energy patch. It enters only as one outer-training-fold-eligible
positive membership and does not run the paper's thresholded sequential
detector.

The authoritative protocol is `docs/paper/STAGE17T_PREREGISTRATION.md`.
`stage17t_frei_chen_subspace_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, exact score-
support preservation, fixed orthonormal-basis and synthetic contracts,
runtime diagnostics, and positions 1/8/15 preview. The compact bank, gamma
`0.55`, gate strength `2.0`, floor `0.10`, grayscale Scharr+NMS, and threshold
fitting remain unchanged. Do not tune the basis, subspaces, normalization,
support, boundary handling, calibration, integration, context, gate,
localizer, or thresholds, and do not advance to larger, rotated, multiscale,
color, learned, selected, weighted, line-subspace, or sequential variants.
The compact controller remains incumbent.

### Stage 18z closure - fold-fitted ICA sparse context rejected; Stage 19a registered

The fixed fold-fitted unlabeled FastICA response-concentration membership was
training-ineligible in all `15/15` UDED-selection folds, so the candidate
exactly reduced to compact MFI and all UDED metrics were unchanged. Official
BSDS500-validation ODS/OIS/AP changed by
`-0.000056/+0.000027/+0.000074`, failing the required ODS margin. All
non-performance contracts passed, but cannot override complete UDED
ineligibility and the failed BSDS condition. The candidate is rejected; do not
tune or extend ICA, sparse/dictionary representations, calibration, or
integration from this result. The compact controller remains incumbent.

The registered next action is `stage19a_generation2_mechanism_checkpoint`, a
live-primary-literature escalation that must select exactly one mechanistically
distinct bounded generation-2 falsification with a preregistered joint UDED-
selection/BSDS500-validation rule. It may not tune Stage 18z or earlier closed
families, combine rejected cues, use dataset identity, relax the cross-dataset
rule, or use protected feedback.

### Stage 18x closure - dual-stencil Teager-energy context rejected; Stage 18y registered

The fixed axial/diagonal Teager-Kaiser positive-consensus membership failed
its conjunctive promotion rule. UDED aggregate F1/precision/recall and mean
fold F1 changed by `+0.000813/+0.000071/+0.002072/+0.000708`, with only
`3/15` fold wins and eligibility in `3/15` folds. Official BSDS500-validation
ODS/OIS/AP changed by `+0.000002/+0.000867/+0.000088`, missing the required
ODS margin. All non-performance contracts passed. The candidate is rejected;
do not tune or extend nonlinear-energy stencils, fusion, higher-order energy,
demodulation, contrast enhancement, calibration, or integration. The compact
controller remains incumbent.

The registered next action is `stage18y_generation2_mechanism_checkpoint`, a
live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
Stage 18x or earlier closed families, combine rejected cues, use dataset
identity, relax the cross-dataset rule, or use protected feedback.

### Stage 18y closure - fold-fitted ICA sparse context registered

The live primary-literature checkpoint selected one fixed unsupervised
information-theoretic representation test. Stage 18z fits a deterministic
16-component `7x7` FastICA analysis bank from 256 unlabeled patches per image
strictly inside each outer UDED training fold. Bell and Sejnowski's natural-
image result motivates localized oriented independent components; Hyvarinen's
robust fixed-point method supplies the classical batch estimator. Positive
evidence is bounded dominance of the largest absolute component response over
the component-response L2 norm, with zero evidence on a constant patch. The
candidate inference path is linear filtering plus a closed-form statistic,
not a neural network, supervised embedding, sparse synthesis code, or exact
author edge detector.

The authoritative protocol is `docs/paper/STAGE18Z_PREREGISTRATION.md`.
`stage18z_ica_sparse_context` is registered with conjunctive UDED-selection
repeated CV and official BSDS500-validation criteria, exact score-support
preservation, deterministic fit/positive-affine contracts, runtime and model-
hash diagnostics, and positions 1/8/15 preview. The compact bank, gamma
`0.55`, gate strength `2.0`, floor `0.10`, median conditioning, grayscale
Scharr+NMS, and threshold fitting remain unchanged. Do not tune or extend ICA,
sparse coding, learned dictionaries, component selection, calibration, or
integration from the result. The compact controller remains incumbent.

The registered next action is `stage16i_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
the failed persistence, fusion, stability, or rolling-guidance families, use
dataset identity, or use protected feedback.

### Stage 16i closure - step-profile context registered

The live primary-literature checkpoint selected one fixed local edge-profile
test. Stage 16j compares a seven-sample intensity profile along the incumbent
Scharr normal against smooth linear shading and a closed three-width family of
centered tanh step templates. The normalized fit advantage is calibrated
inside each outer UDED training fold and, when eligible, appended as one
positive membership to the retained five-feature distorted-Choquet context.
Median conditioning, grayscale Scharr+NMS localization, gamma, gate, and
threshold fitting remain unchanged. The test is a repository-specific bounded
surrogate of Nalwa-Binford surface-model selection, informed by Elder-Zucker
variable-blur analysis, not an exact reproduction.

`stage16j_step_profile_context` is registered with conjunctive UDED-selection
repeated CV and official BSDS500-validation criteria plus a fixed positions
1/8/15 preview. Do not tune profile extent, offsets, template widths,
interpolation, eligibility, calibration, context, gate, localizer, or
threshold grid from the result. The compact controller remains incumbent.

### Stage 16j closure - step-profile context rejected; Stage 16k registered

The fixed step-profile membership failed its conjunctive promotion rule. On
UDED selection it improved aggregate F1 by `+0.00158`, recall by `+0.00441`,
and mean fold F1 by `+0.00156`, with `12/15` fold wins and eligibility in
`14/15` folds; precision changed by only `-0.00007`. However, aggregate F1
missed the preregistered `+0.002` margin. Official BSDS500-validation
ODS/OIS/AP changed by `-0.00198/-0.00196/+0.00158`, so the candidate also
failed the BSDS conditions. It is rejected despite useful local
discriminativeness and UDED stability. Do not tune its profile geometry,
templates, calibration, eligibility, context, gate, localizer, or thresholds.
The compact Choquet-gated grayscale Scharr+NMS controller remains incumbent.

The registered next action is `stage16k_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
the failed profile, persistence, fusion, stability, or conditioning families,
use dataset identity, or use protected feedback.

### Stage 16k closure - exact EDPF chain context registered

The live checkpoint selected one fixed chain-first structural test. Stage 16l
executes the immutable exact author EDPF implementation and uses its binary
contiguous-chain/Helmholtz-validated support, after exactly one fixed
8-neighbourhood raster-alignment dilation, as one outer-training-fold-eligible
positive membership in the retained distorted-Choquet context. Stage-15
development diagnostics associated EDPF's relative benefit with incumbent
fragmentation and edge density, giving an image-internal rationale without a
dataset router. This mechanism is distinct from the failed component NFA,
endpoint linker, SE(2) diffusion, region-stability gate, and connected-
threshold persistence tests. The compact bank, gamma `0.55`, gate strength
`2.0`, floor `0.10`, median conditioning, grayscale Scharr+NMS localizer, and
threshold fitting remain unchanged.

The authoritative protocol is `docs/paper/STAGE16L_PREREGISTRATION.md`.
`stage16l_edpf_chain_context` is registered with conjunctive UDED-selection
5x3 leakage-free CV and official BSDS500-validation criteria, including a
largest-component coverage endpoint and fixed positions 1/8/15 preview. Do not
tune author EDPF parameters, the one-pixel alignment dilation, eligibility,
integration, context, gate, localizer, or threshold grid from the result. The
compact controller remains incumbent pending the outcome.

### Stage 16l closure - exact EDPF chain context rejected; Stage 16m registered

The fixed exact-author EDPF chain-support membership failed its conjunctive
promotion rule. On UDED selection, aggregate F1/precision/recall and mean fold
F1 changed by `-0.000191/-0.000244/-0.000090/-0.000013`; the candidate won
only `8/15` fold-F1 comparisons. The cue was eligible in `15/15` folds and
mean largest-component GT coverage changed by `+0.000030`, but coverage won
only `3/15` comparisons. Official BSDS500-validation ODS/OIS/AP improved by
`+0.013847/+0.005044/+0.014949`, satisfying that axis, but all conditions were
required. The fixed integration is rejected and must not be tuned. This is
another BSDS-positive/UDED-nonpositive mechanism result, not a falsification of
EDPF generally. The compact Choquet-gated grayscale Scharr+NMS controller
remains incumbent.

The registered next action is `stage16m_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
EDPF alignment, eligibility, weighting, integration, or any earlier closed
family, use dataset identity, relax the cross-dataset rule, or use protected
feedback.

### Stage 16m closure - SUSAN local-self-similarity context registered

The live primary-literature checkpoint selected one fixed derivative-free
context test. Stage 16n computes Smith and Brady's initial SUSAN response on
the unchanged median-conditioned grayscale image: a radius-3.4, 37-pixel
circular mask; brightness similarity
`exp(-((I-I0)/(20/255))^6)`; and normalized deficit below the published
three-quarter geometric threshold. It intentionally omits SUSAN direction,
NMS, thinning, and subpixel localization because the response enters only as
one outer-training-fold-eligible positive membership in the retained
distorted-Choquet context. This local self-similarity representation is
distinct from the closed detector-fusion, component/region gating,
conditioning, connected-threshold persistence, step-profile, half-disc
texture, and exact-chain integrations.

The authoritative protocol is `docs/paper/STAGE16N_PREREGISTRATION.md`.
`stage16n_susan_context` is registered with conjunctive UDED-selection 5x3
leakage-free CV and official BSDS500-validation criteria plus a fixed positions
1/8/15 preview. Do not tune the SUSAN mask, brightness threshold, exponent,
geometric threshold, boundary handling, eligibility, calibration, context,
gate, localizer, or threshold grid from the result. The compact Choquet-gated
grayscale Scharr+NMS controller remains incumbent.

### Stage 16n closure - SUSAN context rejected; Stage 16o registered

The fixed initial SUSAN/USAN local-self-similarity membership failed its
conjunctive promotion rule. On UDED selection, aggregate F1 changed by only
`+0.000302` versus the required `+0.002`, precision by `-0.000463`, recall by
`+0.001628`, and mean fold F1 by `+0.000185`; the candidate won only `7/15`
folds despite eligibility in `15/15`. Official BSDS500-validation ODS/OIS/AP
improved by `+0.004674/+0.002200/+0.006049`, satisfying that axis, but all
conditions were required. The candidate is rejected and its fixed mask,
brightness comparison, calibration, and integration must not be tuned. This
does not falsify the complete SUSAN detector. The compact Choquet-gated
grayscale Scharr+NMS controller remains incumbent.

The registered next action is `stage16o_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
SUSAN or earlier closed families, use dataset identity, relax the cross-dataset
rule, or use protected feedback.

### Stage 16o closure - empirical-copula context registered

The live checkpoint selected one fixed marginal-invariance test rather than
another cue, localizer, or structural gate. Stage 16p maps each of the five
retained fold-calibrated membership maps independently to deterministic
image-internal empirical-CDF midranks `(average_rank - 0.5) / N` before the
unchanged distorted-Choquet integral. The hypothesis is that within-image cue
ordering may transfer even when absolute membership marginals shift across
image regimes, directly addressing the repeated BSDS-positive/UDED-weak
pattern without dataset identity or a fitted target adapter. The transform has
no bins, window, mixing weight, or searched parameter.

The authoritative protocol is `docs/paper/STAGE16P_PREREGISTRATION.md`.
`stage16p_copula_context` is registered with conjunctive UDED-selection 5x3
leakage-free CV and official BSDS500-validation criteria plus fixed positions
1/8/15 preview and rank-invariant checks. Singleton weights, gamma `0.55`, gate
strength `2.0`, floor `0.10`, median conditioning, grayscale Scharr+NMS, and
threshold fitting are unchanged. Do not tune the rank definition, ties,
normalization scope, feature subset, weights, aggregation, gate, localizer, or
thresholds from the result. The compact controller remains incumbent.

The first Stage-16p launch stopped before any result artifact because its
inconsistent seed caused the fold-bank preselector to omit the frozen
`gabor4_scale_persistence` feature. A harness-only retry is registered with the
established generation-2 seed `20261009`; the candidate and joint promotion
rule are unchanged, and no scientific feedback has yet been produced.

### Stage 16p closure - empirical-copula context rejected; Stage 16q registered

The seed-corrected fixed empirical-CDF midrank transform failed its conjunctive
promotion rule on both development axes. On UDED selection, aggregate F1,
precision, recall, and mean fold F1 changed by
`-0.00903/-0.00446/-0.01647/-0.00769`, with only `2/15` fold wins. On official
BSDS500 validation, ODS/AP improved by `+0.00848/+0.00135`, but OIS changed by
`-0.00065`, failing the required nonnegative condition. Rank-contract checks
and the fixed preview passed, but cannot override the performance failures.
The candidate is rejected; do not tune its rank definition, scope, ties,
weights, aggregation, gate, localizer, or thresholds. The compact
Choquet-gated grayscale Scharr+NMS controller remains incumbent.

The registered next action is `stage16q_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
empirical marginal normalization or any earlier closed family, use dataset
identity, relax the cross-dataset rule, or use protected feedback.

### Stage 17w closure - semi-global scanline change-point context registered

The live primary-literature checkpoint selected one fixed mid-level scanline
segmentation test rather than another local patch/activity cue. Stage 17x
fits exact piecewise-constant row and column partitions to the unchanged
median-conditioned grayscale image by dynamic programming with a fixed
Schwarz/BIC `sigma_hat^2*log(N)` segment penalty. Adjacent-segment contrast is
written symmetrically to the two samples bordering each selected change point,
row/column evidence is merged by maximum, and the result enters only as one
outer-training-fold-eligible positive membership. The working grid has fixed
maximum side `256`; no textons, color, smoothing, learned penalty, segment-
count marginalization, or UCM postprocessing is used.

The authoritative protocol is `docs/paper/STAGE17X_PREREGISTRATION.md`.
`stage17x_semiglobal_changepoint_context` is registered with conjunctive
UDED-selection repeated CV and official BSDS500-validation criteria, exact
score-support preservation, fixed flat/step/checkerboard and photometric
contracts, runtime diagnostics, and positions 1/8/15 preview. This is a
bounded repository surrogate of Jevnisek and Avidan's SGBD principle, not an
exact reproduction. Do not tune or extend the working grid, directions,
segment model, noise estimator, penalty, raster support, merging,
calibration, or integration family from the result. The compact controller
remains incumbent.

### Stage 16q closure - Sugeno qualitative aggregation registered

The live primary-literature checkpoint selected one fixed aggregation-semantic
test. Stage 16r replaces only the compact context's Choquet arithmetic
accumulation with the discrete Sugeno max-min integral over the same five
fold-calibrated memberships and the same distorted-probability capacity
`mu(A)=(sum w_A)^0.55`. The hypothesis is that limiting a response jointly by
membership level and supporting-coalition capacity may transfer more stably
than arithmetic compensation among moderate cues, without discarding absolute
membership marginals as Stage 16p did. There is no new cue, dataset adapter,
mixing coefficient, or parameter search.

The authoritative protocol is `docs/paper/STAGE16R_PREREGISTRATION.md`.
`stage16r_sugeno_context` is registered with conjunctive UDED-selection 5x3
leakage-free CV and official BSDS500-validation criteria, algebraic contract
checks, and a fixed positions 1/8/15 preview. Median conditioning, grayscale
Scharr+NMS, singleton fitting, gamma `0.55`, gate strength `2.0`, floor `0.10`,
and threshold fitting otherwise remain unchanged. Do not tune the Sugeno
operators, capacity, weights, memberships, gate, localizer, thresholds, or a
Choquet/Sugeno mixture from the result. The compact Choquet controller remains
incumbent.

The first Stage-16r launch stopped before dataset access or result creation
because its runner imported unavailable `scikit-image`. A harness-only retry is
registered with the already-supported Pillow RGB reader; the fixed Sugeno
candidate, seed, folds, parameters, preview, official attachment, and joint
promotion rule are unchanged. This failure supplies no scientific feedback.

That retry also stopped before dataset access because unchanged transitive MFI
pipeline imports require the declared scikit-image dependency. The controller
had used system Python even though the existing repository `.venv` provides the
dependency. A second harness-only retry is registered through a local batch
launcher selecting `.venv`; Stage 16r and its joint rule remain unchanged.

The batch retry stopped before its launcher or dataset access because the
controller's Windows command construction passed literal quotes around the
batch path. A third harness-only retry is registered through a repository-local
Python delegator selecting the same `.venv`; the Stage-16r candidate, seed,
folds, artifacts, official attachment, and joint rule remain unchanged.

### Stage 16r closure - Sugeno qualitative aggregation rejected; Stage 16s registered

The fixed Sugeno max-min context failed its conjunctive promotion rule. On
UDED selection, aggregate F1/precision/recall and mean fold F1 changed by
`+0.000378/+0.000300/+0.000497/+0.000393`, with only `8/15` fold wins; it
missed the required F1 margin and fold-win count. Official BSDS500-validation
ODS/OIS/AP changed by `+0.001498/+0.000473/-0.013481`, missing the ODS margin
and AP condition. Algebraic contract checks and the fixed preview passed, but
cannot override the performance failures. The candidate is rejected; do not
tune Sugeno, the capacity, weights, memberships, gate, localizer, thresholds,
or a Choquet/Sugeno mixture. The compact Choquet-gated grayscale Scharr+NMS
controller remains incumbent.

The registered next action is `stage16s_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
Sugeno or any earlier closed family, use dataset identity, relax the
cross-dataset rule, or use protected feedback.

### Stage 16s closure - gamma-normalized automatic scale selection registered

The live primary-literature checkpoint selected one fixed local edge-scale
test. Stage 16t computes first-order Gaussian gradients on the unchanged
median-conditioned grayscale image at `sigma={1,2,4}` (the `t={1,4,16}`
levels illustrated by Lindeberg), multiplies magnitude by `sigma^0.5`, selects
the maximum normalized response per pixel, and retains spatial NMS at that
selected scale. This is a bounded repository surrogate of Lindeberg's
automatic scale-space edge principle, not a reproduction of continuous edge
curves, subscale interpolation, or saliency integration. It changes only the
localizer; the compact five-member Choquet context, fold fitting, gamma
`0.55`, gate strength `2.0`, floor `0.10`, median conditioning, and thresholds
remain unchanged.

The authoritative protocol is `docs/paper/STAGE16T_PREREGISTRATION.md`.
`stage16t_scale_space_localizer` is registered with conjunctive UDED-selection
5x3 leakage-free CV and official BSDS500-validation criteria, fixed synthetic
scale contracts, and a positions 1/8/15 preview. Do not tune the scales,
gamma normalization, derivative discretization, scale endpoint/tie handling,
NMS, response mapping, conditioning, context, gate, or thresholds from the
result. The compact Choquet-gated grayscale Scharr+NMS controller remains
incumbent.

### Stage 17f closure - photometric quasi-invariant context rejected; Stage 17g registered

The fixed sigma-1 shadow-shading photometric quasi-invariant membership failed
its conjunctive promotion rule despite passing the official BSDS500-validation
axis. On UDED selection, aggregate F1/precision/recall and mean fold F1 changed
by `+0.000756/+0.000826/+0.000594/+0.000509`; the cue was eligible in `12/15`
folds but won only `7/15`, and the aggregate F1 gain missed the required
`+0.002`. Official BSDS500-validation ODS/OIS/AP changed by
`+0.003855/+0.002520/+0.008468`. The synthetic, orthogonality, repeatability,
support, runtime, and fixed-preview contracts passed, but cannot override the
UDED failures. The candidate is rejected; do not tune RGB conditioning,
derivative scale, projection, energy, invariant family, calibration,
integration, context, gate, localizer, or thresholds, and do not advance to
specular, hue, alternative-color-space, multiscale, color-localizer, or learned
photometric variants from this result. The compact Choquet-gated grayscale
Scharr+NMS controller remains incumbent.

The registered next action is `stage17g_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
photometric invariants or earlier closed families, use dataset identity, relax
the cross-dataset rule, or use protected feedback.

### Stage 16x closure - spectral globalization context rejected; Stage 16y registered

The fixed coarse-grid spectral-globalization membership failed its conjunctive
promotion rule. On UDED selection, aggregate F1/precision/recall and mean fold
F1 changed by `-0.000430/-0.000190/-0.000826/-0.000364`, with only `6/15`
fold wins, despite eligibility in `15/15` folds and exact support preservation.
On official BSDS500 validation, ODS/OIS/AP changed by
`+0.001975/+0.001748/+0.011216`; ODS narrowly missed the required `+0.002`
margin. The candidate is rejected and its graph, eigensystem, calibration and
integration must not be tuned. This falsifies only the bounded repository
surrogate, not spectral clustering or exact gPb. The compact Choquet-gated
grayscale Scharr+NMS controller remains incumbent.

The registered next action is `stage16y_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
spectral globalization or earlier closed families, use dataset identity,
relax the cross-dataset rule, or use protected feedback.

### Stage 16t closure - automatic scale selection rejected; Stage 16u registered

The fixed gamma-normalized `sigma={1,2,4}` scale-selected localizer failed its
conjunctive promotion rule. On UDED selection, aggregate F1/precision/recall
and mean fold F1 changed by `-0.01945/+0.00164/-0.05327/-0.02049`, with only
`2/15` fold wins. Official BSDS500-validation ODS/OIS/AP changed by
`+0.00381/+0.00091/-0.01046`: the ODS condition passed, but AP declined. The
candidate is rejected and its scales, normalization, derivative
discretization, scale selection, NMS, response mapping, conditioning,
localizer integration, context, gate, and thresholds must not be tuned from
the result. This falsifies only the fixed finite-scale repository surrogate,
not automatic scale-space edge theory. The compact Choquet-gated grayscale
Scharr+NMS controller remains incumbent.

The registered next action is `stage16u_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
scale-space localization or earlier closed families, use dataset identity,
relax the cross-dataset rule, or use protected feedback.

### Stage 16u closure - exact Structured Edge forest registered

The live primary-literature checkpoint selected the complete Dollár-Zitnick
Structured Edge forest as one bounded non-neural replacement test. The pinned
author code and shipped `modelBsds` predict structured local edge masks and are
mechanistically distinct from Stage 14n's failed shallow scalar pixel forest.
The author inference path passed a dataset-free R2023a synthetic smoke test.
The model is explicitly supervised and trained on BSDS500 train; it is not an
untrained reference. BSDS500 validation and UDED selection remain development
evaluation axes and do not alter the immutable forest.

The authoritative protocol is `docs/paper/STAGE16V_PREREGISTRATION.md`.
`stage16v_structured_forest` compares the fixed exact author detector with
compact MFI under UDED-selection repeated threshold-CV and official BSDS500-
validation scoring. Promotion requires meaningful conjunctive gains on both
axes plus provenance, repeatability, runtime, complexity, map hashes, and the
fixed positions 1/8/15 preview. Do not tune trees, channels, stride,
sharpening, multiscale mode, NMS, calibration, fusion, or routing from the
result. The compact Choquet-gated grayscale Scharr+NMS controller remains
incumbent pending the outcome.

The first Stage-16v launch stopped before author-detector execution when Git's
ownership guard rejected the ignored pinned toolbox checkout during provenance
verification. It produced no candidate map or scientific feedback. A
harness-only retry is registered with process-local `safe.directory` overrides
for the immutable, hash-verified author checkouts; detector/model bytes,
parameters, datasets, folds, artifacts, official attachment, and promotion rule
are unchanged.

That retry reached author inference but stopped after five UDED inputs because
the repository wrapper asserted that raw post-NMS responses could not exceed
one. A targeted diagnostic found finite nonnegative output with maximum
`1.04074215889` and 21 above-one samples on the stopping image; pinned author
`edgesEval.m` instead uses saturating `uint8(E*255)` serialization. No metrics
or official manifest were produced. `stage16v_structured_forest_retry2` is
registered as a harness-only repair using that exact author serialization and
recording raw overshoot provenance; model, parameters, data, folds, evaluator,
and conjunctive promotion rule remain unchanged.

The exact-serialization retry completed all UDED-selection artifacts but
decisively failed the frozen UDED gate: aggregate F1 changed by `-0.03539`,
recall by `-0.14287`, mean fold F1 by `-0.03824`, and the forest won only
`2/15` folds; precision improved by `+0.04297`. It therefore cannot be
promoted or tuned regardless of the pending BSDS attachment. The official
export stopped before validation inference because the sparse vendor worktree
no longer contained the tracked `modelBsds.mat` blob used by the completed
run. One attachment-only retry is registered to materialize that exact blob
from the pinned commit, verify its preregistered SHA-256, and rerun only the
unchanged BSDS500-validation export/evaluator. UDED maps, CV, parameters, and
the scientific rejection remain frozen. The compact controller remains the
incumbent; after attachment closure, route to a mechanistically distinct live-
literature checkpoint.

### Stage 16v closure - exact Structured Edge forest rejected; Stage 16w registered

The attachment-only retry materialized and hash-verified the exact pinned
`modelBsds` blob, preserved the frozen UDED result, and completed official
BSDS500-validation scoring. The Structured Edge forest improved ODS/OIS/AP by
`+0.16732/+0.14456/+0.22316`, but its already frozen UDED-selection result
changed aggregate F1/precision/recall and mean fold F1 by
`-0.03539/+0.04297/-0.14287/-0.03824`, with only `2/15` fold wins. The
conjunctive rule therefore rejects the candidate despite its strong BSDS
result. This is evidence of severe cross-dataset transfer asymmetry for the
fixed BSDS-train author model, not a falsification of structured forests in
general. Do not tune, retrain, calibrate, fuse, or route the forest from this
result. The compact Choquet-gated grayscale Scharr+NMS controller remains
incumbent.

The registered next action is `stage16w_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune or
fuse the forest or any earlier closed family, use dataset identity, relax the
cross-dataset rule, or use protected feedback.

### Stage 16w closure - spectral globalization context registered

The live checkpoint selected one fixed image-wide graph mechanism. Stage 16x
uses the unchanged Scharr+NMS score as an intervening-contour barrier map,
constructs a normalized-Laplacian affinity graph at fixed maximum side `96`,
and retains Arbeláez et al.'s published spectral-Pb radius `5`, affinity scale
`0.1`, and `16` nontrivial eigenvectors. Their gradient-derived signal is
appended only as one outer-training-fold-eligible positive membership; compact
Choquet parameters, gate floor, conditioning, localizer, and threshold fitting
remain unchanged. The bounded implementation is a repository surrogate, not
exact or learned gPb.

The authoritative protocol is `docs/paper/STAGE16X_PREREGISTRATION.md`.
`stage16x_spectral_globalization_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, explicit
precision/recall non-collapse, score-support invariance, a fixed synthetic
step/repeatability contract, runtime diagnostics, and positions 1/8/15
preview. Do not tune the graph, eigensystem, compression, eligibility,
integration, context, gate, localizer, thresholds, gPb, or forest from the
result. The compact Choquet-gated grayscale Scharr+NMS controller remains
incumbent.

### Stage 16y closure - structure-tensor orientation context registered

The live primary-literature checkpoint selected one fixed local orientation-
organization test. Stage 16z computes the scalar spatial structure tensor on
the unchanged median-conditioned grayscale image using Weickert's illustrated
noise/integration scales `0.5/4.0`. Its eigenvalue difference
`lambda_max-lambda_min` is zero for flat or locally isotropic neighborhoods
and positive where one gradient orientation dominates. The cue is appended
only as one outer-training-fold-eligible positive membership; it does not run
coherence-enhancing diffusion or replace grayscale Scharr+NMS. This differs
from Stage 14k's per-pixel CIELAB Di Zenzo color tensor localizer because the
new test is scalar, spatially integrated, and contextual.

The authoritative protocol is `docs/paper/STAGE16Z_PREREGISTRATION.md`.
`stage16z_orientation_coherence_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, explicit
precision/recall non-collapse, exact score-support invariance, a fixed
step/flat/checkerboard contract, runtime diagnostics, and positions 1/8/15
preview. Do not tune tensor scales, evidence normalization, color or
multiscale variants, diffusion, eligibility, integration, context, gate,
localizer, or thresholds from the result. The compact Choquet-gated grayscale
Scharr+NMS controller remains incumbent.

### Stage 16z closure - structure-tensor orientation context rejected; Stage 17a registered

The fixed scalar structure-tensor membership passed every preregistered UDED
condition. Aggregate F1/precision/recall and mean fold F1 changed by
`+0.003263/+0.002639/+0.004184/+0.002705`, with `14/15` fold wins,
eligibility in `15/15` folds, and exact positive-support preservation. The
synthetic, finite/bounded, repeatability, runtime, and fixed-preview contracts
also passed. Official BSDS500-validation ODS/OIS/AP changed by
`+0.001414/+0.000628/+0.010279`; the ODS gain missed the preregistered
`+0.002` margin. Because the rule was conjunctive, the candidate is rejected.
Do not tune tensor scales, evidence normalization, color or multiscale tensor
variants, diffusion, calibration, integration, context, gate, localizer, or
thresholds from this result. This closes only the fixed scalar realization,
not structure-tensor analysis generally. The compact Choquet-gated grayscale
Scharr+NMS controller remains incumbent.

The registered next action is `stage17a_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
structure tensors or earlier closed families, use dataset identity, relax the
cross-dataset rule, or use protected feedback.

### Stage 17a closure - local Mann-Whitney rank context registered

The live primary-literature checkpoint selected one fixed distribution-free
local context test. Stage 17b compares opposed ten-sample half-neighborhoods
inside a radius-2 window in four fixed orientations, gives half credit to ties,
and takes the maximum absolute normalized Mann-Whitney contrast. The cue is
appended only as one outer-training-fold-eligible positive membership in the
unchanged distorted-Choquet context. It tests local spatial ordering and
monotone-photometric invariance, unlike Stage 16p's image-wide membership
midranks, Stage 16j's parametric step profile, or Stage 14l's LBP-histogram
contrast.

The authoritative protocol is `docs/paper/STAGE17B_PREREGISTRATION.md`.
`stage17b_ranklet_context` is registered with conjunctive UDED-selection
repeated CV and official BSDS500-validation criteria, exact support
preservation, fixed synthetic contracts, runtime diagnostics, and positions
1/8/15 preview. Do not tune the radius, orientations, partitions, tie rule,
rank statistic, scale, eligibility, calibration, integration, context, gate,
localizer, or thresholds from the result. The compact Choquet-gated grayscale
Scharr+NMS controller remains incumbent.

### Stage 17b closure - local Mann-Whitney rank context rejected; Stage 17c registered

The fixed radius-2 four-orientation rank cue was training-ineligible in all
`15/15` UDED-selection folds: training edge-versus-texture AUC ranged below
the preregistered `0.56` threshold, so the candidate exactly reduced to the
compact control and all UDED aggregate and fold metrics were unchanged. On
official BSDS500 validation, ODS/OIS/AP changed by
`-0.000012/-0.000201/+0.000098`. The conjunctive rule therefore rejects the
candidate. Its numerical, monotone-invariance, support, runtime, and fixed
preview contracts passed, but cannot override complete UDED ineligibility and
the failed BSDS margins. Do not tune the radius, partitions, orientations,
tie rule, rank statistic, eligibility, calibration, integration, context,
gate, localizer, or thresholds, and do not advance to multiscale, variance,
color, or learned rank variants from this result. The compact Choquet-gated
grayscale Scharr+NMS controller remains incumbent.

The registered next action is `stage17c_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
rank context or earlier closed families, use dataset identity, relax the
cross-dataset rule, or use protected feedback.

### Stage 17c closure - local GMRF Fisher-information context registered

The live primary-literature checkpoint selected one fixed information-
geometric context test. Stage 17d fits the analytic maximum-pseudo-likelihood
parameters of Levada's isotropic pairwise Gaussian Markov random field on each
unchanged median-conditioned grayscale image using the paper's second-order
eight-neighbour system. Its local type-I/type-II observed-Fisher ratio reduces
to squared standardized conditional innovation, so high response identifies a
configuration unexpected under the image's global spatial dependence. The cue
is appended only as one outer-training-fold-eligible positive membership; it
does not replace Scharr+NMS or fit from labels.

The authoritative protocol is `docs/paper/STAGE17D_PREREGISTRATION.md`.
`stage17d_gmrf_information_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, exact score-
support preservation, fixed synthetic contracts, runtime diagnostics, and
positions 1/8/15 preview. Do not tune the neighbourhood, GMRF fit, boundary
handling, evidence transform, eligibility, calibration, integration, context,
gate, localizer, or thresholds from the result, and do not advance to
multiscale, anisotropic, color, mixture, or learned random-field variants. The
compact Choquet-gated grayscale Scharr+NMS controller remains incumbent.

### Stage 17d closure - local GMRF Fisher-information context rejected; Stage 17e registered

The fixed isotropic-pairwise GMRF Fisher-information membership failed its
conjunctive promotion rule. On UDED selection, aggregate F1/precision/recall
and mean fold F1 changed by
`+0.000719/-0.000108/+0.002133/+0.000715`, with `10/15` fold wins and
eligibility in `15/15` folds. The aggregate F1 margin and nonnegative precision
condition failed. On official BSDS500 validation, ODS/OIS/AP changed by
`+0.000312/-0.002259/-0.003687`, failing all three BSDS conditions. The
synthetic, affine-invariance, repeatability, support, runtime, and fixed-preview
contracts passed, but cannot override the performance failures. The candidate
is rejected; do not tune its neighbourhood, estimator, boundary handling,
evidence transform, calibration, integration, context, gate, localizer, or
thresholds, and do not advance to multiscale, anisotropic, color, mixture, or
learned random-field variants from this result. The compact Choquet-gated
grayscale Scharr+NMS controller remains incumbent.

The registered next action is `stage17e_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
GMRF context or earlier closed families, use dataset identity, relax the
cross-dataset rule, or use protected feedback.

### Stage 17e closure - photometric quasi-invariant context registered

The live primary-literature checkpoint selected one fixed physics-based
color-context test. Stage 17f computes van de Weijer, Gevers, and Geusebroek's
shadow-shading photometric quasi-invariant on the channelwise median-
conditioned RGB image: for sigma-1 horizontal and vertical Gaussian
derivatives, it removes the component parallel to the local RGB direction and
uses the combined residual energy. The cue is appended only as one outer-
training-fold-eligible positive membership. It is designed to discount
achromatic shadow/shading derivatives without the low-intensity instability of
fully normalized color invariants.

The authoritative protocol is `docs/paper/STAGE17F_PREREGISTRATION.md`.
`stage17f_photometric_quasi_invariant_context` is registered with conjunctive
UDED-selection repeated CV and official BSDS500-validation criteria, exact
score-support preservation, fixed synthetic contracts, runtime diagnostics,
and positions 1/8/15 preview. It differs from Stage 14k's CIELAB Di Zenzo
localizer because grayscale Scharr+NMS remains unchanged and the color signal
is only photometrically decomposed context. Do not tune RGB conditioning,
derivative scale, projection, energy, invariant variants, eligibility,
calibration, integration, context, gate, localizer, or thresholds from the
result. The compact Choquet-gated grayscale Scharr+NMS controller remains
incumbent.

### Stage 17g closure - local fractal-scaling context registered

The live primary-literature checkpoint selected one fixed stochastic-scaling
context test. Stage 17h estimates a local first-order fractional-Brownian
structure-function law on the unchanged median-conditioned grayscale image at
dyadic lags `1/2/4`, using their minimal centered `9x9` support and four fixed
axes. Positive evidence is `clip(H,0,1) * clip(R2,0,1) * S1(4)`, so constant
regions remain zero while reliable high-exponent deterministic variation is
retained. The cue is appended only as one outer-training-fold-eligible
membership; the compact bank, gamma, gate, floor, grayscale Scharr+NMS, and
threshold fitting remain unchanged.

The authoritative protocol is `docs/paper/STAGE17H_PREREGISTRATION.md`.
`stage17h_local_fractal_context` is registered with conjunctive UDED-selection
repeated CV and official BSDS500-validation criteria, exact score-support
preservation, fixed synthetic contracts, runtime diagnostics, and positions
1/8/15 preview. This is a bounded repository surrogate of Toennies and
Schnabel's local-fractality principle, not an exact reproduction. Do not tune
lags, support, directions, the estimator, evidence factors, multifractal or
wavelet/color variants, calibration, integration, context, gate, localizer, or
thresholds from the result. The compact controller remains incumbent.

### Stage 17h closure - local fractal-scaling context rejected; Stage 17i registered

The fixed local fractional-Brownian scaling membership failed its conjunctive
promotion rule. On UDED selection, aggregate F1/precision/recall and mean fold
F1 changed by `+0.000164/+0.000385/-0.000232/+0.000073`; the cue was eligible
in `15/15` folds and won `11/15`, but aggregate F1 missed the required
`+0.002` margin. Official BSDS500-validation ODS/OIS/AP changed by
`+0.001978/+0.000972/+0.011064`; ODS narrowly missed its required `+0.002`
margin. The synthetic, repeatability, support, runtime, and fixed-preview
contracts passed, but all promotion conditions were required. The candidate
is rejected; do not tune its lags, support, directions, estimator, evidence,
fractal family, calibration, integration, context, gate, localizer, or
thresholds. The compact Choquet-gated grayscale Scharr+NMS controller remains
incumbent.

The registered next action is `stage17i_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
local fractal scaling or earlier closed families, use dataset identity, relax
the cross-dataset rule, or use protected feedback.

### Stage 17i closure - local brightness-entropy context registered

The live primary-literature checkpoint selected one fixed local information-
concentration test. Stage 17j computes Shiozaki's brightness distribution in
each `3x3` window of the unchanged median-conditioned grayscale image,
`p_i=I_i/sum I`, and uses the normalized Shannon-entropy deficit
`1-H(p)/log(9)` as one outer-training-fold-eligible positive membership. An
all-zero window receives zero evidence; reflection is fixed at raster
boundaries. There are no histogram bins, opposed-half comparison, orientation,
scale fit, per-image normalization, or target adapter. This is distinct from
the closed fractal, rank, GMRF, tensor, texture-distribution, structural,
aggregation, conditioning, and localizer families.

The authoritative protocol is `docs/paper/STAGE17J_PREREGISTRATION.md`.
`stage17j_brightness_entropy_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, exact score-
support preservation, fixed synthetic and multiplicative-scale contracts,
runtime diagnostics, and positions 1/8/15 preview. Do not tune the window,
intensity handling, probability definition, entropy family, zero-sum rule,
boundary handling, calibration, eligibility, integration, context, gate,
localizer, or thresholds, and do not advance to multiscale, clustered,
Renyi/Tsallis, color, spatial, histogram-binned, cross-half, or learned entropy
variants from the result. The compact Choquet-gated grayscale Scharr+NMS
controller remains incumbent.

### Stage 17j closure - brightness-entropy context rejected; Stage 17k registered

The fixed `3x3` Shiozaki-style brightness-entropy membership passed every
registered condition except the UDED aggregate-F1 margin. On UDED selection,
aggregate F1/precision/recall and mean fold F1 changed by
`+0.001106/+0.000175/+0.002682/+0.001305`, with `12/15` fold wins and
eligibility in `15/15`, but aggregate F1 missed the required `+0.002` gain.
Official BSDS500-validation ODS/OIS/AP improved by
`+0.007561/+0.003648/+0.012971`. Because the rule was conjunctive, the
candidate is rejected. Do not tune its window, intensity handling,
probability or entropy definition, calibration, integration, context, gate,
localizer, or thresholds, and do not advance to multiscale, clustered,
Renyi/Tsallis, color, spatial, histogram-binned, cross-half, or learned
entropy variants. The compact Choquet-gated grayscale Scharr+NMS controller
remains incumbent.

The registered next action is `stage17k_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
brightness entropy or earlier closed families, use dataset identity, relax the
cross-dataset rule, or use protected feedback.

### Stage 17k closure - isotropic surround-isolation context registered

The live primary-literature checkpoint selected one fixed annular edge-density
context test. Stage 17l computes Grigorescu, Petkov, and Westenberg's isotropic
surround term from the unchanged median-conditioned pre-NMS Scharr magnitude:
the positive part of a Gaussian difference with inner sigma `1`, published
outer ratio `4`, and fixed radius-12 numerical support. Positive evidence is
the bounded complement of the parameter-free suppression slope,
`1-(2/pi)atan(surround/local_energy)`, with zero evidence at zero local energy.
It is appended only as one outer-training-fold-eligible membership; no
suppression strength, hysteresis, orientation term, or parameter search is
introduced.

The authoritative protocol is `docs/paper/STAGE17L_PREREGISTRATION.md`.
`stage17l_surround_isolation_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, exact score-
support preservation, fixed synthetic isolation/density and positive-scale
contracts, runtime diagnostics, and positions 1/8/15 preview. Do not tune the
surround scales, ratio, support, energy source, slope mapping, orientation,
calibration, integration, context, gate, localizer, or thresholds, and do not
advance to adaptive, anisotropic, multiscale, color, end-stopped, facilitated,
or learned surround variants from the result. The compact Choquet-gated
grayscale Scharr+NMS controller remains incumbent.

### Stage 17l closure - isotropic surround-isolation context rejected; Stage 17m registered

The fixed isotropic surround-isolation membership failed its conjunctive
promotion rule. On UDED selection, aggregate F1/precision/recall and mean fold
F1 changed by `-0.000046/-0.000767/+0.001221/+0.000010`; the cue was eligible
in only `10/15` folds and won only `5/15`. Official BSDS500-validation
ODS/OIS/AP changed by `+0.001673/+0.001578/+0.007118`; ODS missed the required
`+0.002` margin. The synthetic, scale-invariance, repeatability, support,
runtime, and fixed-preview contracts passed, but all promotion conditions were
required. The candidate is rejected; do not tune its surround geometry,
energy source, slope mapping, orientation, calibration, integration, context,
gate, localizer, or thresholds, and do not advance to adaptive, anisotropic,
multiscale, color, end-stopped, facilitated, or learned surround variants. The
compact Choquet-gated grayscale Scharr+NMS controller remains incumbent.

The registered next action is `stage17m_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
surround context or earlier closed families, use dataset identity, relax the
cross-dataset rule, or use protected feedback.

### Stage 17m closure - two-scale topological sensitivity registered

The live primary-literature checkpoint selected one fixed variational
sensitivity test. Stage 17n implements Amstutz and Fehrenbach's analytic `h4`
approximation to the parabolic topological gradient: at published heat time
`T=2`, gradients at the coupled times `beta*T` and `(2-beta)*T`, where
`beta=1-sqrt(1-4/pi^2)`, form a symmetrized cross-scale tensor. Positive
evidence is `2*pi*T` times its positive largest eigenvalue, representing the
benefit of inserting an infinitesimal insulating crack. It enters only as one
outer-training-fold-eligible positive membership; it neither selects a scale
nor replaces localization.

The authoritative protocol is `docs/paper/STAGE17N_PREREGISTRATION.md`.
`stage17n_topological_scale_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, exact score-
support preservation, fixed synthetic flat/step/noise/quadratic-scaling
contracts, runtime diagnostics, and positions 1/8/15 preview. Median
conditioning, the compact five-member Choquet context, gamma `0.55`, gate
strength `2.0`, floor `0.10`, grayscale Scharr+NMS, and threshold fitting are
unchanged. Do not tune the heat time, quadrature, Gaussian derivative,
topological cost/PDE family, calibration, integration, context, gate,
localizer, or thresholds from the result. The compact controller remains
incumbent.

### Stage 17n closure - two-scale topological sensitivity rejected; Stage 17o registered

The fixed Amstutz-Fehrenbach `h4` two-scale topological-sensitivity membership
failed its conjunctive promotion rule despite passing the BSDS500-validation
axis. On UDED selection, aggregate F1/precision/recall and mean fold F1 changed
by `-0.000350/-0.000556/+0.000028/-0.000330`; the cue was eligible in `14/15`
folds but won only `3/15`. Official BSDS500-validation ODS/OIS/AP improved by
`+0.006420/+0.004441/+0.014245`. The synthetic, quadratic-scaling,
repeatability, support, runtime, and fixed-preview contracts passed, but cannot
override the UDED failures. The candidate is rejected; do not tune its heat
time, quadrature, Gaussian derivatives, topological cost/PDE, calibration,
integration, context, gate, localizer, or thresholds, and do not advance to
color, multiscale, anisotropic, iterative-restoration, or learned topological
variants from this result. The compact Choquet-gated grayscale Scharr+NMS
controller remains incumbent.

The registered next action is `stage17o_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
topological sensitivity or earlier closed families, use dataset identity,
relax the cross-dataset rule, or use protected feedback.

### Stage 17o closure - local robust-gradient outlier context registered

The live primary-literature checkpoint selected one fixed robust-statistical
local-significance test. Stage 17p computes Scharr magnitude on the unchanged
median-conditioned grayscale image and, in a centered reflected `9x9` window,
uses the local median and `1.4826`-normalized median absolute deviation. If
`d=max(g-median(g),0)` and `s` is that robust scale, positive evidence is the
bounded ratio `d/(d+s)`. The mechanism isolates Black and Sapiro's view of
edges as local gradient outliers without performing their anisotropic
diffusion, changing the image, or replacing localization.

The authoritative protocol is `docs/paper/STAGE17P_PREREGISTRATION.md`.
`stage17p_robust_gradient_outlier_context` is registered with conjunctive
UDED-selection repeated CV and official BSDS500-validation criteria, exact
score-support preservation, fixed flat/step/checkerboard/noise and positive-
scale contracts, runtime diagnostics, and positions 1/8/15 preview. The five
retained memberships, gamma `0.55`, gate strength `2.0`, floor `0.10`, median
conditioning, grayscale Scharr+NMS, and threshold fitting are unchanged. Do
not tune the window, gradient, robust estimator, MAD factor, mapping,
calibration, integration, context, gate, localizer, or thresholds, and do not
advance to multiscale, oriented, adaptive, color, alternative-M-estimator,
diffusive, restorative, or learned outlier variants from the result. The
compact controller remains incumbent.

### Stage 17p closure - local robust-gradient outlier context rejected; Stage 17q registered

The fixed local median/MAD gradient-outlier membership was training-ineligible
in all `15/15` UDED-selection folds (training AUC stayed below `0.56`), so the
candidate exactly reduced to the compact control and all UDED aggregate and
fold metrics were unchanged. Official BSDS500-validation ODS/OIS/AP changed by
only `+0.000035/-0.000086/+0.000100`, also failing the ODS-margin and OIS
conditions. The synthetic, scale-invariance, repeatability, support, runtime,
and fixed-preview contracts passed, but cannot override complete UDED
ineligibility and the failed BSDS criteria. The candidate is rejected; do not
tune its window, gradient, robust estimator, MAD factor, mapping, calibration,
integration, context, gate, localizer, or thresholds, and do not advance to
adaptive, oriented, multiscale, color, alternative-estimator, diffusive,
restorative, or learned outlier variants from this result. The compact
Choquet-gated grayscale Scharr+NMS controller remains incumbent.

The registered next action is `stage17q_generation2_mechanism_checkpoint`, a
high-reasoning live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
robust-outlier context or earlier closed families, use dataset identity, relax
the cross-dataset rule, or use protected feedback.

### Stage 17q closure - directional patch-recurrence context registered

The live primary-literature checkpoint selected one fixed nonlocal recurrence-
geometry test. Stage 17r uses Xu, Xu, and Quan's published `5x5` patches,
`51x51` search, four width-8 directional bands, 16 matches per band, and
`h=0.3` similarity. Positive evidence is the mean absolute directional
nonlocal residual from the paper's Eq. 6: cartoon contours should be poorly
predicted in several directions, while isotropically recurrent texture should
remain predictable. It enters only as one outer-training-fold-eligible
membership and does not run the paper's full morphology-component
decomposition.

The authoritative protocol is `docs/paper/STAGE17R_PREREGISTRATION.md`.
`stage17r_patch_recurrence_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, exact score-
support preservation, fixed flat/step/checkerboard and repeatability
contracts, runtime diagnostics, and positions 1/8/15 preview. Do not tune the
patch/search geometry, bands, directions, match count, similarity, residual,
calibration, integration, context, gate, localizer, or thresholds, and do not
advance to multiscale, color, adaptive, approximate, learned-patch, full-
decomposition, smoothing, or restoration variants from the result. The
compact Choquet-gated grayscale Scharr+NMS controller remains incumbent.

### Stage 17v closure - morphological blur-minimum context rejected; Stage 17w registered

The fixed `3x3` morphological blur-minimum membership passed the official
BSDS500-validation axis but failed the conjunctive UDED gate. UDED aggregate
F1/precision/recall and mean fold F1 changed by
`-0.000167/-0.000396/+0.000244/-0.000150`; the cue was eligible in only
`9/15` folds and won `3/15`. Official BSDS500-validation ODS/OIS/AP improved
by `+0.002346/+0.001524/+0.005760`. All non-performance contracts passed.
The candidate is rejected; do not tune or extend this morphology, support,
smoothing, zero-crossing, calibration, or integration family from the result.
The compact controller remains incumbent.

The registered next action is `stage17w_generation2_mechanism_checkpoint`, a
live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
morphology or earlier closed families, combine rejected cues, use dataset
identity, relax the cross-dataset rule, or use protected feedback.

### Stage 17x closure - semi-global scanline change-point context rejected; Stage 17y registered

The fixed row/column BIC-selected scanline change-point membership passed the
official BSDS500-validation axis and all registered UDED conditions except the
aggregate-F1 margin. UDED aggregate F1/precision/recall and mean fold F1
changed by `+0.001916/+0.000546/+0.004221/+0.001692`, with `13/15` fold
wins and eligibility in `15/15`, but the F1 gain was below the required
`+0.002`. Official BSDS500-validation ODS/OIS/AP improved by
`+0.004943/+0.002056/+0.011994`. The candidate is rejected; do not tune or
extend scanline-DP, change-point, full-SGBD, calibration, or integration
variants from this result. The compact controller remains incumbent.

The registered next action is `stage17y_generation2_mechanism_checkpoint`, a
live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
Stage 17x or earlier closed families, combine rejected cues, use dataset
identity, relax the cross-dataset rule, or use protected feedback.

### Stage 17y closure - adaptive polynomial residual context registered

The live primary-literature checkpoint selected one fixed spatially adaptive
representation-failure test. Stage 17z uses the unmodified MIT-licensed
PolyEdge author source at pinned commit
`53277503faae02514cc9249bccd2083210c00138`. On the unchanged median-
conditioned grayscale image it runs the paper's Section-7 degree-6 Chebyshev-
mesh approximation, maximum quadtree depth `8`, minimum cell size `4`, RMSE
tolerance `1e-3`, sigma-1 smoothed companion reconstruction, and equal average
of the four author-normalized residuals. The continuous residual enters only
as one outer-training-fold-eligible positive membership; the author's
percentile threshold is not run.

The authoritative protocol is `docs/paper/STAGE17Z_PREREGISTRATION.md`.
`stage17z_adaptive_polynomial_residual_context` is registered with conjunctive
UDED-selection repeated CV and official BSDS500-validation criteria, pinned-
source provenance, exact score-support preservation, fixed synthetic/
photometric contracts, runtime diagnostics, and positions 1/8/15 preview.
The compact bank, gamma `0.55`, gate strength `2.0`, floor `0.10`, grayscale
Scharr+NMS, and threshold fitting remain unchanged. Do not tune or extend the
polynomial, node, subdivision, smoothing, residual, normalization, fusion,
threshold, calibration, or integration family from the result. The compact
controller remains incumbent.

### Stage 17z closure - adaptive polynomial residual context rejected; Stage 18a registered

The fixed pinned-author PolyEdge residual failed its conjunctive promotion
rule. On UDED selection, aggregate F1/precision/recall and mean fold F1 changed
by `+0.001554/+0.000345/+0.003594/+0.001405`, with `14/15` fold wins and
eligibility in `15/15`, but aggregate F1 missed the required `+0.002` gain.
Official BSDS500-validation ODS/OIS/AP changed by
`+0.001034/-0.000566/+0.006465`, failing the ODS margin and OIS non-collapse
condition. Source, synthetic, repeatability, support, runtime, and fixed-preview
contracts passed, but all conditions were required. The candidate is rejected;
do not tune or extend the polynomial, nodes, subdivision, smoothing, residual,
normalization, fusion, threshold, coefficient-analysis, calibration, or
integration family. The compact controller remains incumbent.

The registered next action is `stage18a_generation2_mechanism_checkpoint`, a
live-primary-literature escalation that must select exactly one mechanistically
distinct bounded generation-2 falsification with a preregistered joint
UDED-selection/BSDS500-validation rule. It may not tune Stage 17z or earlier
closed families, combine rejected cues, use dataset identity, relax the
cross-dataset rule, or use protected feedback.

### Stage 18a closure - FH adaptive-region boundary context registered

The live primary-literature checkpoint selected one fixed region-adaptive
graph mechanism. Stage 18b runs Felzenszwalb and Huttenlocher's grayscale
eight-neighbour grid segmentation with published natural-image settings
Gaussian sigma `0.8` and `tau(C)=300/|C|`, with non-core minimum-size
postprocessing disabled. Both endpoints of each between-component adjacency
form a binary positive context cue. The mechanism compares external contrast
to accepted internal region variation and is distinct from the earlier
spectral response globalization, component-stability gate, scanline
segmentation, and adaptive-polynomial residual.

The authoritative protocol is `docs/paper/STAGE18B_PREREGISTRATION.md`.
`stage18b_fh_region_boundary_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, exact score-
support preservation, fixed synthetic contracts, runtime diagnostics, and
positions 1/8/15 preview. It is an equation-level scikit-image realization,
not exact author-code reproduction. Do not tune or extend graph smoothing,
scale, connectivity, weights, component processing, boundary rasterization,
color, feature-space, hierarchy, calibration, integration, context, gate,
localizer, or thresholds from the result. The compact controller remains
incumbent.

The first Stage-18b launch stopped before dataset access or result creation
because its reused Stage-17h harness requested three legacy synthetic-contract
aliases absent from the otherwise passing strict FH contract. A harness-only
retry is registered with direct compatibility diagnostics. The candidate,
parameters, datasets, folds, artifacts, evaluator, and promotion rule are
unchanged, and no scientific feedback has yet been produced.

### Stage 18b closure - FH adaptive-region boundary context rejected; Stage 18c registered

The fixed FH region-boundary cue passed the BSDS500-validation axis but failed
the conjunctive UDED gate. UDED aggregate F1/precision/recall and mean fold F1
changed by `-0.000307/-0.000632/+0.000277/-0.000248`, with only `6/15` fold
wins despite `14/15` eligibility. Official BSDS500-validation ODS/OIS/AP
improved by `+0.002858/+0.002241/+0.009290`. The candidate is rejected; do
not tune or extend FH smoothing, graph scale/connectivity/weights, component
processing, boundary rasterization, color, feature-space, hierarchy,
calibration, eligibility, or integration. The compact controller remains
incumbent.

The registered next action is `stage18c_generation2_mechanism_checkpoint`, a
live-primary-literature escalation that must select exactly one mechanistically
distinct bounded generation-2 falsification with a preregistered joint
UDED-selection/BSDS500-validation rule. It may not tune Stage 18b or earlier
closed families, combine rejected cues, use dataset identity, relax the
cross-dataset rule, or use protected feedback.

### Stage 18c closure - active micro-drift variance context registered

The live primary-literature checkpoint selected one fixed active-sampling
test. Stage 18d adapts Schmittwilken and Maertens' multiscale `S-V-N` model:
the unchanged median-conditioned grayscale image is filtered by the five
published isotropic DoG scales, shifted along ten fixed Brownian ocular-drift
paths, integrated by temporal variance, normalized within scale, and bounded
by `E/(1+E)`. Published constants are retained (40 pixels/degree, diffusion
`20 arcmin^2/s`, 0.2 seconds, 10 Hz variance sampling, ten trials, center
sigmas `0.016/0.032/0.064/0.128/0.256` degrees, 2:1 surround); seed
`20261017` freezes the stochastic paths before results. The signal enters only
as one outer-training-fold-eligible positive membership and does not replace
Scharr+NMS. It is an equation-level native-raster adaptation, not exact
author-pipeline reproduction.

The authoritative protocol is `docs/paper/STAGE18D_PREREGISTRATION.md`.
`stage18d_active_drift_variance_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, exact score-
support preservation, fixed synthetic/positive-affine contracts, runtime
diagnostics, and positions 1/8/15 preview. Do not tune or extend drift, DoG,
temporal, normalization, calibration, integration, context, gate, localizer,
or thresholds from the result. The compact controller remains incumbent.

### Stage 18d closure - active micro-drift variance context rejected; Stage 18e registered

The fixed active micro-drift response-variance membership passed the official
BSDS500-validation axis but failed the conjunctive UDED gate. UDED aggregate
F1/precision/recall and mean fold F1 changed by
`-0.000845/-0.000523/-0.001363/-0.000724`, with only `4/15` fold wins despite
eligibility in `15/15`. Official BSDS500-validation ODS/OIS/AP improved by
`+0.002372/+0.001440/+0.009916`. Exact support and all synthetic,
positive-affine, repeatability, runtime, and fixed-preview contracts passed,
but cannot override the UDED failures. The candidate is rejected; do not tune
or extend its drift, filtering, temporal statistic, normalization,
calibration, or integration family. The compact controller remains incumbent.

The registered next action is `stage18e_generation2_mechanism_checkpoint`, a
live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
Stage 18d or earlier closed families, combine rejected cues, use dataset
identity, relax the cross-dataset rule, or use protected feedback.

### Stage 18e closure - hierarchical triangle-partition context registered

The live primary-literature checkpoint selected one fixed image-wide
faint-curve test. Stage 18f uses the immutable official MATLAB implementation
of Ofir et al.'s hierarchical triangle-partition search at pinned commit
`19dc4845b26f81b68f40bc2e3e36bfe1c59d01d2`. The unchanged median-conditioned
grayscale image is isotropically fitted into one reflected `129x129` block,
passed to `runIm(block,false,0)` with all author defaults, and projected back
to native support. Its accumulated statistical contrast/shape response enters
only as one outer-training-fold-eligible positive membership; compact Choquet
aggregation and grayscale Scharr+NMS localization are unchanged. This is an
immutable-author-code integration with a fixed raster adapter, not exact
native-resolution detector reproduction.

The authoritative protocol is `docs/paper/STAGE18F_PREREGISTRATION.md`.
`stage18f_triangle_partition_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, source,
synthetic, repeatability, exact-support, runtime, and positions 1/8/15 preview
contracts. Do not tune or extend the tree, curve family, scores, author
parameters, NMS, block geometry, resampling, projection, calibration,
integration, context, gate, localizer, or thresholds from the result. The
compact controller remains incumbent.

The first Stage-18f launch passed author provenance and its preregistered
synthetic batch but stopped before UDED access because the reused Stage-17h
harness requested two absent legacy contract aliases. No scientific feedback
or manifest was produced. A harness-only retry is registered with truthful
aliases of the existing orthogonal-step positivity and localization checks;
the candidate, protocol, data, artifacts, official evaluator, and promotion
rule are unchanged.

### Stage 18f closure - hierarchical triangle-partition context rejected; Stage 18g registered

The fixed author triangle-partition faint-curve membership passed the official
BSDS500-validation axis but failed the conjunctive UDED gate. UDED aggregate
F1/precision/recall and mean fold F1 changed by
`-0.000864/-0.000920/-0.000720/-0.000786`, with `0/15` fold wins and only
`11/15` eligible folds. Official BSDS500-validation ODS/OIS/AP improved by
`+0.006363/+0.004455/+0.020200`. Source, synthetic, repeatability, exact-
support, runtime, and fixed-preview contracts passed, but cannot override the
UDED failures. The candidate is rejected; do not tune or extend its triangle
tree, curve family, scores, author parameters, block/raster adapter,
calibration, eligibility, or integration family. The compact controller
remains incumbent.

The registered next action is `stage18g_generation2_mechanism_checkpoint`, a
live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
Stage 18f or earlier closed families, combine rejected cues, use dataset
identity, relax the cross-dataset rule, or use protected feedback.

### Stage 18g closure - spectral-residual proto-object context registered

The live primary-literature checkpoint selected one fixed image-wide
statistical-innovation test. Stage 18h implements Hou and Zhang's
spectral-residual saliency equations on the unchanged median-conditioned
grayscale image at the paper's 64-pixel visual scale, with a `3x3` local
log-spectrum average and sigma-8 smoothing. The maximum-scaled saliency map is
projected back to native support and enters only as one outer-training-fold-
eligible positive membership; it does not replace Scharr+NMS or claim exact
author-code reproduction.

The authoritative protocol is `docs/paper/STAGE18H_PREREGISTRATION.md`.
`stage18h_spectral_residual_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, exact score-
support preservation, fixed rare-object/concentration and multiplicative-
scale contracts, runtime diagnostics, and positions 1/8/15 preview. The
compact bank, gamma `0.55`, gate strength `2.0`, floor `0.10`, and localizer
remain unchanged. Do not tune or extend the spectral-residual or saliency
family from the result. The compact controller remains incumbent.

### Stage 18h closure - spectral-residual context rejected; Stage 18i registered

The fixed spectral-residual proto-object membership failed its conjunctive
promotion rule on both development axes. UDED aggregate F1/precision/recall
and mean fold F1 changed by
`-0.000192/-0.000029/-0.000468/-0.000195`, with only `1/15` fold wins and
`5/15` eligible folds. Official BSDS500-validation ODS/OIS/AP changed by
`-0.000023/-0.000360/+0.000103`, failing the ODS margin and OIS non-collapse
condition. Exact support and all non-performance contracts passed, but cannot
override these failures. The candidate is rejected; do not tune or extend the
spectral-residual/saliency family. The compact controller remains incumbent.

The registered next action is `stage18i_generation2_mechanism_checkpoint`, a
live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
Stage 18h or earlier closed families, combine rejected cues, use dataset
identity, relax the cross-dataset rule, or use protected feedback.

### Stage 18i closure - image-internal PMI dependency context registered

The live primary-literature checkpoint selected one fixed statistical-
dependency test based on Isola et al.'s ECCV-2014 PMI boundary principle.
Stage 18j forms a symmetric image-internal 256-level co-occurrence model from
four centered pair axes on the unchanged median-conditioned grayscale image,
uses density-corrected `PMI_rho` at the author-code exponent `1.25`, and maps
negative PMI to bounded positive context. This tests whether recurrent texture
pairs remain statistically associated while rarer cross-object pairs do not.
It stops before the author's KDE, random-forest approximation, multiscale
affinity graph, spectral clustering, OWT, and UCM, and is therefore a bounded
repository surrogate rather than an exact author detector or a revisit of
Stage 16x.

The authoritative protocol is `docs/paper/STAGE18J_PREREGISTRATION.md`.
`stage18j_pmi_dependency_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, exact score-
support preservation, fixed synthetic/statistical contracts, runtime
diagnostics, and positions 1/8/15 preview. The compact bank, gamma `0.55`,
gate strength `2.0`, floor `0.10`, grayscale Scharr+NMS, and threshold fitting
remain unchanged. Do not tune or extend the intensity, pair, co-occurrence,
PMI, KDE, graph/spectral, calibration, or integration family from the result.
The compact controller remains incumbent.

### Stage 18j closure - image-internal PMI dependency context rejected; Stage 18k registered

The fixed image-internal PMI dependency-deficit membership passed the official
BSDS500-validation axis but missed the conjunctive UDED aggregate-F1 margin.
UDED aggregate F1/precision/recall and mean fold F1 changed by
`+0.000534/+0.002268/-0.002507/+0.000636`, with `9/15` fold wins and
eligibility in `15/15`, but aggregate F1 was below the required `+0.002` gain.
Official BSDS500-validation ODS/OIS/AP improved by
`+0.005537/+0.002090/+0.009347`. All non-performance contracts passed. The
candidate is rejected; do not tune or extend the intensity, pair,
co-occurrence, PMI, KDE, graph/spectral, calibration, or integration family.
The compact controller remains incumbent.

The registered next action is `stage18k_generation2_mechanism_checkpoint`, a
live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
Stage 18j or earlier closed families, combine rejected cues, use dataset
identity, relax the cross-dataset rule, or use protected feedback.

### Stage 18k closure - image-torque closure context registered

The live primary-literature checkpoint selected one fixed mid-level closure
test based on Nishigaki, Fermuller, and DeMenthon's CVPR-2012 image-torque
operator. Stage 18l computes signed continuous Scharr-tangent moments at the
paper's illustrated `5x5`, `21x21`, and `45x45` square supports, divides patch
torque by a radial triangle-inequality bound, and analytically backprojects
coherent support to participating edge samples. The maximum bounded support
enters only as one outer-training-fold-eligible positive membership. It does
not use the paper's learned logistic coefficients, create or link contours,
or replace grayscale Scharr+NMS.

The authoritative protocol is `docs/paper/STAGE18L_PREREGISTRATION.md`.
`stage18l_image_torque_context` is registered with conjunctive UDED-selection
repeated CV and official BSDS500-validation criteria, exact score-support
preservation, fixed synthetic closure, polarity and repeatability contracts,
runtime diagnostics, and positions 1/8/15 preview. The compact bank, gamma
`0.55`, gate strength `2.0`, floor `0.10`, conditioning, localizer, and
threshold fitting remain unchanged. Do not tune or extend the torque,
attention/segmentation, calibration, or integration family from the result.
The compact controller remains incumbent.

### Stage 18l closure - image-torque closure context rejected; Stage 18m registered

The fixed image-torque closure-support membership passed the official
BSDS500-validation axis but failed the conjunctive UDED gate. UDED aggregate
F1/precision/recall and mean fold F1 changed by
`+0.000573/-0.000342/+0.002149/+0.000483`, with `9/15` fold wins and
eligibility in `15/15`; aggregate F1 missed the required `+0.002` gain and
precision was negative. Official BSDS500-validation ODS/OIS/AP improved by
`+0.003934/+0.001900/+0.012284`. All non-performance contracts passed. The
candidate is rejected; do not tune or extend torque support, shape, edge
measure, tangent convention, coherence, backprojection, learning, attention,
segmentation, calibration, or integration. The compact controller remains
incumbent.

The registered next action is `stage18m_generation2_mechanism_checkpoint`, a
live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
Stage 18l or earlier closed families, combine rejected cues, use dataset
identity, relax the cross-dataset rule, or use protected feedback.

### Stage 18m closure - sloped-facet structural-break context registered

The live primary-literature checkpoint selected one fixed local surface-model
change test. Stage 18n follows Haralick's sloped-facet edge principle and
Chow's regression-equality statistic: under four fixed axes, two disjoint
`3x3` planar neighborhoods centered two samples to either side of a candidate
are compared with one pooled plane. The F statistic is bounded by `F/(1+F)`,
maximized across axes, and appended only as one outer-training-fold-eligible
positive membership. This tests noise-normalized change between local surfaces
without segmenting the image or changing Scharr+NMS localization.

The authoritative protocol is `docs/paper/STAGE18N_PREREGISTRATION.md`.
`stage18n_facet_break_context` is registered with conjunctive UDED-selection
repeated CV and official BSDS500-validation criteria, exact score-support
preservation, fixed synthetic/photometric contracts, runtime diagnostics, and
positions 1/8/15 preview. The compact bank, gamma `0.55`, gate strength `2.0`,
floor `0.10`, conditioning, localizer, and threshold fitting remain unchanged.
Do not tune or extend the facet geometry, axes, surface model, regression,
structural-break statistic, mapping, calibration, or integration family from
the result. The compact controller remains incumbent.

### Stage 18n closure - sloped-facet structural-break context rejected; Stage 18o registered

The fixed sloped-facet structural-break membership failed both development
axes. UDED aggregate F1/precision/recall and mean fold F1 changed by
`-0.000162/-0.000171/-0.000138/-0.000130`, with only `1/15` fold wins and
eligibility in `2/15`. Official BSDS500-validation ODS/OIS/AP changed by
`-0.000021/+0.000078/+0.000098`, failing the ODS margin. All non-performance
contracts passed, but cannot override these failures. The candidate is
rejected; do not tune or extend its facet geometry, surface model, regression,
statistic, mapping, calibration, eligibility, or integration family. The
compact controller remains incumbent.

The registered next action is `stage18o_generation2_mechanism_checkpoint`, a
live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
Stage 18n or earlier closed families, combine rejected cues, use dataset
identity, relax the cross-dataset rule, or use protected feedback.

### Stage 18o closure - median OWA compact-context aggregation registered

The live primary-literature checkpoint responded to repeated weak or
ineligible single-cue additions by adding no new descriptor. Stage 18p replaces
only distorted-Choquet arithmetic accumulation with Yager's parameter-free
five-input median OWA: after sorting the same retained fold-calibrated
memberships, context is the central order statistic `x_(3)`. This tests an
explicit three-of-five evidence semantics without a capacity, learned
aggregation weight, dataset adapter, or rejected cue combination. It is
distinct from Stage 16r's capacity-limited Sugeno max-min integral.

The authoritative protocol is `docs/paper/STAGE18P_PREREGISTRATION.md`.
`stage18p_median_owa_context` is registered with conjunctive UDED-selection
repeated CV and official BSDS500-validation criteria, algebraic and exact-
support contracts, and positions 1/8/15 preview. The feature bank, membership
calibration, gate strength `2.0`, floor `0.10`, median conditioning, grayscale
Scharr+NMS, and threshold fitting remain unchanged. Do not tune or extend the
OWA vector, quantifier, order statistic, trimming, weighting, capacity,
mixture, calibration, gate, localizer, or thresholds from the result. The
compact Choquet controller remains incumbent.

### Stage 18p closure - median OWA compact-context aggregation rejected; Stage 18q registered

The fixed five-input median OWA failed its conjunctive promotion rule on both
development axes. UDED aggregate F1/precision/recall and mean fold F1 changed
by `-0.001998/-0.001055/-0.003541/-0.001747`, with only `1/15` fold wins.
Official BSDS500-validation ODS/OIS/AP changed by
`+0.000666/-0.000988/-0.012906`; the small ODS increase missed its margin and
OIS/AP regressed. Algebraic, repeatability, exact-support, and fixed-preview
contracts passed, but cannot override the performance failures. The candidate
is rejected; do not tune or extend its OWA vector, quantifier, order statistic,
trimming, weighting, capacity, mixture, calibration, gate, localizer, or
thresholds. The compact Choquet controller remains incumbent.

The registered next action is `stage18q_generation2_mechanism_checkpoint`, a
live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
Stage 18p or earlier closed families, combine rejected cues, use dataset
identity, relax the cross-dataset rule, or use protected feedback.

### Stage 18q closure - contrast-polarity continuation context registered

The live primary-literature checkpoint selected one fixed signed-contour
grouping test based on Geisler and Perry's natural-scene statistics. Stage 18r
computes signed unit Scharr gradients on the unchanged median-conditioned
grayscale image, samples symmetrically along each local tangent at fixed pixel
offsets `1/2/4`, and requires positive polarity/orientation alignment on both
sides through a geometric mean. The unweighted mean across offsets enters only
as one outer-training-fold-eligible positive membership. It does not reproduce
the paper's learned natural-statistics observer, link contours, diffuse a
score, construct a graph, or replace localization.

The authoritative protocol is `docs/paper/STAGE18R_PREREGISTRATION.md`.
`stage18r_polarity_continuation_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, exact score-
support preservation, fixed synthetic polarity/photometric/rotation contracts,
runtime diagnostics, and positions 1/8/15 preview. The mechanism is distinct
from signless tensor coherence, the unoriented-polarity SE(2) lift, binary EDPF
chains, image torque, and Stage 14b anti-texture-map placement. Do not tune or
extend polarity continuation, association fields, contour completion, or its
integration from the result. The compact controller remains incumbent.

### Stage 18r closure - contrast-polarity continuation context rejected; Stage 18s registered

The fixed signed-gradient contrast-polarity continuation membership was
training-ineligible in all `15/15` UDED-selection folds, so the candidate
exactly reduced to compact MFI and all UDED metrics were unchanged. Official
BSDS500-validation ODS/OIS/AP changed by
`-0.000044/-0.000018/+0.000101`, failing the ODS margin and OIS condition.
All non-performance contracts passed, but cannot override complete UDED
ineligibility and the failed BSDS conditions. The candidate is rejected; do
not tune or extend polarity continuation, association fields, contour
completion, or its integration. The compact controller remains incumbent.

The registered next action is `stage18s_generation2_mechanism_checkpoint`, a
live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
Stage 18r or earlier closed families, combine rejected cues, use dataset
identity, relax the cross-dataset rule, or use protected feedback.

### Stage 18s closure - isotonic membership calibration registered

The live checkpoint responded to the complete UDED ineligibility of the fixed
polarity-continuation cue and the broader stagnation of isolated descriptor
additions by adding no cue or localizer. Stage 18t replaces only the hand-shaped
sigmoid marginal of each retained membership with a deterministic weighted
isotonic map fitted inside the outer UDED training fold. Edge and texture
samples receive equal total weight; exact ties are aggregated; weighted
pool-adjacent violators supplies a piecewise-constant nondecreasing map with
nearest-terminal extrapolation. The test asks whether cue ordering is useful
but the incumbent sigmoid shape transfers poorly.

The authoritative protocol is `docs/paper/STAGE18T_PREREGISTRATION.md`.
`stage18t_isotonic_membership_calibration` is registered with conjunctive
UDED-selection repeated CV and official BSDS500-validation criteria, exact
score-support preservation, deterministic algebraic contracts, and positions
1/8/15 preview. This differs from Stage 14m's multivariate logistic fusion and
Stage 16p's label-free image-internal rank transform. The five features,
singleton weights, gamma `0.55`, gate strength `2.0`, floor `0.10`, median
conditioning, grayscale Scharr+NMS, and threshold fitting remain unchanged. Do
not tune or extend calibration, feature, aggregation, gate, localizer, or
threshold choices from the result. The compact controller remains incumbent.

### Stage 18t closure - isotonic membership calibration rejected; Stage 18u registered

The fixed outer-fold weighted isotonic calibration moved both development axes
positively but missed both preregistered primary margins. UDED aggregate
F1/precision/recall and mean fold F1 changed by
`+0.000574/+0.000822/+0.000110/+0.000676`, with `11/15` fold wins; aggregate
F1 was below the required `+0.002`. Official BSDS500-validation ODS/OIS/AP
changed by `+0.001623/+0.000700/+0.003573`; ODS was also below its required
`+0.002`. All non-performance contracts passed, but every condition was
required. The candidate is rejected; do not tune or extend calibration or
combine it with rejected cues. The compact controller remains incumbent.

The registered next action is `stage18u_generation2_mechanism_checkpoint`, a
live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
Stage 18t or earlier closed families, combine rejected cues, use dataset
identity, relax the cross-dataset rule, or use protected feedback.

### Stage 18u closure - relative-variation coherence context registered

The live primary-literature checkpoint selected one fixed local structure-
versus-texture test from Xu et al.'s relative-total-variation framework. Stage
18v computes horizontal and vertical forward differences on the unchanged
median-conditioned grayscale image, then divides the sum of magnitudes of
sigma-3 Gaussian-windowed signed differences by the corresponding sum of
Gaussian-windowed absolute differences. The fixed 15x15 support follows the
public author code; zero total variation maps to zero evidence. Coherent
structural gradients reinforce while oscillatory texture cancels. This direct
bounded ratio does not run the paper's iterative RTV optimizer or smooth the
image, and it differs from signless tensor coherence and bilateral polarity
continuation.

The authoritative protocol is `docs/paper/STAGE18V_PREREGISTRATION.md`.
`stage18v_relative_variation_context` is registered with conjunctive UDED-
selection repeated CV and official BSDS500-validation criteria, exact score-
support preservation, fixed synthetic and photometric contracts, runtime
diagnostics, and positions 1/8/15 preview. The compact bank, gamma `0.55`, gate
strength `2.0`, floor `0.10`, median conditioning, grayscale Scharr+NMS, and
threshold fitting remain unchanged. Do not tune or extend the derivative,
window, scale, ratio, RTV/TV smoothing, calibration, or integration family from
the result. The compact controller remains incumbent.

### Stage 18v closure - relative-variation coherence context rejected; Stage 18w registered

The fixed signed-gradient inherent-to-total variation membership was training-
ineligible in all `15/15` UDED-selection folds, so the candidate exactly
reduced to compact MFI and all UDED aggregate and fold metrics were unchanged.
Official BSDS500-validation ODS/OIS/AP changed by only
`+0.000016/+0.000554/+0.000107`, missing the required `+0.002` ODS margin.
All non-performance contracts passed, but cannot override complete UDED
ineligibility and the failed BSDS margin. The candidate is rejected; do not
tune or extend its derivative, window, scale/support, ratio, calibration,
integration, RTV smoothing, or total-variation family. The compact controller
remains incumbent.

The registered next action is `stage18w_generation2_mechanism_checkpoint`, a
live-primary-literature escalation that must select exactly one
mechanistically distinct bounded generation-2 falsification with a
preregistered joint UDED-selection/BSDS500-validation rule. It may not tune
Stage 18v or earlier closed families, combine rejected cues, use dataset
identity, relax the cross-dataset rule, or use protected feedback.

### Stage 18w closure - dual-stencil Teager-energy context registered

The live primary-literature checkpoint selected one fixed nonlinear local-
activity test from Boudraa and Diop's 2-D Teager-Kaiser energy formulation.
Stage 18x computes the published axial and diagonal quadratic stencils on the
unchanged median-conditioned grayscale image, rectifies their positive parts,
and uses a geometric consensus divided by the analytic input-range bound.
This requires energy support from both complementary stencils and introduces
no smoothing, per-image normalization, fitted cue parameter, or rejected-cue
combination. It is a repository adaptation, not the paper's contrast-
enhancement pipeline.

The authoritative protocol is `docs/paper/STAGE18X_PREREGISTRATION.md`.
`stage18x_teager_energy_context` is registered with conjunctive UDED-selection
repeated CV and official BSDS500-validation criteria, exact score-support
preservation, fixed synthetic/quadratic-scale contracts, runtime diagnostics,
and positions 1/8/15 preview. The compact bank, gamma `0.55`, gate strength
`2.0`, floor `0.10`, median conditioning, grayscale Scharr+NMS, and threshold
fitting remain unchanged. Do not tune or extend the TKEO stencils,
rectification, consensus, normalization, higher-order energy, demodulation,
contrast enhancement, calibration, or integration family from the result.
The compact controller remains incumbent.

### Stage 19a closure - bounded GT-guided program and Stage 19b registered

The user-directed Stage 19--20 policy now supersedes open-ended single-cue
escalation. Stage 19 contains exactly three analysis experiments: 19B
univariate atlas, 19C pairwise redundancy/complementarity, and 19D comparison
of exactly three aggregation families. Stage 19E must freeze an ordered queue
of at most four Stage-20 candidates before any candidate outcome is inspected.
No failed candidate may be replaced; four failures end in synthesis without
automatic literature escalation. A passing candidate stops the queue for
freeze/confirmation planning.

The registered next action is `stage19b_descriptor_relevance_atlas`. It uses
the frozen twelve-cue pool on BSDS500 train with every human annotation
preserved and on UDED selection after excluding known BSDS-origin overlap.
The filename-lineage audit identifies UDED selection item `03-35028` as the
protected BSDS-test photo `35028`; it is excluded without reading protected
image or GT bytes. Stage 19B must not read BSDS validation, select a cue,
promote a detector, invent a descriptor, or alter compact MFI. It emits
machine-readable distributions, per-image AUC/AP/dependence/effect metrics,
1000-replicate image-bootstrap intervals, monotone boundary-probability
curves, consensus strata, annotator support, runtime, the overlap-clean
manifest, and a deterministic positions 1/100/200 BSDS-train descriptor
preview. The official attachment is incumbent-only on BSDS train.

### Stage 19b closure - descriptor atlas complete; Stage 19c registered

The frozen twelve-cue atlas completed on all 200 BSDS500-train images and 14
overlap-clean UDED-selection images without reading BSDS validation or any
protected image/GT blob. All twelve cues had positive mean tolerant-boundary
association in both development domains. Structure-tensor coherence was the
strongest univariate cue by mean tolerant-union AUC in both domains (about
`0.7743` BSDS train and `0.9107` UDED clean), but Stage 19B is explanatory and
does not select a cue or alter the incumbent. The incumbent-only official
BSDS-train attachment obtained ODS/OIS/AP
`0.53548/0.57479/0.51445`; it is documentary development provenance, not a
candidate comparison, and the evaluator remains reference-unverified.

The registered next action is `stage19c_pairwise_complementarity`, experiment
2 of 3. It uses only the frozen pool, BSDS train, and the identical
overlap-clean UDED manifest to measure per-image rank redundancy, conditional
log-loss gain relative to incumbent cues, and signed bilinear pairwise
interaction gain under deterministic image-grouped validation. The
preregistered cross-domain rules freeze a shortlist of at most six descriptors
for Stage 19D. No BSDS validation read, higher-order search, detector
promotion, or architecture change is permitted.

### Stage 19c closure - six-descriptor shortlist frozen; Stage 19d registered

Stage 19C completed on 200 BSDS500-train images and the identical 14-image
overlap-clean UDED-selection manifest, without reading BSDS validation or a
protected image/GT blob. Its preregistered rules froze this Stage-19D order:
`structure_tensor_coherence`, `gabor4_s13`, `semiglobal_changepoint`,
`hessian_s13`, `brightness_entropy`, and `gabor4_s5`. Frei-Chen was pruned as
redundant with brightness entropy under the fixed rule. The incumbent-only
BSDS-train attachment obtained ODS/OIS/AP
`0.535462/0.574704/0.514451`; it contains no candidate comparison and retains
the reference-unverified evaluator caveat.

The registered next action is `stage19d_aggregation_identification`, experiment
3 of 3. It compares exactly the fixed distorted-Choquet control, monotone
nonnegative additive/logistic aggregation, and monotone 2-additive Choquet
aggregation under image-grouped within-domain and cross-domain fitting. It
cannot read BSDS validation, add a family or descriptor, promote a detector,
or alter compact MFI. Stage 19E must then freeze the complete ordered queue of
at most four Stage-20 candidates before Stage 20A runs.

### Stage 19d closure - 2-additive Choquet identified; Stage 19e registered

Stage 19D completed the third and final GT-guided analysis experiment without
reading BSDS500 validation or protected blobs. The monotone 2-additive Choquet
family ranked first under the preregistered identification rule: weaker-domain
mean class-balanced log loss `0.540647`, weaker-domain AUC `0.822024`, and no
cross-domain transfer collapse. The nonnegative additive/logistic family was
classified as transfer-collapsed; the fixed distorted-Choquet control ranked
second among non-collapsed families. This identifies an aggregation family for
synthesis only and does not promote or alter the detector. The incumbent-only
BSDS500-train attachment recorded ODS/OIS/AP
`0.535458/0.574768/0.514449` and contains no candidate comparison.

The registered next action is `stage19e_stage20_queue_freeze`, the mandatory
planning-only synthesis checkpoint. It must freeze and fully preregister the
complete ordered queue of at most four Stage-20 candidates before Stage 20A
executes or any candidate BSDS500-validation result is read. The queue cannot
be expanded or replenished after outcomes; exhausting it without a pass ends
in synthesis without automatic literature escalation. Compact MFI remains the
incumbent.

### Stage 19e closure - four-candidate Stage-20 queue frozen

Stage 19E froze the complete Stage-20 queue before any candidate execution or
BSDS500-validation candidate read. All four entries use the Stage-19D winning
monotone 2-additive Choquet family: (20A) the full six-cue Stage-19C shortlist;
(20B) the four-cue shared-interaction core `gabor4_s13`, semi-global change
point, `hessian_s13`, and `gabor4_s5`; (20C) the dominant Gabor-13/change-point
pair; and (20D) the retained compact five-cue bank as an aggregation-only
fallback. The complete immutable contract is
`docs/paper/STAGE20_QUEUE_PREREGISTRATION.md` and the machine-readable order is
`automation/stage20_frozen_queue.json`.

Every candidate uses outer-fold-only membership/capacity fitting on 14-image
overlap-clean UDED selection, excluding known protected-lineage item
`03-35028` without reading its bytes, plus the unchanged official BSDS500-
validation attachment fitted from all 14 clean UDED images. A candidate must
pass the fixed conjunctive UDED, BSDS, fit/support, and preview rules. Outcomes
cannot alter later entries; there is no fifth candidate. A pass stops for
freeze/confirmation planning, while four failures end in synthesis without
literature escalation. The registered next action is
`stage20a_full_shortlist_2additive_choquet`; compact MFI remains incumbent.

### Stage 20a closure - full-shortlist 2-additive Choquet rejected; Stage 20b active

The frozen six-cue monotone 2-additive Choquet candidate passed every UDED
selection and fit/support condition: aggregate F1/precision/recall and mean
fold F1 changed by `+0.007589/+0.013213/-0.002227/+0.006121`, with `13/15`
fold wins, `15/15` converged capacity fits, and exact support preservation.
Official BSDS500-validation ODS/OIS improved by `+0.007402/+0.003711`, but AP
fell by `-0.043929`. Because the frozen promotion rule requires an ODS gain
of at least `+0.002` and nonnegative OIS and AP changes jointly, Stage 20A is
rejected. Compact MFI
remains incumbent; do not modify the queue, descriptors, fitting, calibration,
or parameters from this outcome.

The registered next action is the already-frozen candidate 2/4,
`stage20b_interaction_core_2additive_choquet`, using the four-cue interaction
core. Later entries remain unchanged, and no replacement or fifth candidate
is permitted.

### Stage 20b closure - interaction-core 2-additive Choquet rejected; Stage 20c active

The frozen four-cue monotone 2-additive Choquet candidate passed every UDED
selection and fit/support condition. Relative to compact MFI, aggregate
F1/precision/recall and mean fold F1 changed by
`+0.007539/+0.013211/-0.002354/+0.006079`, with `13/15` fold wins,
`15/15` converged capacity fits, and exact support preservation. Official
BSDS500-validation ODS/OIS improved by `+0.007330/+0.004178`, but AP fell by
`-0.043939`. The frozen conjunctive rule requires nonnegative AP, so Stage 20B
is rejected. The compact distorted-Choquet controller remains incumbent; do
not tune the descriptors, fitting, calibration, capacity, or parameters from
this result.

The registered next action is the unchanged frozen candidate 3/4,
`stage20c_dominant_pair_2additive_choquet`, using only `gabor4_s13` and
`semiglobal_changepoint`. Stage 20D remains unchanged, and no replacement or
fifth candidate is permitted.

### Stage 20c closure - dominant-pair 2-additive Choquet rejected; Stage 20d active

The frozen two-cue monotone 2-additive Choquet candidate passed every UDED
selection and fit/support condition. Relative to compact MFI, aggregate
F1/precision/recall and mean fold F1 changed by
`+0.008839/+0.011107/+0.004564/+0.006457`, with `12/15` fold wins,
`15/15` converged capacity fits, and exact support preservation. Official
BSDS500-validation ODS/OIS improved by `+0.014305/+0.008814`, but AP fell by
`-0.026222`. The frozen conjunctive rule requires nonnegative AP, so Stage 20C
is rejected. The compact distorted-Choquet controller remains incumbent; do
not tune the descriptors, fitting, calibration, capacity, or parameters from
this result.

The registered next action is the unchanged final queue entry,
`stage20d_incumbent_bank_2additive_choquet`, applying the frozen 2-additive
family to the retained compact five-cue bank. There is no replacement or fifth
candidate. If Stage 20D fails, the bounded program ends in synthesis without
automatic literature escalation.

### Stage 20d closure - frozen Stage-20 queue exhausted without promotion

The final frozen candidate passed every UDED-selection and implementation
condition. Relative to compact MFI, aggregate F1/precision/recall and mean fold
F1 changed by `+0.008531/+0.014096/-0.001226/+0.007238`, with `15/15`
fold wins, `15/15` converged capacity fits, and exact support preservation.
Official BSDS500-validation ODS/OIS/AP instead changed by
`-0.001575/-0.003695/-0.003835`. The conjunctive rule therefore rejects
Stage 20D, and compact distorted-Choquet MFI remains the incumbent.

All four preregistered Stage-20 candidates are now rejected. The campaign
showed that fold-fitted monotone 2-additive Choquet aggregation consistently
improved overlap-clean UDED selection, but did not provide the required joint
BSDS ranking transfer: Stages 20A--20C improved ODS/OIS while reducing AP, and
the aggregation-only Stage 20D reduced all three official metrics. Per the
Stage-19E finite-budget contract, the queue is exhausted with no replacement,
fifth candidate, parameter tuning, or automatic literature escalation. This is
a bounded-program synthesis stop, not attainment of the long-horizon SOTA
goal and not a human blocker.
