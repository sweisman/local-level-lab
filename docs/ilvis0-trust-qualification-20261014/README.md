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

**Completed; qualification failed.** Of the 48 known-answer checks in the
[finite plan](PLAN.md), 44 passed and four failed. All four failures concern the
same 27-parameter nonlinear control, under its four starting points. The
[qualification record](RESULTS.md) preserves the failures and frozen source.
No archival recordings were fitted. The batch ran after the nine-stretch assessment
finished; its allowance is closed and cannot be retried.

The next step is to diagnose the failing control before preparing a revised,
separately frozen candidate. This candidate is not qualified for a matched archival
trial. Current airborne findings are reported separately in the
[verified status](../CURRENT_STATUS.md); these software controls do not change them.
