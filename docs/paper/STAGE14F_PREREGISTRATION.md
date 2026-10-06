# Stage 14f — preregistered d-CC robustness falsification

**Status:** Development-only preregistration, recorded before Stage 14f results are inspected.

## Scientific question

Does replacing the retained positive distorted-Choquet aggregation with d-CC using FBPC and the absolute restricted dissimilarity function improve edge detection under controlled corruption, while preserving clean performance, when all other architecture components are held fixed?

## Fixed comparison

Control: five-feature positive distorted-Choquet context with gamma 0.55.

Candidate: d-CC with FBPC and absolute RDF.

Held fixed in both variants:

- five retained positive features: `gabor4_s5`, `hessian_s7`, `gabor4_s13`, `hessian_s13`, `gabor4_scale_persistence`;
- Stage-12d frozen feature parameters and renormalized frozen subset weights;
- Scharr+NMS localizer;
- context gate strength 2.0 and floor 0.10;
- threshold-selection procedure.

The experiment intentionally excludes gravitational smoothing so that the aggregation layer is the only planned mechanism change.

## Development data and split

Use only the fixed 40-item `synthetic_v2` validation manifest.

- Even-index manifest rows `0,2,...,38` are the 20 clean calibration references used only to fit one threshold per variant.
- Odd-index manifest rows `1,3,...,39` are the 20 paired evaluation references.
- The evaluation references are tested clean and under the same-base generated corruptions.

Thresholds are fitted on calibration-clean images only and then frozen for every evaluation condition.

No UDED held-out, BSDS500 test, BIPEDv2 test, or other external-test result may be used to select parameters or reinterpret the comparison.

## Corruptions

Evaluate Gaussian noise, Gaussian blur, periodic texture, and compound corruption at the predeclared severities `0.35`, `0.65`, and `1.0`, yielding 12 corruption family-severity cells.

## Primary metric and promotion criterion

The primary quantity is the **absolute corrupted-performance advantage**:

`F1_dCC_corrupt - F1_standard_corrupt`,

using mean per-image F1 and averaging equally across the 12 corruption cells.

The d-CC hypothesis receives development support only if all three conditions hold:

1. mean absolute corrupted-F1 advantage is at least `+0.005`;
2. clean F1 difference `F1_dCC_clean - F1_standard_clean` is at least `-0.01`;
3. d-CC has positive mean absolute corrupted-F1 advantage in at least three of the four corruption families.

This criterion is intentionally based on absolute corrupted performance rather than only loss relative to each model's own clean baseline, avoiding the possibility that a lower clean baseline appears artificially more robust simply because it has less performance to lose.

## Secondary robustness diagnostic

Also report clean-referenced degradation advantage:

`(F1_corrupt - F1_clean)_dCC - (F1_corrupt - F1_clean)_standard`.

This quantity describes whether d-CC loses less performance relative to its own clean baseline, but it is **secondary** and does not determine promotion by itself.

## Interpretation rule

Meeting the criterion supports only a targeted development claim and requires a separately registered confirmation before d-CC is retained. Failing the criterion means this isolated d-CC/FBPC/absolute-RDF hypothesis is not promoted on these data. Neither outcome is a final external robustness claim.

Primary methodological motivation: Amorim et al. (2025), *Generalizations of Choquet-like Integrals by Restricted Dissimilarity Functions Applied to Multi-Channel Edge Detection Problems*, DOI 10.3390/app152413273.

This preregistration supersedes the earlier Stage-14f criterion paragraph in `EXPERIMENT_HISTORY.md` that used clean-referenced degradation advantage as the primary promotion criterion. The runner `run_stage14f_rdf_robustness.py` implements the criterion stated here.
