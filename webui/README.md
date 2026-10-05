# MFI-Edge WebUI

Local research interface for testing deployable MFI-Edge variants on arbitrary images.

## Architecture

- **Frontend:** Next.js/React (`webui/`) — the same style of frontend we can later deploy to Vercel.
- **Inference backend:** FastAPI (`desktop_api.py`) — runs locally because the current MFI pipeline is Python/NumPy/OpenCV.
- **Model registry:** `models/deployable_registry.json`.
- **One-command launcher:** `python run_webui.py` starts both services and opens the browser.

The frontend and inference backend are intentionally separated. The UI can later be hosted on Vercel while the inference service remains local or is moved to a GPU/CPU service.

## First run on Windows

Requirements:

- Python 3.11+ recommended
- Node.js 20+ / npm
- Git

From the repository root:

```powershell
git switch mfi-edge-webui
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-webui.txt
python run_webui.py
```

The launcher installs the Next.js packages automatically on the first run. Then open:

- WebUI: `http://127.0.0.1:3000`
- API docs: `http://127.0.0.1:8000/docs`

To skip automatic `npm install`:

```powershell
python run_webui.py --no-install
```

## What the UI shows

For every uploaded image:

1. original image;
2. MFI attention overlay;
3. a slider over `Σ, 25, 13, 7, 5, 3`, where `Σ` is the multiscale fused confidence;
4. final edge map;
5. final edge overlay;
6. runtime and threshold information.

Multiple files can be processed in one request.

## Comparison mode

The WebUI has two execution modes:

- **single model** — the standard inference view;
- **compare 2–4 models** — side-by-side research view.

Comparison mode is designed for model competition rather than just presentation:

- models are still listed in declared validation-rank order;
- quick buttons select the current Top 2, Top 3 or Top 4;
- the same uploaded image is reused across all selected models;
- conditioning, oriented multiscale features, orientation and Scharr+NMS are computed **once per image**;
- only the model-dependent fuzzy measure, confidence and fusion stages are recomputed;
- one synchronized scale control switches all models together between `Σ, 25, 13, 7, 5, 3`;
- each model column shows validation/held-out metrics, attention overlay, final edge overlay, final mask, threshold mode and model-only runtime.

The corresponding backend endpoint is:

```text
POST /api/compare
```

with a JSON list of 2–4 registry IDs in the multipart field `model_ids`.

## Model ordering

The selector is always sorted from the highest to the lowest **declared validation metric**. The current registry uses **UDED Stage-7 selection ODS**, not post-hoc held-out F1. Both values are shown so the validation/generalization distinction remains visible.

The first registry entries come from `results/uded/stage7/top_selection_compact.csv`. They are labelled `stage7-screened`; this does not imply that they beat Scharr on held-out data.

## Thresholds

A deployable model should ideally contain its frozen validation threshold in `models/deployable_registry.json`.

If `threshold` is `null`, the desktop UI uses an image-adaptive score quantile only for visualization/testing. The UI clearly labels this mode as `adaptive-quantile-*`; it must not be reported as the benchmark's frozen-threshold result.

When `results/uded/stage7/selection_all.csv` is present, `src/deployable_models.py` automatically enriches matching registry entries with the frozen Stage-7 threshold.

## Promoting a new validated model

When a model is accepted experimentally:

1. merge/promote the scientific implementation and reproducible benchmark result to `main`;
2. merge `main` into `mfi-edge-webui`;
3. add/update its entry in `models/deployable_registry.json` with:
   - measure and fusion strategy;
   - exact parameters;
   - validation metric used for ranking;
   - held-out metric for reference;
   - frozen threshold;
   - benchmark/version label;
4. verify it through the WebUI on arbitrary images and, preferably, in comparison mode against the current leading models.

This keeps experimental sweeps out of the selector while making every promoted model immediately testable on the desktop branch.

## Learned measures

The current top Stage-7 entries use built-in local/adaptive fuzzy measures and work without external learned-measure files.

If a future promoted model needs learned capacities, copy/generate:

```text
benchmark_outputs/stage5_measures/learned_measures.json
```

The API will automatically append these learned measure specifications to `measure_registry`.

## Vercel

`webui/` is a conventional Next.js application and can be deployed to Vercel. The local FastAPI server is deliberately separate and is **not** assumed to run inside Vercel. For a hosted deployment, set:

```text
NEXT_PUBLIC_MFI_API=https://your-inference-api.example.com
```

For normal desktop use, no deployment is necessary.
