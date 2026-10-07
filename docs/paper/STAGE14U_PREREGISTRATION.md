# Stage 14u preregistration - fixed Yager-rule evidential ignorance

Date registered: 2026-10-07, before any Stage-14u metric or qualitative output
was inspected.

## Question and mechanism

Can explicit separation of edge belief, non-edge belief, and ignorance combine
the retained localizer/context evidence more reliably than another scalar
confidence attenuation?

Seo, Sivakumar, and Kwon (2011, DOI
`10.5391/IJFIS.2011.11.1.019`) provide the edge-detection precedent for
Dempster-Shafer evidence. Yager (1987, DOI
`10.1016/0020-0255(87)90007-7`) shows why normalized Dempster fusion can be
problematic under conflict and supplies a rule that assigns conflict to the
universal hypothesis. Smets and Kennes (1994, DOI
`10.1016/0004-3702(94)90026-4`) establish the pignistic decision layer for
belief functions.

Stage 14u uses the binary frame `Theta={edge, non-edge}` and exactly three
spatially aligned, non-overlapping sources:

1. grayscale Scharr+NMS strength;
2. distorted-Choquet context from the four retained non-persistence cues; and
3. the retained `gabor4_scale_persistence` membership.

Scale persistence is removed from source 2 so that it is not counted twice.
For every source value `q in [0,1]`, the basic belief assignment is fixed as

`m(edge)=max(2q-1,0)`,

`m(non-edge)=max(1-2q,0)`,

`m(Theta)=1-|2q-1|`.

This is the maximally ignorant binary assignment whose pignistic edge
probability remains `q`; there is no reliability coefficient or learned mass
rule. The three assignments are fused in one symmetric conjunctive product.
All empty-set conflict is assigned to `Theta` by Yager's rule. The decision
map is

`BetP(edge)=m(edge)+0.5*m(Theta)`.

The candidate applies the unchanged Stage-12d gate semantics:

`ScharrNMS * [0.10 + 0.90 * BetP(edge)^2]`.

The incumbent remains the five-feature gamma-0.55 Choquet context with the
same gate. Stage 14u is a fixed evidential-aggregation replacement, not a
reproduction of Seo et al.'s complete detector and not a test of every
evidence-theory rule.

## Why this follows Stage 14t

Stage 14t's connected-support NFA surrogate attenuated the incumbent after
fusion and failed both development axes. Threshold persistence would reuse the
same upper-level-component machinery without a sufficiently distinct causal
hypothesis. Uncertainty-controlled diffusion is also deferred because earlier
conditioning screens and fixed gravitational smoothing already warn against
immediately returning to image smoothing.

Evidence theory instead changes the representation of disagreement: lack of
commitment and direct edge/non-edge conflict remain explicit through fusion,
and conflict is not normalized away. The three sources are already validated
parts of the incumbent, so this test introduces no new descriptor, localizer,
or tunable reliability map. It is mechanistically distinct from Stage 14o,
whose cue disagreement widened intervals, deformed a capacity, and then
attenuated an otherwise complete Choquet score.

## Data, fitting, and fixed protocol

- UDED selection uses the existing 5 repeats x 3 folds.
- Compact membership fitting and each variant's score threshold remain inside
  each outer fold.
- The compact five-feature identities, gamma `0.55`, gate strength `2.0`, and
  floor `0.10` stay fixed.
- Source partition, binary mass map, conjunctive product, Yager conflict
  assignment, and pignistic transform are fixed before scoring.
- BSDS500 validation receives native-resolution soft maps exported from a
  context bank fitted on full UDED selection without reading BSDS ground truth.
- The official MATLAB evaluator uses all annotations, 99 thresholds,
  `maxDist=0.0075`, and thinning.
- UDED held-out, BSDS500 test, and BIPEDv2 test are forbidden.
- No source, mass transform, conflict rule, decision transform, gamma, gate,
  floor, or source weighting may be tuned after results are observed.

## Promotion rule

All criteria are conjunctive:

1. UDED aggregate F1 delta is nonnegative;
2. UDED aggregate precision delta is nonnegative, because reliability is the
   claimed mechanism;
3. mean paired fold-F1 delta is nonnegative;
4. candidate wins at least 9 of 15 folds in F1;
5. official BSDS500-validation evaluation completes with feedback allowed;
6. BSDS-val ODS delta is at least `+0.002`;
7. BSDS-val OIS and AP deltas are both nonnegative.

Failure of the official attachment triggers attachment repair only. A failed
fixed point rejects only this three-source least-committed Yager realization;
it does not authorize tuning and does not reject evidence theory generally.

## Outputs and qualitative policy

The runner writes aggregate, fold, per-image, and belief diagnostics, a
repository-local official exporter/manifest, and `best_method_preview.png`.
The fixed preview is the first validation image in the first deterministic CV
split with columns: conditioned input, ground truth, incumbent prediction,
candidate prediction, fused ignorance, and fused conflict. It is documentary
only and cannot affect the decision.
