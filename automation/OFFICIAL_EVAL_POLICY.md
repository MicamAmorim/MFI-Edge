# Official BSDS evaluation policy

This policy governs the optional MATLAB module under
`evaluation/bsds_official/`. It is injected into every autonomous Codex
decision.

## Purpose and separation

The official evaluator is a **post-experiment analysis module**, not part of
the MFI-Edge inference path. Normal Python experiments must remain runnable
without MATLAB. When the module is available, it runs after an image experiment
has produced its normal result and before Codex decides what to do next.

The module uses the original Berkeley BSDS multi-annotator boundary-evaluation
logic (`evaluation_bdry_image`, `collect_eval_bdry`, `correspondPixels`) under
MATLAB. Do not replace its ODS/OIS/AP with the historical Python
consensus/dilation proxy when making matched-protocol claims.

## Dataset roles

From this policy revision onward:

- **BSDS500 validation (`val`) is a development/model-selection split.**
  Official MATLAB ODS/OIS/AP on this split may be used by the agent as
  development evidence.
- **BSDS500 train** may be used only when a future experiment explicitly
  preregisters how it participates in fitting/CV.
- **BSDS500 test remains protected/document-only.** It has already been
  inspected historically and must never guide feature choice, architecture,
  hyperparameters, thresholding, routing, or experiment priority.
- Historical UDED-heldout/BIPED-test/BSDS-test restrictions remain unchanged.

Using BSDS validation for repeated architecture selection makes it development
data; it cannot later be described as untouched evidence. Final generalized
claims still require the project gate and at least one genuinely untouched
external benchmark.

## Default development protocol

Unless an experiment-specific preregistration justifies otherwise, official
BSDS validation evaluation uses:

- all human boundary annotations from the original `.mat` ground truth;
- original `correspondPixels` one-to-one spatial matching;
- `nthresh = 99`;
- `maxDist = 0.0075` of image diagonal;
- morphological thinning enabled;
- native-resolution input images;
- soft boundary maps in `[0,1]`, exported as 8-bit PNG without per-image
  normalization.

The MATLAB executable configured for the current workstation is
`C:\Program Files\MATLAB\R2023a\bin\matlab.exe`. `MATLAB_EXE` may override it
locally.

## Manifest contract for new image experiments

Every **new image-based development experiment** must emit
`official_eval_manifest.json` next to its normal `summary.json` unless it is
genuinely non-image/non-inference research or cannot produce a frozen soft map
for a documented technical reason.

Minimal form:

```json
{
  "schema_version": 1,
  "split": "val",
  "include_incumbent": true,
  "methods": [
    {
      "name": "candidate_name",
      "export": {
        "script": "path/to/repository_local_exporter.py",
        "args": [
          "--image-dir", "{image_dir}",
          "--output-dir", "{output_dir}",
          "--split", "{split}"
        ]
      }
    }
  ]
}
```

The exporter must not read BSDS validation/test ground truth, fit parameters
from those annotations, or choose a per-image normalization from the result.
It must reconstruct the candidate using only training/development information
allowed by its preregistration, then infer on the supplied images.

The controller evaluates both the retained incumbent and the candidate and
injects official metrics plus deltas into the Codex decision prompt.

## How the agent may use validation metrics

BSDS-validation ODS/OIS/AP are decision-capable **aggregate development
metrics**. The agent may use them to:

- reject or promote a preregistered candidate;
- identify a cross-dataset trade-off versus UDED development;
- choose a mechanistically justified next family when a candidate transfers
  poorly.

The agent must not silently turn validation into direct pixel-level training.
Do not inspect individual BSDS validation annotations/error maps to handcraft a
feature, fit a threshold, or micro-tune a parameter after seeing the result.
Prefer bounded hypotheses, preregistration, and cross-dataset agreement.

A useful candidate need not improve every metric, but promotion criteria must
be stated before result inspection and should prioritize ODS together with
precision/recall balance and AP rather than chase a single decimal.

## Protected-split firewall

If a manifest requests `test`, the module refuses by default. A deliberately
authorized protected evaluation must set `allow_protected=true`, and the
result is still marked `feedback_allowed=false`. Codex may document or compare
that result to a **previously frozen** success criterion but may not redesign
from it.

## Evaluator provenance

The module pins source commits rather than following moving branches:

- BIDS/BSDS500 mirror commit
  `a04b7c6c3a9f0ace74bf205c72a43d32e1c72722`;
- Piotr Dollár `edges` commit
  `94260b5d0fc068202598312e01a37604972dcc9e`, used on Windows only to supply
  the compatible `correspondPixels.mexw64`.

Downloaded third-party code lives under the ignored local `vendor/` directory;
our repository contains only wrappers/configuration. Do not edit the vendored
benchmark to improve MFI-Edge scores.

The module records `reference_reproduction_verified=false` until a known
reference result has been reproduced with this exact local MATLAB environment.
Development metrics may guide development before that check, but **no final
SOTA claim** may rely on the evaluator until reference reproduction is
verified.
