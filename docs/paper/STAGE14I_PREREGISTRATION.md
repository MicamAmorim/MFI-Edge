# Stage 14i — fixed geodesic topology-repair falsification

**Status:** Development-only preregistration, recorded before Stage 14i results.

## Scientific question

Can a fixed, interpretable topology stage repair short contour gaps in the retained
compact positive MFI-Edge detector on natural development images without materially
reducing boundary F1 or precision?

This is a postprocessing-mechanism test. It does not alter conditioning, descriptors,
feature selection, fuzzy aggregation, gating, or Scharr+NMS localization. It follows
the failed Stage-14f RDF and Stage-14h gravitational-conditioning hypotheses and does
not continue either family.

## Fixed comparison

Both variants use fold-trained memberships for the retained five features,
positive distorted-Choquet aggregation (`gamma=0.55`), context-gate strength `2.0`
and floor `0.10`, and Scharr+NMS localization.

- Control: threshold the continuous incumbent score with no linking.
- Candidate: after thresholding, apply the repository's MFI/context-guided geodesic
  endpoint linker with `max_gap=8` and `max_mean_cost=0.60`; all other linker
  parameters remain at their code defaults.

The candidate parameters are transferred unchanged from the Stage-4 synthetic
development winner. Stage 14i contains no linker-parameter sweep. Each variant fits
its decision threshold over the same fixed 21-quantile grid on the training portion
of each fold, then freezes it on the paired validation fold.

## Development data and leakage controls

Use only the 15 UDED selection images, resized to maximum side 256, under the existing
five repeats by three folds schedule and fixed seed `20261006`. Within every split:

1. learn memberships and the full positive bank from the training images only;
2. retain the five predeclared stable features;
3. fit each variant's threshold on training images only;
4. evaluate both variants on the untouched fold.

UDED held-out, BSDS500 test, BIPEDv2 test, and all historical external outcomes are
unavailable for design, selection, or interpretation.

## Endpoints and decision rule

Primary boundary endpoint: pooled repeated-CV tolerant F1, with the existing 0.75%
image-diagonal matching tolerance. Report precision and recall as well.

Topology endpoints: GT-overlapping predicted-component count, largest-component GT
coverage, and endpoint count. Repeated folds are paired descriptive events, not
independent samples.

Retain the fixed geodesic stage only if all four conditions hold:

1. aggregate F1 delta is at least `-0.001`;
2. aggregate precision delta is at least `-0.005`;
3. mean paired per-image largest-component GT-coverage delta is at least `+0.03`;
4. fold-mean coverage improves in at least 9 of 15 folds.

Failure leaves the no-link compact positive architecture incumbent. Passing this
development falsification supports only a provisional topology-stage retention; it
does not establish external generalization or SOTA.

## Qualitative artifact

Write `best_method_preview.png` from the first validation image of the first
deterministic repeated-CV split. Columns are conditioned input, ground truth,
no-link incumbent, fixed-geodesic candidate, and retained best. This fixed image is
for inspection only and cannot affect the decision.

## Literature/mechanism checkpoint

The October 2026 refresh found that current neural work now treats crispness and
continuity as explicit bottlenecks: MatchED aligns edge localization with one-to-one
matching, while MS2Edge identifies sparse discontinuities as a limiting failure mode.
Neither neural mechanism is copied into inference. They sharpen the evaluation
question; the concrete non-neural candidate is justified by the repository's earlier
development-only Stage-4 result, where fixed geodesic linking increased F1 by about
0.006 and nearly doubled largest-component GT coverage on held-out synthetic data.

Primary sources:

- Cetinkaya, Kalkan & Akbas (2026), *MatchED: Crisp Edge Detection Using End-to-End,
  Matching-based Supervision*, accepted CVPR 2026, arXiv:2602.20689.
- Fan et al. (2025/2026), *MS2Edge: Towards Energy-Efficient and Crisp Edge Detection
  with Multi-Scale Residual Learning in SNNs*, Pattern Recognition 112883,
  DOI 10.1016/j.patcog.2025.112883.
