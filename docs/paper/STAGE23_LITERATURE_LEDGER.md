# Stage 23 Literature / Code / Protocol Ledger

This ledger is the provenance record for evidence, aggregation, detector, dataset, and evaluator choices in Stage 23.

Every source that materially changes the descriptor shortlist, aggregator shortlist, detector target list, protocol matrix, or implementation strategy must be added here in the same change that preregisters the resulting experiment.

## Required fields

| ID | Source | DOI / official URL | Source type | Method / component | Training class | Dataset / split / metric | Implementation fidelity | Stage-23 decision role | Notes |
|---|---|---|---|---|---|---|---|---|---|

## Training classes

Use one of:

- `fixed-untrained`
- `unsupervised-data-estimated`
- `classical-supervised`
- `neural-reference-only`
- `not-applicable`

## Implementation fidelity

Use one of:

- `author-code-exact`
- `author-code-adapted-protocol-only`
- `faithful-reimplementation`
- `partial-reproduction`
- `conceptual-source-only`

Do not describe a surrogate as an exact reproduction.

## Protocol discipline

Literature-reported and locally re-evaluated metrics must remain separate. Record the exact split, evaluator, matching tolerance, annotation treatment, resizing/thinning/postprocessing, and whether the source number is validation/test/cross-validation whenever these details are available.

## Entries

| ID | Source | DOI / official URL | Source type | Method / component | Training class | Dataset / split / metric | Implementation fidelity | Stage-23 decision role | Notes |
|---|---|---|---|---|---|---|---|---|---|
| S23-01 | Canny (1986), *A Computational Approach to Edge Detection* | `10.1109/TPAMI.1986.4767851` | peer-reviewed primary paper | Gaussian derivative, localization, NMS and hysteresis | fixed-untrained | synthetic criteria; not a BSDS protocol source | conceptual-source-only | anchors local-gradient control and separates evidence from postprocessing | Stage 23 uses repository Scharr evidence, not an exact Canny reproduction |
| S23-02 | Daugman (1985), *Uncertainty Relation...Two-Dimensional Visual Cortical Filters* | `10.1364/JOSAA.2.001160` | peer-reviewed primary paper | 2-D Gabor filters | fixed-untrained | not a boundary benchmark | conceptual-source-only | anchors oriented-frequency family | Stage 23 retains already fixed repository Gabor scales |
| S23-03 | Morrone & Owens (1987); Kovesi (1999/2003) | `10.1016/0167-8655(87)90013-4`; `https://www.peterkovesi.com/papers/phasecorners.pdf` | primary papers / author manuscript | local energy and phase congruency | fixed-untrained | feature-detection experiments | faithful-reimplementation | anchors contrast-normalized phase evidence | first pool uses the frozen Stage-14j PC2 maximum moment, not a parameter search |
| S23-04 | Martin, Fowlkes & Malik (2004), *Learning to Detect Natural Image Boundaries Using Local Brightness, Color, and Texture Cues* | `10.1109/TPAMI.2004.1273918` | peer-reviewed primary paper | brightness/color/texton half-disc gradients and learned combination | classical-supervised | BSDS300 train/test, Berkeley boundary benchmark | conceptual-source-only | anchors opposed-region distribution evidence and multi-cue separation | literature number remains separate from local Stage-23 development results |
| S23-05 | Arbeláez et al. (2011), *Contour Detection and Hierarchical Image Segmentation* | `10.1109/TPAMI.2010.161` | peer-reviewed primary paper | multiscale local cues, spectral globalization, OWT-UCM | classical-supervised | BSDS500 benchmark, ODS/OIS/AP | author-code-adapted-protocol-only | detector census, protocol anchor, later gPb target | Stage 23A does not claim an exact local reproduction |
| S23-06 | Berkeley Segmentation Dataset and Benchmark | `https://www2.eecs.berkeley.edu/Research/Projects/CS/vision/bsds/` | official benchmark | dataset and boundary evaluation | not-applicable | BSDS500 train 200 / val 100 / test 200; multi-annotator PR/F | author-code-exact | defines split roles and standard Berkeley track | local Windows reference reproduction remains unverified |
| S23-07 | Dollár & Zitnick (2013/2015), Structured Forests; official toolbox | `10.1109/TPAMI.2014.2377715`; `https://github.com/pdollar/edges` | peer-reviewed paper / official repository | structured random forest over color, gradient and self-similarity channels | classical-supervised | BSDS500 and cross-dataset author evaluations | author-code-exact | strong classical detector target and evaluator-default cross-check | repository license is MSR-LA Full Rights; pinned model previously reproduced |
| S23-08 | Piotr Dollár `edgesEvalImg.m` | `https://github.com/pdollar/edges/blob/master/edgesEvalImg.m` | official evaluator source | BSDS-compatible matching wrapper | not-applicable | defaults: 99 thresholds, `maxDist=.0075`, thinning on | author-code-exact | verifies local standard-Berkeley configuration | does not repair the documented stochastic Windows matcher caveat |
| S23-09 | Ruzon & Tomasi (1999/2001), Compass; official project | `10.1109/CVPR.1999.784624`; `10.1109/34.969118`; `https://ai.stanford.edu/~ruzon/compass/` | primary papers / author code | adaptive color distributions and EMD in opposed semicircles | fixed-untrained | author natural-image demonstrations; historical benchmarks | author-code-exact | anchors distribution-gradient family and exact detector target | no explicit source license; first landscape uses a portable mechanism map, not Compass output |
| S23-10 | Isola et al. (2014), *Crisp Boundary Detection Using Pointwise Mutual Information*; official repository | `10.1007/978-3-319-10578-9_52`; `https://github.com/phillipi/crisp-boundaries` | peer-reviewed primary paper / author code | image-internal PMI affinity plus spectral clustering | unsupervised-data-estimated | BSDS500 benchmark in paper | partial-reproduction | anchors statistical-dependence evidence and later fidelity target | first pool stops at the already frozen PMI deficit map; no spectral pipeline claim |
| S23-11 | Jevnisek & Avidan (2016), *Semi Global Boundary Detection* | `10.1016/j.cviu.2016.07.004`; `https://www.eng.tau.ac.il/~avidan/papers/CVIP_SGBD.pdf` | peer-reviewed primary paper / author manuscript | dynamic-programming scanline segmentation | fixed-untrained | multiple color/depth benchmarks in paper | partial-reproduction | anchors semi-global changepoint evidence | Stage-17x/23 pool is an explicit row/column bounded surrogate |
| S23-12 | Felzenszwalb & Huttenlocher (2004), *Efficient Graph-Based Image Segmentation* | `10.1023/B:VISI.0000022288.19776.77` | peer-reviewed primary paper | adaptive component graph segmentation | fixed-untrained | segmentation experiments, not Berkeley edge ODS | faithful-reimplementation | anchors region-adaptive boundary support | first pool uses the frozen equation-level grayscale realization |
| S23-13 | Akinlar & Topal (2012), EDPF; official ED_Lib | `10.1142/S0218001412550026`; `https://github.com/CihanTopal/ED_Lib` | peer-reviewed primary paper / official repository | contiguous Edge Drawing chains and Helmholtz/NFA validation | fixed-untrained | author edge/segment experiments; local BSDS-val reproduction | author-code-exact | chain-first strong-detector reference, not first-pool raw evidence | official code is MIT; binary maps expose a single nontrivial operating point |
| S23-14 | Yang et al. (2013/2015), CO/SCO; official author page | `10.1109/CVPR.2013.362`; `10.1109/TIP.2015.2425538`; `https://www.neuro.uestc.edu.cn/vccl/projcvpr2013.html` | peer-reviewed papers / author archives | double-opponent color evidence and spatial-sparseness modulation | classical-supervised | parameters selected on BSDS300 train; test metrics documentary | author-code-exact | color/contextual-suppression detector target | source is research-purpose-only; local exact paired validation maps already exist |
| S23-15 | Akbarinia & Párraga (2018), *Feedback and Surround Modulated Boundary Detection*; official code | `10.1007/s11263-017-1035-5`; `https://github.com/ArashAkbarinia/BoundaryDetection` | peer-reviewed primary paper / author repository | opponent-color, surround and feedback-equivalent contextual hierarchy | fixed-untrained | BSDS500 test in paper; local BSDS-val exact reproduction | author-code-exact | strong untrained detector reference/target | no explicit license; ignored local dependency, not redistributed |
| S23-16 | Weickert (1999), *Coherence-Enhancing Diffusion of Colour Images* | `10.1016/S0262-8856(98)00102-4` | peer-reviewed primary paper | spatial structure tensor and coherence | fixed-untrained | flow-like image examples | conceptual-source-only | anchors orientation-organization evidence | Stage 23 uses only fixed scalar tensor evidence, not diffusion |
| S23-17 | Lindeberg (1998), *Feature Detection with Automatic Scale Selection* | `10.1023/A:1008045108935` | peer-reviewed primary paper | scale-normalized derivatives and scale selection | fixed-untrained | analytic/model-image studies | conceptual-source-only | anchors Hessian/curvature and persistence families | fixed incumbent scales remain unchanged in the first pool |
| S23-18 | Kittler et al. (1998), *On Combining Classifiers* | `10.1109/34.667881` | peer-reviewed primary paper | sum/product/max/min/median classifier combination analysis | not-applicable | classification experiments | conceptual-source-only | motivates equal-sum and conjunctive/disjunctive controls | does not assume edge maps are calibrated posteriors |
| S23-19 | Yager (1988), *On Ordered Weighted Averaging Aggregation Operators...* | `10.1109/21.87068` | peer-reviewed primary paper | ordered weighted averaging | not-applicable | multicriteria aggregation | conceptual-source-only | anchors fixed median OWA control | no OWA weight search is allowed in the first landscape |
| S23-20 | Sugeno (1974), *Theory of Fuzzy Integrals and Its Applications* | `https://ci.nii.ac.jp/naid/10017208296` | primary doctoral thesis | max-min fuzzy integral | not-applicable | aggregation theory | conceptual-source-only | anchors idempotent lattice-style family | Stage 23E must preregister capacity fitting and algebraic checks |
| S23-21 | Grabisch (1997), *k-order Additive Discrete Fuzzy Measures and Their Representation* | `10.1016/S0165-0114(97)00168-1` | peer-reviewed primary paper | k-additive capacities and interaction representation | not-applicable | aggregation theory | faithful-reimplementation | anchors monotone 2-additive Choquet family | bounded singleton/pair model; not a full-capacity search |
| S23-22 | Choquet (1954), *Theory of Capacities* | `10.5802/aif.53` | peer-reviewed primary paper | capacities and Choquet integration | not-applicable | mathematical theory | faithful-reimplementation | anchors ordinary/disorted-capacity Choquet semantics | distorted capacity and d-Choquet terminology remain separate |
| S23-23 | Mély et al. (2016), *A Systematic Comparison Between Visual Cues for Boundary Detection*; official dataset | `10.1016/j.visres.2015.11.007`; `https://serre.lab.brown.edu/resources/the-multi-cue-boundary-detection-dataset` | peer-reviewed primary paper / official dataset | luminance, color, motion and stereo cue diagnosticity | classical-supervised | Multi-Cue 100 scenes; separate boundary and all-edge GT | conceptual-source-only | prospective cross-domain protocol and cue-complementarity source | exact random split manifests/evaluator must be recovered before Stage-23 use |
| S23-24 | Silberman et al. (2012), NYUDv2 | `10.1007/978-3-642-33715-4_54`; `https://cs.nyu.edu/~silberman/datasets/nyu_depth_v2.html` | peer-reviewed primary paper / official dataset | RGB-D indoor scene dataset | not-applicable | conventional 795/654 split; derived edge protocols vary | conceptual-source-only | prospective reserved cross-domain track | input modality, boundary conversion and `0.011` evaluator details require preregistration |
| S23-25 | Soria et al. BIPED / DexiNed documentation; official dataset repository | `10.1016/j.patcog.2023.109461`; `https://github.com/xavysp/MBIPED` | peer-reviewed paper / official dataset repository | dense perceptual edge annotations | neural-reference-only | BIPEDv2 train 200 / test 50 | conceptual-source-only | potential train-only development track and final-protocol census | BIPED test is already inspected and unavailable for optimization |

## Stage-23A shortlist decision

The first landscape is frozen to 13 descriptor maps and eight aggregation
families in `STAGE23_DESCRIPTOR_CENSUS.md` and
`STAGE23_AGGREGATOR_CENSUS.md`. Descriptor extraction cannot begin until
`stage23b_cache_certification` passes. No source above authorizes protected
split access, a descriptor powerset, or a detector intervention before the
complementarity and matched-validation stages.

## Stage-23G live target checkpoint

Primary-source and official-code review was refreshed on 2026-10-30 for
Akbarinia and Parraga's SED paper (DOI `10.1007/s11263-017-1035-5`, accepted
manuscript `https://ddd.uab.cat/record/275061`) and the official repository
`https://github.com/ArashAkbarinia/BoundaryDetection` at the already pinned
commit `11514b80162e5cd93fd244515189649656105a14`. The paper confirms fixed
parameters across BSDS, MBDD, and CID; twelve-orientation Gaussian derivatives;
V1 full/far/iso/orthogonal surround; V2 texture/noise suppression; feedback;
and author-reported component ablations. The public repository still describes
itself as the source/material release for the BMVC and IJCV articles, and no
explicit license was found; local source remains ignored and unredistributed.

SED is selected as the single Stage-23G target because it is the strongest
exact strictly untrained detector already materialized on both allowed
development domains. Its evidence inventory lacks an explicit opposed-region
distribution comparison. Stage 23D's low-redundancy/unique-support evidence
therefore motivates one half-disc gap diagnosis. This does not claim that the
failed Stage-23F half-disc/logistic relationship transferred. Because no
nontrivial Stage-23F aggregation passed jointly, only the equal-mean matched
control is frozen as a possible later intervention, conditional on the
cross-domain gap diagnosis passing.

## Post-Stage-23G1 live escalation — complete PMI detector preflight

The 2026-10-30 refresh retained the primary ECCV paper and official project
page for Isola, Zoran, Krishnan, and Adelson's *Crisp Boundary Detection Using
Pointwise Mutual Information* (DOI `10.1007/978-3-319-10578-9_52`,
`https://web.mit.edu/phillipi/crisp_boundaries/`). The project explicitly
describes an unsupervised detector that estimates image-internal feature-pair
dependency and globalizes it with spectral clustering. The official repository
`https://github.com/phillipi/crisp-boundaries` is pinned at current immutable
commit `ee2d76e98340313a8f92e1b65064a9b4ea90ac77`; it contains a three-clause
BSD-style `License.txt`, the end-to-end `findBoundaries` entry point, color and
local-variance features, fixed `rho=1.25`, KDE affinity estimation, and the
explicit non-approximated `MS_algorithm_from_paper` setting. The paper states
that parameters were tuned on BSDS500 train, so the method is classified as
`unsupervised-data-estimated` with author-tuned fixed parameters rather than
strictly untrained.

This complete method is not Stage 18j's bounded grayscale discrete PMI-deficit
membership: the author detector includes per-image KDE estimation, multiscale
affinity construction, and spectral globalization. It is selected as a
mechanistically distinct strong-detector target after the SED/half-disc route
closed, not as a replacement cue inside SED and not because a failed Stage-23F
cell was reinterpreted. The registered next action is the dataset-free
`stage23g2_pmi_exact_runtime_preflight` under
`docs/paper/STAGE23G2_PREREGISTRATION.md`. No dataset reproduction or missing-
family intervention is authorized until immutable source, build compatibility,
and the exact paper-path synthetic smoke all pass.

## Post-Stage-23G2 live escalation — exact SCO cross-domain surface

The 2026-10-30 refresh revisited Yang et al.'s primary SCO paper (DOI
`10.1109/TIP.2015.2425538`) and the official institutional project/source page
`https://www.neuro.uestc.edu.cn/vccl/projcvpr2013.html`. The paper confirms
that SCO is an oriented double-opponent color/luminance detector followed by a
modified local spatial-sparseness constraint intended to suppress dense texture
responses. Its fixed author path, archive/source hashes, research-only source
notice, and native-resolution BSDS500-validation reproduction were already
established in Stage 15E. Exact SCO obtained local official ODS/OIS/AP
`0.656582/0.682564/0.694939`, while its matched CO precursor obtained
`0.635925/0.665489/0.651767`; those are development/reproduction results under
the reference-unverified local matcher, not literature-test claims.

SCO is selected as the next distinct strong-detector target after the closed
SED/half-disc and complete-PMI routes. It is deterministic, strictly
non-neural, exact-author-code available, and mechanistically different from
SED's feedback/surround hierarchy and PMI's affinity graph. The checkpoint
does not choose a missing cue or reinterpret any failed Stage-23F relationship.
The registered action is `stage23g3_sco_overlap_clean_materialization` under
`docs/paper/STAGE23G3_PREREGISTRATION.md`: materialize exact SCO at the fixed
Stage-23 overlap-clean UDED working raster with per-image hash checkpoints and
reuse the frozen Stage-15E SCO bytes for the official attachment. No GT score,
descriptor extraction, aggregation, intervention, or promotion is authorized.
