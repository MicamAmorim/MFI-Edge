# MFI-Edge WebUI branch

This branch contains the **desktop/web qualitative inspection interface** for MFI-Edge.  It is intentionally separate from the broad experimental branch so that only intentionally promoted models appear in the normal selector.

## Branch role

```text
mfi-edge-local-dev
      -> validated configuration
      -> main
      -> mfi-edge-webui deployable registry
```

The project-wide roadmap is maintained on `main`:

https://github.com/MicamAmorim/MFI-Edge/blob/main/ROADMAP.md

Detailed WebUI instructions: **[`webui/README.md`](webui/README.md)**.

## Quick start

```powershell
git fetch
git switch mfi-edge-webui
git pull
.\run_webui.bat
```

Default services:

```text
WebUI:    http://127.0.0.1:3000
FastAPI:  http://127.0.0.1:8000
API docs: http://127.0.0.1:8000/docs
```

## What the UI supports

- one or multiple uploaded images;
- single-model inference;
- 2–4 model side-by-side comparison;
- models listed in declared validation-rank order;
- fused and per-scale MFI attention heatmaps;
- synchronized scale slider across compared models;
- final edge mask and overlay;
- threshold/runtime metadata;
- reuse of shared preprocessing/features across compared models.

The WebUI is for qualitative diagnosis and deployment-style inspection.  Official model ranking remains the responsibility of the benchmark pipelines.

## Current synchronization status

The deployable registry currently represents intentionally exported/promoted experimental models.  New CH-MFI-v2 families under active development in `mfi-edge-local-dev` should **not** be copied into the selector merely because they exist; they should be added after their selection protocol, frozen threshold and benchmark result are recorded.

## Development branches

- `main` — stable/reproducible line;
- `mfi-edge-local-dev` — current CH-MFI-v2 model research;
- `mfi-edge-webui` — this interface;
- `experiment/uded-railway` — historical/server-side UDED experiment line.

See `webui/README.md` for architecture, endpoints, model-registry rules and Vercel/frontend notes.
