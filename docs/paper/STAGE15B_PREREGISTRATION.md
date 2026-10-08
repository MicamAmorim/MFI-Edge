# Stage 15b preregistration — exact SED reproduction

Status: registered before BSDS500-validation map generation or matched scoring.

## Question and scope

Stage 15b asks what Akbarinia and Párraga's full Surround-modulation Edge
Detection (SED) model obtains under the repository's common BSDS500-validation
path. This is a reproduction/baseline stage. It does not promote SED into
MFI-Edge, modify the retained architecture, or authorize architecture work
before Stage 15p.

## Primary sources and classification

- Akbarinia & Párraga, *Feedback and Surround Modulated Boundary Detection*,
  IJCV 126 (2018), 1367–1380, DOI `10.1007/s11263-017-1035-5`.
- Official author repository:
  `https://github.com/ArashAkbarinia/BoundaryDetection`, pinned at commit
  `11514b80162e5cd93fd244515189649656105a14`.

The method is classified **strictly untrained with fixed author parameters**.
The paper states that the same fixed parameters were used across its datasets
and that no supervised large-dataset learning is used. The paper reports
BSDS500 colour ODS/OIS/AP `0.71/0.74/0.74`; those test-set values remain
literature-only and are stored separately from our validation result.

## Implementation fidelity

The registered candidate is the unmodified author MATLAB full-model entry
point `SurroundModulationEdgeDetector.m`. The repository states that manuscript
F-measures came from the MATLAB implementation; its C++ implementation was used
only for timing. The author MATLAB source is hash-checked at the pinned commit.
Our adapter may only:

1. enumerate native-resolution input JPGs in sorted order;
2. call the author entry point once per image;
3. verify finite, same-size, single-channel output in `[0,1]`;
4. serialize the already-normalized author response directly as rounded 8-bit
   PNG without any additional normalization; and
5. record provenance and runtime.

The author code itself performs its published opponent-channel construction,
multiscale V1 surround processing, V2 processing, feedback-equivalent channel,
intrinsic normalization, and NMS. No detector parameter, source line,
threshold, postprocessor, or image size may be changed after results are seen.

The author repository contains no explicit license file at registration time.
Therefore it is an ignored, locally fetched dependency and its source is not
copied into or redistributed by this repository. This does not change the
scientific fidelity label.

## Dataset and evaluation protocol

- Dataset: all 100 BSDS500 validation images, native resolution.
- Role: development/matched-protocol reproduction; not untouched evidence.
- Detector access to GT: none.
- Official attachment: all human annotations, 99 thresholds,
  `maxDist=0.0075`, thinning enabled, pinned unmodified Windows matcher.
- Comparison: exact SED and the unchanged compact Choquet-gated Scharr+NMS
  incumbent under the same attachment.

Stage 15a closed without reference reproduction verification. Consequently,
the official Windows-path result is useful development evidence but remains
stochastic and uncertified for a final SOTA claim. The fixed-seed Stage-15a
diagnostic matcher is forbidden for this or any dataset score.

## Required artifacts

- one native-resolution soft PNG per validation image;
- per-image detector runtime and output hashes;
- `official_eval_manifest.json`;
- controller-attached ODS/OIS/AP for candidate and incumbent; and
- deterministic `best_method_preview.png` from sorted validation positions
  1, 50, and 100, with panel order: input, mean annotator boundary (display
  only), retained MFI incumbent, exact author SED.

The preview is documentary and may not affect any parameter or later design
choice outside the preregistered Stage-15 diagnostic sequence.

## Decision rule

This stage has no architecture-promotion threshold. If exact export and matched
scoring complete, record SED as a fidelity-verified non-trained baseline and
preserve both agreement and discrepancy with the paper. If execution or the
official attachment fails, repair only the adapter/dependency/evaluator path
and retry the frozen maps; do not tune SED. After closure, continue to the
preregistered Stage-15c reproduction sequence. MFI redesign remains prohibited.
