# MFI-Edge SOTA target ledger

This is the living comparison ledger for the long-horizon goal: an interpretable **non-neural** edge/boundary detector that surpasses the strongest verified neural-network methods under matched official protocols and generalizes across datasets.

Do not copy leaderboard numbers without checking the primary paper/repository and evaluation protocol. Refresh this ledger at literature-escalation checkpoints and immediately before any `goal_reached=true` decision.

## Rules for entries

For each target benchmark, record:

- dataset and exact split;
- official/author-designated evaluator;
- primary metric(s) and tolerance/matching protocol;
- strongest verified neural result found in current literature;
- primary source DOI/URL and publication date;
- date the literature search was refreshed;
- whether code/evaluator is available;
- MFI-Edge frozen-generation result under the same protocol;
- whether that MFI result was obtained without target-test-driven tuning.

Do not compare numerically incompatible protocols as if they were the same benchmark. In particular, the local BSDS tolerant-dilation proxy is not the official Berkeley bipartite/CSA++ evaluation.

## Generalization success gate

The project may set `goal_reached=true` only when all of the following are true:

1. The candidate inference path contains **no neural network or neural feature extractor**.
2. The SOTA literature search has been refreshed from primary sources close to the final evaluation date.
3. A frozen MFI-Edge generation exceeds the strongest verified neural result on the predeclared primary metric for a **multi-benchmark suite of at least three diverse edge/boundary datasets** under matched official or author-designated protocols.
4. At least one benchmark in that final suite is genuinely untouched at the moment the frozen generation is selected.
5. No benchmark/test result in the final suite is used to tune that frozen generation.
6. Results include uncertainty or repeated-run information where the benchmark permits it, plus runtime/complexity reporting.
7. Qualitative output panels are saved for every benchmark so the numerical gain can be visually inspected for boundary quality, localization, texture suppression, continuity, and failure modes.

If a benchmark's strongest neural result cannot be verified under a matching protocol, mark the target `UNRESOLVED` rather than treating a weak or incomparable number as the bar.

## Target table

| Benchmark / split | Official primary metric | Strongest verified neural result | Method / source | Protocol match verified? | Literature refreshed | Frozen MFI-Edge result | Status |
|---|---|---:|---|---|---|---:|---|
| BSDS500 test, single definite output, SS-VOC | ODS F1 after NMS; author protocol uses 0.0075 diagonal tolerance | 0.849 ODS (OIS 0.869, AP 0.899) | SAUGE-L, [AAAI 2025 primary paper](https://ojs.aaai.org/index.php/AAAI/article/view/32615) | Source-side protocol verified; local official/author evaluator not yet established | 2026-10-06 | — | OPEN TARGET |
| BSDS500 test, raw-map crispness-emphasized evaluation (CEval) | ODS/OIS/AP without NMS or thinning; AC also reported | 0.854 ODS for SAUGE+MatchED | MatchED, [CVPR 2026 / arXiv primary paper](https://arxiv.org/abs/2602.20689) | Distinct raw-output protocol; not interchangeable with standard SEval | 2026-10-06 | — | OPEN TARGET |
| NYUDv2 RGB test (654), author protocol | ODS F1; 0.011 diagonal tolerance | 0.794 ODS (OIS 0.803, AP 0.813), zero-shot from BSDS/VOC | SAUGE-L, [AAAI 2025 primary paper](https://ojs.aaai.org/index.php/AAAI/article/view/32615) | Source-side protocol verified; local evaluator/data role not yet predeclared | 2026-10-06 | — | OPEN TARGET |
| Multi-Cue edge, author 3x random 80/20 protocol | Mean ODS F1 over three splits; 0.0075 tolerance | 0.905 ODS (OIS 0.907, AP 0.939), single definite output | SAUGE, [AAAI 2025 primary paper](https://ojs.aaai.org/index.php/AAAI/article/view/32615) | Author protocol verified; exact random splits/evaluator must be recovered before matching | 2026-10-06 | — | OPEN TARGET |
| BIPED, author-designated test | ODS/OIS under author edge-evaluation protocol | 0.906 ODS multi-granularity; strongest fixed single output in the same paper is 0.903 | EDMB*, [WACV 2025 primary paper](https://openaccess.thecvf.com/content/WACV2025/html/Li_EDMB_Edge_Detector_with_Mamba_WACV_2025_paper.html) | Multi-granularity result uses best-candidate selection and is not a single deployable map; local historical fixed-F1 diagnostic is incomparable | 2026-10-06 | — | OPEN TARGET |

## October 2026 protocol notes

- The primary GED preprint (arXiv:2410.03080) reports BSDS500
  ODS/OIS/AP `0.870/0.880/0.907`, NYUDv2 ODS `0.800`, and Multi-Cue edge ODS
  `0.910`. Its model is explicitly granularity-conditioned and described as
  producing controllable multiple predictions, while no official code was
  exposed in the sources checked. EasyControlEdge (arXiv:2602.16238) marks its
  GED rows as an independent reimplementation and obtains BSDS SEval ODS
  `0.859`, not `0.870`. Therefore the GED headline is an **UNRESOLVED
  FRONTIER** rather than silently replacing the current matched single-map
  rows: recover the exact fixed granularity/output-selection and evaluator
  protocol before using it as a final bar.
- EasyControlEdge reports BSDS500 SEval ODS `0.857` and CEval ODS `0.807`
  (K=5), NYUDv2 SEval ODS `0.791`, and BIPED SEval ODS `0.908` with CFG. Its
  CEval result does not exceed the separately listed MatchED CEval target, and
  its guidance/inference-step variants must not be conflated with one frozen
  single-output setting.
- Multi-granularity results are a separate protocol family. MuGE reports BSDS500
  ODS 0.861 under MS-VOC with best matching among granularity candidates, and
  SAUGE reports 0.859 under SS-VOC with 11 candidates. These oracle-style
  candidate-selection numbers are not interchangeable with a single frozen
  output and are not silently used as the single-map target.
- The authors' official DDN/EDMB repository now reports BSDS500 ODS 0.867 for
  DDN using the same multi-granularity strategy
  (https://github.com/Li-yachuan/EDMB). The peer-reviewed DDN article is
  DOI 10.1016/j.neucom.2025.129442, but the accessible primary article text
  describes the original single-output result (ODS 0.836) rather than this
  later repository update. Treat 0.867 as an author-repository
  multi-granularity frontier note, not as the frozen single-map target, until
  its exact candidate-selection protocol is fully documented.
- MatchED reports both standard evaluation (NMS plus thinning) and CEval on raw
  predictions. Its CEval target is listed separately because applying MFI-Edge's
  NMS/linking output to that row would be a protocol mismatch.
- MS2Edge (DOI 10.1016/j.patcog.2025.112883) claims current SOTA across BSDS500,
  NYUDv2, BIPED, PLDU, and PLDM. The accessible primary abstract and official
  repository did not expose its complete numeric tables during this refresh.
  Therefore no headline number from a secondary summary is allowed to replace
  the verified targets above; its exact protocol/metric entries remain
  `UNRESOLVED` pending primary full-table verification.
- These rows refresh the target frontier; they do not predeclare the final
  three-benchmark suite. Dataset availability, untouched status, evaluator
  reproducibility, and license constraints must be settled before a frozen
  generation is taken to final evaluation.

## Historical external diagnostics that are **not** final SOTA gates

- BSDS500 local proxy evaluation: useful transfer evidence only; not official Berkeley metric.
- BIPEDv2 already-inspected test: useful historical frozen-transfer evidence only; unavailable for new model selection and not a genuinely untouched final benchmark anymore.
- UDED held-out: historically inspected; unavailable for optimization and not a fresh final external benchmark.

These can be reported in the paper history, but they cannot by themselves satisfy the final generalization gate.

## Visual evolution record

Each future image-based experiment should save `best_method_preview.png` using fixed/predeclared examples. When an incumbent is promoted, preserve the old preview and add the new one rather than overwriting historical evidence. The paper record should reference the qualitative artifacts for important generations.
