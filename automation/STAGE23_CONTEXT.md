# Stage 23 compact context

Stage 22 is complete and closed. Compact distorted-Choquet MFI remains incumbent. Stage 20C remains a useful diagnostic comparator because it improved BSDS validation ODS/OIS while losing AP.

Stage-22 causal conclusions to carry forward:

- fixed spatial offset is not the dominant AP explanation;
- useful contextual evidence exists; wholesale context weakness is not the main explanation;
- local NMS/competition was not dominant under the preregistered Stage-22D attribution;
- inter-image calibration showed a real diagnostic association but the single preregistered positive-support quantile calibration failed transfer badly and is rejected;
- human-consensus ordering remained weak;
- thesis-legacy evaluation is compatible as a separate longitudinal bridge, not a promotion metric.

The new campaign therefore changes the unit of study. Instead of repeatedly modifying the incumbent, Stage 23 maps:

`descriptor/evidence family × aggregation family × error/benefit profile`

and then uses that map to make prospectively justified interventions in strong non-neural detectors.

User-directed operational requirements:

1. Descriptor maps and every reusable deterministic intermediate must be computed once per exact provenance key and saved to disk.
2. Later stages must import cached maps rather than recomputing them.
3. Scientific reporting must include matched validation/development protocols used by relevant literature whenever available, not only internal UDED screening.
4. After selecting the best improved method, freeze it and run it unchanged on several additional datasets/protocols.
5. The campaign should be portable to a remote CPU worker (Oracle Cloud is the planned first option) for descriptor extraction and factorial screening; MATLAB-specific official Berkeley evaluation may remain a separate local attachment.
6. Choquet remains an important hypothesis because of prior results, but the campaign must compare it against representative alternative aggregation families under identical evidence inputs.

Stage 23A is complete. Primary-source and official-code review froze a first
pool of 13 evidence maps spanning eleven information families and eight
aggregation behaviors. The exact census and bounds are in
`docs/paper/STAGE23_DESCRIPTOR_CENSUS.md`,
`docs/paper/STAGE23_AGGREGATOR_CENSUS.md`, and
`docs/paper/STAGE23_PROTOCOL_MATRIX.md`. Complete detectors remain later
reproduction/intervention targets rather than hidden descriptor inputs.

Stage 23B passed every conjunctive cache certification check. Exact-key reuse
avoided extractor calls, scientific changes made distinct keys, manifests and
artifact hashes agreed, corruption failed closed, GT-declared inference was
rejected before computation, and atomic writes left no temporary file.

Stage 23C completed on the 14-image overlap-clean UDED selection set without
reading the excluded protected-lineage item. All 182 frozen descriptor maps
were computed once, persisted, and then exactly reloaded with valid manifests;
all 13 non-selective repeated-CV baselines and the positions 1/7/14 preview
completed. The individual scores are descriptive and did not prune the pool.

Stage 23D completed with 182 exact cache hits, zero computations, all 78 pair
rows, and no protected-lineage byte read. Its prospective rule froze eight
cross-family pairs, four triples, the incumbent five-cue anchor, and the single
controls `semiglobal_changepoint` and `halfdisc_distribution_contrast`.
Compact MFI remains unchanged; the incumbent-only BSDS attachment supplied no
candidate-selection evidence.

The active next task is
`stage23e_cached_descriptor_aggregator_landscape`. It compares exactly the
eight frozen aggregation behaviors over only those Stage-23D sets, using shared
outer-fold memberships and exact cached maps. Algebraic aliases are labeled,
not counted as independent wins. The fixed rule in
`docs/paper/STAGE23E_PREREGISTRATION.md` may forward at most three primary
cells plus their equal-mean controls to Stage 23F. Stage 23E cannot read a BSDS
candidate result, promote a detector, or alter compact MFI.

Stage 23E completed all 120 nominal cells with 182 exact cache hits and zero
computations. Its frozen rule selected three primary relationships: minimum
conjunction for persistence plus structure-tensor coherence, nonnegative
logistic additive fusion for persistence plus half-disc contrast, and median
OWA for FH boundaries plus half-disc contrast plus tensor coherence. Each
advances only with its matched equal-mean control; compact MFI is unchanged.

Stage 23F completed its scientific inference surface: all four required
descriptor families were extracted once for 100 BSDS500-validation images, all
400 descriptor and 600 aggregate requests were cached, the six frozen map sets
and fixed positions 1/50/100 preview are complete, and validation GT was not
used by inference. The required official evaluator timed out after preserving
complete nonempty match tables for the incumbent and three frontier cells plus
part of the next cell. No partial metric is interpreted.

Retry 1 reached the six-hour limit after completing the fifth method,
`stage23f_pair_04_equal_arithmetic_mean`, and preserving the first nonempty
per-image table for `stage23f_triple_04_median_owa`. No complete six-cell table
or transfer interpretation exists.

Retry 2 also reached the six-hour limit. The first five frontier methods remain
complete, while `stage23f_triple_04_median_owa` still has only one nonempty
per-image table and its matched equal-mean control has not started. No complete
six-cell table or transfer interpretation exists.

A cross-retry infrastructure bug was identified before allowing retry 3 to
continue unchecked: the legacy Python evaluator deleted each method output
directory on entry, so retries restarted already-completed methods even though
the MATLAB wrapper itself could resume nonempty per-image tables within one
process lifetime. The corrected runner
`evaluation/bsds_official/run_official_bsds_resume.py` now preserves completed
method directories, fingerprints frozen predictions plus evaluator provenance,
skips complete methods, resumes partial methods from their existing nonempty
`*_ev1.txt` tables, regenerates only cheap aggregate summaries when needed, and
fails closed on provenance mismatch. The Stage-23 policy now makes this
checkpoint-preserving behavior mandatory for all long-running deterministic
jobs.

Retry 3 stopped before any evaluator work because the new checkpoint-preserving
runner could not resolve its sibling `run_official_bsds` module. This is a
harness-only import defect and supplies no scientific feedback. The runner now
adds its own directory to the module search path explicitly.

Stage 23F is complete. None of the three UDED-selected aggregation advantages
transferred conjunctively against its matched equal mean. Minimum conjunction
on persistence plus tensor coherence improved ODS/OIS by
`+0.05909/+0.03196` but reduced AP by `-0.04275`. Nonnegative logistic
addition on persistence plus half-disc contrast improved ODS/OIS by
`+0.02954/+0.00925` but reduced AP by `-0.00793`. Median OWA on the
FH/half-disc/tensor triple changed ODS/OIS/AP by
`-0.01403/-0.03972/-0.10468`. No cell is promoted or backfilled; compact MFI
remains incumbent and Berkeley reference reproduction remains unverified.

Stage 23G selected exact author-code SED as the strong non-neural target. It is
the strongest exact strictly untrained matched-validation reference already
materialized on both development domains. Its primary architecture already
contains color opponency, oriented Gaussian derivatives, V1 multiscale
surround, V2 texture suppression, shape feedback, and author NMS, but no
explicit opposed-region distribution comparison. The single missing-family
hypothesis is therefore the cached half-disc distribution-contrast evidence,
which Stage 23D found weak individually but low-redundancy and uniquely
supportive across families. This is a gap hypothesis, not a claim that the
failed Stage-23F half-disc relationship transferred.

The active task is `stage23g1_sed_halfdisc_gap_diagnosis`. It runs no detector
or descriptor extractor: it hash-validates exact frozen SED maps and loads the
114 exact Stage-23 half-disc cache artifacts on overlap-clean UDED selection
and BSDS500 validation. A frozen cross-domain rule tests unique GT rescue,
conditional correctness, image stability, and rank nonredundancy. Only a full
pass may later authorize a separately preregistered equal-mean control using
the already frozen Stage-23F membership transform. Failure closes this route
without target/cue substitution. Compact MFI remains incumbent.

Stage 23G1 is complete. It used zero detector runs, zero descriptor
computations, and 114 exact cache hits. All four gap conditions passed on
overlap-clean UDED, but BSDS500-validation mean conditional correctness was
`0.38056`, below the frozen `0.50` requirement; the other three BSDS
conditions passed. The conjunctive rule therefore rejects the missing-family
hypothesis. No SED/half-disc equal-mean intervention is authorized, and the
route closes without cue or target substitution. Compact MFI remains incumbent
and Berkeley reference reproduction remains unverified.

The active next task is the already registered repeatable
`stage23_literature_escalation`. It is planning-only and must preserve the
Stage-23F/G1 negative evidence, score no dataset, avoid reopening or tuning the
SED/half-disc route, and choose at most one prospectively justified distinct
Stage-23 action or close the campaign path if none exists.
