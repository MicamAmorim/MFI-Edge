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

The UDED portion has now failed all non-collapse criteria: aggregate F1 delta
`-0.00980`, precision delta `-0.01532`, mean fold-F1 delta `-0.00798`, and
`0/15` fold wins. Stage 14o therefore cannot be promoted regardless of its
pending BSDS-val metrics. The initial attachment exposed an absolute-path
import issue in the incumbent exporter; the first retry then exposed the same
issue in the candidate exporter. The second retry reached MATLAB but exposed
an evaluator-wrapper bug: MATLAB classifies an existing MEX as file type 3,
while the wrapper accepted only type 2. The third retry passed that check but
MATLAB R2023a could not parse the pinned evaluator's chained
`groundTruth{i}.Boundaries` access. These are plumbing failures before scoring,
not scientific evidence. A fourth attachment-only retry is registered using a
run-local syntax-only compatibility mirror; the pinned vendor source remains
unchanged. Do not rerun the CV or tune the interval mechanism. After the
official metrics are documented, proceed to the preregistered
Ambrosio–Tortorelli phase-field family.

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
