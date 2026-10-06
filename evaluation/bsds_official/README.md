# Official BSDS500 MATLAB evaluation module

This directory adds a **post-experiment evaluator** without changing the normal
Python MFI-Edge pipeline.

## What it does

For image-based development experiments that emit `official_eval_manifest.json`:

1. the research controller finishes the normal Python benchmark;
2. this module exports native-resolution soft boundary maps;
3. MATLAB runs the original Berkeley multi-annotator boundary evaluation;
4. ODS/OIS/AP and deltas versus the retained incumbent are written to
   `results/official_eval/<experiment_id>/summary.json`;
5. those metrics are injected into the Codex decision prompt.

The configured workstation MATLAB is:

`C:\Program Files\MATLAB\R2023a\bin\matlab.exe`

`MATLAB_EXE` overrides the configured path if needed.

## Scientific split policy

`val` is development/model-selection data and its official metrics may guide
the autonomous agent. `test` is protected and is never run automatically.
See `automation/OFFICIAL_EVAL_POLICY.md`.

## Benchmark provenance

The module bootstraps pinned third-party sources on first use into the ignored
`vendor/` directory:

- BIDS/BSDS500 at
  `a04b7c6c3a9f0ace74bf205c72a43d32e1c72722`;
- Piotr Dollár `edges` at
  `94260b5d0fc068202598312e01a37604972dcc9e`.

On Windows the latter supplies the compatible `correspondPixels.mexw64`. The
actual evaluation calls the original Berkeley `evaluation_bdry_image.m` and
`collect_eval_bdry.m`; our `.m` file is only a Windows-safe wrapper.

First use may therefore download the pinned benchmark code plus the requested
BSDS split. Later runs reuse the local vendor checkout and cached incumbent
predictions.

## Manifest

A candidate runner must write this next to its normal `summary.json`:

```json
{
  "schema_version": 1,
  "split": "val",
  "include_incumbent": true,
  "methods": [
    {
      "name": "candidate_name",
      "export": {
        "script": "run_candidate.py",
        "args": [
          "--export-bsds",
          "--image-dir", "{image_dir}",
          "--output-dir", "{output_dir}",
          "--split", "{split}"
        ]
      }
    }
  ]
}
```

The exporter must create one soft PNG per BSDS JPG, with the same stem. It must
not inspect BSDS ground truth. The module checks for complete output before
calling MATLAB.

See `manifest.example.json`.

## Failure behavior

The official evaluator is configured `report_and_continue`: a missing MATLAB,
MEX, toolbox, network bootstrap, or malformed candidate export is recorded in
the official-evaluation summary but does not erase the completed Python
experiment. The agent receives the failure metadata and may repair evaluator
infrastructure without rerunning the benchmark.

The current autonomous-research controller also falls back from live web search
to indexed/disabled search and finally normal Codex, so a transient search
service failure no longer ends the research loop.

## Final-claim guard

The module records `reference_reproduction_verified=false` until a known
reference output has been reproduced locally. Validation metrics are useful for
development immediately, but final SOTA claims remain blocked until that
reference check and the project's multi-benchmark gate are both satisfied.
