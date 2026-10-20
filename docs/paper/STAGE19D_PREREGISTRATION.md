# Stage 19D preregistration — bounded aggregation-family identification

Stage 19D is experiment 3 of 3 in the user-directed Stage-19 analysis budget. It cannot promote a detector or alter compact MFI. It reads only pinned BSDS500 train and the identical 14-image overlap-clean UDED-selection manifest used by Stages 19B–19C. BSDS500 validation and all protected splits are forbidden.

The Stage-19C machine-derived shortlist is frozen, in order, as `structure_tensor_coherence`, `gabor4_s13`, `semiglobal_changepoint`, `hessian_s13`, `brightness_entropy`, and `gabor4_s5`. No descriptor may be added, replaced, or selected using Stage-19D outcomes.

Exactly three families are compared:

1. `distorted_choquet_control`: the five incumbent cues only, with outer-training-fold sigmoid memberships, separation-derived normalized singleton weights, and fixed gamma `0.55`;
2. `nonnegative_additive_logistic`: all six shortlisted memberships with a nonnegative L2-logistic slope vector and free intercept;
3. `monotone_2additive_choquet`: all six shortlisted memberships with a normalized monotone 2-additive capacity, including signed pair Möbius terms subject to all monotonicity constraints.

Each outer fit derives membership midpoints, IQR scales, and positive directions from training images only. Five deterministic image-hash folds are used independently in each domain. The logistic ridge is fixed at `1e-3`. The 2-additive capacity uses the repository's constrained equation-level learner with ridge `1e-4` on at most 30,000 deterministically class-balanced training samples. Choquet context values receive only a monotone two-parameter logistic probability calibration fitted on the same outer training fold. No hyperparameter, descriptor subset, or family is selected inside or outside these folds.

The same fixed fitting procedure is also trained on all images of one domain and evaluated without refitting on the other domain. Report class-balanced log loss, ordinary log loss, Brier score, ROC-AUC, average precision, calibration error, cross-domain transfer, fold/parameter stability, 2-additive Shapley values, and pairwise interaction indices. Transfer collapse is fixed as source-to-target class-balanced log loss exceeding that family's target-domain grouped-CV mean by more than `0.02`. The Stage-19E identification record puts non-collapsed families first, then orders by weaker-domain mean class-balanced log loss and weaker-domain AUC. It is an analysis recommendation, not an architecture decision.

Required artifacts are `aggregation_fold_metrics.csv`, `family_summary.csv`, `cross_domain_transfer.csv`, `parameter_stability.csv`, `choquet_shapley.csv`, `choquet_interactions.csv`, `stage19e_identification.json`, `summary.json`, an incumbent-only BSDS-train `official_eval_manifest.json`, and `best_method_preview.png`. The deterministic preview contains within-domain class-balanced log loss, within-domain AUC, cross-domain class-balanced log loss, and 2-additive interaction stability. It cannot override the numerical rule.

After completion, Stage 19E must synthesize Stages 19B–19D and freeze the complete ordered queue of at most four Stage-20 candidates before any Stage-20 outcome or BSDS500-validation candidate result is inspected.
