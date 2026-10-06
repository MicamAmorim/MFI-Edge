# Official BSDS evaluation policy v2

This policy governs the default-on auxiliary MATLAB module under
`evaluation/bsds_official/`. It is injected into every autonomous Codex
decision.

## Purpose and separation

The official evaluator is a **post-experiment analysis module**, not part of
the MFI-Edge inference path. The detector remains Python and must remain
runnable without MATLAB. When MATLAB is available, every new image-based
development experiment is expected to attach official BSDS500-validation
metrics before Codex decides whether to promote or reject the candidate.

The module uses the original Berkeley BSDS multi-annotator boundary-evaluation
logic (`evaluation_bdry_image`, `collect_eval_bdry`, `correspondPixels`) under
MATLAB. Do not replace its ODS/OIS/AP with the historical Python
consensus/dilation proxy when making matched-protocol claims.

The current workstation MATLAB executable is:

`C:\Program Files\MATLAB\R2023a\bin\matlab.exe`

`MATLAB_EXE` may override it locally.

## Dataset roles

- **BSDS500 validation (`val`) is development/model-selection data.** Official
  MATLAB ODS/OIS/AP on this split may be used by the autonomous agent.
- **BSDS500 train** may be used only when an experiment preregisters how it
  participates in fitting/CV.
- **BSDS500 test remains protected/document-only.** It must never guide feature
  choice, architecture, hyperparameters, thresholding, routing, or experiment
  priority.
- Historical UDED-heldout/BIPED-test/BSDS-test restrictions remain unchanged.

Repeated use of BSDS validation explicitly converts it into development data.
It must never later be described as untouched external evidence.

## Default official protocol

Unless a preregistration explicitly requires a different author-designated
protocol, BSDS validation uses:

- every human boundary annotation from the original `.mat` ground truth;
- original `correspondPixels` one-to-one spatial matching;
- `nthresh = 99`;
- `maxDist = 0.0075` of image diagonal;
- morphological thinning enabled;
- native-resolution images;
- soft boundary maps written as **8-bit PNG in [0,255] without per-image
  normalization**, matching the original evaluator's
  `double(imread(inFile))/255` convention.

The benchmark thresholds are therefore the original fixed 99-point grid in
(0,1), not the project's historical quantile threshold grid.

## Default-on manifest contract

Every newly registered image-based development experiment must emit
`official_eval_manifest.json` next to its normal `summary.json`, unless it is
truly non-image research or cannot reconstruct a frozen inference map for a
documented technical reason.

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

The exporter must reconstruct the candidate from allowed development state and
must not read BSDS validation/test ground truth, fit parameters from those
annotations, normalize per image from GT, or select thresholds from the target
split.

The controller evaluates the retained incumbent and the candidate, stores the
MATLAB result under `results/official_eval/<experiment>/`, and injects the
metrics and deltas into the Codex decision prompt.

## Decision semantics

If official evaluation has `status=completed` and `feedback_allowed=true`, the
agent **must** use ODS/OIS/AP jointly with the experiment's primary UDED or
synthetic metrics. The official validation metrics are not decorative.

A candidate must not be promoted as the new benchmark-aligned incumbent when a
required official validation evaluation is missing or failed. A MATLAB/network
failure does **not** invalidate the underlying scientific experiment and must
not trigger a benchmark rerun; instead the evaluator/export attachment is
retried/repaired and the same result remains pending.

Cross-dataset promotion should prefer candidates with directionally consistent
benefit. A small UDED regression may be acceptable only when preregistered and
when the official BSDS-validation improvement is substantial, reproducible,
and mechanistically interpretable. Do not change the promotion rule after
seeing the metrics.

## Protected-split firewall

If a manifest requests `test`, the module refuses by default. Deliberately
authorized protected evaluation requires `allow_protected=true`; the result is
still marked `feedback_allowed=false`. Codex may document it or check a
previously frozen success criterion but may not redesign from it.

## Evaluator provenance and reproducibility

The module pins source commits rather than following moving branches:

- BIDS/BSDS500 mirror commit
  `a04b7c6c3a9f0ace74bf205c72a43d32e1c72722`;
- Piotr Dollár `edges` commit
  `94260b5d0fc068202598312e01a37604972dcc9e`, used on Windows to supply the
  compatible `correspondPixels.mexw64`.

Downloaded third-party code lives under the ignored local `vendor/` directory;
our repository contains only wrappers/configuration. This avoids silently
modifying or redistributing third-party evaluator code. Do not edit vendored
benchmark files to improve MFI-Edge scores.

The module records `reference_reproduction_verified=false` until a known
reference detector result has been reproduced with this exact MATLAB/MEX
installation. Development metrics may guide development before that check, but
**no final SOTA claim** may rely on the evaluator until reference reproduction
is verified.

## Human-opinion analysis

The official metric must remain unchanged. Auxiliary research may additionally
construct annotator-agreement maps, interval-valued memberships, or reliability
analyses from BSDS train/validation annotations, provided the role is
preregistered. These analyses must never replace official ODS/OIS/AP in SOTA
comparisons.
