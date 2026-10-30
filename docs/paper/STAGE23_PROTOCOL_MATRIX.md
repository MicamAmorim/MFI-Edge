# Stage 23 dataset, detector, and protocol matrix

## Separation rule

This matrix separates local development comparisons from literature headline
test results. A test-only number may describe the frontier but cannot select a
Stage-23 descriptor, aggregator, parameter, architecture, threshold, or
experiment priority. Local tables may combine methods only when split,
annotation treatment, tolerance, thinning/NMS, and output semantics match.

## Dataset and evaluator roles

| Dataset / split | Stage-23 role | Annotation / target | Evaluator contract | Access / optimization status | Required caveat |
|---|---|---|---|---|---|
| UDED selection, overlap-clean 14 images | primary fast development screen | repository edge GT | leakage-free 5x3 outer CV and the experiment-specific tolerant matcher/threshold contract | allowed; item `03-35028` is excluded by filename lineage because it is protected BSDS-test image `35028`, without reading its image or GT bytes | small-domain estimates require per-image/fold stability; no UDED held-out feedback |
| UDED held-out | historical confirmation only | repository edge GT | historical repository protocol | already inspected; forbidden for optimization | documentary only |
| BSDS500 train, 200 | development/fitting or association only when preregistered | every human segmentation boundary | Berkeley matcher or a clearly labeled diagnostic | allowed under explicit preregistration | train metrics are not test metrics |
| BSDS500 validation, 100 | main literature-comparable Berkeley development track | every human boundary annotation | `nthresh=99`, `maxDist=0.0075` image diagonal, thinning on, native resolution, one-to-one `correspondPixels`, 8-bit maps without per-image normalization | allowed development feedback | local Windows matcher is stochastic and `reference_reproduction_verified=false`; cannot support a final SOTA claim |
| BSDS500 test, 200 | protected final/documentary | every human boundary annotation | same Berkeley standard when eventually authorized | forbidden for Stage-23 selection | no architecture or parameter choice from the outcome |
| BIPEDv2 train, 200 | potential later development track | one expert-cross-checked dense edge map per image | author edge-evaluation code/contract must be pinned before use | allowed only after preregistration and license/data audit | edge target is denser than BSDS object-boundary target |
| BIPEDv2 test, 50 | historical external/documentary | dense edge map | author protocol | already inspected; forbidden for optimization | not an untouched final benchmark |
| Multi-Cue, author 100-scene corpus | prospective literature-comparable track; exact development/final partition unresolved | separate object-boundary and all-edge annotations from multiple observers | published later work commonly uses three random 80/20 splits and Berkeley-style ODS/OIS/AP; exact split seeds and edge-vs-boundary track must be recovered before scoring | no Stage-23 access until a split manifest and role are preregistered | never mix edge and boundary targets or average incompatible random splits |
| NYUDv2 RGB/RGB-D, 795/654 conventional split | prospective cross-domain/final track | derived semantic/object boundaries; RGB and RGB-D are separate inputs | literature commonly uses Berkeley-style evaluation with `maxDist=0.011`; exact GT conversion, NMS, resize, and evaluator must be pinned | reserve the 654-image evaluation split from development unless a later preregistration explicitly assigns a non-final role before access | do not compare RGB-only to RGB-D without labeling inputs |

## Official Berkeley implementation facts

The Berkeley benchmark expects a soft, one-pixel-wide boundary map in `[0,1]`
and reports maximum F over the precision-recall curve. The repository's
development attachment uses the pinned Berkeley code and Piotr Dollár Windows
`correspondPixels` compatibility binary with 99 thresholds, `0.0075` diagonal
tolerance, and thinning. Piotr's documented `edgesEvalImg` defaults independently
confirm `thrs=99`, `maxDist=.0075`, and `thin=1`.

Stage 15A found that the shipped Windows matcher path uses clock-seeded random
sampling and lacks the reference seed needed to reproduce the fixture within
`1e-4`. Development metrics remain decision-capable under existing policy, but
`reference_reproduction_verified=false` must remain attached to every local
Berkeley table and no final SOTA claim may depend on it.

## Strong non-neural detector target map

| Detector | Evidence stack / aggregation | Training class | Official code and license status | Matched local status | Stage-23 use |
|---|---|---|---|---|---|
| compact MFI incumbent | median-conditioned Gabor/Hessian/persistence memberships; distorted-capacity Choquet; Scharr+NMS | development-fitted non-neural | repository code | complete on UDED/BSDS validation | anchor and final baseline |
| gPb-OWT-UCM | brightness, color, texton gradients; learned linear local cue fusion; spectral globalization; oriented watershed | classical-supervised | Berkeley source/benchmark; redistribution/license must be audited per artifact | no exact Stage-23 reproduction yet | architecture census and possible later target after fidelity audit |
| Structured Edge forest | LUV/color, gradient/orientation and self-similarity channels; structured random forest; NMS | classical-supervised on BSDS | official `pdollar/edges`; MSR-LA Full Rights license | exact pinned model previously reproduced; severe UDED transfer asymmetry | later supervised-classical reference/target, never an unsupervised hidden feature extractor |
| SED | opponent-color responses, surround modulation, continuation/feedback hierarchy | fixed-untrained | official author MATLAB at pinned commit; no explicit license, ignored/unredistributed | exact BSDS-validation maps available | strong untrained detector reference; gap diagnosis must respect license/portability |
| CO / SCO | double-opponent color/achromatic filters; max pooling; SCO adds spatial-sparseness weighting | parameter-fixed, author-tuned on BSDS300 train | complete official archives; research-purpose-only | exact paired BSDS-validation maps available | contextual-suppression reference and possible later target after prospective gap selection |
| Compass | adaptive CIELAB color signatures in opposed semicircles; EMD; max orientation | fixed-untrained | complete author archive; no explicit license | exact sigma-4 validation maps available; clock-seeded clustering recorded | distribution-evidence reference; first landscape uses a portable mechanism-level map, not the exact detector |
| PMI boundaries | image-internal color/variance feature-pair KDE/PMI affinity; multiscale spectral clustering | unsupervised-data-estimated; fixed parameters author-tuned on BSDS500 train | official BSD-style `phillipi/crisp-boundaries`, pinned commit `ee2d76e98340313a8f92e1b65064a9b4ea90ac77` | bounded PMI cue tested previously; complete author detector now registered for dataset-free runtime preflight only | active distinct strong-detector target after SED/half-disc closure; exact development reproduction remains conditional on preflight pass |
| EDPF | gradient anchors and contiguous chains; Helmholtz/NFA validation | fixed-untrained | official `CihanTopal/ED_Lib`, MIT | exact binary validation maps available | chain-first structural reference; binary single-operating-point AP limitation retained |
| SGBD | optimal 1-D scanline segmentation over multiple directions; response fusion | fixed/untrained in the published formulation | primary paper available; author-code availability/license unresolved | bounded row/column surrogate only | mechanism source in first landscape; exact detector requires separate fidelity checkpoint |
| QFrD | quaternion RGB fractional Dirac/QFT response, NMS and hysteresis | parameter-fixed, author-tuned | official repository pinned; no explicit license | exact author-code validation maps available | fractional reference only; Stage 14s/15i family remains closed to tuning |

No target detector is selected for modification in Stage 23A. Stage 23G target
choice occurs only after the cached UDED landscape and matched validation
frontier establish a prospective evidence/aggregation rule.

## Publication-table requirements

For each later method table, record:

- dataset version and exact manifest/split;
- development, confirmation, or protected role;
- input modality;
- annotation treatment;
- evaluator implementation and commit/hash;
- threshold count/grid, matching tolerance, thinning/NMS, resizing and output
  serialization;
- whether parameters were fixed, data-estimated, classically supervised, or
  neural-reference-only;
- author-reported test number in a separate column from local matched results;
- code/license/fidelity label;
- `reference_reproduction_verified` state where Berkeley matching is used.

## Primary protocol sources

- Berkeley Segmentation Dataset and Benchmark:
  `https://www2.eecs.berkeley.edu/Research/Projects/CS/vision/bsds/`.
- Arbeláez et al., DOI `10.1109/TPAMI.2010.161`.
- Piotr Dollár `edgesEvalImg` official source:
  `https://github.com/pdollar/edges/blob/master/edgesEvalImg.m`.
- Mély et al., Multi-Cue, DOI `10.1016/j.visres.2015.11.007`; official Serre
  Lab dataset release.
- Silberman et al., NYUDv2, ECCV 2012, DOI
  `10.1007/978-3-642-33715-4_54`.
- Soria et al., BIPED/DexiNed official dataset repository
  `https://github.com/xavysp/MBIPED` and DOI
  `10.1016/j.patcog.2023.109461` for BIPEDv2 documentation.
