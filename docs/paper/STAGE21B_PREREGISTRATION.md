# Stage 21B preregistration — three-protocol frozen-map retrospective

## Role and frozen inputs

Stage 21B is the first scientific result of Stage 21, but it fits and promotes
no detector. It reads only BSDS500 validation and the exact serialized maps
already produced for compact MFI and Stage 20A--20D. Every input PNG is hashed
before scoring. Missing, duplicate, dimension-mismatched, or non-identical
100-image manifests stop the run; no map may be regenerated or substituted.

The methods are reported in this fixed order: incumbent compact distorted-
Choquet MFI, Stage 20A, Stage 20B, Stage 20C, and Stage 20D.

## Three non-interchangeable tracks

1. `berkeley_standard`: pinned Berkeley all-annotation matching with
   `nthresh=99`, `maxDist=0.0075`, and `thinpb=true`. Report ODS/OIS/AP,
   ODS/OIS precision and recall, and the complete threshold PR table.
2. `berkeley_maxdist_0p025_sensitivity`: the identical implementation and
   settings with only `maxDist=0.025`. Report the same fields and paired
   deltas from Track 1.
3. `estrada_jepson_0p025_fuzzy_comparison`: the hash-pinned KITT v1.00 backup
   matcher certified in Stage 21A, renamed byte-identically only for MATLAB
   loading. Use all annotations, `0.025` image-diagonal distance, KITT's union
   machine matches and accumulated annotation recall, and equal-weight F.
   Evaluate the fixed serialized threshold `0.5` and the fixed 99-threshold
   grid `0.01,...,0.99`; report fixed and best-grid P/R/F separately.

The KITT result is best-public-source fidelity, not proof of equivalence to an
unpublished private evaluator. The two 0.025 tracks must never be conflated.
Neither can promote a model. Berkeley results retain
`reference_reproduction_verified=false` and the Stage-15a RNG caveat.

## Outputs and stop rule

The run must emit the four CSV tables named by the Stage-21 program, complete
PR tables for both Berkeley tracks and the Estrada--Jepson grid, hashes and
provenance, a JSON and Markdown summary, and `best_method_preview.png` from
sorted validation positions 1, 50, and 100. The preview columns are input,
annotation union, incumbent, 20A, 20B, 20C, and 20D; it is documentary only.

Completion authorizes Stage 21C only. Any scoring or artifact failure permits
only an attachment/harness repair over the same frozen bytes and protocols.
No scientific parameter, map, threshold grid, or Stage-20 model may change.
