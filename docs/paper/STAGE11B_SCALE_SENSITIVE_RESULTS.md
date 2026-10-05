# Stage 11b — Scale-sensitive edge-signature results

Date: 2026-10-05

## Why this rerun existed

Stage 11 exposed an implementation artifact in the historical `oriented` descriptor mode: several nominal 3/5/7 responses were exactly identical because lower/upper parameter floors collapsed multiple operators to the same effective scale. Stage 11b introduced `oriented_ms`, preserving the historical mode for reproducibility while giving each nominal scale a genuinely distinct parameter schedule.

## Scale audit

The audit on UDED image `01-0843x4` found:

- historical `oriented`: **22 exact duplicate descriptor/scale pairs out of 80**;
- `oriented_ms`: **0 exact duplicate pairs out of 80**.

The corrected fine-scale schedule is therefore genuinely scale-sensitive.

## Signature diagnostics

Selection and held-out results:

| score | selection AUC | selection AP | held-out AUC | held-out AP |
|---|---:|---:|---:|---:|
| analytical signature | 0.6293 | 0.4169 | 0.6606 | 0.4257 |
| logistic diagnostic | 0.6887 | 0.4879 | **0.6992** | **0.5029** |

Neither diagnostic collapses on held-out. The logistic model is not the proposed detector; it is an upper-bound diagnostic showing that the current feature space contains relational/signed information that the simple positive analytical combination does not fully exploit.

## Main discriminative pattern

### Edge vs texture

The strongest individual properties are dominated by genuinely fine/mid-scale oriented structure:

- `gabor4_s5`: AUC 0.7370;
- `gabor4_s3`: 0.7296;
- `gabor4_s7`: 0.7239;
- `gabor4_mean`: 0.7146;
- `hessian_s7`: 0.6903.

The corrected scale map is not flat: descriptor usefulness depends on scale. Gabor favors very fine scales, whereas Hessian/Laplacian/steered-Hessian show different preferred scales.

### Edge vs near-edge pixels

Exact-GT vs immediately adjacent pixels is much harder:

- `fine_vs_coarse_gradient`: AUC 0.6055;
- `normal_contrast_s3`: 0.6005;
- `normal_minus_tangent_s3`: 0.5994;
- `grad_s3`: 0.5983;
- `gradient_scale_persistence`: 0.5921.

This should not be interpreted as a semantic edge/non-edge problem. Under tolerant boundary evaluation, pixels close to a thin GT contour may represent localization uncertainty rather than true negatives. Therefore the near-edge ring should be treated as an **ambiguous/localization population**, not allowed to dominate context-signature learning.

## Candidate-signature redundancy

The selected analytical signature remains correlated. It contains multiple Gabor scales plus gradient/normal-contrast family responses. This confirms that the Stage-12 model should not simply sum more filter responses. The scientific target should be a compact set of *properties* and *relations*.

## Important logistic sign pattern

The standardized logistic diagnostic assigns both positive and negative coefficients. Examples among the largest coefficients:

Positive:

- `gabor4_s3`;
- `fine_vs_coarse_gradient`;
- `normal_contrast_s3`;
- `grad_s3`;
- `laplacian_s3` / `hessian_s3`.

Negative conditional contributions include:

- `laplacian_s13`;
- `steered_hessian_s5`;
- `normal_minus_tangent_s7`;
- `coherence_iso_s3`;
- `laplacian_s7`;
- several scale-variance/mean terms.

This is a key clue: the useful signature is not purely monotone in every raw descriptor. A true boundary may be characterized by **contrasts between scale responses** and by the simultaneous presence of positive evidence and absence of texture-like evidence.

## Architectural consequence

Stage 12 should split the problem into at least two interpretable roles:

1. **Context / texture-rejection signature** — decides whether a high-gradient structure looks boundary-like rather than texture/background.
2. **Localization / centerline signature** — helps a precise localizer decide where within a boundary neighborhood the final thin contour should lie.

The near-edge population belongs primarily to role 2, not to the negative class of role 1.

A preferred analytical form is therefore a dual/bipolar fuzzy architecture rather than a single all-positive sum:

```text
image
 -> scale-sensitive structural descriptors
 -> positive boundary memberships ---------> non-additive positive evidence
 -> texture/anti-boundary memberships -----> non-additive negative evidence
 -> context gate

image -> fixed precise localizer (Scharr first)
     -> context gate + optional localization signature
     -> NMS / frozen threshold
     -> edge map
```

Possible mathematical realizations to compare:

- two monotone Choquet channels, `C_plus - lambda*C_minus`;
- a bipolar Choquet / bi-capacity formulation;
- signed contrastive scale descriptors transformed into ordinary monotone memberships before Choquet aggregation.

The fixed-Scharr variant should be tested before reintroducing the dynamic localizer, because CH-MFI-v2 already showed that extra adaptivity can degrade localization.

## Next experimental decision

Do **not** launch the wide sweep.

Next:

1. revise Stage-11 reporting so texture/background/context discrimination is separated from the ambiguous near-edge localization task;
2. add generic cross-scale relational descriptors (fine-minus-coarse, scale centroid/peak, scale entropy/persistence) rather than hand-picking one logistic coefficient pattern;
3. implement a Stage-12 pilot with fixed Scharr + analytical signature gate;
4. compare all-positive aggregation against dual/bipolar fuzzy evidence;
5. only after the fixed-localizer pilot improves or matches Scharr should dynamic localization/topology be reintroduced;
6. replicate stable signature properties on BSDS/BIPED before claiming a general edge signature.

## Claim discipline

Current evidence supports:

- the historical fine-scale implementation had real scale collapse;
- `oriented_ms` fixes exact duplication;
- useful boundary-vs-texture information exists in the corrected descriptor space;
- a simple linear diagnostic extracts more of that information than the current all-positive analytical signature;
- exact-GT vs near-edge discrimination is weak and should be interpreted primarily as localization/annotation ambiguity.

It does **not** yet support claiming a universal edge signature or a detector better than Scharr.
