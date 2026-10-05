# MFI-Edge WebUI

Local research interface for testing and comparing deployable MFI-Edge variants on arbitrary images.

Project-wide priorities and model-generation status are maintained in the canonical roadmap on `main`:

https://github.com/MicamAmorim/MFI-Edge/blob/main/ROADMAP.md

## Architecture

- **Frontend:** Next.js/React (`webui/`).
- **Inference backend:** FastAPI (`desktop_api.py`) using the repository's Python/NumPy/OpenCV MFI-Edge implementation.
- **Deployable model registry:** `models/deployable_registry.json`.
- **Launcher:** `run_webui.py` starts both services and opens the browser.
- **Windows shortcut:** `run_webui.bat` creates/uses `.venv`, installs Python requirements, then launches the app.

The frontend and inference backend are intentionally separated. The Next.js frontend can later be hosted on Vercel while inference remains local or is moved to a public CPU/GPU API.

## Current branch

Use the dedicated desktop branch:

```powershell
git fetch
git switch mfi-edge-webui
git pull
```

## Requirements

- Python 3.11+ recommended
- Node.js 20+ / npm
- Git

## Fastest first run on Windows

From the repository root, double-click or run:

```powershell
.\run_webui.bat
```

The batch file:

1. creates `.venv` if it does not exist;
2. activates it;
3. installs `requirements-webui.txt`;
4. lets `run_webui.py` install the Next.js packages on the first run;
5. starts the FastAPI backend and Next.js frontend;
6. opens the WebUI in the browser.

Default endpoints:

- WebUI: `http://127.0.0.1:3000`
- API docs: `http://127.0.0.1:8000/docs`
- API health: `http://127.0.0.1:8000/api/health`

## Manual first run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-webui.txt
python run_webui.py
```

Useful launcher options:

```powershell
python run_webui.py --no-install
python run_webui.py --no-browser
python run_webui.py --api-port 8001 --web-port 3001
```

`--no-install` skips `npm install` when `webui/node_modules` is absent, so use it only after the frontend dependencies are already installed.

## Single-model mode

For each uploaded image the UI displays:

1. original image;
2. fused MFI attention overlay (`Σ`);
3. attention overlays for windows `25, 13, 7, 5, 3`;
4. synchronized attention-scale slider/tabs;
5. final binary edge map;
6. final edge overlay on the original image;
7. threshold value and threshold mode;
8. runtime information;
9. downloadable edge mask and edge overlay.

Multiple images can be uploaded in one request. The API currently accepts up to **64 images per request**.

The single-model backend endpoint is:

```text
POST /api/infer
```

## Comparison mode

The WebUI can compare **2 to 4 models side by side** on the same image or image batch.

Comparison mode is intended for model competition and qualitative diagnosis:

- models remain listed in declared validation-rank order;
- quick controls select the current Top 2, Top 3 or Top 4;
- image resize, Median3 conditioning, oriented multiscale features, gradient orientation and Scharr+NMS are computed **once per image**;
- the prepared image/features are reused by every selected model;
- only the model-dependent fuzzy measure, MFI confidence and fusion stages are recomputed;
- one synchronized attention control switches every model between `Σ, 25, 13, 7, 5, 3`;
- each model column displays validation and held-out metrics, attention overlay, final edge overlay, final mask, threshold mode and model-specific runtime;
- shared preprocessing time is reported separately.

The comparison backend endpoint is:

```text
POST /api/compare
```

It expects a multipart `model_ids` field containing a JSON list (or comma-separated fallback) of 2–4 deployable registry IDs.

## Model ordering

The selector is sorted from highest to lowest **declared validation metric**. The current Stage-7 registry is ordered by **UDED selection ODS**, not post-hoc held-out F1.

Both Selection ODS and Held-out F1 are displayed so that validation performance and generalization remain distinguishable.

The current Stage-7 entries are experimental screened models. Their presence in the WebUI does **not** mean they statistically outperform Scharr on held-out data.

CH-MFI-v2 variants currently under development in `mfi-edge-local-dev` must not be copied into the normal selector merely because they exist.  They should be promoted only after the selection rule, frozen threshold and held-out result are preserved.

## Thresholds and benchmark fidelity

A deployable model should ideally contain the exact frozen validation threshold used by its benchmark.

If a registry entry has `threshold: null`, the desktop UI falls back to an image-adaptive score quantile **for visualization and exploratory testing only**. This mode is explicitly reported as:

```text
adaptive-quantile-...
```

A result produced with that fallback must not be reported as the frozen-threshold benchmark result.

When `results/uded/stage7/selection_all.csv` is available in the checkout, `src/deployable_models.py` automatically enriches matching Stage-7 registry entries with the exported frozen threshold.

## Attention maps

The attention view contains:

- `Σ`: final fused multiscale MFI confidence;
- `25`: attention from the 25×25 scale;
- `13`: attention from the 13×13 scale;
- `7`: attention from the 7×7 scale;
- `5`: attention from the 5×5 scale;
- `3`: attention from the 3×3 scale.

The WebUI renders attention both as heatmaps and as heatmap overlays on the input image. These maps are diagnostic representations of MFI confidence/ranking; they are not calibrated posterior probabilities unless a future model explicitly provides that calibration.

## Promoting a new validated model

When a new model is accepted experimentally:

1. complete the model-selection protocol in `mfi-edge-local-dev`;
2. preserve exact code/config, validation metric, frozen threshold and held-out/test result;
3. promote/merge the scientific implementation and reproducible benchmark result to `main`;
4. merge/sync the relevant inference code into `mfi-edge-webui`;
5. add or update its entry in `models/deployable_registry.json` with:
   - model family/stage;
   - measure;
   - fusion/controller strategy;
   - exact parameters;
   - validation metric and protocol used for ranking;
   - held-out/test metric for reference only;
   - frozen threshold;
   - benchmark/result path;
6. verify the model in single mode;
7. compare it side by side against the current leading models;
8. update the project roadmap.

This keeps the thousands of exploratory sweep configurations out of the normal selector while making promoted variants immediately testable.

## Learned measures

Built-in local/adaptive measures work directly from the source code.

A promoted model that depends on learned capacities must ship or document the exact learned artefact required for reproduction.  Historical Stage-5 models may use:

```text
benchmark_outputs/stage5_measures/learned_measures.json
```

Future CH-MFI models may additionally require promoted versions of regime/scale learned artefacts; those files should enter the WebUI branch only together with a validated model entry.

## Vercel / hosted frontend

`webui/` is a conventional Next.js application and can be deployed as a frontend on Vercel. The current FastAPI inference server is separate and is **not** expected to execute inside Vercel.

For a hosted frontend, configure:

```text
NEXT_PUBLIC_MFI_API=https://your-inference-api.example.com
```

The inference API must be reachable from the user's browser and its CORS configuration (`MFI_WEB_ORIGINS`) must allow the frontend origin.

For ordinary desktop use, no cloud deployment is required.

## Research-use caveats

The WebUI is an inference/inspection tool, not a replacement for the benchmark scripts. In particular:

- do not rank models by post-hoc test/held-out performance;
- do not treat adaptive-quantile visualization output as a frozen-threshold benchmark;
- use the benchmark pipeline for official ODS/OIS/AP/F1 reporting;
- keep the model registry limited to configurations we intentionally promote for inspection/deployment;
- keep the roadmap synchronized whenever the promoted model generation changes.
