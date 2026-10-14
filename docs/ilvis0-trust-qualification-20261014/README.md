# Damped trust-region solver qualification

The completed 200-evaluation continuation left all three target comparisons
unfinished. Saved histories show many rejected corrections, sensitivity to starting
points and, in one case, a stalled primary despite unused evaluations. This separate
candidate changes how the optimizer proposes and accepts a step.

It limits each correction to a trust region, adds scaled damping in weak directions,
and checks agreement between predicted and actual objective improvement. Physical
models, calibration bounds, receiver weights and integration clock are unchanged.
The final acceptance test uses the existing **undamped** correction and fresh
stationarity, objective and actual-position checks. Small damped steps cannot
establish convergence by themselves.

**Prepared; qualification has not yet run.** The [finite plan](PLAN.md) defines
48 checks, with zero NASA-data fits. A metadata-only waiter starts the checks after
the active nine-stretch sequence finishes and releases its four-thread allocation.
It does not pause, restart or change that active study. Test execution is charged
once; interrupted or failed qualification is not retried automatically.

Passing these controls would justify a separately frozen matched archival trial.
It would not establish statistical significance, a global optimum or the cause of
the background field. The current public finding remains 41 globe preferences,
zero flat and 12 unresolved pending audited results from the active recovery.
