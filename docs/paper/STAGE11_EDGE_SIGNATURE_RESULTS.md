# Stage 11 edge-signature results — first UDED run

Status: **diagnostically useful, but superseded for scale-sensitive conclusions by Stage 11b**.

The first signature-discovery run used the historical `oriented` descriptor mode on the UDED 15-image selection / 15-image held-out split.  GT was used only to label diagnostic populations; the candidate signature itself was frozen from selection and evaluated on held-out.

## Main result

The selection-frozen analytical signature generalized in the correct direction:

| Score | Selection AUC | Selection AP | Held-out AUC | Held-out AP |
|---|---:|---:|---:|---:|
| analytical signature | 0.6263 | 0.4233 | **0.6613** | **0.4372** |

This is evidence that the descriptor space contains a reproducible edge-vs-hard-negative signal, but the signal is only moderate.  It is not sufficient by itself to claim a competitive detector.

## What the first signature learned

The selected eight properties were:

1. `gabor4_s7`
2. `gabor4_s13`
3. `grad_s7`
4. `fine_vs_coarse_gradient`
5. `gabor4_max`
6. `normal_contrast_max`
7. `gradient_scale_persistence`
8. `normal_tangent_ratio`

Approximately 39% of the analytical weight fell on three Gabor-derived terms (`gabor4_s7`, `gabor4_s13`, `gabor4_max`), so the first signature is not yet a compact semantic decomposition of edge structure.

The strongest edge-vs-texture single-property result was Gabor at the fine nominal scales (AUC separation about 0.722 on selection).  By contrast, edge-vs-near-edge discrimination was much harder: the best individual properties were only around 0.59 AUC separation.  This supports the architectural interpretation that the signature is currently more useful as **texture rejection/context** than as the final edge localizer.

The sign of `normal_tangent_ratio` was negative in the selected analytical fit.  This is a useful warning not to hard-code the intuitive assumption that every true boundary must have a larger version of every directional descriptor.  Stage 12 should derive memberships from empirical direction/stability rather than semantic intuition alone.

## Critical diagnostic finding: nominal 3/5/7 scales partially collapsed

Post-analysis of `signature_samples_compact.npz` found **22 exact duplicate descriptor/scale column pairs** in the historical feature mode.  In particular, windows 3, 5 and 7 produced exactly identical sampled values for several important descriptors, including:

- gradient;
- Laplacian;
- Hessian;
- normal contrast;
- normal-minus-tangent;
- steered Hessian;
- Gabor4;
- and some additional 3/5 coherence duplication.

This explains why several rows in the first cross-scale AUC plot were identical across 3/5/7 and why the earlier scale-capacity analysis found near-identical fine-scale banks.

### Root cause

The historical `oriented` implementation intentionally remains frozen for reproducibility, but its parameter floors/clips make fine windows share effective parameters:

- Gaussian smoothing used `sigma=max(0.8, window/12)`;
- Gabor frequency used `min(0.25, 2/window)`;
- normal/tangent sampling used minimum radii 1.0 and 1.5;
- other local-statistic floors similarly collapse some fine scales.

At windows 3/5/7, these schedules often reduce to the same effective operator.

This is not a reason to discard Stages 3--10; those results remain valid for the implementation that was actually tested.  It **is** a reason not to interpret those three nominal windows as three independent physical scales.

## Stage 11b correction

A new backward-compatible `oriented_ms` mode has been added.  It keeps the same eight descriptor semantics but uses genuinely distinct scale schedules for smoothing, directional sampling, structure-tensor integration and Gabor frequency.  The historical `oriented` mode is untouched.

Before Stage 11b signature discovery, run `audit_multiscale_features.py`.  It writes a reproducible old-vs-new duplicate audit.  Then rerun the same signature protocol with `analyze_gt_edge_signatures_ms.py`.

The Stage 11b launcher is:

```powershell
.\run_stage11_signature.bat
```

It now performs both the scale audit and the corrected signature analysis, including the small logistic diagnostic upper bound.

## Scientific decision

**Do not yet build Stage 12 around the first candidate signature.**

Proceed to Stage 12 only after the `oriented_ms` rerun answers:

1. whether the analytical signature still generalizes;
2. whether edge-vs-texture and edge-vs-near-edge separation improve;
3. whether the selected feature set becomes less redundant;
4. how much better a simple learned linear upper bound is than the analytical membership score.

If the corrected analytical signature remains stable, Stage 12 will treat it as image-derived context/evidence and test it as a fuzzy/analytical controller of a precise localizer rather than as a supervised end-to-end detector.
