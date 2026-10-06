# Stage 12d — repeated leakage-free bipolar CV

## Protocol

Stage 12d stopped using the repeatedly inspected UDED held-out half.  Model-family ranking used only the 15 UDED selection images with **5 repeated 3-fold outer CV splits** (15 validation folds total).  For every split, the positive and anti-texture evidence banks and the decision threshold were rebuilt using only the training images.

The tested families were:

- positive distorted-capacity Choquet control;
- separable bi-capacity with independent positive/negative distortion exponents;
- the Stage-12 ratio combiner as an empirical control.

The fixed localizer remained median-conditioned Scharr + NMS.

## Main result

Repeated-CV Scharr baseline:

- precision: **0.65587**
- recall: **0.87829**
- F1: **0.75095**

Overall winner:

`positive__gp0.55__a2__floor0.1`

- precision: **0.66983**
- recall: **0.87528**
- F1: **0.75889**
- delta vs Scharr: **+0.00794**
- mean fold F1: **0.75910**
- fold SD: **0.03612**
- minimum fold F1: **0.70214**

Best separable bi-capacity:

`bicap__gp0.55__gm1.75__l0.35__a2__floor0.1`

- precision: **0.66989**
- recall: **0.87308**
- F1: **0.75811**
- delta vs Scharr: **+0.00715**
- mean fold F1: **0.75841**
- fold SD: **0.03683**
- minimum fold F1: **0.70057**

Best ratio control:

`ratioctl__gp0.55__gm1__l1__a2__floor0.1`

- F1: **0.75669**
- delta vs Scharr: **+0.00573**

## Family-level interpretation

The Stage-12c held-out observation had made the dual/bipolar branch look clearly superior.  Repeated leakage-free development CV changes that interpretation.

The positive-only family now wins narrowly.  The separable bi-capacity remains highly competitive: 12 of the global top 20 configurations are bi-capacity variants, versus 8 positive controls, and their top-10 mean CV F1 is essentially tied.  However, the best bi-capacity is about 0.00079 F1 below the positive winner.

A paired inspection across the 15 repeated folds shows that the best bi-capacity beats the positive winner in only 5/15 folds; the average per-fold difference is approximately -0.00069 F1.  Therefore the current data do **not** support a claim that explicit negative evidence improves UDED development performance.  The scientifically defensible conclusion is instead:

> positive multiscale boundary evidence is robustly useful; anti-texture evidence is stable and plausible, but its incremental value over the positive controller remains unresolved.

This makes external transfer more important than further UDED tuning.

## Evidence-bank stability

Very stable positive evidence:

- `gabor4_s5`: 15/15 splits
- `hessian_s7`: 15/15
- `gabor4_s13`: 15/15
- `hessian_s13`: 15/15
- `gabor4_scale_persistence`: 15/15
- `gabor4_max`: 14/15
- `gabor4_fine_coarse_balance`: 14/15
- `gabor4_scale_entropy`: 13/15

Stable anti-texture evidence:

- `steered_hessian_scale_centroid`: 15/15
- `descriptor_normal_dominance`: 14/15
- `steered_hessian_peak_fineness`: 12/15
- `hessian_peak_fineness`: 11/15
- `laplacian_peak_fineness`: 10/15

The positive bank therefore looks substantially more stable than the lower-ranked tail of the negative bank.  This is consistent with the positive-only model narrowly winning repeated CV.

## Scientific decision

Four representatives were frozen before any external BSDS/BIPED result:

1. overall/positive control: `positive__gp0.55__a2__floor0.1`;
2. best separable bi-capacity: `bicap__gp0.55__gm1.75__l0.35__a2__floor0.1`;
3. best ratio control: `ratioctl__gp0.55__gm1__l1__a2__floor0.1`;
4. the explicit positive-control entry, identical to the overall winner.

The corresponding memberships, weights, midpoints, scales and thresholds are stored in `results/local_dev/stage12d_bipolar_cv/frozen_candidates.json` on the workstation output tree.

## Next step

Do not inspect or optimize on the UDED held-out half again.

Stage 13a applies the frozen representatives unchanged to BSDS500.  The first runner uses consensus-thresholded BSDS ground truth and the project's tolerant-dilation metric only as an external-transfer diagnostic.  A later stage must implement the official Berkeley multi-annotator bipartite matching protocol before publication-level comparisons are made.

## Stage 13a external transfer record (BSDS500 test)

The frozen candidates were evaluated on all 200 BSDS500 test images at max-side
256 using the UDED-selection thresholds. Mean inference time was 2.373 s/image
(474.6 s total). Under the project's consensus-thresholded GT and tolerant-
dilation matcher, fixed F1 was 0.19104 for Scharr+NMS, 0.19309 for the positive
control, 0.19352 for the separable bi-capacity, and 0.19437 for the ratio
control. Paired bootstrap intervals for the three frozen candidates' F1 deltas
versus Scharr were respectively [0.00160, 0.00253], [0.00196, 0.00300], and
[0.00268, 0.00407]. This is descriptive evidence that all three fixed
representatives slightly exceed the baseline under this transfer diagnostic;
the ratio control has the largest observed delta. It does not establish
publication-grade generalization or identify a preferred family: BSDS test is
one-shot and these comparisons use a nonofficial matcher. No candidate or
threshold is changed based on the result. An independent frozen replication
(for example BIPED) and official Berkeley evaluation remain outstanding.
