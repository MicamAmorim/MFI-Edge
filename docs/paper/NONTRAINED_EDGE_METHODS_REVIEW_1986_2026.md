# Non-trained edge/boundary detection review, 1986–2026

Purpose: Stage-15 literature/reproduction seed for MFI-Edge.
Created: 2026-10-07.
Scope: methods whose inference does not require a trained neural network or learned supervised classifier. Papers that fit weights/classifiers/dictionaries from labeled edge data are explicitly marked trained and excluded from the strict non-trained frontier.

## Interpretation rules

- **Strictly non-trained**: no supervised training from boundary ground truth; no learned classifier; no neural/foundation-model features.
- **Author-fixed / analytically parameterized**: allowed as non-trained, but reported parameters may still have been chosen empirically by the authors. Reproduction notes must distinguish this from parameter-free claims.
- **Trained classical**: random forests, SVMs, learned fusion weights, learned dictionaries, etc. These are not part of the strict non-trained frontier even if they are commonly called 'traditional' or 'non-deep'.
- Literature headline metrics are not assumed comparable unless split, threshold policy, matching tolerance, thinning, annotation treatment, resizing and map representation match.
- Our official-protocol re-evaluation and the literature-reported metric must be stored separately.

## Audit table

| Year | Method / paper | Training class | DOI / primary source | Code / implementation status | Reported benchmark evidence | Stage-15 value |
|---|---|---|---|---|---|---|
| 1986 | Canny, *A Computational Approach to Edge Detection* | strictly non-trained | `10.1109/TPAMI.1986.4767851` | OpenCV and many implementations | foundational gradient/NMS/hysteresis reference; later BSDS reproductions commonly place it around the ~0.58–0.60 ODS range depending on protocol | mandatory protocol baseline |
| 1986 | Di Zenzo, *A Note on the Gradient of a Multi-Image* | strictly non-trained | `10.1016/0734-189X(86)90223-9` | multiple reimplementations | multichannel/vector gradient; no original BSDS500 protocol | historical color-gradient reference; Stage 14k already tested a related fixed Lab tensor realization |
| 1987 | Deriche, recursive optimal edge detector | strictly non-trained | `10.1007/BF00123164` | multiple implementations | recursive formulation, scale-cost efficiency | efficiency/control baseline, not a primary Stage-15 accuracy target |
| 1993 | Trahanias & Venetsanopoulos, vector order-statistics color edge detection | strictly non-trained | `10.1109/83.217230` | no official repository verified in this review | early vector-color morphology/statistics literature | historical multichannel aggregation context |
| 1997 | Smith & Brady, SUSAN | strictly non-trained | `10.1023/A:1007963824710` | widely reproduced | classic USAN local-structure detector; pre-modern BSDS protocol | conceptual reference and optional baseline |
| 1999 | Ruzon & Tomasi, *Color Edge Detection with the Compass Operator* | strictly non-trained | `10.1109/CVPR.1999.784624` | faithful reimplementation likely required | compares color distributions in oriented half-discs rather than only means | **high-priority distribution-boundary mechanism (15f)** |
| 1999 | Kovesi, phase congruency feature detection | strictly non-trained | author publication/code; no single DOI used here | author code exists | contrast/brightness-invariant phase feature family | already partially interrogated by Stage 14j; retain as context |
| 2003 | Grigorescu et al., non-classical receptive-field surround inhibition | strictly non-trained | `10.1109/TIP.2003.814250` | historical implementations/demos | texture-edge suppression via oriented surround interactions | key ancestor of contextual non-trained frontier |
| 2004 | Canny plus surround suppression / contextual inhibition | strictly non-trained | `10.1016/j.imavis.2003.12.004` | historical implementations | demonstrates major role of context beyond local gradient | mechanism-level reference for 15q |
| 2012 | Topal & Akinlar, Edge Drawing | strictly non-trained | `10.1016/j.jvcir.2012.05.004` | author code `https://github.com/CihanTopal/ED_Lib` | chain construction from anchors/gradient, designed for real-time edge segments | **high-priority structural baseline (15d/15s)** |
| 2012 | Akinlar & Topal, EDPF | strictly non-trained / parameter-free claim | `10.1142/S0218001412550026` | author code in `ED_Lib` | Edge Drawing with Helmholtz/a-contrario false-detection validation | **highest-priority exact reproduction (15d); Stage 14t is not equivalent** |
| 2013 | Yang et al., *Efficient Color Boundary Detection with Color-Opponent Mechanisms* (CO) | strictly non-trained | `10.1109/CVPR.2013.362` | public MATLAB code, including `COBoundary.m`; public mirror found at `https://github.com/jackygsb/Efficient-Color-Boundary-Detection-with-Color-opponent-Mechanisms` | paper reports competitive BSDS natural-boundary performance for a biologically motivated color-opponent model | **reproduce as contextual/color baseline (15e)** |
| 2013 | multiscale non-classical receptive-field contour integration | strictly non-trained | `10.1016/j.neucom.2012.09.027` | official code not verified | multiscale contextual integration | mechanism reference |
| 2014 | multifeature surround inhibition (MCI) | strictly non-trained | `10.1109/TIP.2014.2361210` | official code not verified | contextual texture suppression; computationally heavy in reported reproductions | mechanism/ablation reference rather than literal first implementation |
| 2015 | SCO / double-opponency + sparseness constraint | strictly non-trained | `10.1109/TIP.2015.2425538` | implementation availability to verify before Stage 15e | reported BSDS values around `ODS .67 / OIS .71 / AP .71` in the paper family | strong contextual reference; reproduce if code/protocol can be verified |
| 2015 | hierarchical/superpixel Gestalt-style boundary integration | strictly non-trained | `10.3390/s151026654` | code not verified | BSDS300/500 style experiments; hierarchical grouping | secondary structural reference |
| 2018 | Akbarinia & Párraga, **SED — Feedback and Surround Modulated Boundary Detection** | strictly non-trained | `10.1007/s11263-017-1035-5` | author implementation should be sought/verified before reproduction | widely reported around `ODS .71 / OIS .74 / AP .74` on BSDS500 in the method's evaluation | **highest-priority non-trained contextual baseline (15b)** |
| 2018 | BIHCD bio-inspired hierarchical contour detector | strictly non-trained | Sensors 18(8):2559 (paper-level metadata to verify in ledger before implementation) | code not yet verified | reported F around ~.70 and AP around ~.74 under its protocol | useful contextual reference; parameter sensitivity requires caution |
| 2018 | simplified MCI (sMCI) | strictly non-trained | `10.3389/fncom.2018.00028` | paper reproducible | primarily an efficiency simplification of MCI | low implementation priority unless needed for speed study |
| 2019 | multibandwidth/logarithmic texture inhibition | strictly non-trained | `10.1049/iet-ipr.2019.0214` | code not verified | BSDS evaluation under paper-specific settings | texture-suppression mechanism reference |
| 2021 | Lu et al., **Vector co-occurrence morphological edge detection for colour image** | strictly non-trained | `10.1049/ipr2.12290` | no official code verified in this review | paper reports BSDS500 and describes ODS/AP comparison; headline values in secondary table reading have been unusually high relative to some included baselines | **highest-priority independent protocol audit (15c)** |
| 2021 | disparity/dynamic receptive-field contour models | non-neural but may require RGB-D/depth | `10.1016/j.patcog.2020.107657` | code not verified | evaluated on NYUD/BSDS-style data depending on variant | not primary RGB-only Stage-15 target |
| 2024 | MSCNOGP multiscale closest-neighbor + grid partition | strictly non-trained | `10.1007/s00371-023-02894-y` | official code not verified | modern analytic/multiscale detector; paper metrics not assumed Berkeley-compatible | secondary reproduction candidate |
| 2023 | FACAFCV fractional-order ant-colony edge detector | parameter-fixed but image-specific; non-learned | `10.3390/fractalfract7060420` | no immutable author implementation used | high optimal-F values on corrupted images are separate from its BSDS500 ODS/OIS/AP `0.589/0.608/0.533` table | Stage-15j protocol-control example; no reproduction or fractional retuning |
| 2024 | BPAED Bernstein-polynomial adaptive edge detection | strictly non-trained | `10.1016/j.compeleceng.2024.109397` | no public author code or complete executable contract located | BSDS500/BIPED/MDBD/NYUv2 generic F1/accuracy/Pratt metrics omit the Berkeley ODS matcher and threshold protocol | Stage-15j closed as an incompatible headline, not a direct frontier number |
| 2024/2025 | Zhang et al., **Contour detection model inspired by V1 surround modulation** | strictly non-trained | `10.1007/s11760-024-03634-y` | no article-specific public code or supplement located in the 2026-10-08 audit | reports average optimal F-score `0.703` on BSDS500 and further NYUD testing; exact split/evaluator/output contract unresolved and not assumed identical to Berkeley ODS | **Stage-15h dataset-free fidelity preflight; no surrogate authorized** |
| 2025 | Yang, Peng & Wu, **Edge Detection Using Texture Gradients and Surround Modulation** | strictly non-trained | `10.1007/s11760-025-04339-6` | code not verified as of this review | paper explicitly argues prior bio-inspired work suppresses texture edges while overlooking useful texture-boundary cues; reports an ODS improvement over compared bio-inspired methods | **priority-max mechanism for MFI diagnosis (15g/15o)** |
| 2025 | multiscale mathematical morphology variants (AMMGK/AMDD family) | strictly non-trained | `10.1371/journal.pone.0319852` | open paper; code status to verify | reports PR/FOM-style experiments rather than matched Berkeley ODS/OIS/AP | robustness/mechanism reference |
| 2025 | MUSAN / USAN + feature matching neuromorphic formulation | strictly non-trained inference | `10.1038/s41467-024-55224-8` | paper reports accompanying data/code resources; verify exact repository/Zenodo before use | BSDS-style qualitative/metric evidence but not treated as matched official ODS | efficiency/hardware interest; low Stage-15 accuracy priority |
| 2025 | Amorim et al., d-CF/d-XC/d-CC restricted-dissimilarity Choquet-like integrals | strictly non-trained | `10.3390/app152413273` | repository lineage integrated in MFI research | BSDS500/UDED under Bezdek/Estrada–Jepson-style framework rather than official Berkeley ODS/OIS/AP | central fuzzy lineage; retain protocol distinction |
| 2026 | **Fractional Dirac Operators for Edge Detection** (QFrD family) | strictly non-trained | `10.3390/fractalfract10060412` | paper reports implementation/code availability to verify before exact audit | BSDS benchmark with reported `ODS 0.6145 / OIS 0.6361 / AP 0.5996` for the proposed method under its stated toolbox/protocol | **modern analytic reference (15i), not invitation to retune Stage 14s** |
| 2026 | Gao & Gao multiscale Gabor + directional Sobel | strictly non-trained; empirically fixed | `10.1007/s10791-026-10008-0` | no public source/immutable implementation located | reports BSDS500 F1 `0.888` with direct pixelwise formulas but no ODS/OIS, matcher tolerance, annotation aggregation, split, threshold scope, or thinning contract | Stage-15j protocol-incompatible headline; no surrogate reproduction |

## Strict exclusions from the non-trained frontier

The following are important historical or modern baselines but **not strictly non-trained** under Stage-15 rules:

| Method family | Why excluded from strict non-trained frontier |
|---|---|
| Pb/mPb/gPb learned combinations | fusion/calibration weights are learned from labeled boundary data in the standard formulations |
| SCG | learned sparse-code dictionaries / discriminative components |
| Sketch Tokens | learned random forest / patch token model |
| Structured Edges | trained structured random forest |
| Oriented Edge Forests | trained random forest / calibration |
| HED, RCF, BDCN, DexiNed, PiDiNet, EDTER, transformer/foundation-model detectors | trained neural networks or pretrained neural features |

They may remain in `SOTA_TARGETS.md` as comparison targets, but they cannot be used as evidence that a method is 'non-trained'.

## Key conclusions driving Stage 15

### 1. The strongest non-trained literature is contextual, not merely differential

The literature trajectory suggests that gains beyond Canny-like local gradients often come from orientation-specific surround interactions, multiscale context, color opponency, structure and texture-distribution evidence. Modern mathematically sophisticated differential operators remain useful references, but the largest conceptual gap to strong natural-boundary detectors appears contextual/structural.

### 2. Texture must be decomposed into negative and positive evidence

A textured interior can be anti-boundary evidence, but a **change between texture distributions across a candidate boundary** is positive evidence. Stage 15g/15o must test this distinction directly rather than treating all texture as suppression material.

### 3. Stage 14t does not falsify EDPF

EDPF first constructs edge chains and validates those chains using Helmholtz/a-contrario meaningfulness. Stage 14t instead applied a repository-specific NFA-style attenuation over connected upper-level components of the incumbent score. Those are scientifically different mechanisms.

### 4. Reported high numbers need protocol reproduction

Any literature result substantially above the well-established contextual non-trained range must be audited under the same evaluator before being used as a frontier claim. Stage 15c and 15j exist specifically for this reason.

### 5. The next MFI architecture should be evidence-led

Before Stage 15p, the project should know whether the incumbent's missing true positives are specifically recovered by surround, distributional half-disc, texture-boundary, or chain-support mechanisms. The redesign should then integrate only mechanisms with demonstrated development-only complementarity.

## Primary/official sources verified during the 2026-10-07 review

- Canny, J. (1986). *A Computational Approach to Edge Detection*. IEEE TPAMI. DOI `10.1109/TPAMI.1986.4767851`. PubMed metadata: `https://pubmed.ncbi.nlm.nih.gov/21869365/`.
- Ruzon, M. & Tomasi, C. (1999). *Color Edge Detection with the Compass Operator*. CVPR. DOI `10.1109/CVPR.1999.784624`.
- Yang, K.-F. et al. (2013). *Efficient Color Boundary Detection with Color-Opponent Mechanisms*. CVPR. DOI `10.1109/CVPR.2013.362`. CVF paper and public code mirror verified during review.
- Akbarinia, A. & Párraga, C. A. (2018). *Feedback and Surround Modulated Boundary Detection*. IJCV 126:1367–1380. DOI `10.1007/s11263-017-1035-5`.
- Topal, C. & Akinlar, C. (2012). *Edge Drawing: A Combined Real-Time Edge and Segment Detector*. DOI `10.1016/j.jvcir.2012.05.004`.
- Akinlar, C. & Topal, C. (2012). *EDPF: A Real-time Parameter-free Edge Segment Detector with a False Detection Control*. DOI `10.1142/S0218001412550026`. Author implementation: `https://github.com/CihanTopal/ED_Lib`.
- Lu, Y. et al. (2021). *Vector co-occurrence morphological edge detection for colour image*. IET Image Processing 15:3063–3070. DOI `10.1049/ipr2.12290`.
- Zhang, Z. et al. (2025 issue; online 2024). *Contour detection model inspired by V1 surround modulation*. DOI `10.1007/s11760-024-03634-y`.
- Yang, D., Peng, B. & Wu, X. (2025). *Edge Detection Using Texture Gradients and Surround Modulation*. Signal, Image and Video Processing 19:727. DOI `10.1007/s11760-025-04339-6`.
- *Fractional Dirac Operators for Edge Detection* (2026). Fractal and Fractional 10(6):412. DOI `10.3390/fractalfract10060412`.

## Verification debt

Before an exact Stage-15 reproduction is registered, the agent must verify the following from primary sources rather than copying this review uncritically:

- exact author-code location and license/version for SED/SCO where relevant;
- exact reported SED/CO/SCO metric table and split/protocol;
- exact vector-co-occurrence implementation details and whether official code exists;
- exact protocol behind any unusually high 2026 F/F1 claim;
- exact code/release for the 2025 texture-gradient/surround method;
- QFrD repository/release and evaluator details;
- any parameter that was selected on BSDS labels in the original paper, because that changes the classification from parameter-free to author-calibrated for our purposes.

The agent must record resolution of each debt in `STAGE15_LITERATURE_LEDGER.md`.
