# Stage 15 literature decision ledger

Purpose: append-only scientific provenance for literature-driven Stage-15 decisions.

This file complements `BIBLIOGRAPHY_MATRIX.md`. The matrix is the paper-wide bibliography map; this ledger records **which source materially caused which Stage-15 decision**.

## Mandatory fields

Every new literature-driven decision must add or update a row with:

- `ID` — stable source identifier;
- `Reference` — authors/year/title;
- `DOI / official URL`;
- `Source type` — primary peer-reviewed / primary preprint / official code / official benchmark / secondary;
- `Training class` — strictly untrained / author-fixed / trained classical / neural / uncertain;
- `Protocol evidence` — dataset, split, metric family and known compatibility caveats;
- `Mechanistic role` — what scientific idea the source supports;
- `Decision role` — reproduce / baseline / diagnostic / defer / exclude;
- `Stage(s)` — Stage-15 stage IDs materially linked to this source;
- `Verification state` — verified / partly verified / verification debt;
- `Decision note` — concise explanation of why this source affected the plan.

Do not silently delete a row because a paper later proves incompatible. Update its state and preserve the historical decision.

## Initial ledger — 2026-10-07 transition review

| ID | Reference | DOI / official URL | Source type | Training class | Protocol evidence | Mechanistic role | Decision role | Stage(s) | Verification state | Decision note |
|---|---|---|---|---|---|---|---|---|---|---|
| S15-E01 | Canny (1986), *A Computational Approach to Edge Detection* | `10.1109/TPAMI.1986.4767851` | primary peer-reviewed | strictly untrained | predates BSDS500; later implementations vary | local gradient + NMS/hysteresis reference | baseline/protocol audit | 15a | verified bibliographic metadata | required measurement floor |
| S15-E02 | Ruzon & Tomasi (1999), *Color Edge Detection with the Compass Operator* | `10.1109/CVPR.1999.784624` | primary peer-reviewed | strictly untrained | original CVPR protocol; not assumed Berkeley500-compatible | oriented half-disc **distribution** contrast | reproduce/diagnostic | 15f,15o | DOI/title verified; implementation debt | directly tests distribution change beyond mean gradient |
| S15-E03 | Grigorescu et al. (2003), non-classical receptive-field surround inhibition | `10.1109/TIP.2003.814250` | primary peer-reviewed | strictly untrained | historical natural-image evaluation | oriented surround texture suppression | mechanistic baseline | 15q | bibliographic role verified | ancestor of strong contextual family |
| S15-E04 | Topal & Akinlar (2012), *Edge Drawing* | `10.1016/j.jvcir.2012.05.004`; official code `https://github.com/CihanTopal/ED_Lib` at `69b8d081bd6d28192d816ec0ed02aff9186d73c1` | primary peer-reviewed + official author code | strictly untrained; fixed algorithm | paper evaluates chain quality/speed rather than Berkeley ODS/OIS/AP; repository ED constructs one-pixel connected chains from anchors | chain construction and continuity | reproduce/diagnostic | 15d,15s | paper, official repository, immutable commit, and MIT license verified 2026-10-08; local C++ dependency preflight pending | ED chain construction is the substrate for exact EDPF and is mechanistically distinct from post-hoc component linking |
| S15-E05 | Akinlar & Topal (2012), *EDPF* | `10.1142/S0218001412550026`; official code `https://github.com/CihanTopal/ED_Lib` at `69b8d081bd6d28192d816ec0ed02aff9186d73c1` | primary peer-reviewed + official author code | strictly untrained; author-fixed implementation despite the parameter-free user interface | official source constructs grayscale EDPF with Prewitt, gradient threshold 11, anchor threshold 3, then chain-level Helmholtz validation with embedded `divForTestSegment=2.25` and `EPSILON=1.0`; native output is a binary `CV_8UC1` map, so official Berkeley AP has a single-operating-point limitation | chain-level Helmholtz/a-contrario meaningfulness | exact-code reproduce/diagnostic | 15d,15t | DOI, author repository, immutable commit, source hashes, scalar output, MIT license, and build contract audited 2026-10-08; dataset-free build smoke pending | Register `stage15d_edpf_build_preflight`; only a successful build/smoke may advance to native-resolution validation. Stage 14t is not equivalent and cannot falsify EDPF. |
| S15-E06 | Yang et al. (2013), *Efficient Color Boundary Detection with Color-Opponent Mechanisms* | `10.1109/CVPR.2013.362`; CVF paper; public MATLAB code mirror | primary peer-reviewed + public code | strictly untrained | BSDS-family evaluation; exact metric reproduction to verify | color opponency and contextual boundary representation | reproduce/baseline | 15e | DOI/paper/code mirror verified; protocol details debt | separates color/context contribution from Scharr-only localization |
| S15-E07 | Yang et al. (2015), SCO / double-opponency + sparseness constraint | `10.1109/TIP.2015.2425538` | primary peer-reviewed | strictly untrained | reported strong BSDS contextual performance; exact author code/protocol to verify | contextual sparseness/surround | reproduce if fidelity possible | 15e | partial; code/protocol debt | strong member of non-trained bio-inspired family |
| S15-E08 | Akbarinia & Párraga (2018), **SED — Feedback and Surround Modulated Boundary Detection** | `10.1007/s11263-017-1035-5`; official code `https://github.com/ArashAkbarinia/BoundaryDetection` at `11514b80162e5cd93fd244515189649656105a14` | primary peer-reviewed + official author code | strictly untrained; fixed author parameters | paper reports BSDS500 colour test ODS/OIS/AP `0.71/0.74/0.74`; exact-code repository re-evaluation on BSDS500 validation obtained `0.678546/0.709152/0.712814` under the common native-resolution path, so test literature and local validation remain separate | V1/V2 surround + feedback contextual integration | **retained exact-code reproduction baseline** | 15b | exact run, paper, table, author code, commit, source hashes, and R2023a compatibility verified 2026-10-08; local evaluator remains reference-uncertified | Author MATLAB full model completed on 100 validation images with only batch I/O/direct 8-bit adaptation. No explicit source license was found, so code remains ignored and unredistributed. Result is diagnostic baseline evidence, not an MFI promotion or final SOTA claim. |
| S15-E09 | Lu et al. (2021), **Vector co-occurrence morphological edge detection for colour image** | `10.1049/ipr2.12290`; primary full text `https://ietresearch.onlinelibrary.wiley.com/doi/full/10.1049/ipr2.12290` | primary peer-reviewed open access | strictly untrained | Table 5 reports BSDS500 boundary ODS/OIS/AP `0.76/0.79/0.77`, but the scored split, matcher version, tolerance, thinning, threshold grid, annotation handling, and map convention are not fixed; these numbers are documentary and not comparable to the repository path | HSV/HDHSV vector morphology + local co-occurrence-adaptive structuring elements | **closed fidelity-unresolved; no surrogate scored** | 15c | primary full text and dataset-free contract audited 2026-10-08; no author code/supplement found; exact and faithful implementation blocked by omitted parameters/conventions | The preflight confirmed unresolved R, kernel scales, sigma terms, d/T/S/J values, hue reference, HSV coordinate construction, vector-to-scalar output, gradient choice, padding/postprocessing, and exact Berkeley protocol. Stage 15c closes without detector execution or dataset feedback. |
| S15-E10 | Zhang et al. (2025 issue), *Contour detection model inspired by V1 surround modulation* | `10.1007/s11760-024-03634-y` | primary peer-reviewed | strictly untrained | reports average optimal F-score `0.703` on BSDS500 and NYUD follow-up; metric not assumed identical to Berkeley ODS | adaptive multiscale surround modulation | reproduce/diagnostic | 15h | DOI/result statement verified; code debt | directly relevant to image-internal adaptation without dataset router |
| S15-E11 | Yang, Peng & Wu (2025), **Edge Detection Using Texture Gradients and Surround Modulation** | `10.1007/s11760-025-04339-6` | primary peer-reviewed | strictly untrained | BSDS500/MBDD paper claims improvement over bio-inspired comparisons; exact code/protocol debt | **positive texture-boundary evidence + surround** | **priority-max reproduce/diagnostic** | 15g,15o,15p | DOI/abstract thesis verified; implementation/protocol debt | motivates separating interior texture suppression from cross-boundary texture change |
| S15-E12 | *Fractional Dirac Operators for Edge Detection* (2026) | `10.3390/fractalfract10060412` | primary peer-reviewed | strictly untrained | reports BSDS ODS/OIS/AP including proposed fractional Dirac detector | modern analytic/fractional reference | benchmark/audit | 15i | paper/DOI verified; exact code release debt | useful contemporary baseline; does not justify reopening Stage-14s tuning |
| S15-E13 | Amorim et al. (2025), *Generalizations of Choquet-like Integrals by Restricted Dissimilarity Functions Applied to Multi-Channel Edge Detection Problems* | `10.3390/app152413273` | primary peer-reviewed / project lineage | strictly untrained | BSDS500/UDED under Bezdek/Estrada–Jepson-style evaluation; not directly official Berkeley ODS/OIS/AP | fuzzy aggregation lineage | historical/core project context | all Stage 15 | verified project source | Stage-15 matched evaluator is needed to connect lineage to official boundary metrics |
| S15-E14 | Berkeley Segmentation Dataset and Benchmark; Arbelaez et al. (2011), *Contour Detection and Hierarchical Image Segmentation* | official benchmark `https://www2.eecs.berkeley.edu/Research/Projects/CS/vision/bsds/`; mirror `https://github.com/BIDS/BSDS500`; DOI `10.1109/TPAMI.2010.161` | official benchmark + primary peer-reviewed | not applicable (evaluation source) | soft boundary map, threshold sweep, all human boundaries; pinned code supplies one-to-one `correspondPixels`, ODS/OIS/AP aggregation, default `maxDist=0.0075` and thinning | matched measurement and evaluator reproduction | protocol audit / reference fixture | 15a and all official attachments | official source verified; local reference reproduction failed, with clock-seeded matcher nondeterminism causally confirmed 2026-10-07 | Fixed seed made fresh-process fixture tables identical but did not meet shipped-reference agreement; Stage 15a closed uncertified, and the controlled binary is forbidden for dataset scoring |

## Excluded-but-contextual source classes

These methods can appear in the general bibliography/SOTA target ledger but must not be mislabeled as strictly non-trained:

| Class | Examples | Reason |
|---|---|---|
| trained classical boundary detectors | gPb learned combinations, SCG, Sketch Tokens, Structured Edges, OEF | learned weights/dictionaries/classifiers/forests from data |
| trained neural boundary detectors | HED, RCF, BDCN, DexiNed, PiDiNet, EDTER and successors | trained neural inference path |
| pretrained/foundation-model edge systems | any detector relying on pretrained neural features | violates Stage-15 strict non-trained inference constraint |

## Agent update rule

For every `research_planning` or `literature_escalation` decision during Stage 15:

1. inspect this ledger first;
2. use primary sources/live web for new claims;
3. add the source **before or in the same commit** that preregisters the experiment it motivates;
4. store reported metrics with protocol qualifiers;
5. state whether implementation is exact author code, faithful reimplementation, or repository-specific surrogate;
6. if a source is later found trained or protocol-incompatible, preserve the row and update the classification/decision note;
7. synchronize `BIBLIOGRAPHY_MATRIX.md` when the source is important enough for the future manuscript.

A Stage-15 experiment whose core mechanism is literature-motivated but has no corresponding ledger entry is considered incompletely preregistered.
