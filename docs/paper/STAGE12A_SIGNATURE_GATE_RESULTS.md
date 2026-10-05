# Stage 12a — Fixed-Scharr + context-signature gate

## Purpose

Stage 12a tested the cleanest consequence of the Stage-11b finding: use the discovered edge-v-texture signature as **context**, while keeping Scharr+NMS as the precise localizer.

The experiment deliberately avoided the dynamic localizer. Signature features and gate hyperparameters were selected using the 15-image selection split only; the 15-image held-out split was used once with the frozen selection winner.

## Configuration

Feature mode: `oriented_ms + relational signature`.

The selected context signature was dominated by scale-sensitive Gabor/Hessian evidence and cross-scale relations. The strongest feature was `gabor4_s5` (edge-v-texture AUC 0.7370), followed by `hessian_s7`, `gabor4_fine_coarse_balance`, `gabor4_max`, `hessian_s13`, `gabor4_s13`, Gabor scale persistence/entropy, `grad_max`, and `hessian_mean`.

Sixteen soft gate configurations were screened: multiplicative, centered and exponential modulation with different strengths/floors.

## Result

Baseline Scharr+NMS:

- selection CV F1: **0.7335105**
- selection ODS: **0.7664215**
- held-out precision: **0.6671212**
- held-out recall: **0.8884559**
- held-out F1: **0.7620423**

Selection winner:

`siggate__multiply__a2__floor0.25`

- selection CV F1: **0.7358666**
- selection ODS: **0.7681574**
- selection AP: **0.7697725**

Frozen held-out result:

- precision: **0.6686296**
- recall: **0.8863443**
- F1: **0.7622457**
- delta F1 vs Scharr: **+0.0002034**
- paired-bootstrap 95% CI: **[-0.0013260, 0.0018423]**
- P(delta > 0): **0.5748**

The four other selection-ranked finalists were also effectively tied with Scharr on held-out. None produced a statistically meaningful gain.

## Interpretation

Stage 12a is a useful near-null result rather than a failure of the signature hypothesis.

1. The signature gate no longer causes the large performance loss seen in the monolithic CH-MFI-v2 path. Separating **context** from **localization** restored the Scharr baseline almost exactly.
2. Selection shows a small but consistent preference for stronger modulation (winner: multiplicative strength 2, floor 0.25), but the held-out gain is negligible and the bootstrap CI crosses zero.
3. Precision increased slightly while recall decreased slightly. Therefore the context map behaves mainly as a weak texture suppressor, not as a source of new localization evidence.
4. Qualitatively, the signature highlights object/structural boundaries well, but still lights up substantial internal texture. Because the final gate is smooth and preserves a nonzero floor, the gated Scharr ranking remains very close to the original Scharr ranking. The selection threshold can compensate for much of the modulation, explaining the tiny held-out delta.
5. Stage 11b showed that a linear diagnostic can extract more information from the feature space than the all-positive analytical score. That, together with signed logistic coefficients, motivates testing **non-additive and contrastive/bipolar evidence** rather than simply increasing gate strength.

## Scientific decision

Do not return to the wide CH-MFI sweep and do not reintroduce the dynamic localizer yet.

Proceed to Stage 12b with fixed Scharr and two questions:

1. Can a non-additive fuzzy aggregation of the same edge-signature memberships outperform the weighted analytical average?
2. Is there useful **anti-edge / texture evidence** that should be aggregated separately from positive edge evidence?

The next experiment therefore compares distorted-capacity Choquet aggregation with an optional dual positive/texture evidence path, while retaining the same selection/held-out discipline.
