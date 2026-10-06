# Stage 14k preregistration — CIELAB vector-gradient localizer

Date registered: 2026-10-06, before Stage 14k result inspection.

## Motivation and hypothesis

The retained controller localizes boundaries with a median-conditioned
grayscale Scharr response. This discards chromatic discontinuities and cannot
let aligned channel evidence reinforce a shared edge direction. Di Zenzo's
multi-image gradient (DOI `10.1016/0734-189X(86)90223-9`) provides a fixed
analytical tensor construction for the direction and rate of maximum change
across vector channels. The Berkeley local-boundary lineage independently
establishes brightness and CIELAB color differences as distinct useful cues
(Martin et al., 2004, DOI `10.1109/TPAMI.2004.1273918`; Arbeláez et al., 2011,
DOI `10.1109/TPAMI.2010.161`).

Hypothesis: a fixed CIELAB Di Zenzo tensor localizer supplies chromatic boundary
evidence absent from grayscale Scharr and improves UDED-selection repeated-CV
F1 after the same compact fuzzy context gate, without an unacceptable precision
loss.

## Authorized data and fixed comparison

- Use only the 15 UDED selection images.
- Use the existing deterministic 5 repeats x 3 folds.
- Never load or inspect UDED held-out, BSDS500 test, or BIPEDv2 test outcomes.
- In every training fold, relearn the positive bank and retain exactly the five
  preregistered compact features.
- Keep distorted-Choquet gamma `0.55`, context-gate strength `2.0`, floor
  `0.10`, resize policy, tolerant metric, and fold construction unchanged.
- Fit one threshold independently for each variant on the training portion of
  each outer fold, then freeze it for the paired validation portion.

Control: channel-collapsed median conditioning followed by grayscale
Scharr+NMS, as in the incumbent.

Candidate: convert RGB to CIELAB; divide all three Lab coordinates by the same
factor `100` so the Lab metric is preserved; independently apply the fixed 3x3
median to each Lab channel; take fixed 3x3 Scharr derivatives; construct the
Di Zenzo 2x2 tensor; use the square root of its maximum eigenvalue as magnitude
and the corresponding eigenvector angle for NMS; apply the unchanged compact
context gate.

No color-space, channel-weight, median-size, derivative-kernel, normalization,
fusion, or NMS sweep is allowed. The test is a localizer replacement, not a
router or a grayscale/color mixture.

## Primary endpoint and promotion rule

Aggregate tolerant F1 across all paired outer validation events is primary.
Promote the color-tensor localizer only if all conditions hold:

1. aggregate F1 delta versus the incumbent is at least `+0.001`;
2. aggregate precision delta is at least `-0.002`;
3. mean paired fold F1 delta is positive; and
4. the candidate wins at least 9 of 15 paired fold events.

Repeated-CV fold events are descriptive, not independent samples. If any
criterion fails, retain grayscale Scharr and do not tune the color construction
from this result. A passing result establishes development support only and
requires a separate confirmation before freezing a new generation.

## Required outputs

- `summary.json`
- `variant_ranking.csv`
- `fold_results.csv`
- `per_image_metrics.csv`
- `best_method_preview.png`

The deterministic preview uses the first validation image of the first split.
Columns are RGB input, ground truth, grayscale-Scharr incumbent prediction,
CIELAB-tensor candidate prediction, and retained best. It is documentary only
and cannot affect promotion.
