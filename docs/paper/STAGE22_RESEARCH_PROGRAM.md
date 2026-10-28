# Stage 22 — Finite Causal Resolution and Thesis-Legacy Comparison Program

## Status and authority

This user-directed bounded program starts after the completed Stage 21 synthesis stop. It supersedes any generic open-ended literature escalation until Stage 22 is completed. Compact distorted-Choquet MFI remains the incumbent at entry. Stage 20C remains the principal frozen diagnostic comparator because it repeatedly improved ODS/OIS/local support while losing AP.

Stage 22 has a hard budget of **five scientific stages (22A–22E)**. Harness-only retries do not consume the budget. No sixth scientific experiment, replacement candidate, post-hoc parameter sweep, or automatic literature escalation is allowed. At the end of 22E the controller must stop with `continue=false` for human synthesis and planning.

## Global firewall

- BSDS500 test remains protected and must not be read for development or tuning.
- BSDS500 validation is development-only and may be used only under the already documented official-evaluation policy.
- BSDS500 train may be used for fitting only when explicitly preregistered.
- UDED/BSDS filename-lineage overlap exclusions remain active.
- Stage 22A–22D are diagnostic/comparative and cannot promote a detector.
- Stage 22E may test **at most one** causally chosen candidate under the fixed branch rule below.
- Berkeley standard `nthresh=99`, `maxDist=0.0075`, `thinpb=true`, all annotations remains the primary modern protocol.
- Berkeley `0.025`, Estrada–Jepson/KITT `0.025`, and thesis-legacy `getBoundaries -> ejBCM-F` are separate non-promotional comparison tracks and must never be conflated.
- The thesis-legacy source files vendored under `evaluation/legacy_thesis/` are provenance artifacts. Preserve their bytes and licenses; do not optimize or silently modernize them.

## Frozen thesis-legacy semantics

The historical thesis path is:

`continuous aggregated map -> getBoundaries(map, inf) -> binary boundary image -> ComparisonResiduals('ejBCM-F', ..., Dist=0.025) -> ejmBasedConfusionMatrix -> Estrada–Jepson matching`

The thesis reports each automatically detected boundary map against each human annotation using the EjBCM procedure and keeps the **largest F0.5 per image** for the legacy best-match summary. Stage 22 must additionally preserve per-GT values so mean/median-of-best reporting variants can be reconstructed transparently rather than inferred later.

The exact Drive-derived source manifest and SHA-256 hashes are authoritative in `evaluation/legacy_thesis/SOURCE_MANIFEST.json`.

## Stage 22A — Thesis legacy protocol certification

**Purpose:** certify the exact historical code path before scoring frozen detector outputs.

No BSDS image, GT, UDED image, candidate map, or protected split may be read.

Required checks:

1. Verify every vendored source hash.
2. Materialize the v1.00 backup matcher as a run-local `estradaJepsonMatching.m` without modifying source bytes.
3. MATLAB synthetic exact-match and shifted-boundary microcases for `ComparisonResiduals('ejBCM-F',...)`.
4. MATLAB synthetic continuous-ridge smoke case through `getBoundaries(..., inf)`; record whether it produces a nonempty binary map.
5. Record MATLAB/toolbox availability, source versions, licensing/provenance, and any compatibility caveat.

**Stop rule:** Stage 22B is authorized only if exact hashes and ejBCM-F microcases pass. A getBoundaries compatibility failure may receive one harness-only compatibility diagnosis, but no scientific metric may be interpreted until the historical transform is executable without changing its mathematical operations.

## Stage 22B — Frozen thesis-legacy retrospective benchmark

**Purpose:** create a direct longitudinal comparison bridge to the thesis/articles.

Frozen map sets only; no fitting, regeneration, tuning, or promotion.

Methods:

- compact distorted-Choquet incumbent;
- Stage 20C dominant-pair 2-additive Choquet;
- Stage 21H consensus-pairwise candidate may be included only as a labeled rejected diagnostic comparator if its exact maps are already frozen and complete; absence does not block the stage.

For each method/image:

1. start from the continuous detector map used by the modern pipeline;
2. apply exact `getBoundaries(map, inf)`;
3. compare resulting binary map separately with every human GT via thesis ejBCM-F at `Dist=0.025`;
4. save per-image/per-GT precision, recall, F0.5 and GT identifier;
5. report:
   - best F0.5 per image, then mean, median, Q25/Q75 and bootstrap 95% CI;
   - mean and median of all per-GT F0.5 values;
   - mean/median of per-image means across GTs;
   - distribution of which annotator/GT becomes the best match;
   - the already-certified aggregate KITT Stage-21B score in a **separate** table for contrast, never as the same metric.

This stage is comparison-only. No legacy metric can promote or tune a model.

## Stage 22C — Inter-image score calibration diagnosis

**Purpose:** test the leading Stage-21 hypothesis that useful within-image ordering fails to transfer to a common global score scale across images.

Frozen incumbent and Stage 20C maps only. No matcher rerun is needed where frozen standard-Berkeley counts suffice; exact maps may be read for score-distribution diagnostics.

Required analyses:

- per-image score quantiles, positive-support density, entropy and dynamic range;
- per-image standard-Berkeley best threshold distribution and its variance/IQR;
- relationship between per-image threshold, edge density, image regime, OIS gain and AP/envelope changes;
- pooled-vs-within-image rank decomposition;
- oracle diagnostic: quantify how much aggregate PR/AP could change under per-image monotone rescaling using GT-derived per-image optimal mappings **only as an upper bound**, never as a candidate;
- unlabeled normalization simulations (rank/quantile/z/robust-scale families) may be evaluated only as diagnostic transformations and must not be promoted or selected in 22C.

**Decision statistic:** preregister a calibration-dominance score before inspecting results, combining (a) dispersion of best thresholds, (b) recoverable oracle AP gap, and (c) cross-image versus within-image ranking discrepancy.

## Stage 22D — Local competition / NMS rank-swap diagnosis

**Purpose:** determine whether localizer coupling/NMS is the dominant remaining source of early-PR degradation.

Reuse byte-identical Stage-21F pipeline reconstruction for incumbent and Stage 20C.

Required analyses:

- rank changes from context -> shared Scharr -> pre-NMS combination -> post-NMS;
- high-consensus GT pixels promoted/demoted at each transition;
- local winning/losing pairs inside fixed spatial neighborhoods;
- duplicate/parallel response multiplicity and suppression events;
- fraction of early-PR errors attributable to score-scale mismatch versus local competition;
- no new NMS parameter sweep.

**Decision statistic:** preregister an NMS/competition-dominance score before inspection.

## Stage 22E — One causal candidate, then stop

Exactly one candidate is permitted. Choose it mechanically from 22C/22D using the preregistered dominance scores:

### Branch C — calibration dominates

Test one **unlabeled per-image monotone score standardization** that uses only statistics of the candidate score map itself, with all transform family and constants frozen from BSDS500 train/UDED training before BSDS validation. The transform may change cross-image comparability but must preserve within-image pixel ordering. No GT-derived per-image threshold or validation fit is allowed.

### Branch N — local competition dominates

Test one **context-preserving local competition rule** that changes only the final local suppression/selection mechanism while keeping descriptors, memberships and 2-additive aggregation frozen. Parameters must be fixed from training/development data before BSDS validation; no sweep on validation is allowed.

### Tie / neither dominates

If neither score exceeds its preregistered dominance threshold, **do not invent a candidate**. Stage 22 ends after 22D with `continue=false` and a synthesis explaining that the diagnostics did not causally isolate a sufficiently strong mechanism.

### Promotion rule

If 22E runs, promotion is conjunctive:

- overlap-clean UDED repeated CV: no material recall collapse and positive aggregate F1 evidence;
- standard Berkeley BSDS500-validation: `delta ODS >= +0.002`, `delta OIS >= 0`, `delta AP >= 0`;
- exact-support/implementation checks pass;
- legacy/fuzzy loose protocols are descriptive only and cannot rescue a failure.

Whether 22E passes or fails, Stage 22 ends immediately with `continue=false`. No second candidate or tuning pass.

## Required synthesis

At closure, write a compact causal table with columns:

`hypothesis | evidence for | evidence against | falsified? | implication`

covering at minimum: fixed spatial offset, context weakness, NMS/local competition, inter-image calibration, human-consensus ranking, legacy-thesis protocol compatibility, and the Stage-22E mechanism if run.
