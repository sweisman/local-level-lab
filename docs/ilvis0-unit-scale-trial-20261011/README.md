# Can fixed solver scaling finish the prediction comparison?

**Completed: five of six fits converged; comparison qualification did not pass.**
The flat-disc fit with upstream removal allowed exhausted its 200-evaluation limit.
The completed prediction trial had five
converged fits and one unfinished flat-disc fit. This separate comparison preserves
the flight, models, calibration bounds, timing and training/prediction split. It
changes how the numerical search scales parameter steps, while recording more
diagnostic information.

Both dense solver settings passed 24/24 known-optimum controls. The implemented
candidate passed its focused tests. These are software checks; the matched airborne
trial did not recover the unfinished comparison. See the [analytic screen](../ilvis0-prediction-audit-20261011/SOLVER_SCREEN.md)
and [saved prediction audit](../ilvis0-prediction-audit-20261011/README.md).

The [plan](PLAN.md) specifies six new fits, 200 evaluations per fit and no retries,
with two numerical threads. Estimated runtime is roughly 55–65 minutes if every
fit uses its allowance. The worker preserves every result and publishes its evidence
when finished. A separate metadata-only watcher then verifies the numerical freeze
and builds the matched report automatically; it performs no fits. Runtime progress
and report completion are recorded separately in the study's data directory. The
original unfinished fit stays preserved, and this study does not authorize any
archive-wide rerun or change to the scientific evidence gate.

[The matched results](RESULTS.md) show which fits converged,
whether the five previously completed objectives were preserved, and how prediction
errors changed. The six starts used 749 evaluations and about 33.4 minutes of fitting
and diagnostics. The no-removal prediction comparison favors globe; the full two-case
comparison remains unresolved. More completed fits alone do not establish physical
calibration or statistical significance. No retries or replication starts are authorized.
