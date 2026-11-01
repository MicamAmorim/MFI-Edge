# Stage 24 — Residual/Error Suppression Campaign Preregistration

## Question

After statistically supported complementary evidence is aggregated, are the remaining errors characterized by reproducible residual-response structure that can be suppressed without destroying valid boundaries?

## Integrity repair before experimentation

Stage 24 begins with `run_stage24_preflight.py`. It blocks execution unless the one-to-one matcher passes perfect/shift/thick/fragment/empty synthetic cases, float artifacts round-trip exactly, quantized files are rejected as scientific-map inputs, and the official BSDS evaluator path is present.

Canonical GT remains in native geometry. Descriptor inference is normalized at max-side 256 and only the float score is registered to native geometry.

## Development design

Dataset: overlap-clean UDED selection, 14 retained images, known protected lineage excluded before bytes are read.

Outer evaluation: deterministic 5×3 repeated folds.

Within each outer-training fold:
1. fit cue memberships from exact GT labels;
2. select the descriptor pair using a train-only complementarity proxy;
3. fit/screen the bounded aggregators;
4. fit/screen the bounded residual suppressors;
5. choose the operating threshold on training data;
6. evaluate once on the outer validation fold with one-to-one matching.

The validation fold does not participate in pair, aggregator, suppressor, parameter, or threshold selection.

## Aggregators

Equal arithmetic mean, minimum conjunction, maximum disjunction, median, and nonnegative logistic additive fusion.

## Suppressors

Identity; local coherence; exponential disagreement compression; monotone response compression; and a learned contextual gate using fusion magnitude, local mean/std, high-pass residual, cue min/max/mean, and disagreement.

The learned gate is balanced logistic and train-only. It is a validity gate, not a calibrated-probability claim.

## Residual anatomy

After UDED-only freezing, report successful exact-background suppression, wrongly suppressed exact-GT responses, and local-support/disagreement summaries for base TP versus base FP. These exact-pixel labels are diagnostic and separate from the tolerant one-to-one evaluation metric.

## Freeze and external confirmation

The modal pair and recipe across outer folds are frozen; ties use UDED outer-validation mean F1. The frozen model is fitted on all overlap-clean UDED and written to `frozen_model.json`.

Only after freeze may BSDS500 validation be exported. The exporter reads images and the frozen model, never BSDS GT, and emits terminal 8-bit PNGs solely because the pinned official Berkeley evaluator requires image files. The upstream scientific map remains float. BSDS500 test is protected and explicitly rejected.

## Literature-detector transfer

The intended literature transfer remains part of the program, but Stage 24 fails closed on legacy quantized detector maps. A literature route is eligible only after float-preserving author/native maps have been materialized. PNG-to-float conversion is not recovery of the original scientific signal.

## Stop / resume

Create `automation/STOP_STAGE24` to request a safe stop. Completed outer folds are checkpointed individually and reused on restart.
