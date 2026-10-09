# Stage 16b preregistration — fixed SED/MFI expert mean

Status: preregistered before candidate-result inspection.
Registered: 2026-10-08.
Predecessor: `stage16a_generation2_mechanism_checkpoint`.
Experiment ID: `stage16b_fixed_sed_mfi_fusion`.

## Question and rationale

Does one fixed, interpretable combination of the two strongest mechanistically
complementary non-neural paths improve both development datasets without an
image router or learned fusion weight?

The compact MFI controller supplies multiscale Gabor/Hessian persistence and a
precise grayscale Scharr+NMS localizer. Exact author-code SED supplies
colour-opponent V1 responses, contrast-dependent surround modulation, larger
orthogonal V2 pooling, and feedback. Stage 15 established three relevant facts:

1. SED is the strongest exact non-trained reference under the common local
   BSDS500-validation path (`0.678546/0.709152/0.712814` ODS/OIS/AP).
2. At the fixed Stage-15m proximity contract, MFI and SED each retain substantial
   GT-supported response absent from the other (`35.6%` and `32.0%`).
3. SED's advantage rises with incumbent fragmentation and edge density, while
   SED has fewer unsupported pixels and larger supported components.

Akbarinia and Párraga's primary paper attributes SED's gains to contour
strengthening/continuation and texture suppression. Kittler et al.'s primary
combination analysis finds the sum rule comparatively robust to estimation
errors. Stage 16b borrows only that fixed-sum rationale; it does **not** claim
that either edge map is a calibrated posterior probability.

## Frozen mechanism

For each image, serialize both constituent soft maps to the repository's fixed
8-bit `[0,255]` convention, map them back to `[0,1]`, and compute

`score16b = 0.5 * compact_MFI + 0.5 * exact_author_SED`.

The weight `0.5` is fixed now and is not searched. Each constituent retains its
own conditioning, context, localization, and NMS path. No threshold, method
label, dataset identity, ground truth, oracle winner, fragmentation statistic,
or learned router enters inference. This is a detector-level expert mean, not
Stage 15p texture integration and not a revival of Stage-14 linking.

The exact SED dependency is commit
`11514b80162e5cd93fd244515189649656105a14`. Its source remains an ignored,
hash-verified local dependency because no explicit source license was found;
the repository does not redistribute it.

## Development datasets and fitting

### UDED selection

- Use only the 15 predesignated selection images, downscaled exactly as the
  incumbent to maximum side 256.
- Run exact SED once on losslessly serialized resized RGB inputs. SED reads no
  ground truth and has no fitted parameter.
- Reuse the deterministic 5-repeat x 3-fold outer split construction.
- In every outer fold, fit compact MFI memberships and each variant's scalar
  threshold on that outer training fold only.
- Evaluate compact MFI, exact SED, and their fixed equal mean on the identical
  validation images with the existing tolerant UDED metric.
- UDED held-out is forbidden.

### BSDS500 validation

- Treat validation as development data under the official-evaluation policy.
- Reuse the frozen exact Stage-15b SED maps when complete; do not tune or alter
  SED. Reconstruct the unchanged incumbent through its registered exporter.
- Export the fixed mean at native resolution as 8-bit PNG without candidate-
  specific normalization.
- Score the incumbent, exact SED constituent, and candidate with all
  annotations, 99 thresholds, `maxDist=0.0075`, thinning, and the unmodified
  Windows matcher.
- The Stage-15a matcher remains stochastic and reference-uncertified. The
  fixed-seed diagnostic matcher is forbidden for dataset scoring.
- BSDS500 test is forbidden.

## Conjunctive promotion rule

The candidate is promoted only if **all** conditions pass.

### UDED conditions

Against **each** constituent separately:

1. aggregate F1 delta is at least `+0.002`;
2. mean paired outer-fold F1 delta is nonnegative;
3. candidate wins at least `9/15` outer folds.

In addition, candidate aggregate precision must be no more than `0.002` below
the higher aggregate precision of the two constituents.

### BSDS500-validation conditions

The official attachment must complete. Relative to the better constituent for
each metric:

1. ODS delta is at least `+0.002`;
2. OIS delta is nonnegative;
3. AP delta is nonnegative.

No condition may be weakened after seeing results. Passing only one dataset,
or merely beating the old MFI incumbent while remaining below exact SED, is a
failure. A failed candidate is not micro-tuned; weights, normalizations,
nonlinear means, routers, and constituent parameters remain closed unless a
future live-literature checkpoint independently justifies a different family.

## Outputs and qualitative contract

The runner must write:

- `summary.json`;
- `variant_ranking.csv`;
- `fold_results.csv`;
- `per_image_metrics.csv`;
- exact UDED SED map hashes and runtimes;
- `official_eval_manifest.json`;
- `best_method_preview.png`.

The preview uses fixed UDED-selection positions 1, 8, and 15. Columns are
input, GT, compact-MFI out-of-fold prediction, exact-SED out-of-fold
prediction, and equal-mean out-of-fold prediction. It is documentary only and
cannot change the decision.

## Sources

- Akbarinia & Párraga (2018), *Feedback and Surround Modulated Boundary
  Detection*, IJCV 126:1367–1380, DOI `10.1007/s11263-017-1035-5`; official
  code `https://github.com/ArashAkbarinia/BoundaryDetection` at the commit above.
- Kittler, Hatef, Duin & Matas (1998), *On Combining Classifiers*, IEEE TPAMI
  20(3):226–239, DOI `10.1109/34.667881`.

## Interpretation boundary

Stage 16b is a bounded generation-2 falsification, not a final SOTA test. A pass
would provisionally change the development incumbent and require later
ablation, efficiency, licensing/dependency planning, robustness, and untouched
external evaluation. It cannot establish the long-horizon multi-benchmark
goal by itself.
