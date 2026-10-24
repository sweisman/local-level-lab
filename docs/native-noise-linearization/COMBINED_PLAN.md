# Check native and receiver errors together

The native-history and persistent-receiver components have passed their separate
software checks. Combine them on twelve generated histories covering all three
physical candidates, both processing cases and both gravity treatments.

Use four unequal packet intervals, four interior position queries and the
unchanged native motion equations. Retain positive sensor-bias coordinates,
the declared correction scales and shared query/endpoint increment noise.
Include receiver offsets, drift and two persistent components with explicit
per-epoch coordinate transformations. No observations are fitted.

Compare the combined covariance with the sum of an independently evaluated
receiver covariance and the separately calculated native covariance. Preserve
the native mean positions. Compare whitening of every active native calibration
column with an independent dense Cholesky calculation. Compare future means
and marginal covariance conditioned only on the first two generated errors.
Use explicit row scaling for the independent reference, so coordinate-unit
differences do not dominate the numerical check.

Freeze a separate source/environment request, twelve cases, at most 108 native
calls, 144 conservative packet steps, two cached builds, one numerical thread
and a cooperative five-minute allowance. Charge work before execution. No
random draws, optimizer starts, original reads or protected reads are allowed.
Preserve the prior single-step, native-history and receiver qualification scopes
and unused allowances unchanged.

This checks the components together at fixed calibration. It does not include
calibration-estimation uncertainty, estimate the archive error law or demonstrate
nonlinear prediction coverage. Those gates remain before broader aircraft fits.

[Native history result](README.md) ·
[Persistent receiver errors](../integrated-noise-covariance/RECEIVER_PLAN.md) ·
[Prediction assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
