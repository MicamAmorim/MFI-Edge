# Stage 19 — GT-guided descriptor and aggregation analysis

Status: user-directed bounded research program, registered before Stage-19 GT-guided outcomes are inspected.

## Motivation

The completed Generation-2 campaign repeatedly found one of three patterns: isolated context cues were training-ineligible on UDED, produced only sub-margin improvements, or improved BSDS500 validation more than UDED. The fixed median OWA also failed, while Stage 18t isotonic membership calibration improved both development axes but remained below the preregistered margins. This motivates a temporary change from open-ended cue invention to a bounded explanatory study of the relationship between human boundary annotations and interpretable descriptor evidence.

The Stage-19 question is:

> Which descriptor properties and pairwise interactions are consistently associated with human-labeled boundaries in more than one development domain, and which interpretable aggregation family best represents that shared structure?

Stage 19 is not a detector-promotion stage. The compact Choquet-gated Scharr+NMS model remains incumbent until a later candidate passes the usual conjunctive promotion rule.

## Finite research design

The analysis contains exactly three scientific experiments:

1. **Stage 19B — descriptor relevance atlas.** Measure univariate boundary association, uncertainty, monotonic conditional-probability structure, and human-consensus behavior.
2. **Stage 19C — redundancy and complementarity.** Measure pairwise redundancy, conditional information, interaction/synergy, and cross-dataset stability.
3. **Stage 19D — aggregation-family identification.** Compare exactly three interpretable aggregation families on the Stage-19C shortlist.

Stage 19A is only the transition checkpoint. Stage 19E is only the synthesis/preregistration checkpoint.

After Stage 19E, the agent may execute **at most four** frozen Stage-20 candidate experiments. The complete Stage-20 queue must be committed before Stage 20A executes. Candidate failures may not cause new candidate invention or queue expansion. A successful candidate stops the queue for freeze/confirmation planning; four unsuccessful slots stop the campaign with a synthesis report.

Thus the bounded program contains at most seven scientific experiments after the transition: three analysis experiments plus four candidate experiments.

## Development data roles

### BSDS500

- **Train:** primary GT-guided analysis set for Stage 19B–19D.
- **Validation:** not read by Stage 19B–19D; reserved for official Stage-20 development evaluation.
- **Test:** forbidden for Stage-19/20 model choice or tuning.

All BSDS-train human boundary annotations are preserved individually. Stage 19 may derive exact annotator-consensus fractions and a fixed tolerant/soft target using the established Berkeley geometric tolerance (`maxDist=0.0075`), but these analysis targets never replace official ODS/OIS/AP.

### UDED

UDED selection is a second development domain. For Stage-19 GT-guided fitting/analysis, remove any known BSDS-origin overlap before sampling. Record the resulting manifest explicitly. UDED held-out remains forbidden for optimization.

All fitting and resampling are grouped by image. Pixel-random train/test splitting is prohibited.

## Frozen descriptor pool

Stage 19 begins with the following twelve interpretable cues, frozen before GT-guided outcomes:

### Incumbent bank

1. `gabor4_s5`
2. `hessian_s7`
3. `gabor4_s13`
4. `hessian_s13`
5. `gabor4_scale_persistence`

### Analysis-only candidate cues

6. structure-tensor coherence (Stage 16z)
7. brightness entropy (Stage 17j)
8. directional patch recurrence (Stage 17r)
9. semi-global change-point evidence (Stage 17x)
10. Frei-Chen patch-subspace evidence (Stage 17t)
11. PMI/dependency evidence (Stage 18j)
12. image-torque/closure evidence (Stage 18l)

Use raw cue evidence rather than previously fused candidate detector scores. If an exact repository reconstruction is unavailable for one cue, document the limitation and omit that cue rather than inventing a replacement.

## Stage 19B — descriptor relevance atlas

For each cue and each development domain, report at minimum:

- edge and non-edge distributions;
- grouped ROC-AUC and AP;
- mutual-information/dependence estimate;
- effect direction and magnitude;
- monotone empirical `P(boundary | descriptor)` curve;
- image-bootstrap uncertainty;
- deterministic fixed-example visualizations;
- for BSDS train, behavior as annotator consensus increases.

Use exact and fixed tolerant GT views as robustness views. Do not tune the tolerance.

Stage 19B produces an explanatory atlas only. It does not select or promote a detector.

## Stage 19C — redundancy, conditional information, and interaction

Restrict the search to pairwise relations. Do not perform higher-order combinatorial searches.

For each pair, report:

- rank correlation/redundancy;
- incremental information relative to incumbent evidence;
- grouped-validation gain of an interpretable pairwise interaction model over its additive counterpart;
- interaction/effect sign by domain;
- shared-stability score emphasizing the weaker development domain.

Predeclared pruning rules:

- if two cues have absolute rank correlation at least `0.90` in both development domains, keep the one with stronger minimum-domain relevance unless conditional-gain analysis demonstrates complementary information;
- a descriptor considered shared-relevant must have boundary association in the same direction in both domains and must not be worse than chance in either;
- if more than six descriptors remain after redundancy pruning, retain at most six using the strongest minimum-domain standardized relevance.

The resulting shortlist is frozen for Stage 19D.

## Stage 19D — aggregation-family identification

Using at most six shortlisted descriptors, compare exactly three families under image-grouped/nested development fitting:

1. current distorted-Choquet context as fixed control;
2. monotone nonnegative additive/logistic aggregation;
3. monotone 2-additive Choquet aggregation with pairwise terms.

No fourth family may be added after results are seen.

Report:

- within-domain grouped validation;
- cross-domain transfer;
- probabilistic calibration/log-loss or another preregistered probabilistic loss;
- ranking metrics;
- parameter/fold stability;
- Shapley importance for Choquet models;
- pairwise Choquet interaction indices.

Stage 19D identifies a justified model family and interactions but does not itself alter the incumbent.

## Stage 19E — synthesis and frozen Stage-20 queue

Stage 19E must be completed before any Stage-20 candidate is evaluated on BSDS validation.

It must:

1. summarize the three Stage-19 experiments;
2. distinguish shared evidence from dataset-specific evidence;
3. identify supported descriptor subsets and pairwise interactions;
4. preregister no more than four Stage-20 candidates;
5. commit the entire ordered queue before Stage 20A runs.

A previous near-winner can enter the queue only if Stage 19 independently supports its descriptor/interactions. Prior near-win status is not sufficient.

## Stage 20 — bounded candidate campaign

The queue contains at most four executable candidates, 20A–20D. Each candidate must have a frozen architecture, fitting/calibration procedure, UDED repeated-CV rule, official BSDS500-validation export/evaluation rule, deterministic preview, runtime outputs, and promotion thresholds.

No candidate outcome may alter the remaining queue. There is no fifth candidate.

If a candidate passes its full preregistered conjunctive rule, freeze it and stop the queue for confirmation/external planning. If all four fail, stop the autopilot and write a synthesis rather than continuing automatically to new mechanism families.

## Incumbent during Stage 19

The frozen incumbent remains:

`median conditioning -> gabor4_s5 / hessian_s7 / gabor4_s13 / hessian_s13 / gabor4_scale_persistence -> positive distorted Choquet (gamma 0.55) -> context gate (strength 2.0, floor 0.10) -> grayscale Scharr+NMS -> fold-fitted/frozen threshold`

The no-neural inference constraint remains unchanged. Ground truth is used only for allowed development analysis/fitting and is never available at inference.
