# Stage 12c — leakage-free evidence-bank CV

## Why this rerun was necessary

Stage 12b selected positive/texture evidence banks once on all 15 UDED selection images and then cross-validated only the threshold.  That did not contaminate the held-out split, but it made the reported inner-CV optimistic because feature-bank selection was not inside each fold.

Stage 12c rebuilt the positive and negative banks **inside every outer-fold training set**, fit the threshold on that same training set, and evaluated only the untouched validation fold.

The repeatedly inspected UDED held-out half is now treated as **development confirmation only**, not as a publication test.

## Leakage-free selection result

Scharr repeated/outer-fold baseline on the 15 selection images:

- CV F1: **0.73351**
- precision: 0.65181
- recall: 0.83863

Formal selection winner:

`fuzzypos__g0.55__a2__floor0.1`

- CV F1: **0.76376**
- delta vs Scharr: **+0.03024**
- precision: 0.66219
- recall: 0.90212

The best dual model was almost tied in leakage-free CV:

`dual__g0.55__product__l0.35__a2__floor0.1`

- CV F1: **0.76347**
- delta vs Scharr: **+0.02996**

Thus the large selection gain from Stage 12b was not caused solely by the evidence-bank leakage.

## Development-confirmation result

The formal positive-only winner did **not** improve the repeatedly inspected UDED held-out set:

- Scharr held-out F1: **0.76204**
- positive winner held-out F1: **0.76133**
- delta: **-0.00071**
- bootstrap 95% CI: **[-0.00391, 0.00286]**

However, multiple dual models that were already among the top selection-ranked candidates improved held-out F1:

| selection rank | candidate | held-out F1 | delta vs Scharr | 95% CI |
|---:|---|---:|---:|---|
| 2 | dual product, lambda=.35 | 0.76444 | +0.00240 | [-0.00131, 0.00578] |
| 3 | dual product, lambda=.70 | 0.76798 | +0.00594 | [0.00106, 0.01152] |
| 5 | dual product, lambda=.70, weaker gate | 0.76682 | +0.00477 | [0.00086, 0.00914] |
| 6 | dual ratio, lambda=.70 | 0.76907 | +0.00702 | [0.00203, 0.01315] |
| 7 | dual ratio, lambda=1.0 | **0.77023** | **+0.00819** | **[0.00249, 0.01473]** |

These held-out numbers must **not** be used to choose the exact next configuration, because the split has been inspected repeatedly.  They are useful only as architectural evidence that the separated anti-texture bank is not arbitrary.

## Family-level pattern

The leakage-free selection ranking contains a broad dual plateau rather than one isolated lucky candidate:

- the positive family has the single highest CV-F1;
- the dual family occupies most of the global top-20;
- `gamma=0.55` dominates the top region;
- the best dual candidate differs from the positive winner by only about 0.00028 CV-F1.

This supports continuing with **bipolar / positive-vs-negative evidence as a model family**, without choosing a hyperparameter based on UDED held-out performance.

## Evidence-bank stability

Very stable positive features across all 3 outer folds:

- `gabor4_s5`
- `hessian_s7`
- `gabor4_max`
- `hessian_s13`
- `gabor4_s13`
- `gabor4_fine_coarse_balance`
- `gabor4_scale_persistence`
- `gabor4_scale_entropy`

Very stable anti-texture features across all 3 folds:

- `steered_hessian_scale_centroid`
- `descriptor_normal_dominance`
- `steered_hessian_peak_fineness`

The negative bank therefore has a reproducible interpretation: **texture is being recognized primarily by scale-distribution / scale-location properties of curvature-like responses**, not simply by large gradient magnitude.

## Visual interpretation

The dual preview shows that the anti-texture map is not a complement of the positive map. It responds strongly to structured/background texture while retaining a different spatial pattern around true object boundaries. The combined context remains visually close to the positive evidence around strong boundaries but suppresses/reweights many texture-heavy regions.

## Scientific decision

Stage 12c justifies a formalized bipolar experiment, but it also exposes a validation problem: 3-fold CV on only 15 selection images has high fold-to-fold variance.  The next stage therefore must:

1. stop using UDED held-out during architecture development;
2. use repeated leakage-free CV on the 15 selection images;
3. test a mathematically explicit **separable bi-capacity**
   `v(A,B)=mu_plus(A)-lambda*mu_minus(B)`;
4. allow independent capacity shapes for positive and negative evidence;
5. freeze candidates from UDED selection only;
6. carry those frozen candidates to an external BSDS/BIPED validation stage.

This is Stage 12d.
