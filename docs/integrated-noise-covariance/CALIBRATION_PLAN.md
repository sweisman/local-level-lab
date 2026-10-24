# Include uncertainty from estimating calibration

The native and receiver components propagate a declared error law at fixed
calibration. A fitted calibration is uncertain too. Its effect must not vanish
from a prediction simply because the optimizer returned one parameter point.

First qualify the linear, fixed-design calculation. Use earlier observations
only for generalized least-squares estimation, preserving their temporal
covariance. Predict later observations using both the estimated mean and the
error information carried from earlier observations. Add the calibration
uncertainty without counting that earlier information twice.

Keep every supplied calibration column. Require explicit parameter units and
numerical rank/estimability tolerances. If training leaves a direction unknown
and that direction changes the later prediction, return unidentifiable with
no finite prediction covariance. A rank-deficient calibration may still make
an estimable prediction if every unknown direction cancels there. Do not add
an unstated prior, drop nuisance columns or repair variance to obtain an answer.

Compare with independently formed dense generalized least-squares prediction
weights and their complete error covariance. Cover all 27 columns, correlated
errors, several training cutoffs, parameter rescaling, identifiable predictions
with redundant parameters and genuinely unidentifiable later predictions.
Accept only training residuals; no later measured residual is an input.

Use at most sixteen deterministic generated cases, sixteen epochs, 27 parameter
columns, one numerical thread and a cooperative two-minute allowance. No random
draws, native calls, optimizer starts, original reads or protected reads occur.
Bind a fresh formal request to the exact sources and numerical environment.

This first step assumes an unrestricted linear mean and a supplied Gaussian
error law. It does not cover nonlinear calibration, parameters constrained at
bounds, estimation of the error law or simultaneous confidence over a flight.
Those require their own qualification before applying uncertainty statements
to the aircraft fits. Existing physical accuracy limits and failed controls
remain unchanged.

[Covariance overview](README.md) ·
[Combined native/receiver gate](../native-noise-linearization/COMBINED_PLAN.md) ·
[Prediction assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
