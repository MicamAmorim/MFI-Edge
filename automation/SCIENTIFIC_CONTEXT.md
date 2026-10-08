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
