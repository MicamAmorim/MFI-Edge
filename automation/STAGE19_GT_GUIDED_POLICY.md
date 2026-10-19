# Stage 19–20 bounded GT-guided research policy

Status: user-directed active research program. This file temporarily supersedes the generic "keep escalating to another mechanism" behavior until the bounded program below is completed or the user explicitly changes it.

## Why this program exists

Stages 16–18 produced many isolated cue additions with weak, ineligible, or dataset-asymmetric gains. Several near-winners and the positive-but-submargin Stage 18t isotonic calibration suggest that the next useful question is not simply "which new cue should be added?" but:

1. which interpretable descriptors are actually associated with human-labeled boundaries;
2. which descriptors are redundant versus conditionally complementary;
3. which interactions are stable across UDED and BSDS development data; and
4. which aggregation family best represents those stable relations.

The compact Choquet-gated grayscale Scharr+NMS controller remains the incumbent throughout Stage 19. Stage 19 is analysis/identification, not a promotion campaign.

## Hard finite budget

The program has a finite budget and MUST NOT continue indefinitely.

- Stage 19A: transition/planning checkpoint only; not counted as a scientific experiment.
- Stage 19B: GT/descriptor atlas and univariate relevance — experiment 1 of 3.
- Stage 19C: redundancy, conditional complementarity, pairwise interaction, and cross-dataset stability — experiment 2 of 3.
- Stage 19D: bounded aggregation-family identification — experiment 3 of 3.
- Stage 19E: synthesis/preregistration checkpoint only; not counted as a scientific experiment.
- Stage 20: at most FOUR preregistered candidate/promotion experiments, frozen as a queue by Stage 19E before any Stage-20 result is inspected.

Therefore the total remaining scientific-experiment budget under this program is at most SEVEN: exactly three GT-guided analysis experiments plus at most four candidate experiments.

No failed Stage-20 candidate may be replaced by a newly invented candidate after its outcome is known. No post-hoc queue expansion is allowed. If all four Stage-20 slots fail, stop the autopilot and produce a synthesis report instead of falling back to open-ended literature escalation. If a Stage-20 candidate passes the full preregistered joint promotion rule, stop the candidate queue and freeze the promoted generation for confirmation/external planning.

## Dataset firewall for Stage 19

Stage 19 is allowed to use only development data:

- BSDS500 TRAIN is the primary multi-annotator GT-guided analysis set.
- UDED selection may be used as a second development domain, but all known BSDS-origin overlaps must be excluded from GT-guided fitting/descriptor analysis. The overlap manifest must be checked explicitly before sampling.
- BSDS500 validation MUST NOT be read by Stage 19B–19D. It is reserved as the Stage-20 official development-evaluation axis.
- UDED held-out, BSDS500 test, BIPEDv2 test, and any protected/external split are forbidden for Stage-19 fitting, ranking, descriptor selection, interaction selection, or aggregation-family selection.
- Splits and resampling are by IMAGE, never by random pixels from the same image across train/test folds.

Stage 20 may return to the established UDED-selection repeated leakage-free CV plus official BSDS500-validation evaluation, using the frozen candidate queue from Stage 19E.

## Fixed descriptor pool for Stage 19

Freeze the analysis pool before inspecting Stage-19 GT-guided outcomes. Use the raw/interpretable cue maps, not previous candidate detector scores.

Incumbent five:

1. `gabor4_s5`
2. `hessian_s7`
3. `gabor4_s13`
4. `hessian_s13`
5. `gabor4_scale_persistence`

Mechanistically distinct analysis-only additions selected from completed development history before Stage-19 outcomes:

6. Stage 16z structure-tensor coherence
7. Stage 17j brightness entropy
8. Stage 17r directional patch recurrence
9. Stage 17x semi-global change-point evidence
10. Stage 17t Frei-Chen patch-subspace evidence
11. Stage 18j PMI/dependency evidence
12. Stage 18l image-torque/closure evidence

If one cue cannot be reconstructed from existing repository code without changing its scientific definition, document that as an implementation limitation; do not silently substitute a new variant.

## Ground-truth targets

BSDS500 train must preserve individual annotators. Derive, for analysis only:

- per-annotator boundary support;
- exact consensus fraction across annotators;
- a fixed tolerant/soft boundary target based on distance to human boundaries using the already established Berkeley `maxDist=0.0075` geometry, without tuning the tolerance.

UDED uses its provided single GT map, with both exact binary and the same fixed distance-tolerant analysis view.

These derived targets are explanatory/development targets only. They do not replace official Berkeley ODS/OIS/AP evaluation.

## Stage 19B — experiment 1/3: descriptor relevance atlas

For every frozen descriptor, report separately for BSDS-train and overlap-clean UDED development:

- edge/non-edge distributions;
- image-grouped ROC-AUC and AP;
- mutual information or an explicitly documented nonparametric dependence estimate;
- effect direction and magnitude;
- monotonic empirical `P(boundary | descriptor)` curves;
- BSDS human-consensus strata (for example increasing annotator agreement);
- image-bootstrap uncertainty;
- deterministic qualitative maps on predeclared examples.

No architecture change, cue selection, or promotion occurs in Stage 19B.

## Stage 19C — experiment 2/3: redundancy and complementarity

Use only Stage-19 development data and the frozen descriptor pool. Analyze pairwise relations only; no higher-order interaction search.

Report:

- descriptor correlation/redundancy by image and dataset;
- conditional/incremental information relative to incumbent cues;
- pairwise interaction/synergy using a predeclared interpretable model and image-grouped validation;
- whether effect direction and interaction sign agree across UDED and BSDS-train;
- a shared-stability score that penalizes domain disagreement.

Redundancy pruning rule: if two descriptors have absolute rank correlation >= 0.90 in both development domains, retain the one with the stronger minimum-domain relevance unless a preregistered conditional-gain test shows complementary information.

Shared-relevance rule: a descriptor must have boundary association in the same direction in both domains and must not be worse than chance in either domain. If more than six survive after redundancy pruning, retain at most six by the strongest minimum-domain standardized relevance. This produces the Stage-19D shortlist. No protected result may influence the shortlist.

## Stage 19D — experiment 3/3: aggregation-family identification

Using at most six descriptors from Stage 19C, compare exactly these three interpretable families under image-grouped/nested development fitting:

1. current distorted-Choquet context as the fixed incumbent/control;
2. monotone nonnegative additive/logistic aggregation;
3. monotone 2-additive Choquet aggregation with pairwise interaction terms.

Do not add a fourth family after seeing results. Do not tune the family list. Report per-domain and cross-domain transfer, calibration/log-loss or another preregistered probabilistic objective, boundary-ranking metrics, Shapley importance for Choquet models, pairwise interaction indices, and parameter stability across folds/domains.

Stage 19D identifies a family/subset/interactions for the synthesis checkpoint; it does not itself promote the detector.

## Stage 19E — frozen synthesis checkpoint

Before reading any BSDS500-validation outcome for a Stage-20 candidate, Stage 19E must:

1. summarize Stage 19B–19D;
2. identify only descriptors/interactions that are supported by the preregistered shared-development rules;
3. create a frozen queue of no more than four Stage-20 candidate experiments;
4. preregister every candidate, its exact architecture, fitting/calibration rule, UDED CV rule, BSDS-val export/evaluation rule, qualitative preview, runtime outputs, and promotion thresholds;
5. commit the entire queue before Stage 20A executes.

The queue may contain combinations, learned non-neural aggregation, or recalibration only when directly justified by Stage-19 evidence. A previous near-winner may be used only if Stage-19 analysis independently demonstrates shared relevance/complementarity; prior near-win status alone is insufficient.

## Stage 20 finite candidate campaign

- Maximum four executed candidates: 20A–20D.
- Evaluate each with the established leakage-free UDED-selection development protocol and official BSDS500-validation attachment.
- Preserve the current evaluator caveat: Windows Berkeley matching remains stochastic/reference-reproduction-unverified; fixed-seed diagnostic matching is forbidden for dataset scoring.
- No Stage-20 outcome may alter the remaining frozen queue.
- Do not add a fifth candidate.
- If one candidate passes the full preregistered conjunctive promotion rule, freeze/promote it and stop this campaign for confirmation planning.
- If none passes after the fourth slot, return `continue=false`, `requires_human=false`, write a synthesis of what was learned, and stop. Do not invoke autonomous literature escalation automatically.

## Incumbent and inference constraints

Until a Stage-20 candidate passes its preregistered promotion rule, the incumbent remains:

`median conditioning -> retained multiscale Gabor/Hessian/persistence memberships -> positive distorted Choquet (gamma 0.55) -> context gate (strength 2.0, floor 0.10) -> grayscale Scharr+NMS -> fold-fitted/frozen threshold`

No neural model, pretrained neural feature, neural embedding, or neural postprocessor is permitted. GT is used only during allowed development analysis/fitting and is never available at inference.
