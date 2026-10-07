# MFI-Edge mechanism research agenda — 2026-10-06 V2

This document is the **active hypothesis backlog** injected into autonomous
research decisions. It is not permission for an exhaustive sweep. The agent
must choose one bounded, preregistered falsification at a time and move to a
mechanistically different family after failure or stagnation.

## 1. What the accumulated evidence now says

The retained compact positive Choquet context + grayscale Scharr+NMS is much
harder to beat than expected. Stages 14i–14n have already falsified several
easy ways of adding complexity:

- hard geodesic linking improved little connectivity and harmed F1;
- one fixed phase-congruency statistic was individually useful but added no
  incremental value;
- a fixed CIELAB Di Zenzo localizer degraded precision/F1;
- half-disc LBP texture-distribution contrast added almost nothing;
- linear logistic cue fusion traded recall for precision and lost F1;
- a shallow randomized forest kept recall nearly unchanged but produced a
  large precision deficit.

The repeated pattern is important: **the bottleneck is not obtaining strong
responses; it is deciding which strong responses are trustworthy and which
structures deserve globally coherent continuation.** The next mechanisms
should therefore add principled uncertainty, geometry, global regularization,
or a genuinely new localization basis rather than another classifier over the
same cues.

Stages 14o–14q have now completed the first three priorities below without a
promotion. Interval-capacity uncertainty collapsed on UDED and lost BSDS AP;
the Ambrosio–Tortorelli phase field and fixed anisotropic singularity bank both
acted mainly as sharpening mechanisms, raising precision or BSDS ODS while
losing recall, OIS, and/or AP. These fixed forms must not be tuned from their
outcomes. The active next step is a live primary-literature checkpoint before
choosing a bounded mechanism at Priority D or later.

From this revision onward, every new image-based development experiment should
also expose a frozen exporter to the default-on official BSDS500-validation
MATLAB evaluator. UDED repeated-CV remains the historical development axis;
BSDS-val ODS/OIS/AP becomes the benchmark-aligned transfer axis.

---

## 2. Priority A — interval uncertainty + reliability-conditioned capacity field

### Core idea

Combine two mature fuzzy ideas in a constrained form:

1. replace each crisp membership `mu_i(x)` by an interval
   `[mu_i^-(x), mu_i^+(x)]` whose width is produced by image-derived
   uncertainty; and
2. let uncertainty deform the **capacity itself**, but only through a convex
   interpolation between two fixed valid capacities.

Let `u(x) in [0,1]` be uncertainty derived without GT from cross-scale
disagreement, local orientation dispersion, or descriptor instability. Let
`g_C` be the retained distorted-Choquet capacity and `g_A` a fixed additive
capacity. Define

`g_x(A) = (1-u(x)) g_C(A) + u(x) g_A(A)`.

Because a convex combination of normalized monotone capacities is again a
normalized monotone capacity, this gives a mathematically clean **local
adaptive measure** without learning an unconstrained fuzzy measure per pixel.

For interval memberships, compute lower/upper Choquet envelopes
`C^-(x), C^+(x)`. Use midpoint as contextual evidence and interval width
`w(x)=C^+(x)-C^-(x)` as an explicit reliability penalty in the gate.

A simple first gate is

`score(x) = ScharrNMS(x) * [floor + (1-floor) * G(midpoint(x)) * (1-w(x))]`

with incumbent `gamma=0.55`, strength `2.0`, floor `0.10` held fixed except for
the analytically defined uncertainty attenuation.

### Why this is especially promising now

Stage14n preserved recall while losing precision. That says “edge response
exists” is not the hard problem; distinguishing trustworthy boundaries from
ambiguous texture is. Interval width supplies an explicit **ignorance channel**
instead of forcing every cue into a crisp edge/non-edge membership.

Recent work directly supports local adaptive fuzzy measures for edge detection:
C. Marco-Detchart et al., *Sliding window based adaptative fuzzy measure for
edge detection*, Expert Systems, DOI `10.1111/exsy.13730` (first published
2024). Earlier interval/type-2 edge work includes:

- H. Bustince, E. Barrenechea, M. Pagola, J. Fernandez, *Interval-valued fuzzy
  sets constructed from matrices: Application to edge detection*, Fuzzy Sets
  and Systems 160(13), 2009, DOI `10.1016/j.fss.2008.08.005`.
- P. Melin, O. Mendoza, O. Castillo, *An improved method for edge detection
  based on interval type-2 fuzzy logic*, Expert Systems with Applications
  37(12), 2010, DOI `10.1016/j.eswa.2010.05.023`.
- T. Chaira, A. K. Ray, *Construction of fuzzy edge image using Interval Type II
  fuzzy set*, International Journal of Computational Intelligence Systems 7,
  2014, DOI `10.1080/18756891.2013.862356`.

### First falsification to prefer

This should be the default next mechanism unless fresh primary literature gives
stronger evidence for another direction.

- UDED-selection: existing 5x3 leakage-free repeated CV.
- BSDS500 validation: official MATLAB multi-annotator ODS/OIS/AP.
- No sweep of interval widths, gamma, gate strength, or local capacity family.
- Use one deterministic uncertainty construction normalized from training
  statistics only.
- Promotion must require no meaningful UDED collapse and a preregistered,
  nontrivial BSDS-val ODS/precision benefit.

If this fails, do not micro-tune intervals. Move to Priority B or C.

---

## 3. Priority B — MFI-coupled Ambrosio–Tortorelli phase field

### Core idea

The current post-threshold linker failed because it adds discrete connections
*after* localization. Instead optimize the discontinuity set itself through a
variational phase field.

A schematic energy is

`E(u,v) = D(u,I) + alpha v^2 |grad u|^2`
`         + beta [epsilon |grad v|^2 + (1-v)^2/(4 epsilon)]`
`         + eta Phi(v, MFI)`.

`v` is the continuous edge/phase field. The MFI context enters only as a fixed
spatial prior or coefficient; it does not replace the image data term.

The Ambrosio–Tortorelli approximation is a classical tractable approximation
to Mumford–Shah free-discontinuity energies. It is also attractive for this
project because modern work explicitly studies uncertainty propagation into
reconstructed edges: M. Hintermüller, S.-M. Stengl, T. M. Surowiec,
*Uncertainty Quantification in Image Segmentation Using the Ambrosio–Tortorelli
Approximation of the Mumford–Shah Energy*, Journal of Mathematical Imaging and
Vision 63 (2021), DOI `10.1007/s10851-021-01034-2`.

### Why it attacks a different failure mode

Stage14i showed that hard topology repair is too blunt. A phase-field energy
penalizes total edge-set complexity and discontinuity length jointly with image
evidence. It can suppress spurious isolated responses while favoring coherent
boundaries without adding arbitrary endpoint paths.

### Minimal falsification

Use one literature-derived normalized `(epsilon, alpha, beta)` configuration
and one fixed MFI coupling. No grid search. Compare soft phase field and final
localized map against the unchanged incumbent on UDED CV + official BSDS val.

---

## 4. Priority C — shearlet singularity localizer

### Core idea

Replace only the localization basis. Scharr is compact and strong, but it is a
first-order local operator. Shearlets are multiscale anisotropic directional
systems with theoretical characterizations of edge location and orientation.

Primary anchors:

- K. Guo, D. Labate, W.-Q. Lim, *Edge analysis and identification using the
  continuous shearlet transform*, Applied and Computational Harmonic Analysis
  27(1), 2009, DOI `10.1016/j.acha.2008.10.004`.
- K. Guo, D. Labate, *Characterization and Analysis of Edges Using the
  Continuous Shearlet Transform*, SIAM Journal on Imaging Sciences 2(3), 2009,
  DOI `10.1137/080741537`.

### Minimal falsification

Use one fixed small discrete shearlet bank and deterministic fine-scale modulus
maxima/orientation. Keep the retained five-feature MFI context gate unchanged.
First compare direct localizer replacement with Scharr+NMS. Only consider a
router if errors are demonstrably complementary on development data.

---

## 5. Priority D — orientation-lifted geometry on SE(2)

### Core idea

Lift the image from `(x,y)` into position-orientation space `(x,y,theta)` and
perform contour enhancement/completion along orientation-consistent paths.
This attacks crossings, junctions, and elongated contour continuity in a way
that ordinary 2-D geodesic linking cannot.

Relevant mathematical image-analysis literature includes:

- R. Duits, E. Franken, *Left-invariant parabolic evolutions on SE(2) and
  contour enhancement via invertible orientation scores*, Parts I/II,
  Quarterly of Applied Mathematics 68 (2010), including DOI
  `10.1090/S0033-569X-10-01173-3` for the nonlinear diffusion part.
- E. Franken, R. Duits, *Crossing-Preserving Coherence-Enhancing Diffusion on
  Invertible Orientation Scores*, IJCV 85 (2009).
- G. Citti, B. Franceschiello, G. Sanguinetti, A. Sarti,
  *Sub-Riemannian Mean Curvature Flow for Image Processing*, SIAM Journal on
  Imaging Sciences, DOI `10.1137/15M1013572`.

### Why this is not “linking again”

Stage14i linked endpoints in the image plane. SE(2) completion carries local
orientation as a state variable and favors paths that are coherent in both
position and orientation. It is a different geometry, especially at crossings
and near junctions.

### Minimal falsification

Use a fixed orientation score and one literature-derived diffusion/completion
scale. Use MFI only as a multiplicative confidence field or stopping term.
Measure ODS/F1 plus a preregistered continuity metric; do not optimize the
orientation discretization from results.

---

## 6. Priority E — fractional-order localizer

Integer first/second derivatives impose a particular noise/localization
trade-off. Fractional differentiation offers a continuum between derivative
orders and has been studied specifically for thin/selective and noise-robust
edge detection.

Primary anchor: B. Mathieu, P. Melchior, A. Oustaloup, Ch. Ceyral,
*Fractional differentiation for edge detection*, Signal Processing 83(11),
2003, DOI `10.1016/S0165-1684(03)00194-4`.

Minimal test: one literature-motivated fractional order versus Scharr, with the
same MFI context and NMS semantics. No order sweep unless the single-point test
shows real cross-dataset promise.

---

## 7. Priority F — uncertainty-controlled nonlinear PDE conditioning

### Anisotropic diffusion

Perona–Malik scale space was designed to smooth within regions while preserving
or sharpening semantically meaningful boundaries. Primary anchor: P. Perona,
J. Malik, *Scale-space and edge detection using anisotropic diffusion*, IEEE
TPAMI 1990 / Berkeley technical report UCB/CSD-88-483.

A principled MFI variant is to make the diffusivity depend on uncertainty:
strong, reliable boundary evidence lowers cross-boundary diffusion; uncertain
texture permits more smoothing.

### Shock filtering

Osher–Rudin shock filters use nonlinear time-dependent PDEs to create
piecewise-smooth images with jumps aligned to an edge detector. Primary anchor:
S. Osher, L. I. Rudin, *Feature-Oriented Image Enhancement Using Shock
Filters*, SIAM Journal on Numerical Analysis 27(4), 1990,
DOI `10.1137/0727053`.

A combined diffusion/shock mechanism may be useful only if each component has
a fixed, literature-derived role: diffusion suppresses texture/noise and shock
sharpens stable discontinuities. Do not create a free PDE parameter grid.

### Fuzzy/interval PDE coefficients

“Fuzzy differential equations” should enter only where uncertainty has a
physical/mathematical role. The defensible route is an interval or fuzzy
coefficient in an established PDE, driven by the interval-width reliability
from Priority A. For example, uncertainty can define an interval of allowed
diffusivities rather than inventing an unrelated fuzzy ODE.

---

## 8. Priority G — Dempster–Shafer evidence and explicit ignorance

Map a small number of independent evidence sources to masses on
`{edge, non-edge, ignorance}`. Fuse them with a preregistered evidence rule and
use conflict/ignorance to attenuate the localizer.

This is structurally distinct from Choquet: Choquet models non-additive
importance/interactions among cue values, whereas evidence theory explicitly
represents lack of commitment and conflict.

Literature anchors include S. H. Kwon et al., *Dempster-Shafer's Evidence
Theory-based Edge Detection*, International Journal of Fuzzy Logic and
Intelligent Systems 11(1), 2011, and earlier color-edge work based on
Dempster–Shafer theory (ICIP 2000, DOI `10.1109/ICIP.2000.899833`).

Minimal test: only Scharr+NMS, positive Choquet context, and cross-scale
persistence as sources. No large mass-rule search.

---

## 9. Priority H — persistent topology across threshold filtrations

Do not impose arbitrary target Betti numbers on natural images. Instead use
**persistence across thresholds** as a confidence mechanism: components or
contour fragments that survive a broad score filtration are more likely to be
structural than short-lived texture responses.

A first implementation should produce a persistence-derived soft saliency map
that reweights the existing score. It must not hard-link components. This is
consistent with modern use of persistent homology as a structural regularizer
in image processing, while avoiding a neural topological loss.

If useful, follow later with curvature-aware persistence or graph-based
component stability; do not start with a full topological optimization stack.

---

## 10. Secondary mathematical families

### Euler elastica / curvature regularization

If Ambrosio–Tortorelli improves continuity but rounds corners or over-shortens
high-curvature boundaries, consider an Euler-elastica/curvature penalty as a
second-stage hypothesis. Variational elastica models are established for
edge-preserving restoration and contour geometry; this is a follow-up, not a
first move.

### Non-local graph total variation

Construct a graph of similar patches or oriented structures and regularize edge
confidence with graph TV. This can suppress repetitive texture while
preserving repeated structural boundaries, but it is computationally heavier.
Graph-TV literature provides a principled non-local alternative to local
smoothing.

### Reliability-conditioned Shapley/capacity diagnostics

Before learning free local capacities, use analytical reliability fields to
study how marginal contributions change by regime. If Shapley order changes
consistently with uncertainty, that is evidence for a later bounded adaptive
capacity model. Do not learn arbitrary per-pixel capacities from validation GT.

---

## 11. Human-opinion uncertainty as an auxiliary research program

The official BSDS evaluator must remain untouched for SOTA comparison. In a
separate development analysis, preserve annotator-level information instead of
collapsing it to a consensus mask.

Define an agreement field approximately as

`p_GT(x) = (# annotators with a matched boundary near x) / N_annotators`.

Then study:

- calibration of MFI confidence versus human agreement;
- whether interval width from Priority A grows where annotators disagree;
- whether some image regions have systematic annotator reliability patterns;
- whether interval-valued GT or reliability-weighted annotator analyses explain
  false positives that are actually plausible minority opinions.

Do **not** use learned annotator weights to alter official ODS/OIS/AP. If a
future paper proposes a weighted-opinion metric, report it only as a separate
analysis with the official metric alongside it.

---

## 12. Promotion logic from now on

The development decision should become explicitly multi-axis:

1. **UDED selection, repeated leakage-free CV** — historical continuity and
   resistance to overfitting.
2. **BSDS500 validation, original MATLAB multi-annotator evaluator** — ODS,
   OIS, AP under the benchmark-aligned protocol.
3. **Synthetic robustness**, when the mechanism claims noise/blur/texture
   robustness.
4. **Qualitative fixed examples**, documentary only, never an optimization
   signal.

For a new image-based candidate, the official MATLAB attachment should be
completed before promotion. A candidate that gains on only one development
source should be treated cautiously. Prefer mechanisms with directionally
consistent gains, or a clearly preregistered trade-off that materially improves
BSDS ODS/precision without a meaningful UDED collapse.

BSDS test, BIPED test, historical UDED held-out, and any future protected final
split remain outside the optimization loop.

---

## 13. Recommended autonomous order

The first three entries have been tested and rejected in their registered
fixed forms. Unless a new primary source found by live research gives stronger
mechanistic justification, continue from entry 4:

1. ~~interval uncertainty + convex reliability-conditioned capacity field~~ — Stage 14o not promoted;
2. ~~MFI-coupled Ambrosio–Tortorelli phase field~~ — Stage 14p not promoted;
3. ~~shearlet singularity localizer~~ — Stage 14q not promoted;
4. **SE(2) orientation-lifted diffusion/completion**;
5. fractional-order localizer;
6. uncertainty-controlled anisotropic diffusion / shock filtering;
7. Dempster–Shafer explicit ignorance;
8. threshold-persistence topology;
9. graph-TV or curvature refinements.

Each item is a hypothesis family, not a hyperparameter sweep. A failed bounded
falsification should trigger a mechanistic move, not dozens of nearby variants.
