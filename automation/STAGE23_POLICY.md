# Stage 23 campaign-specific controller policy

This policy supersedes conflicting generic automation instructions on branch `mfi-edge-stage23`.

## Registry override

For Stage 23, the active experiment registry is:

`automation/stage23_experiments.json`

Any generic instruction referring to `automation/experiments.json` as the active registry is historical for this branch. Register exactly one next Stage-23 experiment in `automation/stage23_experiments.json` unless a bounded preregistered batch is explicitly authorized by the Stage-23 agenda.

## Primary campaign agenda

Read and obey:

- `docs/paper/STAGE23_EVIDENCE_AGGREGATION_CAMPAIGN.md`
- `docs/paper/STAGE23_LITERATURE_LEDGER.md`
- `automation/STAGE23_CONTEXT.md`
- `automation/research_goal.json`
- the general `automation/SCIENTIFIC_CONTEXT.md`

Stage 22 is closed. Do not reopen Stage 22, tune its rejected calibration transform, or register a Stage 22F.

## Cache-first rule — mandatory

Everything reusable must be persisted to disk. Descriptor extraction is a one-time operation per exact cache identity.

Canonical cache root: `cache/local_dev/stage23/`.

For any descriptor/derived transform/aggregated map that later stages may reuse:

1. compute a content/provenance key from dataset/split/image, preprocessing, descriptor/transform id, parameters, implementation version/hash, and relevant code version;
2. check for an exact valid cache artifact before computation;
3. if valid, load it and do not call the extractor;
4. if missing, compute once, save atomically, hash it, and append/update manifest metadata;
5. if corrupt or provenance-mismatched, fail closed; do not silently overwrite;
6. a scientific change creates a new cache key rather than mutating the old artifact.

Aggregator screens must consume cached descriptor maps. They must not re-extract descriptors merely because a new aggregator or evaluator is being tested.

If a deterministic derived normalization/transform is reused more than once, cache it too. If a candidate score map is reused by multiple evaluators/diagnostics, persist the frozen map and reuse it.

Do not commit large cache artifacts to Git. Commit code, manifests/specification schemas, small provenance summaries, and scientific results only.

## Checkpoint/resume rule — mandatory

Long-running deterministic work must be restartable from the last valid persisted unit. A retry is a continuation, not a fresh experiment.

For evaluators, descriptor jobs, aggregate-map generation, dataset-wide diagnostics, and any other multi-item process that may exceed a controller/runtime limit:

1. persist each completed atomic unit as soon as it is valid;
2. before processing an item, test whether an exact provenance-matched valid artifact already exists;
3. if it exists, reuse it and skip computation;
4. if a job is interrupted, the next retry must resume only missing/invalid units;
5. never delete or overwrite valid completed work merely because a new process/retry has started;
6. derived summaries may be regenerated from preserved atomic outputs, but the expensive atomic outputs themselves must remain immutable;
7. attach an identity/provenance record to resumable output directories and fail closed on identity mismatch;
8. logs must distinguish `skip complete`, `resume partial`, and `compute new` so repeated work is auditable.

A runner that claims to be resumable but clears its output directory or recomputes already valid units violates Stage-23 policy.

## Literature / descriptor / aggregator census

Stage 23A is a real research-planning stage. Use high reasoning plus live web research. Prefer primary papers, official author repositories, and official benchmark documentation.

Map:

- evidence/descriptor families used by strong non-neural detectors;
- aggregator families used in image processing, fusion, edge detection, and related classification contexts when mechanistically relevant;
- strong non-neural detector architectures and exact evidence stacks;
- validation/test datasets and evaluators used in the literature;
- source code availability, license, and reproduction fidelity.

Do not choose descriptors merely because they are easy to implement. Prefer coverage of mechanistically distinct evidence families and descriptors actually implicated in strong classical/non-neural methods.

Do not assume Choquet is best. Include simple additive controls and other mathematically distinct aggregation families so gains can be attributed to interaction structure rather than to combining multiple cues per se.

## Factorial-search discipline

The campaign is not an unrestricted powerset search.

Required ordering:

1. descriptor census;
2. cache certification;
3. one-time descriptor extraction;
4. individual descriptor baselines;
5. GT-conditioned complementarity/redundancy map;
6. bounded complementary descriptor sets;
7. descriptor × aggregator screen;
8. literature-comparable validation frontier;
9. gap-guided improvement of strong non-neural detectors;
10. frozen multi-dataset evaluation.

Prune by redundancy/complementarity before higher-order combinations. Preserve negative cells in the scientific record.

## Dataset / protocol rules

- Development choices may use only development-authorized data under existing leakage rules.
- `UDED held-out` remains non-optimization evidence.
- `BSDS500 test`, `BIPEDv2 test`, and any inspected final/test split must not drive descriptor, aggregator, parameter, architecture, or experiment-priority choices.
- BSDS500 validation is a development-comparable Berkeley track under the existing official-evaluation policy.
- For scientific comparison, research and reproduce the author-designated validation/development splits and evaluator settings used by relevant literature whenever available.
- If a literature paper reports only test metrics, keep those headline values separate from local development/validation re-evaluation. A test result cannot select the model.
- After the best improved method is selected and frozen, evaluate it unchanged on multiple datasets, with at least one genuinely untouched external/final benchmark if feasible.

## Ground-truth analysis

GT may be used only under the declared development role and must never leak into inference evidence.

Complementarity analysis should quantify, where feasible:

- score/rank correlation;
- TP/FP overlap;
- unique TP/FP support;
- conditional correctness such as `P(A correct | B wrong)`;
- localization support near GT;
- precision/recall regime differences;
- per-image stability;
- redundancy clusters.

The goal is to learn `evidence structure -> useful aggregation property`, not merely rank methods by one scalar score.

## Strong-detector intervention rule

When Stage 23 reaches gap-guided detector improvement:

- reproduce/validate the target detector first;
- diagnose what evidence it already contains;
- identify a missing complementary evidence family from the Stage-23 map;
- choose the aggregation family prospectively from prior Stage-23 evidence;
- test a bounded intervention under the same evaluator;
- do not blindly attach Choquet to every detector.

## Publication artifacts

Every image-based experiment still requires deterministic qualitative output. Publication-grade stages must retain per-image/per-fold data, evaluator provenance, runtime/memory where practical, and enough frozen metadata to reconstruct tables without rerunning descriptor extraction.

## Oracle / remote-worker portability

Stage-23 cache and runners should be portable to a Linux CPU worker such as Oracle Cloud. Avoid unnecessary Windows-only assumptions in newly written descriptor/aggregation code. MATLAB-dependent official Berkeley evaluation may remain a separate local attachment; descriptor generation and factorial screening should not require MATLAB unless a specific author implementation makes that unavoidable.
