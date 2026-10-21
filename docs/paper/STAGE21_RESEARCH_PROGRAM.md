# Stage 21 Research Program — Protocol Certification, Fuzzy-Literature Comparison, Ranking and Localization Diagnosis

## Purpose

Stage 21 is a new bounded program, separate from the completed Stage 19–20 campaign. Its purpose is to (1) certify that MFI-Edge is evaluated with protocols that are directly comparable to published work, (2) obtain an explicit comparison with the fuzzy edge-detection literature that uses Estrada–Jepson matching with a 2.5% image-diagonal tolerance, and (3) diagnose why Stage 20 monotone 2-additive Choquet candidates improved UDED and often BSDS ODS/OIS while losing BSDS AP.

The long-horizon target remains strong generalized non-neural edge detection. Stage 21 must not reinterpret secondary 2.5% results as the primary BSDS target. The primary promotion endpoint remains the standard Berkeley/BSDS protocol at maxDist = 0.0075 of the image diagonal.

## Global scientific rules

1. **Primary BSDS protocol:** original Berkeley multi-annotator boundary benchmark, all human annotations, one-to-one matching, `nthresh=99`, `maxDist=0.0075`, `thinpb=true`, and reporting of ODS/OIS/AP plus full PR curves.
2. **Protected split firewall:** BSDS500 test remains protected and must not be read for development. Train/val may be used according to existing repository policy; test is used only after a final frozen model/protocol is selected.
3. **Reference certification before literature claims:** before claiming direct numerical comparability to published BSDS results, reproduce at least one known reference output through the local evaluator and document exact code/version/platform. Until then, preserve `reference_reproduction_verified=false` and label MFI scores accordingly.
4. **2.5% Berkeley sensitivity track:** run the same Berkeley matcher with `maxDist=0.025` only as a spatial-tolerance sensitivity analysis. It is not a replacement for standard BSDS.
5. **2.5% Estrada–Jepson fuzzy-literature track:** implement/verify a faithful Estrada–Jepson-style correspondence protocol matching the conventions used by the target fuzzy literature, with tolerance `0.025 * image_diagonal`. Report only metrics whose definitions are protocol-compatible with the cited papers.
6. **No protocol conflation:** Berkeley 0.025 and Estrada–Jepson 0.025 are separate endpoints. Do not call Berkeley 0.025 an Estrada–Jepson reproduction.
7. **No promotion by loose tolerance:** no model may be promoted because of Berkeley 0.025 or Estrada–Jepson 0.025 performance. Promotion is governed by Berkeley 0.0075 only.
8. **No post-hoc rescue:** Stage 20A–20D maps/models are frozen for retrospective diagnostics. No descriptor, capacity, threshold, calibration, localizer, or NMS tuning is allowed while generating retrospective comparison results.
9. **Literature provenance:** any paper or code materially used to define Stage 21 protocols must be registered in the literature ledger/bibliography with DOI or official URL, exact protocol role, implementation fidelity, and training status.
10. **Finite program:** Stages 21A–21G are diagnostic/certification stages. At most one new mechanism/candidate may be preregistered in Stage 21H after the diagnostics. No open-ended fallback search is authorized by this program.

## Frozen retrospective model set

Stage 21B must evaluate the already-existing outputs/models without refit or tuning:

- incumbent compact distorted-Choquet MFI;
- Stage 20A full six-cue monotone 2-additive Choquet;
- Stage 20B four-cue interaction-core monotone 2-additive Choquet;
- Stage 20C dominant `gabor4_s13` + `semiglobal_changepoint` monotone 2-additive Choquet;
- Stage 20D incumbent five-cue bank with monotone 2-additive Choquet aggregation.

If an exact frozen map cannot be reproduced from registered artifacts/code without changing scientific parameters, report the missing reproducibility artifact as an infrastructure/reproducibility issue; do not substitute a newly tuned variant.

---

## Stage 21A — Protocol certification and implementation audit

**Role:** infrastructure/methodological certification, not a candidate experiment.

### 21A.1 Berkeley standard certification

- Pin the exact Berkeley/BSDS evaluator source and dependencies.
- Verify all-human-annotation accumulation and one-to-one correspondence behavior.
- Verify `nthresh=99`, `maxDist=0.0075`, `thinpb=true`.
- Prefer a deterministic/reference-checkable environment (Linux/WSL/container if necessary) if the current Windows matcher cannot produce a stable reference reproduction.
- Reproduce at least one known public/reference boundary-map result or official precomputed benchmark output sufficiently to establish evaluator fidelity.
- Record platform, source commits, compiler/MATLAB/toolbox versions, seeds where relevant, and reproduction deltas.
- Do not silently replace the official Berkeley matcher with a proxy.

### 21A.2 Berkeley 2.5% sensitivity evaluator

- Reuse the same certified Berkeley pipeline, changing only `maxDist` from `0.0075` to `0.025`.
- Keep all other settings identical.
- Label outputs `berkeley_maxdist_0p025_sensitivity`.

### 21A.3 Estrada–Jepson 2.5% fuzzy-literature evaluator

- Identify the exact Estrada–Jepson correspondence definition and, where available, reference implementation used or cited by the target fuzzy/Choquet literature.
- Implement or vendor a faithful evaluator under a pinned version/commit.
- Use maximum correspondence distance `0.025 * sqrt(H^2 + W^2)`.
- Preserve the target papers' convention for multiple human annotations, matching uniqueness, threshold sweep/fixed threshold, and aggregation.
- Validate on synthetic micro-cases whose expected correspondences are unambiguous: exact match, one-pixel offset, competing predictions for one GT pixel, competing GT pixels for one prediction, crossing/nearby contours, and tolerance-boundary cases.
- Document any ambiguity where a target paper does not fully specify evaluator details instead of guessing silently.

### Stage 21A stop rule

Do not begin Stage 21B until:

- Berkeley 0.0075 is either reference-certified or explicitly documented as still reference-unverified with the exact blocker;
- Berkeley 0.025 sensitivity mode is implemented as a parameter-only variant of the same pipeline;
- Estrada–Jepson 0.025 is implemented and micro-case verified to the best fidelity supported by primary sources.

A failure to certify an evaluator is an evaluation/infrastructure blocker, not a scientific failure of MFI-Edge.

---

## Stage 21B — First scientific result: three-protocol retrospective benchmark

**This is the first scientific experiment of Stage 21.** It produces a direct protocol-comparison result without fitting a new detector.

Run the same frozen retrospective model set under three distinct tracks:

### Track P — primary standard

- matcher: Berkeley/BSDS;
- `maxDist=0.0075`;
- report ODS, OIS, AP, full PR curve, ODS precision/recall, OIS precision/recall.

### Track S — Berkeley tolerance sensitivity

- matcher: same Berkeley/BSDS implementation;
- `maxDist=0.025`;
- report ODS, OIS, AP, full PR curve;
- report deltas relative to Track P for each same frozen map/model.

### Track F — fuzzy-literature comparison

- matcher: certified Estrada–Jepson-style evaluator;
- `maxDist=0.025`;
- report Precision, Recall and F-measure exactly according to the target literature's aggregation convention;
- where the literature distinguishes a fixed operating threshold from a threshold sweep, report both `F_fixed` and `F_best_threshold`, clearly separated;
- include exact literature-comparison eligibility notes for every table row.

### Required Stage 21B tables

1. `stage21b_berkeley_standard.csv`
2. `stage21b_berkeley_0p025_sensitivity.csv`
3. `stage21b_estrada_jepson_0p025_fuzzy_comparison.csv`
4. `stage21b_cross_protocol_deltas.csv`
5. a human-readable Markdown/JSON summary with the exact protocol definitions and comparability caveats.

### Stage 21B interpretation rules

- Do not average metrics across protocols.
- Do not compare ODS/AP numerically against F-measure from a different evaluator as though they were the same endpoint.
- A strong Estrada–Jepson 2.5% score may support comparison to the fuzzy literature but cannot promote a model.
- A large gain from Berkeley 0.0075 to Berkeley 0.025 is evidence of tolerance sensitivity, not proof by itself of a localization defect.
- Compare only against papers whose dataset split, ground-truth treatment, threshold procedure and matching protocol are compatible; otherwise mark the comparison as approximate/non-equivalent.

---

## Stage 21C — Anatomy of PR/AP degradation

Using incumbent and Stage 20A–20D, with emphasis on the incumbent and Stage 20C:

- export complete Berkeley 0.0075 PR curves;
- locate curve crossing points;
- report precision at fixed recall values (at least 0.25, 0.50, 0.75, 0.90 where supported);
- report AP contribution/area by recall bands;
- report predicted-edge density as a function of threshold;
- analyze per-image AP/ODS changes rather than aggregate values only;
- identify whether Stage 20 candidates gain only near a narrow operating point or across substantial PR regions.

No new detector is fitted in Stage 21C.

---

## Stage 21D — Ranking versus localization diagnosis

Test competing explanations for the Stage 20 pattern:

- **ranking hypothesis:** correct boundary evidence exists but positives and negatives are ordered poorly across thresholds;
- **localization hypothesis:** evidence is associated with the right structures but is spatially displaced, broadened or duplicated;
- **mixed hypothesis:** both effects occur.

Required analyses should include score distributions for matched positives/negatives, rank-based measures, GT-to-prediction and prediction-to-GT distance distributions, duplicate/parallel-edge behavior, and comparison across the tolerance tracks without refitting models.

---

## Stage 21E — Spatial-tolerance response curve

For the frozen incumbent and the most informative Stage 20 candidates (minimum incumbent + 20C; include others when artifacts permit without refit), evaluate the same maps with Berkeley matching at:

- `maxDist=0.00375`;
- `maxDist=0.0075`;
- `maxDist=0.015`;
- `maxDist=0.025`.

Produce `ODS(d)`, `OIS(d)` and `AP(d)` curves/tables. This is a diagnostic sensitivity study. Only `d=0.0075` remains the primary endpoint.

---

## Stage 21F — Context/localizer/NMS decomposition

Measure where ranking/localization quality changes through the detector pipeline, using already-frozen computations wherever possible:

1. contextual/aggregation score before the final localizer;
2. Scharr/local evidence;
3. context-local combination before NMS;
4. final output after NMS.

At each observable stage, compute rank/discrimination and spatial-localization diagnostics that are meaningful for that representation. Do not claim official BSDS scores for intermediate representations unless they satisfy the same output assumptions as the official evaluator.

Goal: determine whether AP degradation originates primarily in contextual aggregation, context/local coupling, or NMS/localization.

---

## Stage 21G — Human-consensus ranking analysis

Use the BSDS multi-annotator information without leaking protected test data into development.

For development-allowed images, construct an annotator-consensus strength signal and study whether model scores respect increasing human agreement. Report at least:

- Spearman correlation between score and consensus where meaningful;
- Kendall tau or equivalent rank agreement;
- pairwise ranking accuracy between higher- and lower-consensus boundary locations;
- performance stratified by consensus strength;
- representative failure cases where weak/textural edges outrank strongly agreed boundaries.

This stage is diagnostic and does not authorize fitting a new model to the test split.

---

## Stage 21H — At most one causally justified new mechanism

Only after Stages 21B–21G are complete may one new mechanism be preregistered. Its design must be explicitly caused by the diagnostic evidence.

Examples of eligible directions, only if supported by prior stages:

- rank-aware/pairwise objective for capacity fitting if ranking is the demonstrated bottleneck;
- localization-preserving/context-amplitude modulation if spatial displacement is the demonstrated bottleneck;
- consensus-aware learning target if human-consensus ordering is the demonstrated bottleneck.

The exact Stage 21H hypothesis, parameters, datasets, fitting protocol, stop rules, promotion rule and maximum experiment count must be frozen before its result is read. Stage 21 authorizes only one new mechanism/candidate family; no open-ended architecture search follows automatically.

### Primary promotion rule for Stage 21H

Promotion must use the certified Berkeley `maxDist=0.0075` development protocol and preserve the existing conjunctive spirit:

- `delta ODS >= +0.002` relative to the frozen incumbent;
- `delta OIS >= 0`;
- `delta AP >= 0`;
- no implementation/support contract failure;
- required cross-domain/development stability checks preregistered before execution.

Results at 0.025 under either Berkeley or Estrada–Jepson are secondary and cannot rescue a failure of the primary rule.

---

## Expected scientific outputs

Stage 21 should leave the repository with:

- a reference-certified or explicitly unresolved Berkeley evaluator status;
- a documented Berkeley 0.025 sensitivity mode;
- a faithful, documented Estrada–Jepson 0.025 fuzzy-literature comparison evaluator;
- the first direct retrospective three-protocol comparison for incumbent and Stage 20A–20D;
- a diagnosis of whether Stage 20's ODS/OIS-versus-AP tension is primarily ranking, localization or their interaction;
- at most one preregistered new mechanism based on that diagnosis.

## Registered first action

The first action after activating Stage 21 is **Stage 21A protocol certification**. The agent must research primary scientific sources and exact evaluator implementations before registering any scientific experiment. Once 21A is complete, the first scientific experiment is **Stage 21B**, the three-protocol retrospective benchmark using Berkeley 0.0075, Berkeley 0.025 and Estrada–Jepson 0.025 on the frozen incumbent and Stage 20A–20D outputs.
