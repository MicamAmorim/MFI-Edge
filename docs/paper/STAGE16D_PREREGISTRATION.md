# Stage 16d preregistration — fixed stable-region-boundary gate

Date registered: 2026-10-09, before any Stage-16d metric or qualitative output
was inspected.

## Question and mechanism

Can stability of the *regions separated by an edge response*, rather than
support inside connected response components, suppress fragmented texture
while preserving boundaries across the structurally different UDED-selection
and BSDS500-validation development domains?

Donoser, Riemenschneider, and Bischof, *Linked Edges as Stable Region
Boundaries* (CVPR 2010, DOI `10.1109/CVPR.2010.5539833`) construct a component
tree over an inverted 8-bit gradient map and identify region contours whose
shape persists across levels. Their experiments fix minimum region area
`400`, level displacement `5`, maximum chamfer distance `10`, and minimum
retained fragment length `70`. The paper reports that this mid-level region
support reduces clutter but can lower recall.

Stage 16d tests one transparent repository-specific surrogate of that
mechanism. It does **not** claim an exact reproduction: public primary material
does not provide the authors' node-selection implementation. The serialized
compact-MFI score is quantized once to 8 bits. At each nonredundant cutoff,
4-connected low-response regions of at least 400 pixels are compared with
their enlarged regions five levels later. Ancestor-boundary fragments within
10 pixels of the current boundary are retained when their 8-connected length
is at least 70. Each fragment receives threshold saliency multiplied by
normalized inverse mean chamfer distance. Maximum support across levels forms
one `[0,1]` stability map after the region-boundary pixels are projected by
one 4-neighbor lattice step onto the separating nonzero score sites. This
fixed projection reconciles the region-interior contour lattice with the NMS
response lattice; it is not a fitted dilation radius.

The only candidate change is a second context gate:

`candidate = incumbent * [0.10 + 0.90 * stability^2]`.

The exponent `2.0` and floor `0.10` are inherited unchanged from the incumbent
context gate. No parameter, cutoff, fusion weight, or router is fitted or
searched.

## Distinction from exhausted mechanisms

- Stage 14t tested an NFA of connected *upper-level edge-response components*.
  Stage 16d instead tests shape persistence of *lower-level adjacent regions*
  and their boundaries. It does not alter the Stage-14t null, test count, or
  attenuation.
- Stage 14i linked endpoints after localization. Stage 16d adds no pixels and
  performs no endpoint repair.
- Stage 16b averaged two complete detector maps. Stage 16d uses only the
  compact incumbent and introduces no SED dependency, detector averaging, or
  learned routing.
- The failed Stage-15p texture cue is not used.

This direction is motivated by the completed development evidence: Stage 15l
associated fragmentation with method deltas; Stage 15m found stronger
supported components for SED than MFI; and Stage 15n established a large
UDED/BSDS difference in GT component fragmentation. Those results motivate a
joint test but do not select any Stage-16d parameter.

## Data, fitting, and fixed protocol

- UDED selection uses the existing 5 repeats × 3 folds.
- Compact membership fitting and each variant's threshold remain inside each
  outer fold.
- The stability operator consumes the fold-specific incumbent after common
  8-bit serialization.
- BSDS500 validation uses the frozen incumbent exporter and applies the same
  fixed operator without reading BSDS ground truth or normalizing per image.
- Official scoring retains all annotations, 99 thresholds,
  `maxDist=0.0075`, thinning, and native resolution.
- UDED held-out, BSDS500 test, and BIPEDv2 test are forbidden.
- The area, level delta, chamfer radius, fragment length, connectivities,
  stability transform, exponent, floor, and serialization may not be tuned
  from the result.

## Promotion rule

All criteria are conjunctive:

1. UDED aggregate F1 delta is at least `+0.002`;
2. UDED aggregate precision delta is nonnegative;
3. UDED aggregate recall delta is no worse than `-0.01`;
4. mean paired fold-F1 delta is nonnegative;
5. candidate wins at least `9/15` folds in F1;
6. official BSDS500-validation evaluation completes with feedback allowed;
7. BSDS-val ODS delta is at least `+0.002`;
8. BSDS-val OIS and AP deltas are both nonnegative.

A failed attachment is repaired without rerunning CV. Failure of any scientific
criterion rejects this fixed surrogate and does not falsify component-tree or
stable-boundary theory generally. It does not authorize parameter tuning.

## Outputs and qualitative policy

The runner writes aggregate, fold, per-image, and stability diagnostics plus a
repository-local official exporter/manifest. `best_method_preview.png` uses
fixed UDED-selection positions 1, 8, and 15. Columns are input, ground truth,
out-of-fold compact-MFI prediction, stability support, and out-of-fold
candidate prediction. The preview is documentary only.
