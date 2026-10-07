# Stage 14q preregistration — fixed anisotropic singularity localizer

Date registered: 2026-10-07, before any Stage-14q metric or qualitative output
was inspected.

## Question and mechanism

Can a fixed multiscale anisotropic directional representation localize natural
boundaries more effectively than the incumbent compact Scharr operator while
leaving the retained MFI context gate unchanged?

Guo, Labate and Lim (2009, DOI `10.1016/j.acha.2008.10.004`) and Guo and
Labate (2009, DOI `10.1137/080741537`) establish the motivation: shearlet
coefficients characterize edge location and orientation through anisotropic
multiscale singularity analysis. Stage 14q is a deliberately small discrete
operationalization, not a reproduction of a continuous shearlet transform.
It uses eight fixed odd anisotropic Gaussian-derivative atoms: normal scales
`1` and `2` pixels, tangent scale twice the normal scale, and edge-normal
angles `0`, `45`, `90`, and `135` degrees. The maximum absolute response and
its winning atom orientation define the soft response and NMS direction.

Only the localization basis changes. The median conditioning, retained five
compact memberships, distorted-Choquet gamma `0.55`, context-gate strength
`2.0`, and floor `0.10` remain unchanged. No router or mixture is tested.

## Data, fitting, and fixed protocol

- UDED selection uses the existing 5 repeats × 3 folds.
- Compact membership fitting and the score threshold remain inside each outer
  fold; the atom bank is globally fixed.
- BSDS500 validation receives native-resolution soft maps exported from a
  context bank fitted on full UDED selection without reading BSDS ground truth.
- The official MATLAB evaluator uses all annotations, 99 thresholds,
  `maxDist=0.0075`, and thinning.
- UDED held-out, BSDS500 test, and BIPEDv2 test are forbidden.
- No scale, angle, elongation, atom, normalization, NMS, gate, or fusion sweep
  is allowed after results are observed.

## Promotion rule

All criteria are conjunctive:

1. UDED aggregate F1 delta is nonnegative;
2. UDED aggregate precision delta is nonnegative;
3. mean paired fold-F1 delta is nonnegative;
4. candidate wins at least 9 of 15 folds;
5. official BSDS500-validation evaluation completes with feedback allowed;
6. BSDS-val ODS delta is at least `+0.002`;
7. BSDS-val OIS and AP deltas are both nonnegative.

Failure of the official attachment triggers attachment repair only. A failure
on either development axis blocks promotion. A failed single-point result does
not disprove shearlet edge theory, but it does prohibit tuning this atom bank
from its outcome; the next step must be a mechanistically distinct agenda item.

## Outputs and qualitative policy

The runner writes aggregate, fold, per-image and atom-use diagnostics, a
repository-local official exporter/manifest, and `best_method_preview.png`.
The fixed preview is the first validation image in the first deterministic CV
split with columns: conditioned input, ground truth, incumbent, candidate, raw
maximum modulus, and retained incumbent. It is documentary only.
