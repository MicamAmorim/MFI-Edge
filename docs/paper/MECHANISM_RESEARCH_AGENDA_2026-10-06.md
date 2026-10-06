# MFI-Edge mechanism research agenda — 2026-10-06

This is a **hypothesis backlog**, not permission for a brute-force sweep. The
autonomous agent should select one minimal falsification at a time, preregister
it, and move to a mechanistically different family after failure/stagnation.

## What the recent failures say

The current compact positive Choquet context + grayscale Scharr+NMS remains
surprisingly hard to beat. Stages 14i–14n collectively rule out several easy
ways of adding complexity:

- hard geodesic linking harmed F1 despite small connectivity gains;
- one phase-congruency moment was discriminative but added no incremental value;
- a fixed CIELAB Di Zenzo localizer lost precision/F1;
- half-disc LBP texture contrast added almost nothing;
- linear logistic cue fusion traded recall for precision and lost F1;
- a shallow nonlinear forest preserved recall but suffered a large precision
  deficit.

The next useful mechanisms should therefore add **new information or a
principled global/uncertainty model**, not merely another classifier over the
same five cues.

## Priority A — interval/type-2 fuzzy uncertainty around the five stable cues

### Mathematical idea

Replace each crisp membership `mu_i(x)` by an interval
`[mu_i^-(x), mu_i^+(x)]` whose width is driven by image-derived uncertainty
such as cross-scale disagreement, local orientation dispersion, or
descriptor instability. Aggregate lower/upper memberships with the **same
retained capacity** first; use interval midpoint/lower confidence for context
and interval width as an explicit uncertainty penalty in the gate.

This is not a free interval-valued parameter search. The first experiment
should use one fixed, normalized uncertainty construction and preserve
gamma=0.55, strength=2.0, floor=0.10 except for a preregistered analytical
mapping from interval width to gate attenuation.

### Why it attacks our failure mode

The Stage14n forest's recall stayed nearly fixed while precision collapsed.
That suggests the bottleneck is not “can we respond to edges?” but “when is a
strong response trustworthy?”. Interval width gives the model a third state:
**uncertain**, instead of forcing every cue into confident edge/non-edge
evidence.

### Literature anchors

- H. Bustince et al., *Interval-valued fuzzy sets constructed from matrices:
  Application to edge detection*, Fuzzy Sets and Systems 160(13), 2009.
  DOI: `10.1016/j.fss.2008.08.005`.
- P. Melin, O. Mendoza, O. Castillo, *An improved method for edge detection
  based on interval type-2 fuzzy logic*, Expert Systems with Applications
  37(12), 2010. DOI: `10.1016/j.eswa.2010.05.023`.
- T. Chaira, A. K. Ray, *Construction of fuzzy edge image using Interval Type II
  fuzzy set*, International Journal of Computational Intelligence Systems 7,
  2014. DOI: `10.1080/18756891.2013.862356`.

### Minimal falsification

Compare crisp incumbent versus interval-envelope incumbent under the existing
5x3 leakage-free UDED-development protocol **and** official BSDS-validation
ODS/OIS/AP. Require a meaningful precision/ODS gain without material UDED F1
regression. Do not tune interval widths from BSDS pixels.

---

## Priority B — MFI-driven Ambrosio–Tortorelli phase field

### Mathematical idea

The Mumford–Shah model represents an image together with a discontinuity set.
The Ambrosio–Tortorelli approximation replaces the discontinuity set by a
continuous phase field, making edge-set regularization computationally
tractable. Instead of adding endpoints after thresholding (Stage14i), use MFI
context as a spatial prior/coefficient in the phase-field energy so that
boundary continuity and false-edge length are optimized jointly.

A schematic development energy is:

`E(u,v) = data(u,I) + alpha * v^2 |grad u|^2
          + beta * (epsilon |grad v|^2 + (1-v)^2/(4 epsilon))
          + eta * Phi(v, MFI)`

where `v` is the soft edge/phase variable and `Phi` anchors the phase field to
the MFI boundary likelihood without forcing it to copy MFI.

### Why it attacks our failure mode

Stage14i showed that discrete geodesic linking is too blunt: it improved some
coverage but harmed F1. A variational model penalizes the **length and
complexity of the entire discontinuity set** while trading that against image
evidence, which can improve continuity without indiscriminately adding pixels.

### Literature anchors

- L. Ambrosio, V. M. Tortorelli, classical elliptic approximation of
  free-discontinuity/Mumford–Shah energies.
- M. Hintermüller, M. Stengl, T. M. Surowiec, *Uncertainty Quantification in
  Image Segmentation Using the Ambrosio–Tortorelli Approximation of the
  Mumford–Shah Energy*, Journal of Mathematical Imaging and Vision 63 (2021).
  This is especially relevant because it treats uncertainty in a phase-field
  segmentation setting.

### Minimal falsification

One fixed literature-derived `(epsilon, alpha, beta)` scale normalized to image
size; MFI enters only through a fixed coupling term. Compare to the unchanged
incumbent. No parameter grid until a single point shows nontrivial promise.

---

## Priority C — shearlet directional singularity localization

### Mathematical idea

Scharr is an excellent compact first-order localizer but uses a very limited
local basis. Continuous/discrete shearlets are multiscale, anisotropic,
directional systems with theoretical edge-location/orientation
characterizations. Use fine-scale shearlet modulus maxima/orientation as a
new localizer, while keeping the five-feature MFI branch as context.

### Why it attacks our failure mode

Stage14j says appending one phase statistic to the context bank is not enough;
Stage14k says simply making the gradient vector-valued/color is not enough.
Shearlets change the **geometric basis of localization itself** and may detect
elongated singularities with better texture rejection.

### Literature anchor

- K. Guo, D. Labate, W.-Q. Lim, *Edge analysis and identification using the
  continuous shearlet transform*, Applied and Computational Harmonic Analysis
  27(1), 2009. DOI: `10.1016/j.acha.2008.10.004`.

### Minimal falsification

Use a fixed small shearlet system and a deterministic modulus-maxima
localizer. First compare it directly with Scharr+NMS under the same context
gate; only consider a routed/local mixture if development errors are actually
complementary.

---

## Priority D — Dempster–Shafer evidence with explicit ignorance/conflict

### Mathematical idea

Map the localizer and stable memberships to masses on
`{edge, non-edge, ignorance}` rather than immediately compressing them to one
probability. Fuse masses with a fixed evidential rule; use conflict and
ignorance as uncertainty signals.

### Why it is distinct from Choquet

Choquet models non-additive importance/interactions among cue values. An
evidential model can represent **lack of commitment** and conflict explicitly.
That is attractive when the principal failure is precision under ambiguous
texture rather than missing raw response.

### Minimal falsification

Use only a few predeclared evidence sources: Scharr+NMS, positive Choquet
context, and cross-scale persistence. Avoid a large rule/weight search.
Compare conflict-aware attenuation against the incumbent gate.

---

## Priority E — fractional-order differential localizer

### Mathematical idea

Fractional derivatives interpolate between smoothing-like and
differentiation-like behavior and can alter the localization/noise trade-off.
Use one literature-motivated noninteger derivative order as a direct
replacement for the Scharr localizer, followed by the same orientation/NMS and
same fuzzy context gate.

### Literature anchor

- Fractional differentiation for image/edge processing, Signal Processing
  83(11), 2003. DOI: `10.1016/S0165-1684(03)00194-4`.

### Minimal falsification

One fixed order plus the integer-order Scharr control. Do not sweep order from
the result. A positive result can later justify a bounded development-only
order study.

---

## Secondary research directions

### Persistent topology across thresholds

Do **not** impose a fixed Betti-number target on arbitrary natural images.
Instead, treat connected edge components that persist across a threshold
filtration as more credible than short-lived texture components. This can be a
post-score saliency/reweighting mechanism rather than hard linking.

### Curvature/elastica and second-order free-discontinuity regularization

If Ambrosio–Tortorelli length regularization improves continuity but rounds
corners or loses high-curvature boundaries, test a curvature/elastica or
Blake–Zisserman-like second-order term. This is a follow-up only after the
simpler phase-field hypothesis has evidence.

### Fuzzy/interval coefficients in PDEs

“Fuzzy differential equations” should not be added merely because they are
mathematically exotic. A defensible route is to make the coefficient of a
well-established anisotropic-diffusion or phase-field PDE interval/fuzzy and
derive it from the interval width of boundary evidence. This turns epistemic
uncertainty into **how strongly the PDE is allowed to smooth**, rather than
inventing an unrelated fuzzy ODE.

### Reliability-conditioned capacities

Adaptive weights/capacities remain promising only in a tightly constrained
form. Prefer a one-parameter reliability-conditioned deformation of the
existing capacity, where reliability comes from image-derived uncertainty.
Do not fit a free local fuzzy measure at every pixel.

### Human-opinion uncertainty

Keep the official BSDS evaluator unchanged for SOTA comparison. Separately,
on development data, derive an agreement map

`p_GT(x) = (# annotators marking a boundary near x) / (# annotators)`

and study whether model confidence/interval width is calibrated to human
agreement. Annotator-specific reliability weighting may be scientifically
interesting, but it belongs in an **auxiliary analysis**, not in the official
ODS/OIS/AP computation.

## Research-order recommendation

The next literature escalation should prefer the following order unless new
primary literature gives a stronger reason:

1. interval/type-2 uncertainty around the retained five-feature fuzzy context;
2. Ambrosio–Tortorelli/Mumford–Shah phase-field regularization;
3. shearlet directional localizer;
4. Dempster–Shafer explicit ignorance/conflict;
5. fractional-order localizer;
6. persistent-threshold topology;
7. fuzzy/interval PDE coefficients and curvature refinements.

The agent must still select **one** next preregistered falsification, not launch
this list as a factorial sweep.

## Cross-dataset decision principle

From the official-evaluator patch onward, image-based development should be
judged on two complementary axes:

- existing leakage-free UDED development metrics for continuity with the
  historical program;
- official multi-annotator BSDS500-validation ODS/OIS/AP for benchmark-aligned
  transfer.

A candidate that gains only by exploiting one development set should be
treated cautiously. Prefer mechanisms whose effect is directionally
consistent or whose trade-off is mechanistically interpretable before
promotion.
