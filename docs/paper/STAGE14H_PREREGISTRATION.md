# Stage 14h — gravitational conditioning falsification

**Status:** Development-only preregistration, recorded before Stage 14h results.

## Scientific question

Does replacing the current median 3×3 input conditioning with the repository's
grayscale gravitational smoother improve the retained compact positive
distorted-Choquet controller under paired synthetic corruption?

This isolates the preprocessing mechanism from Stage 14f's failed d-CC
aggregation hypothesis. The literature motivating this test reports gains for
gravitational smoothing in its own single-scale, RGB multi-channel detector;
it does not establish an expected gain for this grayscale, multiscale MFI
pipeline.

## Fixed comparison

Control: median 3×3 conditioning, followed by the retained five-feature
positive distorted-Choquet context and Scharr+NMS gate.

Candidate: replace only median conditioning with grayscale gravitational
smoothing (`G=0.05`, `omega_c=20`, `iterations=30`,
`interaction_radius_frac=0.02`, `step=0.20`), before both the descriptor and
Scharr branches. Features, frozen weights, aggregation (`gamma=0.55`), gate
strength/floor, threshold procedure, and localizer are otherwise identical.
No parameter sweep is permitted in this experiment.

## Development data and split

Use only the fixed 40-item `synthetic_v2` validation manifest. Even rows
0,2,...,38 are clean calibration references; odd rows 1,3,...,39 are paired
evaluation references. For each evaluation reference, compare clean output
and same-base Gaussian noise, blur, periodic texture, and compound corruption
at severities 0.35, 0.65, and 1.0. Fit one threshold per variant on the 20
clean calibration images and freeze it across all conditions.

UDED held-out, BSDS500 test, and BIPEDv2 test are unavailable for this test.

## Primary metric and decision rule

Primary: mean per-image absolute F1 advantage (gravitational minus median),
averaged equally over the 12 corruption family-severity cells. Development
support requires all of:

1. mean corrupted-F1 advantage at least `+0.005`;
2. clean mean per-image F1 delta at least `-0.01`;
3. positive mean absolute advantage in at least three of four corruption
   families.

Report paired per-image outcomes and family/severity summaries descriptively.
This is a falsification test, not a final robustness claim; promotion requires
separate development confirmation.

Primary literature: Amorim et al. (2025), *Generalizations of Choquet-like
Integrals by Restricted Dissimilarity Functions Applied to Multi-Channel Edge
Detection Problems*, DOI <https://doi.org/10.3390/app152413273>. The exact
methodological role and transfer limitation are recorded in the bibliography
matrix.
