# Frozen remaining precision-study plan

9 fixed targets; **65 starts / 12,810 native sweeps maximum**. The ceiling estimate is **72.3 serial hours**, scaled by interval duration from the completed precision study. Actual endpoint continuations may finish much earlier.

One worker uses four numerical threads. Every primary/repeat has at most 200 fitting evaluations; each control has forty. Each start permits two diagnostic predictions. No retries or budget expansion.

Gradient tolerance stays 1e-4, fresh relative objective change 1e-8, predicted position change at most 1 mm axis RMS and 1 cm at any epoch. Repeat/control agreement requires relative objective difference ≤1e-6 and receiver-position RMS difference ≤1 cm per axis. These are numerical criteria, not measured sensor accuracy.

Complete selected stretches, observed increments and receiver positions, models, bounds, weights, clock and qualified wider-arithmetic kernel are unchanged. Starts use frozen primary endpoints, not whichever earlier attempt has the lowest cost. Every charged interruption remains failed. Journals, source/input/environment hashes, exclusive locks and atomic results preserve the audit trail.

All six primaries are fitted afresh on each of the nine earlier excluded stretches, with the original scheduled repeat. Launch requires completion of the preceding budget stage with passing controls. That gate cannot alter the preselected targets. Per-stretch completion requires every primary, its repeat and both controls.
