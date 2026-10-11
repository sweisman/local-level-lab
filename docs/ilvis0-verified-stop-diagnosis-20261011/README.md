# Completed stopping trial: why the sixth fit remains unfinished

**Five of six fits completed. The verified-stopping revision did not qualify.**
The remaining stationary-disc fit reached a nearly stationary point, but its bounded
local stability check failed the declared measurement-step limit. No saved fit is relabeled.

An **IMU (inertial measurement unit)** measures turning and acceleration. This audit
uses saved results from the same 7.30-minute IMU21 control, median ground speed
878.1 km/h. It performs **zero optimizer starts and zero native predictions**.

## Exact stopping evidence

The unfinished fit's stationarity ratio is **9.35e-06**
against the unchanged 10⁻⁴ projected-gradient threshold. Its saved final cost and
gradient match the previous fixed-scale attempt. The last accepted callback is at
evaluation 191; only 1
terminal callback passes both cost and residual-step stability checks. Three are required
for the callback exit. SciPy did not report successful termination.

The additional bounded linear correction predicts a relative cost change of
**2.4148 × 10⁻¹²**, far below the 10⁻⁸ cost limit. However, its relative residual-vector
step is **1.5541 × 10⁻⁶**, or **1.5541 times**
the 10⁻⁶ step limit. The fresh nonlinear probe was therefore not attempted. A failed
linear screen is not evidence that a fresh nonlinear probe would fail or pass.

Cost and residual-vector movement measure different things: individual errors can change
while their squared sum barely changes. A tiny gradient or cost change alone cannot
replace the declared combined stopping rule. The trial used 736 evaluations, including
prediction diagnostics, and about 35.6 minutes. The allowance is spent; no retry is authorized.

| Processing case | Model | Saved status | Exit | Stationarity / threshold |
|---|---|---|---|---:|
| bias1_unsubtracted | sphere_rotating | converged | three_stable_callbacks | 0.00548 |
| bias1_unsubtracted | sphere_still | converged | scipy_stop | 0.00133 |
| bias1_unsubtracted | flat_still | converged | three_stable_callbacks | 7.77e-07 |
| bias1_profiled_removal | sphere_rotating | converged | scipy_stop | 0.063 |
| bias1_profiled_removal | sphere_still | converged | three_stable_callbacks | 0.000577 |
| bias1_profiled_removal | flat_still | unresolved | unresolved | 9.35e-06 |

All five originally completed fits remain completed. Their largest relative training-cost
increase is 2.9139e-06%, below the declared 0.1% agreement limit. Qualification
failed because the sixth fit remains unfinished, not because those five worsened.

## Calibration and interpretation

The unfinished fit retains 15 parameters at limits and a
full-Jacobian condition ratio of 5.15e+07. Its weakest
direction mixes gravity_delta (0.901), gyro_gain_y (0.236), gyro_gain_x (0.224), gyro_gain_z (0.184), accel_bias_z (0.180). These normalized loadings describe a local full-Jacobian
direction, not feasible confidence limits or a physical calibration measurement.

The completed no-removal prediction comparison still favors globe. The removal-allowed
comparison remains unfinished, and rotation is withheld for the combined comparison.
An unfinished flat fit does not provide positive flat-Earth evidence. Numerical stopping
does not settle the separate clock, calibration or uncertainty questions.

[Fit checks](fit-diagnostics.csv), [parameter values](parameter-diagnostics.csv),
and [weak directions](weak-directions.csv) preserve the saved numerical evidence.
The [matched results](../ilvis0-verified-stop-trial-20261011/RESULTS.md) retain track
errors and the scientific status.

## What to do next

Do not loosen the stability threshold merely because this result misses it by a factor
of 1.55. Do not rerun the same failed identity or extend the completed allowance.
Prepare independent physical controls for the calibration/timing interaction and
alternative numerical strategies. In parallel, audit existing timestamp and residual
evidence as specified in the [focused diagnostic plan](../ILVIS0_DIAGNOSTIC_PLAN.md).
Joint Z gain–offset profiles and any fresh observed test require their own finite scope.
Recording replication and a corpus rerun remain deferred.

Reproduce this saved-data audit without fitting:

```sh
env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-verified-stop-diagnosis-20261011/build_report.py
```
