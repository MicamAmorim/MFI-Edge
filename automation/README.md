# MFI-Edge local research autopilot — Stage 15

This loop replaces the manual cycle:

`run .bat -> send results -> receive next code -> git pull -> run next .bat`.

The PC remains the compute worker. Codex is invoked **only after an experiment finishes or fails**, returns one structured decision, edits the workspace if needed, and exits. It is not kept alive while benchmarks run.

## Research generations

The exploration-first agent through Stage 14u is frozen at:

- branch: `archive/research-agent-v14u-2026-10-07`
- commit: `fd5d060db1bec40e6697141c55e61b616f4d7b28`

The active reproduction/diagnostic generation is:

- branch: `mfi-edge-stage15`
- agenda: `docs/paper/STAGE15_RESEARCH_PROGRAM.md`
- transition review: `docs/paper/NONTRAINED_EDGE_METHODS_REVIEW_1986_2026.md`
- decision-source ledger: `docs/paper/STAGE15_LITERATURE_LEDGER.md`
- previous-generation snapshot: `docs/paper/AGENT_GENERATION_V14_SNAPSHOT.md`

Stage 15 deliberately pauses open-ended architecture invention through Stage 15o. The agent must first audit protocol, reproduce strong non-trained methods, and analyze error complementarity. Architecture-changing MFI experiments are conditional from Stage 15p onward.

## First Stage-15 launch

Requirements:

- Git repository switched to `mfi-edge-stage15`;
- Python environment used by MFI-Edge;
- Codex CLI installed and logged in (`codex --version` should work).

From the repository root:

```powershell
git fetch origin
git switch mfi-edge-stage15
git pull --ff-only
Remove-Item automation\STOP -ErrorAction SilentlyContinue
.\run_research_autopilot.bat --reset-state
```

`--reset-state` is intentional for the generation transition. The scientific history is preserved in Git/docs; the old runtime cursor should not decide the first Stage-15 experiment.

The Stage-15 configuration starts at the registered `autonomous_literature_escalation` checkpoint. Because the Stage-15 program is injected as the active research agenda on every decision, the first high-reasoning/live-web analysis must begin with Stage 15a protocol/reproduction planning rather than inventing a Stage-14v-style mechanism.

## Cost behavior

No model call is made while a long benchmark is running. One `codex exec` call occurs only after a result is ready. Normal experiment decisions use the configured medium reasoning; literature/research checkpoints use high reasoning with live-web fallback. The default model is configured in `automation/config.json`.

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
- enforces the dataset feedback policy carried by each experiment;
- injects the Stage-15 agenda, scientific context, SOTA ledger and official-evaluation policy into decisions.

### Stage-15 bibliography rule

Literature is scientific input, not disposable prompt context. When a paper/code/protocol materially causes a decision, the agent must preserve it in `docs/paper/STAGE15_LITERATURE_LEDGER.md` in the same change that preregisters the experiment, and synchronize `docs/paper/BIBLIOGRAPHY_MATRIX.md` when the source belongs in the future manuscript. DOI/official URL, protocol role, implementation fidelity and training status must be recorded.

A literature-driven Stage-15 experiment with no corresponding ledger entry is incompletely preregistered.

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
.\run_research_autopilot.bat --dry-run --reset-state
```

Keep commits local:

```powershell
.\run_research_autopilot.bat --no-push
```

## How a new iteration is created

After a run, Codex receives a compact event summary plus the paths of generated files, the persistent scientific context, the current Stage-15 research agenda, official-evaluation policy and SOTA target ledger. It may read local files, update code/docs, and register exactly one next experiment in `automation/experiments.json`. Its final message must conform to `automation/decision.schema.json`.

For Stage 15, a literature-driven preregistration must also update the Stage-15 literature ledger. Stages 15a–15o are reproduction/diagnostic work and must not opportunistically redesign MFI-Edge.

If the next experiment is registered and `continue=true`, the Python controller runs it automatically. Otherwise the v4 controller routes soft stops back through the autonomous literature checkpoint unless there is a real hard blocker or the final goal is reached.

## Files

- `research_controller_v4.py` — active orchestration layer.
- `config.json` — active branch, budgets, research agenda, protected files and push behavior.
- `experiments.json` — allow-listed experiment registry and dataset-feedback policy.
- `CODEX_POLICY.md` — global scientific and operational rules supplied to every Codex call.
- `SCIENTIFIC_CONTEXT.md` — compact persistent cross-iteration scientific memory.
- `docs/paper/STAGE15_RESEARCH_PROGRAM.md` — active Stage-15 campaign and preregistered ordering constraints.
- `docs/paper/STAGE15_LITERATURE_LEDGER.md` — paper/code/protocol-to-decision provenance.
- `decision.schema.json` — structured response contract.
- `runtime/` — ignored local logs/state/prompts/answers.
