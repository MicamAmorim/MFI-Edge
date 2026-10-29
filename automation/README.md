# MFI-Edge local research autopilot — Stage 23

Stage 23 starts after the bounded Stage 22 program closed. The active campaign is defined in:

- `docs/paper/STAGE23_EVIDENCE_AGGREGATION_CAMPAIGN.md`
- `automation/STAGE23_POLICY.md`
- `automation/STAGE23_CONTEXT.md`
- `automation/research_goal.json`
- `docs/paper/STAGE23_LITERATURE_LEDGER.md`

The active controller is `automation/research_controller_v5.py` and the active experiment registry is `automation/stage23_experiments.json`.

## Campaign idea

The campaign maps:

`descriptor/evidence family × aggregation family × error/benefit profile`

before using that map to improve strong non-neural edge detectors by diagnosed gaps. Choquet remains an important hypothesis but is no longer assumed to be the best aggregator.

## Cache-first rule

Descriptor maps and every reusable deterministic intermediate are persistent scientific artifacts.

Canonical cache root:

`cache/local_dev/stage23/`

For an exact provenance identity, compute once and reuse thereafter. Ordinary later stages must not silently re-extract a descriptor or regenerate a reusable transform. Scientific changes create new cache keys. Corrupt or provenance-mismatched artifacts fail closed.

`src/stage23_cache.py` implements the content-addressed array cache. Stage 23B certifies exact-key reuse, distinct scientific keys, corruption detection, and the GT-leakage guard before large extraction is allowed.

The cache is ignored by Git, so normal pulls do not delete it. On a remote worker such as Oracle Cloud, keep the repository/cache on persistent storage.

## Launch

Requirements:

- Git;
- the repository Python environment;
- Codex CLI installed and logged in (`codex --version`);
- branch `mfi-edge-stage23`.

From the repository root in PowerShell:

```powershell
git fetch origin
git switch mfi-edge-stage23
git pull --ff-only
Remove-Item automation\STOP -ErrorAction SilentlyContinue
.\run_research_autopilot.bat --reset-state
```

`--reset-state` is intentional when moving from the completed Stage-22 controller state to the new Stage-23 registry.

The first action is Stage 23A, a high-reasoning/live-web research checkpoint. It performs no benchmark scoring. It builds the descriptor census, aggregator census, protocol matrix, and literature ledger, then proceeds to the cache certification before any large image extraction.

## Stop / resume

Stop before the next action:

```powershell
New-Item automation\STOP -ItemType File
```

Resume:

```powershell
Remove-Item automation\STOP -ErrorAction SilentlyContinue
.\run_research_autopilot.bat
```

Run one experiment plus one Codex analysis:

```powershell
.\run_research_autopilot.bat --once
```

Preview the first command without executing it:

```powershell
.\run_research_autopilot.bat --dry-run --reset-state
```

## Dataset / reporting discipline

UDED selection is the fast screening bed under the existing leakage policy. Publication-oriented candidates must also be tested on author-designated validation/development splits and matched evaluators used by relevant literature whenever available. BSDS500 validation remains the main development-aligned Berkeley track.

Protected/final test outcomes may be reported only after freezing and may not drive descriptor choice, aggregator choice, thresholds, parameters, architecture, routing, or experiment priority.

After the best improved method is selected and frozen, it is run unchanged across multiple diverse datasets/protocols, including at least one genuinely untouched external/final evaluation when feasible.
