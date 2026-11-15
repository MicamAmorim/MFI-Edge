# Exploratory image groups, 15 November 2026

This analysis is separate from the completed Stage24 campaign. Features and clusters do not use GT or model performance. Per-image winners and group modes are retrospective descriptions of held-out results, not a learned prospective selector.

Known exact mathematical aliases are collapsed for votes (OWA median/median; optimistic/maximum; pessimistic/minimum; centered/equal mean; two-input median/equal mean). This correctness clarification was added after the initial plan to avoid splitting votes across names of the same function. Other ties receive fractional votes.

195 implementation candidates have complete coverage (70 image/fold records). Coverage filtering, scales, PCA dimension and K are not optimized against F1. Each image is represented by its mean score over five repetitions. A singleton cluster has no evidence of within-group generalization.

NMS is not guaranteed to yield a one-pixel skeleton. The extra-thinning audit measures redundant pixels in final refitted UDED maps and does not estimate held-out F1 changes. Group modes remain conditional on the existing NMS protocol. BSDS already applies morphological thinning before matching.

Reproduce: python scripts/analyze_stage24_image_groups.py --research-root PATH_TO_RESEARCH --out NEW_DIRECTORY using the scientific environment. No detector fitting or threshold search occurs.
