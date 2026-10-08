# Stage 15k preregistration — frozen per-image oracle matrix

Status: registered after the Stage-15j protocol audit and before inspecting any
cross-method per-image comparison. This is a diagnosis stage, not an MFI
architecture or promotion experiment.

## Question

Across the already frozen BSDS500-validation outputs, which exact Stage-15
reference methods win on which images, and how much descriptive upper-bound
headroom exists if an oracle chooses a method per image?

## Frozen inputs

- unchanged compact MFI incumbent;
- exact author-code SED and EDPF;
- paired exact author-code CO and SCO;
- exact author-code Compass at the registered sigma-4 setting;
- exact pinned-author QFrD at its registered defaults.

No detector, prediction map, MATLAB matcher, threshold sweep, or protected
split is rerun. The analysis reads the frozen BSDS500-validation PNG maps and
the existing 99-threshold per-image Berkeley count tables produced by each
method's completed official attachment. The Stage-15a caveat remains: those
tables came from the stochastic, reference-uncertified Windows matcher.

## Fixed metrics

For every image and method, record precision, recall, F1, and the four raw
Berkeley count contributions at:

1. the raw 99-point threshold nearest that method's already reported ODS
   threshold, with the lower raw index winning an exact distance tie; and
2. the per-image best raw threshold, with the first raw index winning an exact
   F1 tie.

Build pairwise win/loss/tie tables for both views, aggregate-count method
rankings, and a per-image method oracle. The oracle sums the selected method's
raw count contributions across images and reports its gain over the best
single method under the same diagnostic view. Method order breaks exact oracle
ties: incumbent, SED, EDPF, CO, SCO, Compass, QFrD.

The oracle is deliberately ground-truth-informed and is not a deployable
router, official ODS/OIS score, or permission to design a router. It is a
descriptive complementarity bound for Stages 15l–15o.

## Deterministic qualitative artifact

`best_method_preview.png` uses sorted validation positions 1, 50, and 100.
Columns are input, mean annotator boundary for display, incumbent, SED, EDPF,
CO, SCO, Compass, and QFrD. It is documentary only and cannot select features,
methods, thresholds, or future architecture.

## Decision semantics

Stage 15k does not promote, combine, or alter any method. Its result must be
recorded before exactly one Stage-15l image-regime characterization is
registered. Any later routing or integration hypothesis remains prohibited
until the complete diagnostic sequence through Stage 15o supports it and a
separate architecture-changing experiment is preregistered.
