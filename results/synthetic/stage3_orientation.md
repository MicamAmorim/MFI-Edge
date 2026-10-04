# Stage 3 — orientation robustness and directional descriptors

Date: 2026-10-04

## Data correction

The original synthetic diagonal case had a ground-truth line with a different slope from the actual step boundary in the generated image. This was the main reason for the previously very low diagonal F1. The diagonal GT has been corrected to be the exact boundary of the same region used to generate the image.

Therefore, the original Stage-1/Stage-2 numerical rankings should be treated as superseded until fully re-run on the corrected dataset.

## Descriptor analysis

The legacy implementation already composes the horizontal and vertical first derivatives via:

grad = sqrt(gx^2 + gy^2)

and also uses hxy in the Hessian eigenvalue magnitude and sxy in structure-tensor coherence.

However, two sources of angular bias remained:
- square local-statistics windows;
- no explicit comparison of intensity change across the edge normal versus along the edge tangent.

New feature modes:
- legacy: original 8 descriptors;
- rotinv: isotropic Gaussian tensor/statistics and disk-shaped local range;
- oriented: explicit normal contrast, normal-minus-tangent contrast, and steered Hessian n^T H n;
- combined: rotinv + explicit directional cues.

## Corrected five-image test — MFI-Edge-SCHARR

Using the corrected diagonal GT:

| Feature mode | ROI q | ODS | OIS | AP | R50 | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| legacy | 0.70 | 0.98731 | 0.98440 | 0.99410 | 1.000 | 0.81606 |
| oriented | 0.80 | 0.98731 | 0.98440 | 0.99425 | 1.000 | 0.82124 |

Per-image F1 for legacy at the global ODS threshold:
- vertical: 1.0000
- diagonal: 0.9968
- circle: 0.9967
- box: 0.9891
- two_scale: 0.9394

This confirms that the previous diagonal failure was primarily a GT mismatch, not a fundamental inability to detect diagonal edges.

## 0–175 degree easy orientation sweep

Angles were sampled every 5 degrees using the same noise realization for every angle to isolate orientation sensitivity.

All MFI-SCHARR feature modes reached the same ODS = 0.98526 and mean F1 = 0.98688 because the task is saturated. The MFI ROI covered 100% of the true boundary for the selected operating points.

## Hard orientation stress test

A more discriminative test used:
- angle: 0 to 175 degrees in 5-degree increments;
- contrast: 0.35 vs 0.65;
- Gaussian blur sigma = 1.2;
- Gaussian noise variance = 0.01;
- 96x96 images;
- same noise realization across angles;
- MFI backbone CF1F2(CL,CL), q=0.1;
- scales 25,13,7,5,3.

| Method | ODS | OIS | AP | R50 | ROC-AUC |
|---|---:|---:|---:|---:|---:|
| MFI-Edge-SCHARR oriented | **0.56335** | **0.56434** | **0.49920** | **0.54601** | 0.62525 |
| MFI-Edge-SCHARR rotinv | 0.54128 | 0.54359 | 0.46701 | 0.52946 | 0.62091 |
| MFI-Edge-SCHARR combined | 0.52396 | 0.52404 | 0.43865 | 0.51957 | 0.61727 |
| MFI-Edge-SCHARR legacy | 0.49605 | 0.49541 | 0.38559 | 0.00000 | 0.60052 |
| SCHARR | 0.44009 | 0.43912 | 0.30743 | 0.00000 | 0.55150 |
| MFI oriented only | 0.24749 | 0.26954 | 0.14708 | 0.00000 | **0.79780** |
| CANNY persistence | 0.10714 | 0.11168 | 0.05660 | 0.00000 | 0.57279 |

Orientation stability at the selected global ODS threshold:

| Feature mode | mean F1 | min F1 | std F1 | mean GT coverage by ROI | min GT coverage |
|---|---:|---:|---:|---:|---:|
| oriented | **0.56311** | **0.42631** | **0.06024** | **0.99466** | **0.80769** |
| rotinv | 0.54182 | 0.27790 | 0.07559 | 0.97814 | 0.58667 |
| combined | 0.52279 | 0.27790 | 0.09243 | 0.95261 | 0.59333 |
| legacy | 0.49541 | 0.30747 | 0.07816 | 0.94014 | 0.70492 |

## Interpretation

The user's hypothesis was partly correct. The first-order gradient was already composed from horizontal and vertical derivatives, but explicit normal/tangential descriptors and isotropic neighborhoods materially improve robustness when contrast is weak, blur is present, and noise is stronger.

The strongest current variant is therefore the orientation-aware proposal stage:

MFI-Edge-SCHARR (oriented)

where MFI proposes a spatial ROI and Scharr performs final localization.

The high ROC-AUC of MFI-only oriented (0.7978) together with its low ODS (0.2475) reinforces the architectural interpretation: MFI is strong as a ranking/attention signal, but not yet as the final one-pixel boundary localizer.
