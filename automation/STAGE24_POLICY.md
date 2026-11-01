# Stage 24 mandatory policy — Evaluation Integrity + Residual/Error Suppression

Stage 24 is prospective and does not rewrite Stage 23 results.

## Hard scientific invariants

1. **Ground truth is native and immutable.** No resize, interpolation, dilation, erosion, skeletonization, blur, or tolerance band may replace the canonical GT used for learning labels.
2. **Tolerance is matcher-only.** Internal UDED evaluation uses maximum-cardinality one-to-one boundary matching with tolerance `0.0075` of image diagonal.
3. **No duplicated TP credit.** Thick/dense predictions cannot match one GT element more than once.
4. **BSDS final development metrics are official.** ODS/OIS/AP for the one-shot BSDS500-validation confirmation come only from `evaluation/bsds_official`. Internal matching must never be labeled Berkeley-equivalent.
5. **Inference geometry is explicit.** Descriptor inference uses max-side 256. Float scores, not GT, are registered back to native evaluation geometry.
6. **Scientific maps are floating point.** Canonical maps are `.npy` float32 with identity/hash sidecars. PNG is allowed only as visualization or terminal official-evaluator adapter.
7. **No quantized-map reuse.** Historical uint8 PNG maps cannot become Stage-24 scientific inputs.
8. **Selection is nested.** Pair, aggregator, suppressor, parameter, and threshold selection occur only inside each outer training fold. Outer validation is untouched until evaluation.
9. **Training target is exact GT.** Distance-derived/tolerant soft targets are separate ablations and cannot silently replace GT.
10. **External confirmation is one-shot.** The UDED-derived model is frozen before BSDS500-validation export; the exporter may not inspect BSDS ground truth.
11. **Protected test data stay protected.** The Stage-24 exporter rejects BSDS `test`.
12. **RNG is deterministic.** Seeds derive from base seed `20261101` plus stage/fold identity.
13. **Cache reuse is fail-closed.** Reuse requires matching source hash, descriptor code hash, preprocessing, inference geometry, dtype, and artifact hash.
14. **Residual terminology is conservative.** False-positive residual responses are not called noise until evidence supports that interpretation.

## Registered campaign

- Base seed: `20261101`
- UDED outer CV: 5 repeats × 3 folds
- Inference geometry: max-side 256
- Canonical scientific artifact: float32 `.npy`
- Stop sentinel: `automation/STOP_STAGE24`

## Bounded residual families

The screen contains identity control, local-coherence suppression, cue-disagreement compression, monotone weak-response compression, and a learned contextual residual gate. The learned gate uses train-fold exact GT only. Oracle GT-distance gates are diagnostic-only and ineligible for selection.

## Literature transfer

A literature detector may enter Stage 24 only through float-preserving author/native maps or a fresh float-preserving materialization. Legacy quantized PNG detector maps are explicitly rejected as scientific inputs; this rule may not be bypassed for convenience.
