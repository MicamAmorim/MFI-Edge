# Independent LLM review and Stage24G-L course corrections (2026-11-03)

The third-party review primarily inspected the older main commit 9692c36 (October 5), not a completed 24G-L. Historical results remain unchanged. This file records how the newer branch addresses relevant findings and what must stay out of claims.

## Applicable to NEW campaign

- WRONG DIAGONAL NMS: confirmed in src/postprocess.py on both main and research branch. Corrected +45 degrees to compare upper-left/lower-right, and +135 to compare upper-right/lower-left. Added signed direction and border regression tests. Old NMS results are not numerically comparable to the new protocol.
- HISTORICAL CF1F2 (Dimuro et al., Fuzzy Sets and Systems 378, 2020, Eq. 9): old src/operators.py uses x_(1) without explicit F2(0,mu(N)), and does not collapse ties. Preserve historical output. Added separate src/stage24_strict_generalized_cf1f2.py with distinct-value groups, correct initial term, and tests of the GM/GM counterexample. Include five explicitly named gCF1F2 variants in new landscape. Do not conflate these with quasi-arithmetic Choquet variants.
- COPULA MISLABELS: historical COPULA_LIKE includes arbitrary bivariate fusion functions. A new explicit mathematical audit checks margins and 2-increasing rectangular volumes on finite grids; it flags invalid candidates, but numeric screening is NOT a proof. Only qualified candidates enter mathematical claims.
- HAMACHER N-ARY: old vector heuristic was not associative. Replaced the hamacher mode with the correct associative n-ary formula, preserving the old heuristic as hamacher_legacy. Added unit test.
- CODE DRIFT: added source/config fingerprints across critical operators, descriptors, NMS and controls. Resume under a different source/config is blocked instead of mixing checkpoints. Preflight and unit tests fail closed.

## Already corrected or deliberately inapplicable

- Legacy Stage3/4 repeated fine scales: Stage23/24 descriptor registry uses the newer oriented_ms schedule. Earlier oriented/combined numerical outcomes stay historical.
- Legacy 40 percent surprisal plateau: src/pipeline.py still has truncated empirical background; this is NOT the Stage24G descriptor pair inference. Do not claim a calibrated null distribution or interpret Stage4 ROI as confirmed. Future legacy experiment requires a frozen null model and a new protocol.
- Phantom combined-mode twelfth channel: duplicate gradient magnitude still exists in historical combined mode. Stage24G uses individually registered descriptors, not this combined vector; do not interpret it as 12 independent features.
- Legacy vector-dependent adaptive power/local additive modes do not define one fixed fuzzy capacity. Current Stage24G uses monotone trained capacity tables. Do not identify that heuristic as SWAFED, nor assert capacity monotonicity from local weight normalization.
- Legacy Stage4 unfair baselines, old Canny quantiles, truncated AP, many-to-one matching: cannot support current Paper A claims. Stage24 uses native GT and one-to-one UDED; BSDS validation uses original Berkeley multi-annotator matcher. Historical synthetic scores remain pilot.
- Legacy diffusion np.roll border wrap and ROI feather identity: not used in Stage24G; repair separately if that historical pipeline is reintroduced.
- The old local BSDS parser with brittle .mat field indices and majority GT is NOT the official MATLAB path. New references must use Berkeley all-annotation evaluation.
- Non-uint8 inputs are explicitly blocked by new UDED loader while 16-bit legacy feature scaling is not certified. An expanded multi-bit dataset must receive an independently tested normalization fix.
- Second-order Laplacian/DoG peak localization is a real possible weakness; Stage24G individual-descriptor native comparisons and NMS factorial provide diagnostics, but not a causal proof.

## Remaining unresolved publication gates

- Independent Berkeley reference reproduction verified=false.
- 14 UDED unique images; repeated 15 folds are NOT independent samples.
- Stage24G inner selection is CONDITIONAL on earlier outer-train discovery; do not label it fully independent joint nested CV.
- BSDS500 val is development, not untouched final confirmation.
- External detector original float maps and complete protected benchmarks are not yet available.
- Tuned Canny/learned detector reference is missing; do not claim SOTA or comprehensive classical superiority.
- The paper generalization theorem requires formal mathematical verification beyond finite grids, even though Eq.9 implementation now matches its specified structure.

## Operation

PowerShell at the MFI-Edge root:

    git fetch origin
    git switch mfi-edge-stage24-residual-suppression
    git pull --ff-only origin mfi-edge-stage24-residual-suppression
    .\run_stage24_paper_a_recertification.bat --phase preflight

Run full campaign ONLY if this command passes, then:

    .\run_stage24_paper_a_recertification.bat --phase all

The launcher compiles and executes regression tests first; no expensive experiment starts after failures. Original Stage23/24 results and paper drafts are not overwritten. Local MATLAB, UDED data and Git repository state have not been executed by the assistant.
