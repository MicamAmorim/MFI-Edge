# MFI-Edge local research autopilot

This loop replaces the manual cycle:

`run .bat -> send results -> receive next code -> git pull -> run next .bat`.

The PC remains the compute worker. Codex is invoked **only after an experiment finishes or fails**, returns one structured decision, edits the workspace if needed, and exits. It is not kept alive while benchmarks run.

## First use

Requirements:

- Git repository on branch `mfi-edge-local-dev`;
- Python environment used by MFI-Edge;
- Codex CLI installed and logged in (`codex --version` should work).

From the repository root:

```powershell
git switch mfi-edge-local-dev
git pull
.\run_research_autopilot.bat
```

The launcher starts with `stage13a_bsds_transfer`. The controller itself runs `git pull --ff-only`, so after the first setup you normally launch only the autopilot.

## Cost behavior

No model call is made while a long benchmark is running. One `codex exec` call occurs only after a result is ready. The default reasoning effort is `low`; leave `MFI_CODEX_MODEL` unset to use the model configured in your Codex CLI.

Optional model override:

```powershell
$env:MFI_CODEX_MODEL = "<model available in your Codex CLI>"
.\run_research_autopilot.bat
```

## Safety / scientific integrity

The controller:

- executes only experiment IDs registered in `automation/experiments.json`;
- accepts only repository-local Python scripts or `.bat` launchers;
- reloads the allow-list after every Codex edit;
- refuses automatic commits if Codex changes protected scientific files;
- runs `git diff --check` and Python syntax checks on edited `.py` files;
- commits/pushes Codex edits itself; Codex is instructed never to commit/push;
- persists state and logs under ignored `automation/runtime/`;
- refuses to rerun completed experiments marked `one_shot`;
- enforces the dataset feedback policy carried by each experiment.

For Stage 13a, `feedback_policy=document_only_no_tuning`: BSDS500 test may be documented, but it may not tune the frozen Stage-12d model. A legitimate next autonomous step is an independent frozen replication such as BIPED, or implementation of an official evaluator without model tuning.

## Stop / resume

Stop before the next action by creating:

```powershell
New-Item automation\STOP -ItemType File
```

Resume:

```powershell
Remove-Item automation\STOP
.\run_research_autopilot.bat
```

State is preserved in `automation/runtime/state.json`.

Start over deliberately:

```powershell
.\run_research_autopilot.bat --reset-state
```

Run only one experiment + one Codex analysis:

```powershell
.\run_research_autopilot.bat --once
```

Run the experiment without calling Codex:

```powershell
.\run_research_autopilot.bat --no-codex
```

Preview the first command without running it:

```powershell
.\run_research_autopilot.bat --dry-run
```

Keep commits local:

```powershell
.\run_research_autopilot.bat --no-push
```

## How a new iteration is created

After a run, Codex receives only a compact event summary plus the paths of the generated files. It may read those local files, update code/docs, and register exactly one next experiment in `automation/experiments.json`. Its final message must conform to `automation/decision.schema.json`.

If the next experiment is registered and `continue=true`, the Python controller runs it automatically. Otherwise the loop stops safely.

## Files

- `research_controller.py` — orchestration, budgets, execution, Codex calls and Git validation.
- `config.json` — branch, budgets, reasoning effort, protected files and push behavior.
- `experiments.json` — allow-listed experiment registry and dataset-feedback policy.
- `CODEX_POLICY.md` — scientific and operational rules supplied to every Codex call.
- `decision.schema.json` — structured response contract.
- `runtime/` — ignored local logs/state/prompts/answers.
