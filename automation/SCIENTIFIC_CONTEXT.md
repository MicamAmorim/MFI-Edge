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
