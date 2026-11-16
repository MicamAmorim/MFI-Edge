# Paper A — finishing plan (honest gates, no invented confirmation)

**Status:** pipeline code installed; not a scientific freeze, not journal-ready.
The user may run the central PowerShell launcher repeatedly. It uses the
previously certified 56 UDED caches without reprocessing any detector maps.

## Milestone A — development-only fitted parameter export

Source: 14 known Stage24 UDED discovery images only. These have already
been exposed to exploratory hypothesis selection, so any fitted model is
**development**, never new confirmatory evidence.

Optional command after explicit authorization to open ONLY those development GT:

```powershell
.\.venv\Scripts\python.exe scripts\fit_paper_a_development_uded14.py --authorize-uded-development-gt
```

The script requires all 56 original float caches/sidecars to exist and
match the historical provenance; it does not regenerate missing maps.
It fits one shared sigmoid membership for each hypothesis, a three-input
generalized Choquet capacity and Möbius coefficients for H2, and four
development-only thresholds (candidate/control per H1/H2) using existing
Stage24 matching/NMS. Model fitting uses no BIPED or MultiCue GT.

Produces an export and a recipe suffixed `_UNATTESTED.json` on F:.
Those parameter values are **not** promoted automatically. Fitting may
use the UDED-14 data only if their scene lineage does not overlap the
proposed confirmatory cohort; known MultiCue capture 4113 is held.
Every `no_confirmatory_overlap_attested` stays null until independently
verified against the final cohort and training source hashes. The
parameter-fit module is research code and must pass validation tests.

## Milestone B — certify dataset semantics and independent units

Use only pre-outcome metadata/images to resolve previously known UDED
exposure, duplicate source content, near duplicates and scene/capture
dependence for BIPEDv2 and MultiCue. MultiCue 4113 must remain excluded.
Do not silently pick 150/180/220 just because synthetic power looks high.
Choose the minimum important effect, eligible domain composition, GT task
`edges` versus `boundaries`, annotation decoding, empty masks and missing
data rules before any confirmatory F1 inspection.

Prepare `frozen_cohort_manifest.csv` with the exact eight columns in
`docs/paper_a_confirmation/candidate_manifest.template.csv` and
explicit `pass` reviews. Every scene_group must be unique **per domain**
for the current independence contract; otherwise adjust unit/collapsing
policy before freezing.

## Milestone C — immutable prospective freeze

An independent reviewer signs scientific lineage, H2 capacity,
thresholds, scene independence, annotation semantics, N and test.
Update protocol.json to `frozen` through a reviewed Git commit before
opening confirmation GT. Create local `freeze_approval.json` with
reviewer, timestamp, frozen Git SHA, and SHA256 of protocol, fixed recipe
and cohort CSV. The launcher creates only a template with all approvals
false. Never auto-fill this template with true.

## Milestone D — confirmatory image-to-paired-outcome executor

**Not implemented/certified yet.** Needs an audited BIPED/MultiCue original
image and GT decoder, deterministic descriptor-map extraction or verified
reusable content caches, fixed H1/H2 membership and Choquet inference,
fixed per-operator thresholds, native-geometry NMS and exact one-to-one
matching per annotation. It must produce *one* X1/Y1/X2/Y2 row per
independent capture in `certified_outcomes.csv` and independently signed
`certified_outcomes_provenance.json` with actual CSV SHA and source commit.
GT may only be opened after Milestone C. Report a negative outcome even
if both predicted associations fail.

## Milestone E — statistics, manuscript, reproducibility

Once milestones A–D are certified, the one-command launcher automatically
runs signed domain-blocked Spearman tests with 100000 permutations,
Holm across H1/H2 and stratified bootstrap confidence intervals.
It writes a result supplement, a scientific draft for independent review
and a SHA-manifested ZIP, rather than claiming accepted publication.

## Safety / status

- No stage launches old Stage24 reprocessing or expensive 2700-pair rescans.
- GT for the prospective cohort stays closed before a valid freeze.
- Training output is deliberately not independently attested by the fitter.
- A green unit test is a code test, not proof of scientific hypothesis.
- The article may legitimately conclude **H1/H2 NOT CONFIRMED**.
- Independent numerical review, references, figures and submission styling
  are necessary after the final outcomes are computed.

**One-line launcher:**

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_finish_paper_a.ps1
```
