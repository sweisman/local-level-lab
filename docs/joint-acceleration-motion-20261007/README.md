# Fitting wind and aircraft-motion correction together

The acceleration correction must depend on the same wind and orientation assumptions as
the Earth-model prediction. Otherwise the fit could adjust aircraft heading while its
motion subtraction stayed fixed at a different heading.

The joint research prototype now recomputes both at every trial parameter value. Observed
GPS velocity and IMU force determine acceleration and apparent vertical direction. The
wind candidate determines aircraft heading. The uncertain forward reference determines
how that heading maps into the IMU axes. The prototype recovers gravity direction, computes
aircraft rotation and the model prediction in the same orientation, then averages them
over the same minutes. Its derivatives include both paths through wind and orientation.

Six explicit error parameters represent coherent GPS-acceleration and accelerometer-force
errors. They enter the same prediction, with provisional uncertainty scales and priors.
The joint covariance therefore includes their coupling to wind, orientation and model
coefficients. These six patterns are not a complete model of measurement errors; validated
coverage, correlations and instrument systematics remain open.

Time support is fixed before optimization using observable data and a bound covering
simultaneous error perturbations. The fit cannot improve its objective by dropping different
minutes at different parameter values. All six saved cases retain the same83minutes.

## Checks and saved-data work

**Complete:** all24optimizer calls converged and the six free fits nested below the
fixed-model fits. No nesting restart was needed and no fit approached a parameter bound.
All cases used the same83minutes. Residual variation after joint refitting is7.92–8.57°/hour:
8.49–8.57for broader wind and7.92–8.03for physical wind/TAS. Completed optimizer time sums
to309.86seconds; that is not a measured wall time. Sixteen focused checks pass. A resume
check skipped all completed fits, preserving exactly24starts and24completions.

This confirms that the correction survives joint optimization in these saved development
recordings. It does not establish calibrated model separation: the weights and error model
remain provisional, and no empirical decision is enabled. Matching gyro and GPS/force
filter bandwidth and validating measurement covariance are the next processing checks.

Six saved reference states were evaluated without fitting. Both wind candidates passed
independent derivative checks. At those earlier parameter values, residual variation was
about11°/hour for the broader wind candidate and15°/hour for physical wind/TAS. The older
parameters came from a different motion treatment; these are reference checks, not optima.
Local coefficient uncertainty remains substantial under the frozen older gyro weights.

A bounded diagnostic refit then uses these same six recordings. It makes one free fit and
three fixed-model fits per case, with one predefined free restart only if the objectives
fail to nest. The scope allows at most30optimizer calls, including interrupted starts,
and200evaluations per fit. No new simulated recording or bootstrap is included. Empirical
decisions and production use are disabled.

The runner freezes source, input, policy and numerical-environment identities. One
numerical thread is used. Every optimizer start is journaled and fsynced; completed fits
have atomic metadata and hash-checked parameter archives. Resume skips those fits, retains
interrupted starts and refuses source/environment changes. A process lock excludes duplicate
workers. If the call limit is exhausted, the runner stops rather than extending its scope.

## Evidence and continuation

| File | Purpose |
|---|---|
| `review.json` | Joint predictions, derivative checks, nuisance-projection diagnostics and local covariance at saved reference states. |
| Task-ID `.npz` archives at this directory's root | Parameters, fixed support, predictions, Jacobians and joint/conditional covariance for those evaluations. |
| `reference-evaluation-source.py` | Exact report-producer source for the reference evaluation. |
| `refits/plan.json` | Frozen bounded refit scope, sources, settings and environment. |
| `refits/status.json`, `refits/attempts.jsonl`, `refits/run.lock` | Progress, append-only optimizer history and process lock. |
| `refits/<task-id>/<fit>.npz` and `<fit>.json` | Completed fit parameters/predictions/covariance, metadata and hashes. Temporary files are incomplete writes. |
| `refits/<task-id>/result.json` | Per-case convergence, nesting and diagnostic residual/objective summary. |
| `refits/review.json` | Final combined refit assessment. |
| `refit-assessment.json` | Independent checkpoint, optimizer-count, nesting and all-fit boundary review. |

This finite scope is complete; no worker is active and no resume is needed. The unused
optimizer-call reserve is not permission for additional fits. For interruption recovery in
this frozen scope, read `refits/status.json` before any resume. An active worker needs no duplicate. The command
below resumes only the frozen missing work and preserves the30-call maximum:

```sh
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 /home/sweisman/venv/bin/python analysis/tests/refit_joint_acceleration_motion.py docs/observed-pair-replay-20261007/run --output docs/joint-acceleration-motion-20261007/refits
```

Implementation: `analysis/tests/joint_acceleration_motion.py`; reference evaluator:
`review_joint_acceleration_motion.py`; refitter: `refit_joint_acceleration_motion.py`;
fixtures: `test_joint_acceleration_motion.py`. All remain outside production analysis.

The gyro weights still come from the original preliminary fits. GPS/TAS speed remains
conditionally modeled at bin resolution. Coriolis/curvature acceleration bounds, complete
measurement covariance, filter bandwidth and independent uncertainty validation remain
necessary. No projection diagnostic here changes the frozen eligibility gate, and no raw
objective difference is a calibrated model rejection or an Earth-model conclusion.
