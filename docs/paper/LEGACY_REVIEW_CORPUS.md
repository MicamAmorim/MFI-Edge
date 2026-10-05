# Legacy systematic-review corpus — MFI-Edge / CH-MFI

This document preserves the **primary-study layer** behind the two earlier systematic reviews so that the future MFI-Edge paper does not depend on reconstructing old reading decisions from memory.

It complements `BIBLIOGRAPHY_MATRIX.md`, which focuses on the papers that directly shaped the current architecture.  Here the objective is different: preserve the historical corpus, the methodological family each work belongs to, the lesson we extracted, and whether that lesson still matters to MFI-Edge.

> Source note. The aggregation/pre-aggregation review reports **24 included papers**, but its method-group table and discussion collectively reference 25 method papers because reference [52] appears in the FCM discussion/table although it is absent from the earlier inclusion list. We keep the discussed paper here and flag this source-table inconsistency rather than silently deleting it.

---

# A. Fuzzy-logic edge-detection corpus from the 2023 SLR

The fuzzy-edge review selected a broader literature set and highlighted the following 17 explicitly fuzzy edge-detection works in its synthesis table.

| ID | Work | Core idea / short reading note | Relevance to MFI-Edge | Current stage |
|---|---|---|---|---|
| LF01 | Gonzalez et al. (2017), **Edge detection methods based on generalized type-2 fuzzy logic systems** | Generalized type-2 fuzzy logic represents uncertainty in edge evidence. | Historical motivation for treating ambiguity as structured information rather than noise. | Related work / uncertainty |
| LF02 | Castillo et al. (2017), **Review of Recent Type-2 Fuzzy Image Processing Applications** | Surveys type-2 fuzzy image processing and its uncertainty-handling advantages. | Background for uncertainty-aware fuzzy processing. | Related work |
| LF03 | Moya-Albor, Ponce & Brieva (2017), **An Edge Detection Method using a Fuzzy Ensemble Approach** | Combines multiple detector responses through a fuzzy ensemble. | Direct conceptual ancestor of the planned `MFI-Hybrid` detector-level fuzzy ensemble. | Future MFI-Hybrid |
| LF04 | Gonzalez, Melin & Castillo (2017), **Edge detection method based on general type-2 fuzzy logic applied to color images** | General type-2 fuzzy edge detection on color imagery. | Supports multi-channel uncertainty and color-aware extensions. | Related work / future color branch |
| LF05 | Balabantaray et al. (2017), **A Quantitative Performance Analysis of Edge Detectors with Hybrid Edge Detector** | Hybrid detector evaluated quantitatively against classical methods. | Historical evidence that hybridization can outperform isolated detectors. | Benchmark framing |
| LF06 | Flores-Vidal et al. (2018), **A New Edge Detection Approach Based on Fuzzy Segments Clustering** | Groups candidate pixels into fuzzy edge segments rather than treating pixels independently. | Strong conceptual link to our later topology/linking stage. | Topology / continuity |
| LF07 | Bueno et al. (2018), **Two-phase flow bubble detection method ... using fuzzy image processing** | Fuzzy image processing in a noisy applied setting. | Robustness/application context rather than direct architecture. | Background |
| LF08 | Baghbani, Jamasb & Khodabakhshi (2019), **A method for image edge detection based on interval-valued fuzzy sets** | Interval-valued membership derived from pixel/neighborhood intensities. | Supports local uncertainty and interval evidence representations. | Future uncertainty branch |
| LF09 | Flores-Vidal et al. (2019), **A new edge detection method based on global evaluation using fuzzy clustering** | Evaluates connected fuzzy segments globally. | Reinforces region/segment-level decision making instead of purely pointwise fusion. | Topology / region reasoning |
| LF10 | Dhargupta et al. (2019), **Fuzzy edge detection based steganography using modified Gaussian distribution** | Uses fuzzy edge localization as a robust support for adaptive embedding. | Application evidence; limited direct architectural effect. | Background |
| LF11 | Bhogal & Agrawal (2019), **Image Edge Detection Techniques Using Sobel, T1FLS, and IT2FLS** | Compares Sobel with type-1 and interval type-2 fuzzy systems. | Supports classical-localizer + fuzzy-reasoning comparisons. | Baseline framing |
| LF12 | Kumar, Singh & Kumar (2019), **Information hiding with adaptive steganography based on novel fuzzy edge identification** | Fuzzy inference determines edge regions for adaptive embedding. | Evidence for fuzzy confidence maps as useful intermediate representations. | Background |
| LF13 | Dhivya & Prakash (2019), **Edge detection of satellite image using fuzzy logic** | Fuzzy edge detection in remote sensing. | Cross-domain robustness motivation. | External-domain motivation |
| LF14 | Dorrani, Farsi & Mohamadzadeh (2020), **Image Edge Detection with Fuzzy Ant Colony Optimization Algorithm** | Fuzzy reasoning combined with metaheuristic optimization. | Reminds us that capacity/operator fitting can be treated as an optimization problem. | Capacity learning context |
| LF15 | Kumawat & Panda (2021), **A robust edge detection algorithm based on FBIR using improved Canny with fuzzy logic** | Fuzzy logic refines a classical Canny-style pipeline. | Close conceptual precedent for fuzzy evidence controlling a precise classical localizer. | CH-MFI motivation |
| LF16 | Raheja & Kumar (2021), **Edge detection based on type-1 fuzzy logic and guided smoothening** | Couples guided smoothing and type-1 fuzzy detection. | Supports explicit conditioning ablations before fuzzy aggregation. | Conditioning |
| LF17 | Tripathi et al. (2021), **Edge Detection on Medical Images Using Intuitionistic Fuzzy Logic** | Uses intuitionistic fuzzy logic to model ambiguity in medical boundaries. | Relevant to future annotation/model-uncertainty work. | Future uncertainty-aware MFI |

## Legacy fuzzy-review lesson that still matters

The fuzzy SLR already suggested three ideas that reappear in CH-MFI:

1. fuzzy methods are particularly attractive when **uncertainty/noise** is central;
2. hybrids between fuzzy reasoning and classical detectors are common and often useful;
3. higher-order/interval fuzzy representations are an alternative to collapsing evidence immediately to a binary label.

The modern project should cite this corpus mainly as **historical positioning**, while UAED/RankED and the current fuzzy-capacity literature provide the stronger contemporary uncertainty story.

---

# B. Aggregation / pre-aggregation corpus from the Axioms 2023 review

The review grouped the retained methods into three families.  The table below preserves the reviewed method papers and maps each one to the current project.

## B1. Multiple descriptors / multiple detections + aggregation

| ID | Work | Core method | What we should remember for MFI-Edge | Current architectural link |
|---|---|---|---|---|
| LA01 | Marco-Detchart et al. (2021), **Neuro-inspired edge feature fusion using Choquet integrals** | Multiple elementary visual cues fused by generalized Choquet operators. | Direct precedent for non-additive descriptor fusion; still one of our most important ancestors. | MFI-Classic / MFI-Fuzzy++ |
| LA02 | Qiu et al. (2021), **Learning from Human Uncertainty by Choquet Integral for Optic Disc Segmentation** | Choquet fuses predictions/segmentations under expert disagreement. | Connects non-additive fusion to annotator uncertainty and expert variability. | Future annotation-uncertainty branch |
| LA03 | Marco-Detchart et al. (2018), **Consensus image feature extraction with ordered directionally monotone functions** | Neighborhood evidence aggregated with ordered directional behavior to form feature maps/consensus. | Supports direction-aware local feature fusion and pre-aggregation. | Oriented descriptors / operator family |
| LA04 | Zhang et al. (2018), **A mixture model for image boundary detection fusion** | Treats boundary detection as consensus/fusion among detector outputs. | Strong historical argument for detector-level fusion; aligns with future MFI-Hybrid. | Future detector ensemble |
| LA05 | Gu et al. (2022), **An Improved Wavelet Modulus Algorithm Based on Fusion of Light Intensity and Degree of Polarization** | Fuses intensity-derived and polarization-derived edges, with NMS/thresholding. | Shows complementary sensing channels can improve connectivity. | Future heterogeneous-input extension |
| LA06 | Lin, Wang & Wan (2023), **DXYW: a depth-guided multi-channel edge detection model** | X/Y/W-inspired channels plus depth-guided fusion. | Supports explicit far/near/context cues and depth as a useful context source. | Future depth/context branch |
| LA07 | Ge et al. (2021), **WGI-Net: A weighted group integration network for RGB-D salient object detection** | RGB-D grouped integration for salient-region boundaries. | Example of learned cross-modal weighting; supports context routing. | MFI-Hybrid / future depth |
| LA08 | Fang, Zhao & Zhang (2020), **Cross-modal image fusion guided by subjective visual attention** | Cross-modal fusion guided by visual-attention relevance. | Precedent for attention/context-conditioned fusion. | Context analyzer / attention interpretation |
| LA09 | Bentkowska et al. (2020), **New fuzzy local contrast measures: Definitions, evaluation and comparison** | Defines local fuzzy contrast and aggregates local contrast evidence. | Direct support for local contrast as an explicit descriptor/context cue. | Descriptor stack / context |
| LA10 | Yang et al. (2019), **Multimodal Medical Image Fusion Based on Fuzzy Discrimination with Structural Patch Decomposition** | Salient structural patches + fuzzy decision maps + weighted fusion. | Supports feature-group decomposition before final fusion. | Partition-conditioned aggregation |
| LA11 | Flores-Vidal et al. (2022), **New Aggregation Approaches with HSV to Color Edge Detection** | Aggregates HSV information to strengthen Sobel/Canny color edges. | Direct precedent for aggregating channels around classical localizers. | Color extension / localizer control |
| LA12 | Li et al. (2020), **A Biologically Inspired Contour Detection Model Based on Multiple Visual Channels and Multi-Hierarchical Visual Information** | Multi-channel, multi-hierarchical visual information. | Historical support for hierarchical cues and multiple visual channels. | CH-MFI hierarchy |
| LA13 | Gudipalli et al. (2019), **Hybrid colour infrared image edge detection using RGB-YCbCr image fusion** | Fuses edges from different color/infrared representations. | Reinforces heterogeneous edge evidence fusion, though original study lacked strong quantitative validation. | Future MFI-Hybrid |
| LA14 | Lopez-Molina et al. (2018), **Self-adapting weighted operators for multiscale gradient fusion** | Self-adaptive weighted fusion of gradients produced under different Gaussian scales. | One of the clearest historical precedents for adaptive multiscale fusion and scale relevance. | Scale routing / granularity |
| LA15 | Hait et al. (2022), **The Bonferroni mean-type pre-aggregation operators construction and generalization: Application to edge detection** | Bonferroni-type pre-aggregation for feature extraction/edge detection. | Supports non-average/pre-aggregation families beyond Choquet. | Operator competition |
| LA16 | Wang et al. (2018), **Using Local Edge Pattern Descriptors for Edge Detection** | Flexible local directional descriptor fused across directions/parameters. | Supports explicit local directional structure and multi-parameter fusion. | Oriented descriptor family |

## B2. Aggregated distance functions + fuzzy C-means

| ID | Work | Core method | What we should remember | Current architectural link |
|---|---|---|---|---|
| LD01 | Pap, Nedovic & Ralevic (2021), **Image Fuzzy Segmentation Using Aggregated Distance Functions and Pixel Descriptors** | Builds a richer FCM distance from multiple color/spatial descriptors using OWA/PP/WAMP-like aggregation. | Shows that aggregation can act on the **metric itself**, not only on detector scores. | Future metric/context-space experiments |
| LD02 | Ralevic, Delic & Nedovic (2022), **Aggregation of fuzzy metrics and its application in image segmentation** | Aggregates fuzzy metrics for segmentation. | Supports metric-level fusion and fuzzy similarity design. | Future metric fusion |
| LD03 | Delic, Nedovic & Pap (2019), **Extended power-based aggregation of distance functions and application in image segmentation** | Extended power aggregators combine color/texture distances before FCM. | Compact interaction/weighting of heterogeneous descriptors. | Capacity simplification context |
| LD04 | Nedovic, Ralevic & Pavkov (2018), **Aggregated distance functions and their application in image processing** | Convex/aggregated channel distances used in image processing/FCM. | Baseline for additive metric aggregation. | Background / metric branch |
| LD05 | Ljubo, Delic & Ralevic (2018), **OWA aggregated distance functions and their application in image segmentation** | OWA combines intensity/neighborhood distances. | Supports neighborhood + intensity evidence and ordered aggregation. | Context / ordered aggregation |

> **Source-table note:** the review's method discussion also includes reference [52] (`LD04`) although its earlier '24 papers' inclusion list does not contain [52]. For reproducibility we retain it and treat the discrepancy as a source-table issue.

## B3. Type-2 fuzzy / neutrosophic aggregation

| ID | Work | Core method | What we should remember | Current architectural link |
|---|---|---|---|---|
| LT01 | Nagarajan et al. (2018), **A Type-2 Fuzzy in image extraction for DICOM image** | Triangular interval type-2 fuzzy numbers represent image evidence before aggregation. | Alternative explicit uncertainty representation. | Future uncertainty branch |
| LT02 | Nagarajan et al. (2018), **Edge Detection on DICOM Image using Triangular Norms in Type-2 Fuzzy** | Triangular norms/type-2 fuzzy morphology/gradients. | Evidence that aggregation operators can act directly in fuzzy morphological processing. | Future morphology/uncertainty |
| LT03 | Martinez et al. (2019), **General Type-2 Fuzzy Sugeno Integral for Edge Detection** | Aggregates four directional gradients using a generalized type-2 Sugeno integral. | Direct precedent for directional-gradient fuzzy integration and blur robustness. | Fuzzy measure/operator comparison |
| LT04 | Kaur & Garg (2022), **A new method for image processing using generalized linguistic neutrosophic cubic aggregation operator** | Neutrosophic cubic aggregation for image operations/noise handling. | Broader uncertainty formalism; useful as related work, not current core. | Related work / robustness |

---

# C. Historical gaps from the 2023 aggregation review that CH-MFI now explicitly tests

The original review identified gaps that are now useful for framing novelty:

| 2023 gap / observation | Current CH-MFI response |
|---|---|
| No consensus on which aggregation/pre-aggregation family is best for edge fusion | Factorial operator/capacity competition with frozen validation/held-out protocol |
| Strong reliance on weighted means / average-like operators | CF/CC/CF1F2, RDF families, distorted capacities, Choquet-inspired and partition-conditioned operators |
| Need to combine feature extraction and information fusion | Descriptor extraction, within-scale nonadditive fusion, then multiscale hierarchy |
| Direct ensemble of classical detectors by aggregation was proposed as future work | Planned MFI-Hybrid with classical + TEED/PiDiNet + MFI outputs |
| Depth/context cues useful in complex/low-contrast scenes | Context analyzer designed to accept blur/noise/texture/frequency now, depth later |
| Multiscale relevance changes with image detail | Hierarchical coarse/fine branch + granularity control + scale-specific capacity bank |
| Neighborhood information matters | SWAFED/local-context variants + topology/linking |
| Quantitative cross-method comparison was missing | BSDS500/UDED/BIPED target protocol with ODS/OIS/AP, fixed-F1, bootstrap and runtime |

---

# D. How to use this corpus when writing the future article

Do **not** cite all legacy papers indiscriminately. Use them as a structured archive:

- **Introduction / historical fuzzy edge detection:** LF01–LF17 selectively, with the 2023 SLR as the main synthesis citation.
- **Aggregation and descriptor fusion:** LA01, LA03, LA09, LA14, LA15 are especially relevant.
- **Detector-level fusion:** LF03, LA04, LA11, LA13.
- **Metric / clustering aggregation:** LD01–LD05 only if the manuscript discusses aggregation outside direct score fusion.
- **Uncertainty formalism:** LF01/LF02/LF08/LF17 and LT01–LT04 as historical background; contemporary UAED/RankED should carry the main modern argument.
- **Multiscale / context:** LA06, LA08, LA12, LA14.

For the current 2024–2026 architecture-driving literature (FO-CAR, SWAFED, distorted probabilities, conditional Choquet/OWA, hierarchical Choquet, Choquet-inspired/partitioned aggregation, NBED, Mask2Edge, UAED, RankED, MuGE, TEED, etc.), use `BIBLIOGRAPHY_MATRIX.md`.

---

# E. Metadata audit checklist

Before manuscript submission:

1. import complete BibTeX for all legacy works that are actually cited in the final manuscript;
2. verify author names, issue/page/article numbers and DOI against publisher/Crossref;
3. retain the 24-vs-25 review-table discrepancy only in the research notebook, not as a manuscript claim unless discussing review methodology;
4. resolve the user-supplied 2026 FSS PII `S0165011426003714` before citing it;
5. distinguish **faithful reproduction**, **paper-inspired implementation**, and **our own generalization** in both diagrams and text.
