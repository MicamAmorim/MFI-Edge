# Stage 11 — Edge Signature Discovery

## Scientific purpose

Stage 11 is a **diagnostic science step**, not a final supervised detector.

The central hypothesis is that the current CH-MFI descriptor stack contains many correlated filter responses but does not yet explicitly represent the more invariant structural properties that distinguish a true boundary from a high-gradient non-boundary.

We therefore use ground truth to answer:

> Which image-derived properties are systematically present at true boundaries and absent, or weaker, in near-edge and textured hard negatives?

The intended long-term use is to translate stable properties into explicit analytical/fuzzy memberships in Stage 12. GT must not be an inference-time input.

---

## Four sampled populations

For every prepared image:

1. **edge** — exact GT edge pixels;
2. **near_edge** — non-GT pixels within a small morphological neighborhood of GT;
3. **texture** — high-gradient pixels far from GT;
4. **background** — low-gradient pixels far from GT.

The most important contrast is **edge vs texture**, because visual inspection of CH-MFI attention maps showed substantial activation on textured regions. Edge vs near-edge is also important because it tests localization/selectivity rather than only edge-vs-flat-background discrimination.

---

## Feature space

Stage 11 preserves the current orientation-aware descriptor stack at each scale `{25,13,7,5,3}` and adds aggregated and structural properties.

Existing scale-resolved descriptors:

- gradient;
- Laplacian;
- Hessian;
- isotropic coherence;
- normal contrast;
- normal-minus-tangent contrast;
- steered Hessian;
- 4-orientation Gabor maximum.

For each descriptor the analysis also includes across-scale mean, max and standard deviation.

New structural descriptors include:

- **orientation consistency across scales** — doubled-angle circular agreement weighted by gradient magnitude;
- **normal/tangent contrast ratio** — whether contrast is concentrated across the local edge normal rather than along the tangent;
- **step consistency** — agreement of opposite-side contrast at two radii;
- **step-likeness** — contrast strength × normal dominance × radial consistency;
- **gradient scale persistence** — mean/max multiscale response ratio;
- **fine-vs-coarse gradient balance**;
- **descriptor normal dominance** derived from normal and normal-minus-tangent responses;
- **structural edge consensus** — exploratory geometric mean of orientation consistency, normal/tangent dominance and multiscale persistence.

These are intentionally interpretable properties rather than additional opaque filters.

---

## Statistical tests

On the **selection split only**, for every candidate property and each negative population we compute:

- rank AUC;
- oriented AP;
- discretized mutual information;
- Cohen effect size;
- population means/medians/quantiles;
- correlation/redundancy among candidate properties.

The candidate analytical signature is selected by a robustness score that emphasizes edge-vs-texture while also requiring useful edge-vs-near separation. Highly redundant properties are suppressed by a correlation threshold.

No held-out statistic is used to choose the signature.

---

## Candidate analytical signature

For each retained property `z_j`, Stage 11 exports a monotone sigmoid membership

\[
\mu_j(x)=\sigma\left(d_j\frac{z_j(x)-c_j}{s_j}\right),
\]

where:

- `d_j` is the selected direction;
- `c_j` is the selection-derived midpoint between edge and hard-negative medians;
- `s_j` is a robust selection-derived scale;
- the final exploratory analytical score is a normalized weighted sum of these memberships.

This is **not yet the final fuzzy model**. It is a compact, interpretable probe of whether the discovered signature generalizes at all.

Stage 12 may replace this sum with Choquet/conditional/partitioned aggregation, but only after Stage 11 identifies which properties deserve to be aggregated.

---

## Learned diagnostic upper bound

A linear/logistic diagnostic may later be fitted on exactly the same feature space and selection split.

Its role is diagnostic:

- if the learned diagnostic generalizes but the analytical signature does not, the descriptors contain useful information and the bottleneck is aggregation/calibration;
- if neither generalizes, the descriptor/signature space is inadequate;
- if both generalize, prefer the simpler analytical/fuzzy representation unless the learned model provides a scientifically justified advantage.

The learned diagnostic must never be silently presented as the proposed analytical MFI detector.

---

## Generalization requirement

UDED is only the development dataset for Stage 11.

Before claiming a general edge signature, repeat the analysis on at least BSDS500 and BIPED and compare direction/effect stability. A property should influence the final generalist detector only if it is stable across datasets or if a principled context rule explains the difference.

With BSDS500, preserve individual annotators where possible. This will allow a later extension from binary GT to boundary-consensus/uncertainty signatures.

---

## Decision tree after the Stage-11 run

### A. Analytical signature generalizes strongly

Proceed to **Stage 12 — Signature-informed MFI**:

```text
image
 -> structural properties
 -> fuzzy memberships
 -> non-additive/contextual aggregation
 -> localizer control
 -> edge map
```

### B. Learned diagnostic is strong, analytical signature weak

Do not add more raw filters immediately. Redesign the fuzzy/analytical aggregation so it can represent the useful interactions exposed by the diagnostic.

### C. Both are weak

Revise the descriptor space. Possible next additions include stronger multiscale persistence, explicit profile symmetry/asymmetry, phase/frequency evidence, junction/line-vs-step discrimination, and improved texture-rejection cues.

---

## Implementation

Primary files:

- `src/edge_signature.py`
- `analyze_gt_edge_signatures.py`
- `run_stage11_signature.bat`

Default output directory:

`results/local_dev/edge_signature/`

The output is ignored by Git by default until a compact result is explicitly curated and committed.
