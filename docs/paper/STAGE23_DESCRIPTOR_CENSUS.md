# Stage 23 descriptor / evidence census and first-landscape shortlist

## Scope and decision rule

This Stage-23A census groups evidence by the information it represents, not by
the name of a detector. It was fixed before any Stage-23 descriptor map was
extracted or scored. Literature test numbers are provenance only and did not
select the pool. The first landscape is intentionally broad enough to expose
different evidence structures but small enough for complete cache provenance
and pairwise complementarity analysis.

The final inference constraint remains non-neural. Supervised classical
detectors appear below as later reproduction targets, not as hidden feature
extractors for the first descriptor landscape.

## Evidence-family census

| Evidence family | Primary examples | Signal represented | Typical aggregation / downstream use | Training class | Stage-23 role |
|---|---|---|---|---|---|
| Local first-order gradient | Canny (1986); Scharr/local derivative implementations | abrupt local intensity change and orientation | NMS, hysteresis, additive score | fixed-untrained | required localization/control evidence |
| Vector/color discontinuity | Di Zenzo (1986); Yang et al. CO/SCO (2013/2015) | chromatic plus achromatic change without premature grayscale collapse | max over orientations/channels; spatial-sparseness modulation | fixed or author-tuned | portable CIELAB tensor-gradient evidence in the first pool; exact CO/SCO retained as detector references |
| Oriented frequency/texture | Daugman (1985); Martin et al. (2004); gPb | energy in orientation/spatial-frequency channels | learned linear cue fusion, multiscale averaging | fixed filters or classically supervised fusion | two incumbent Gabor scales retained to expose within-family redundancy |
| Curvature / second order | scale-space Hessian/ridge analysis (Lindeberg, 1998) | ridge, valley, and local curvature response | scale selection or cue fusion | fixed-untrained | two incumbent Hessian scales retained as a separate differential family |
| Cross-scale persistence | Lindeberg (1998); incumbent MFI lineage | repeatability of oriented evidence across scale | context gating / scale selection | fixed-untrained | retained incumbent persistence map |
| Local orientation organization | structure tensor / Weickert (1999) | dominance of one gradient orientation over an integration neighborhood | coherence cue, anisotropic processing | fixed-untrained | challenger; strong Stage-19 univariate association but no prior promotion |
| Phase alignment / local energy | Morrone & Owens (1987); Kovesi (1999/2003) | contrast-normalized alignment of Fourier phases across scale/orientation | max moment, thresholding, cue fusion | fixed-untrained | challenger; use the already fixed Kovesi-style maximum moment |
| Opposed-region distribution contrast | Ruzon & Tomasi Compass (1999/2001); Martin et al. (2004) | brightness/color/texture distribution change across an oriented support | max over orientations; EMD or histogram distance | fixed or classically supervised fusion | portable half-disc distribution contrast; exact Compass stays a reference detector |
| Image-internal statistical dependence | Isola et al. (2014) PMI boundaries | low association of feature pairs across an object boundary | affinity graph, spectral clustering | unsupervised-data-estimated | bounded PMI dependency-deficit map, before spectral globalization |
| Semi-global change point | Jevnisek & Avidan (2016) | piecewise-stable row/column regions and their transition locations | max / probability fusion over scan directions | fixed-untrained | fixed row/column change-point map |
| Region-adaptive contrast | Felzenszwalb & Huttenlocher (2004) | external contrast relative to accepted within-region variation | graph segmentation then component boundary rasterization | fixed-untrained | fixed FH between-component boundary support |
| Chain / contour significance | Akinlar & Topal EDPF (2012) | contiguous gradient chains validated by Helmholtz false-alarm control | chain validation and binary output | fixed-untrained | later detector target; omitted from the first map pool because it is a complete binary detector and less portable than the analytic cues |
| Learned structured patch evidence | Dollár & Zitnick Structured Forests (2013/2015) | structured local edge masks from color, gradient, and self-similarity channels | forest averaging plus NMS | classical-supervised | later strong-detector target only; no forest output enters the unsupervised descriptor pool |
| Bio-inspired contextual suppression | Akbarinia & Párraga SED (2018); Yang et al. SCO (2015) | color opponency, surround modulation, continuation, and texture suppression | fixed hierarchy / multiplicative modulation | fixed-untrained or author-tuned | later exact-reference and gap-guided target; not decomposed into undocumented surrogate channels |

## Frozen first-landscape descriptor maps

Stage 23C may extract exactly the following 13 raw evidence maps on the
overlap-clean UDED selection manifest. Each map receives a content-addressed
identity containing all parameters, preprocessing, source-image hash, function
identity, and code version. Stage 23C may repair implementation contracts
before scoring, but it may not substitute a different scientific descriptor
under the same id.

| ID | Canonical descriptor id | Family | Fixed definition / source of parameters | Status before Stage 23 |
|---|---|---|---|---|
| D01 | `scharr_pre_nms_magnitude` | local gradient | median-conditioned grayscale Scharr magnitude before NMS; repository incumbent convention | localizer/control |
| D02 | `lab_dizenzo_tensor_gradient` | vector/color discontinuity | fixed CIELAB Di Zenzo maximum tensor eigen-response used by Stage 14k, before NMS | previously failed as a localizer; untested as evidence in this landscape |
| D03 | `gabor4_s5` | oriented frequency | retained four-orientation scale-5 response | incumbent anchor |
| D04 | `hessian_s7` | curvature | retained scale-7 Hessian response | incumbent anchor |
| D05 | `gabor4_s13` | oriented frequency | retained four-orientation scale-13 response | incumbent anchor |
| D06 | `hessian_s13` | curvature | retained scale-13 Hessian response | incumbent anchor |
| D07 | `gabor4_scale_persistence` | cross-scale persistence | retained incumbent persistence response | incumbent anchor |
| D08 | `structure_tensor_coherence` | orientation organization | scalar structure-tensor eigenvalue-difference evidence at fixed noise/integration scales `0.5/4.0` | Stage 16z near miss; Stage 19 strongest univariate cue |
| D09 | `phase_congruency_max_moment` | phase alignment | fixed-default Kovesi PC2 maximum covariance moment used by Stage 14j | individually eligible but not incrementally promoted |
| D10 | `halfdisc_distribution_contrast` | opposed-region distribution | fixed portable oriented half-disc histogram contrast; exact binning/support must be copied from its Stage-23C preregistration and becomes part of the cache key | new first-landscape map; Compass/gPb mechanism, not exact Compass |
| D11 | `pmi_dependency_deficit` | statistical dependence | frozen Stage-18j image-internal symmetric 256-level `PMI_rho`, exponent `1.25`, four pair axes | prior single-cue addition missed UDED margin |
| D12 | `semiglobal_changepoint` | semi-global change point | frozen Stage-17x row/column BIC piecewise-constant change-point response, max side `256` | prior single-cue addition narrowly missed UDED margin |
| D13 | `fh_region_boundary` | region-adaptive contrast | frozen Stage-18b grayscale 8-neighbour FH boundary, sigma `0.8`, `tau(C)=300/|C|`, no minimum-size postprocessing | prior single-cue addition failed UDED gate |

The first pool deliberately includes previously rejected single-cue additions.
Their rejection concerned one integration with compact MFI; it does not answer
whether their errors complement other evidence or which aggregation property
best uses them. Conversely, a strong individual descriptor is not guaranteed a
place in a complementary set.

## Exclusions from the first landscape

- Exact SED, SCO, Compass, EDPF, Structured Forest, and PMI spectral-pipeline
  outputs are complete detectors or depend on non-portable / restricted author
  code. They are detector targets or reproduction references, not interchangeable
  raw descriptors.
- Neural feature maps and pretrained embeddings are forbidden.
- Stage-22 calibration transforms and rejected post-result variants are closed.
- Brightness entropy, Frei-Chen, morphology, recurrence, ICA, Teager energy,
  and the other Stage-16--18 single-cue studies are not added to this first pool.
  They remain negative evidence and may not silently re-enter through aliases.

## Complementarity-first pruning contract for Stages 23D--23E

Stage 23D must analyze all 13 cached maps but may forward at most:

- eight cross-family pairs;
- four cross-family triples;
- the unchanged five-map incumbent anchor set;
- up to two single-map controls needed to interpret an interaction.

Selection must be deterministic and preregistered before Stage 23D scoring. It
must jointly use score/rank redundancy, unique tolerant true-positive support,
unique false-positive burden, reciprocal conditional correctness, and
per-image stability. No unrestricted powerset is permitted. A family may retain
more than one scale only when Stage 23D shows nonredundant support; otherwise one
representative is kept. Stage 23E consumes only cached maps and the frozen sets
emitted by Stage 23D.

## Source anchors

The decision-driving primary sources and official code pages are recorded with
training/fidelity/protocol fields in `STAGE23_LITERATURE_LEDGER.md`. The most
important anchors are Canny (DOI `10.1109/TPAMI.1986.4767851`), Daugman (DOI
`10.1364/JOSAA.2.001160`), Martin et al. (DOI
`10.1109/TPAMI.2004.1273918`), Arbeláez et al. (DOI
`10.1109/TPAMI.2010.161`), Ruzon and Tomasi (DOI
`10.1109/CVPR.1999.784624`), Isola et al. (DOI
`10.1007/978-3-319-10578-9_52`), Jevnisek and Avidan (DOI
`10.1016/j.cviu.2016.07.004`), and Felzenszwalb and Huttenlocher (DOI
`10.1023/B:VISI.0000022288.19776.77`).
