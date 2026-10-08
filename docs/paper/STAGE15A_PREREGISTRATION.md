# Stage 15a preregistration — evaluator and protocol audit

Status: registered before Stage-15a result inspection.  This is a reproduction
and measurement stage, not an MFI architecture experiment.

## Question

Does the repository's Windows/MATLAB path reproduce the boundary-evaluation
fixture shipped with the pinned BSDS500 benchmark, and what measurement floor
do fixed Canny, the ungated repository Scharr+NMS localizer, and the retained
incumbent establish on BSDS500 validation under exactly that path?

## Frozen protocol

- Dataset: BSDS500 validation only; development feedback, never untouched
  external evidence.
- Evaluator: pinned Berkeley `evaluation_bdry_image`, `collect_eval_bdry`, and
  `correspondPixels`; all annotators, native resolution, 99 thresholds,
  `maxDist=0.0075`, and thinning enabled.
- Export: 8-bit `[0,255]` PNG, read as `double/255`; no export-time per-image
  normalization.
- Reference check: re-evaluate the five PNG maps under the pinned
  `bench/data` fixture at its published five-threshold setting.  ODS, OIS, and
  AP must each agree with the shipped `test_2/eval_bdry.txt` value within
  `1e-4`.  This only verifies the local evaluator path; it is not a detector
  benchmark result.
- Canny: scikit-image Canny with sigma `1.0`, absolute low/high thresholds
  `0.10/0.20`, non-quantile thresholds, constant-zero boundary mode.  Its
  binary output is explicitly a fixed-operating-point audit, not a soft Canny
  ranking claim.
- Scharr: the incumbent's exact median-3, robust-scaled Scharr, sigma-1
  orientation, four-direction NMS path without its contextual gate.
- Incumbent: the unchanged compact five-membership distorted-Choquet gate and
  grayscale Scharr+NMS exporter already used by the official module.

The Canny and Scharr instantiations are strictly untrained but
repository-/library-fixed; neither is claimed to reproduce a particular
published BSDS table.  Their ODS/OIS/AP values are new matched-protocol local
baselines.

## Audits and artifacts

The runner records source commits and SHA-256 hashes, paired native image/GT
counts and sizes, annotator-count range, output convention, MATLAB compatibility
transform, and a protocol matrix distinguishing official-compatible metrics
from the historical BSDS proxy and UDED metric.

`best_method_preview.png` uses sorted validation positions 1, 50, and 100,
fixed before results, with columns: input, mean annotator boundary for display,
fixed Canny, repository Scharr+NMS, retained incumbent.  It is documentary and
cannot choose parameters or the next architecture.

## Decision semantics

Stage 15a succeeds as an audit only if the fixture reproduction passes and the
full validation attachment completes for all three baselines.  Success may set
`reference_reproduction_verified=true` for this pinned installation after the
result is reviewed.  It does not promote a detector, change the incumbent, or
authorize architecture work before Stage 15p.  A plumbing failure is repaired
without changing maps or parameters.  After closure, proceed to Stage 15b as
already ordered by the Stage-15 program.

Primary protocol sources checked on 2026-10-07:

- Berkeley Segmentation Dataset and Benchmark:
  https://www2.eecs.berkeley.edu/Research/Projects/CS/vision/bsds/
- Pinned BSDS500 mirror: https://github.com/BIDS/BSDS500
- Canny (1986), DOI `10.1109/TPAMI.1986.4767851`.
