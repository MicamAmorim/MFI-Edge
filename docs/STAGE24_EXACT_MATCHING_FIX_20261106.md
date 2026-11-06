# Exact matching runtime correction — 2026-11-06

The 37-hour stall was reproduced for Di Zenzo NMS on native UDED imagery.
The restricted 8-neighbour matching certificate stalled; bypassing it exposed a
second slow maximum_bipartite_matching case on 13-BIPED-1C. Neither is retained.
The full Euclidean radius graph now uses unit-capacity maximum flow (Dinic):
source -> prediction -> GT -> sink, all capacities one. This computes exactly
the same maximum-cardinality one-to-one metric. GT, thresholds and NMS unchanged.

Validation: all 55 selected regressions passed, including independent random
bipartite graph oracle and serial/parallel threshold equivalence. The actual
Di Zenzo NMS train fold completed 27 matchings (3 thresholds x 9 native images)
in an approximately 8-second standalone process including loading/preparation.
No claim that every future graph has bounded runtime is made.

scripts/migrate_stage24_exact_solver_fix.py accepts only the previous reviewed
matcher and a pinned hash of the new implementation. It verifies all other
source hashes, refuses unsupported group checkpoints, backs up the original
fingerprint, records checkpoint SHA256 values, and updates only the reviewed
matcher entry. Saved individual checkpoints remain byte-identical.
