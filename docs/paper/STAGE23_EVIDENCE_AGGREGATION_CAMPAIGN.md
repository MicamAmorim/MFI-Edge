# Stage 23 — Evidence × Aggregation Landscape and Gap-Guided Non-Neural Improvement

## Purpose

Stage 23 begins after the bounded Stage 22 causal program closed without promotion. Its goal is **not** another local tuning loop around the current compact distorted-Choquet MFI. The campaign first maps the non-neural evidence and aggregation design space, then uses the resulting empirical principles to improve strong non-neural edge detectors by targeting diagnosed gaps.

Primary research questions:

1. Which descriptor/evidence families provide genuinely complementary boundary information?
2. Which aggregation families preserve or exploit each kind of complementarity?
3. Which descriptor–aggregator interactions improve precision, recall, ranking/AP, localization, calibration, and robustness, and which only duplicate existing evidence?
4. Can those learned relationships be used prospectively to improve strong non-neural detectors by adding only the evidence they lack and selecting an aggregation rule justified by the observed interaction structure?

The campaign keeps the final inference path non-neural. Supervised classical detectors may be reproduced as external reference architectures, but supervised GT-derived weights/features must never silently enter the unsupervised/non-neural candidate family.

---

## Non-negotiable cache / reuse contract

Descriptor extraction is expensive and must be treated as a reusable scientific artifact.

### Extract once, reuse everywhere

For a fixed `(dataset, split, image, preprocessing, descriptor implementation, descriptor parameters, code version)` tuple, the descriptor map is computed **once** and then loaded from disk by all later stages. Aggregator experiments must not recompute descriptor maps.

Canonical local cache root:

`cache/local_dev/stage23/`

Recommended layout:

```text
cache/local_dev/stage23/
  descriptors/
    <dataset>/<split>/<descriptor_id>/<cache_key>/<image_id>.npy
  transforms/
    <dataset>/<split>/<transform_id>/<cache_key>/<image_id>.npy
  manifests/
    descriptor_manifest.jsonl
    transform_manifest.jsonl
  locks/
```

The cache is local/runtime data and is intentionally ignored by Git. It must survive ordinary `git pull` operations and controller restarts. On Oracle or another worker, place the repository/cache on persistent storage.

### Cache identity

Every reusable artifact must record enough provenance to prevent silent cache poisoning:

- dataset name and split;
- image identifier plus source hash when practical;
- preprocessing pipeline/version;
- descriptor/transform canonical id;
- all descriptor parameters;
- implementation module/function;
- implementation version or Git commit/hash;
- output shape and dtype;
- artifact SHA-256;
- creation timestamp;
- whether the artifact is raw evidence, normalized evidence, or a derived transform;
- whether any GT information was used (inference evidence must say `false`).

Changing any scientific input creates a **new cache key**. Never overwrite an old map under the same key.

### Recompute policy

If an exact valid cache artifact exists, recomputation is forbidden during ordinary experiments. A cache miss may compute and persist the artifact. A corrupt/mismatched artifact must fail closed and be repaired only by an explicit cache-repair/rebuild action whose reason is recorded.

Where later stages repeatedly use deterministic derived representations (for example a fixed normalization of a raw descriptor), cache those derived maps too rather than regenerating them repeatedly.

### Aggregator outputs

If an aggregated score map will be reused by later diagnostics/evaluators, save it with the same provenance discipline. Do not regenerate a frozen candidate map merely to run another evaluator.

---

## Dataset and publication protocol discipline

### Development / screening

UDED selection remains the fast screening bed where allowed by the existing leakage policy. It is used for descriptor baselines, complementarity analysis, bounded descriptor-set selection, and the descriptor × aggregator landscape. Repeated leakage-free folds are required whenever fitting/selection is involved.

### Literature-comparable validation

Models intended for scientific reporting must also be evaluated on the **author-designated validation/development splits and matched evaluators used by the relevant literature whenever those splits/protocols are available**. The campaign must research and record, method by method:

- dataset/version;
- exact split;
- metric definition;
- matching tolerance;
- annotation treatment;
- resizing/thinning/postprocessing;
- whether the reported number is validation, test, training, or cross-validation;
- whether the original method was supervised, unsupervised/data-estimated, or fixed/untrained.

BSDS500 validation remains the main development-aligned Berkeley track. Literature headline numbers from BSDS500 **test** must not be treated as directly comparable development evidence. If a paper reports only test results, reproduce or evaluate the method on the matched development/validation track first; test is reserved for frozen reporting and cannot drive selection.

### Final frozen multi-dataset evaluation

After the best improved method is selected and frozen, run it unchanged on several diverse datasets/protocols. At least one final benchmark/split should remain genuinely untouched until the frozen method is selected. Final/external outcomes are documentary and cannot trigger further tuning of that frozen generation.

---

## Campaign phases

### 23A — Literature census + protocol/implementation map

Research-planning stage. No detector fitting.

Build a primary-source census of:

1. descriptor/evidence families used by strong non-neural edge/boundary detectors;
2. aggregation families used in edge detection, image fusion, pattern recognition, and related classification contexts when mechanistically relevant;
3. strongest non-neural detector architectures and their exact descriptor stacks;
4. validation/test datasets and evaluator protocols used for published comparisons;
5. author code / faithful implementation availability and licensing.

Descriptor families should be grouped by information type rather than only by algorithm name, e.g. gradient/orientation, color/opponency, Gabor/frequency, Hessian/curvature, texture-distribution, statistical dependence/affinity (PMI-like), changepoint, patch structure, multiscale persistence, region/context, spectral/global cues, and other distinct families found in the literature.

Aggregation families should be grouped by mathematical behavior, including at minimum simple additive controls, order-statistic/rank aggregation, fuzzy integrals/non-additive interaction, idempotent lattice-style families, and conjunctive/disjunctive controls. Exact families are finalized only after the literature census.

Deliverables:

- `docs/paper/STAGE23_DESCRIPTOR_CENSUS.md`
- `docs/paper/STAGE23_AGGREGATOR_CENSUS.md`
- `docs/paper/STAGE23_PROTOCOL_MATRIX.md`
- updates to `docs/paper/STAGE23_LITERATURE_LEDGER.md`
- a bounded preregistered descriptor and aggregator shortlist for the first landscape.

### 23B — Cache infrastructure certification

Implement the content-addressed descriptor/transform cache, manifest validation, hash checks, atomic writes, and read-through reuse API.

Certification must include:

- a tiny deterministic image set;
- first call computes and stores;
- second call loads without invoking extractor;
- byte/hash identity check;
- parameter/preprocessing change creates a distinct key;
- corrupt artifact fails closed;
- no GT path is reachable from inference descriptor extraction.

Do not launch the large landscape until the cache contract is certified.

### 23C — One-time UDED descriptor extraction + individual baselines

Extract every preregistered descriptor needed for the first landscape exactly once on the allowed UDED development images and save the maps.

Then evaluate each descriptor independently using only cached maps. Record at minimum precision, recall, F1, threshold policy, score distribution, support density, and deterministic qualitative previews. Individual weakness does not automatically eliminate a descriptor; a weak descriptor may survive if it has strong unique true-positive evidence.

### 23D — Ground-truth-conditioned complementarity map

Using cached descriptor maps, quantify pairwise and selected higher-order complementarity without re-extraction.

At minimum report:

- score-map correlation/rank correlation;
- TP overlap and unique TP contribution;
- FP overlap and unique FP contribution;
- `P(A correct | B wrong)` and reciprocal form under a preregistered tolerance/matching rule;
- complementarity by precision/recall regime;
- localization support near GT;
- per-image stability;
- redundancy clusters.

The output is a descriptor complementarity matrix/graph and a bounded set of non-redundant descriptor pairs/triples for aggregation screening.

### 23E — Descriptor × aggregator factorial screen on UDED

This is a **bounded factorial landscape**, not an unrestricted powerset search.

Use only cached descriptor evidence from 23C/23D. For the preregistered complementary descriptor sets, compare representative aggregation families under identical inputs and postprocessing. Include simple controls so any Choquet gain can be attributed to non-additive interaction rather than merely averaging multiple cues.

Report not only the winner but the behavioral profile of each cell:

- Δprecision;
- Δrecall;
- ΔF1;
- ranking/AP proxy where valid;
- calibration/score-scale behavior;
- localization behavior;
- robustness/stability across folds/images;
- interaction/synergy indicators.

The scientific target is a relationship of the form:

`evidence structure -> useful aggregation property`

not merely `aggregator X has the highest mean F1`.

### 23F — Literature-comparable validation landscape

Promote only a small preregistered frontier from 23E. Extract the needed descriptor maps **once per new dataset/split** and cache them. Evaluate the frontier under matched validation protocols used by the literature, with BSDS500 validation as the primary Berkeley development track and additional author-designated validation tracks where feasible.

All methods compared on a given table must use protocol-compatible metrics. Keep literature-reported headline numbers separate from local matched-protocol re-evaluations.

This stage should establish which descriptor/aggregator principles survive beyond UDED.

### 23G — Gap-guided improvement of strong non-neural detectors

Select strong non-neural detector architectures from the census. For each target detector:

1. reproduce or faithfully materialize the baseline under a matched development/validation protocol;
2. characterize its existing evidence families;
3. diagnose its error/gap profile against GT and against the Stage-23 evidence map;
4. identify one missing complementary evidence family;
5. choose the aggregation family prospectively from the 23E/23F interaction map;
6. test one bounded intervention while preserving the target detector's strengths;
7. compare baseline vs improved version under the same evaluator.

Do not blindly place Choquet on top of every detector. Choquet remains a privileged hypothesis because of prior MFI evidence, but it must win against appropriate controls under matched inputs.

### 23H — Freeze best improved method + multi-dataset generalization

Once the best improved method is selected from development-authorized evidence, freeze:

- descriptor set and implementations;
- preprocessing;
- aggregation family and parameters;
- localizer/postprocessing;
- calibration;
- thresholds/routing rules;
- software commit and cache provenance.

Then run the frozen method unchanged across several datasets, including at least one untouched external/final evaluation if available. Produce publication-grade tables, confidence intervals where appropriate, deterministic previews, runtime/memory measurements, and protocol provenance.

No post-freeze result may trigger tuning of that frozen generation.

---

## Scientific products / paper structure

The campaign is deliberately capable of producing multiple papers without requiring them all to succeed.

### Paper A — Descriptor–Aggregator Landscape

Core claim if supported: different evidence structures benefit from different aggregation properties, with a reproducible map of complementarity, redundancy, and descriptor × aggregator interactions.

### Paper B — Gap-Guided Improvement of Non-Neural Edge Detectors

Core claim if supported: the landscape can prospectively diagnose a strong detector's missing evidence and select an aggregation strategy that improves it under matched validation protocols.

### Paper C — General Framework

Only if repeated success across multiple detector architectures supports it: a general framework for improving non-neural edge detectors through selective evidence integration.

Use `framework`, `principles`, or `empirical model` before claiming a general theory. A theory-level claim requires repeated cross-architecture and cross-dataset support.

---

## Operational constraints

- Everything reusable is persisted to disk with provenance.
- Descriptor maps are never recomputed simply because a later experiment needs them.
- The agent may create new cache keys for scientifically changed descriptors, but must not mutate old cache identities.
- Large combinatorial searches require preregistration and pruning by complementarity first.
- Protected/test splits never drive descriptor choice, aggregator choice, parameters, architecture, or experiment priority.
- Every image-based experiment still produces deterministic qualitative artifacts.
- Negative results are retained; they contribute to the evidence/aggregation map.
- Literature and code provenance are written to the Stage-23 ledger, not left only in agent logs.
