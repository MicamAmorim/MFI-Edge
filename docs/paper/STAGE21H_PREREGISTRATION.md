# Stage 21H preregistration — consensus-ranked 2-additive Choquet

## Causal diagnosis

Stage 21G completed the frozen Stage-21 diagnostic sequence. Across BSDS500
validation annotation-union pixels, compact MFI's pooled higher-consensus
pairwise accuracy was only `0.522750`; Stage 20C reached only `0.523074`.
Stage 20C nevertheless improved standard-Berkeley ODS/OIS, tolerant-union
ranking, and spatial support. Together with the persistent AP loss, this makes
human-importance ordering—not another cue or a wholesale localization
replacement—the bounded Stage-21H target.

## Single candidate

`stage21h_consensus_pairwise_choquet` is the only candidate authorized by
Stage 21. It retains Stage 20C's fixed `gabor4_s13` and
`semiglobal_changepoint` memberships, monotone 2-additive Choquet form,
scalar monotone calibration, median conditioning, context gate strength `2.0`,
floor `0.10`, grayscale Scharr+NMS localizer, and threshold procedure. It
changes only the capacity-fitting loss.

Inside every outer UDED training fold, deterministic pairs require tolerant
UDED boundary samples to outrank background. The second development source is
all 200 BSDS500-train images with every annotation preserved. At each pixel,
consensus is the fraction of annotations having a boundary within the same
fixed `1.5`-pixel radius used by Stage 21G; deterministic within-image pairs
require every higher consensus level to outrank every lower level, including
zero. Exactly 512 stratified pairs are drawn per image and source. The two
domains contribute equal mean pairwise logistic loss, independent of their
different image counts. Interaction ridge `1e-4`, seed `20261028`, SLSQP
constraints, and 700-iteration limit are fixed. Membership and final scalar
calibration remain fitted only from the applicable outer UDED training fold,
so consensus supervision changes capacity interactions rather than adding a
target-domain calibration adapter.

For the official BSDS500-validation exporter, the same fit uses all 14
overlap-clean UDED-selection images plus BSDS500 train. The known UDED item
`03-35028`, which has protected BSDS-test lineage, remains excluded without
reading its image or GT bytes. BSDS validation ground truth is never read by
the exporter, and BSDS test remains protected.

The pairwise large-margin/ranking principle is classical and non-neural; the
implementation uses convex logistic pair ordering under the existing
normalized monotone-capacity constraints. It is a repository objective, not
an exact reproduction of an author edge detector. The inference path is
unchanged and contains no neural component.

## Evaluation and promotion

Overlap-clean UDED selection uses the established 5x3 leakage-free repeated
CV. Relative to compact MFI, all of the following are required:

- aggregate F1 delta at least `+0.002`;
- aggregate precision delta nonnegative;
- aggregate recall delta at least `-0.003`;
- mean paired fold-F1 delta nonnegative and at least 9/15 fold wins;
- 15/15 converged capacity fits and exact positive-score-support preservation.

The required standard-Berkeley BSDS500-validation attachment uses
`nthresh=99`, `maxDist=0.0075`, thinning, and all annotations. It must improve
ODS by at least `+0.002` with nonnegative OIS and AP changes. Every condition
is conjunctive. Berkeley/Estrada–Jepson `0.025` results cannot rescue a
failure. `reference_reproduction_verified=false` remains explicit, so no
final SOTA claim may rely on this local evaluator.

The deterministic preview uses overlap-clean UDED positions 1/7/14 with
input, GT, compact-MFI out-of-fold prediction, candidate out-of-fold
prediction, and candidate continuous score. It is documentary only.

No loss mixing weight, pair count, radius, target transform, cue, capacity
order, descriptor, membership, calibration, gate, localizer, NMS, or threshold
may be tuned from the result. A pass stops for freeze/confirmation planning.
A failure ends the finite Stage-21 program in synthesis: there is no second
Stage-21H candidate and no automatic replacement or literature escalation.
