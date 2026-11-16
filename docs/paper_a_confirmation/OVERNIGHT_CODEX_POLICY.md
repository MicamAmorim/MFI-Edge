# Paper A overnight Codex policy — autonomous but fail-closed

Only run the local controller `scripts/paper_a_overnight_agent.py` on branch
`experiment/paper-a-conditional-confirmation` with clean initial Git worktree.
The local user explicitly authorized overnight code repair, manuscript updates
and Git commits/push on this branch. This authorization **does not** lift
scientific restrictions or authorize publishing external datasets.

Permitted work: inspect existing code, test errors, synthetic unit tests,
edit the Paper A draft, correct read-only audit/packaging scripts, build
reproducibility ZIP, make reviewed-per-file-scoped commits and push the branch.

Never open or analyze the protected confirmatory ground truth/H5/F1 or
select/tune on BIPED/MultiCue candidate labels. Never train, recompute
descriptors, run an external benchmark, overwrite Stage24 artifacts or
edit `docs/paper_a_confirmation/protocol.json`, cohort/exclusion decisions,
frozen_models.json, source scientific algorithms or historical evidence.
Never report significant H1/H2 results without a preregistered freeze
and actual held-out evaluation. Synthetic power is not actual outcome.

Do not use git add -A, git clean, git reset --hard, git push --force,
install packages, delete/replace user data, or change branches. Do not
issue arbitrary network commands. If a protected change would be needed,
document the blocker and stop that correction.

Approved local outputs on F: contain only logs, hashes, manuscript drafts
and curated code/documentation packages without third-party images, GT,
model result scores or large NPY scientific arrays.

The controller checks file scope, diff, syntax, tests and Git branch before
committing; Codex must not commit or push on its own. A complete paper
with confirmed findings is scientifically impossible while protocol status
is `draft_not_frozen`. Deliver a comprehensive truthful DRAFT instead.
