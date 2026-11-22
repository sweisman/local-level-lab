# Qualify exact rejected-proposal reuse on generated aircraft fits

Use the same eight generated cases as the
[sealed full-fit trial](MATCHED_TRIAL_FITS_RESULT.md). They include all
four fitted models on the specified-field disc history with profiled
removal and the zero-field globe history without removal. Retain the
same earlier and later time split, motions, zero starts, wider
arithmetic, offsets and candidate limits. Reuse the archived reference
fits and forecasts. Run one opt-in candidate for each case.

Require the initial training cost to reproduce, then apply the original
fresh stopping and prefix checks. For each reference that passed
stopping, require the new fit to pass, its training cost to agree
within 1e-8 relative and its maximum later position difference from
the sealed forecast to be at most 0.01 m. These scales follow the
existing cost-stability and forecast-equivalence checks. For the
old stopping failure, retain its original label, require no material
increase in training cost, and report the new fit's actual outcome
and forecast change. A numerical mismatch fails the task.

Charge each training evaluation and forecast before execution. Allow
80 training evaluations and one forecast per task, four single-thread
workers, and a 20-minute cooperative wall cap. Verify the exact source
and environment tests and the shared task recovery qualification before
launch. The frozen recovery allowance permits at most two charged
starts per task, at most two technical interruptions across the study,
and a 40-minute continuation limit. The recovery planner reuses every
completed result and preserves every charge. This comparison uses no
recorded aircraft input and changes no archived fit disposition.
