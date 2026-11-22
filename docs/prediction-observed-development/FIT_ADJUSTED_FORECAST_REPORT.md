# Known-answer forecasts also drift

The completed generated control fitted two 900-second aircraft recordings. It
used the first 600 receiver reports to fit, then saved a forecast for the
remaining 300 reports. This saved-only check now compares those unused future
forecasts with each recording's **known generated physical trajectory**. No
fit or native propagation was repeated. No future receiver noise was added.

| Generated input | Later horizontal RMS | Later height RMS | Last 100-report horizontal RMS |
|---|---:|---:|---:|
| Increment-error truth | **50.47 m** | 1.54 m | 77.43 m |
| Point-error truth | **84.35 m** | 4.94 m | 111.86 m |

Fitting either candidate error law to the same generated recording gives
practically identical results. All four original fits passed their numerical
stopping checks, but each reached calibration bounds. The first generated
recording's horizontal RMS grows from 15.95 m in the first future 100 reports
to 77.43 m in the last; the second grows from 55.34 to 111.86 m. The score
uses an exact ellipsoidal coordinate-to-Cartesian conversion and projects the
physical displacement onto local north, east and up. It reconstructs the
generator's Cartesian truth to within **3 nanometres** in both cases.

The generator also supplies known sensor calibration. In the increment-error
recording, the true normalized X-gyro gain is **+0.20** while the fit reaches
**−1.00**; its true Y gain is **−0.15** while the fit also reaches **−1.00**.
In the point-error recording, the true Z-gyro bias is **+0.25** while the fit
reaches **+1.00**, and the true time offset is **+0.07** while the fit reaches
**−1.00**. These are positions relative to the fit's permitted limits, not
device specifications. Their disagreement demonstrates incomplete recovery
of generated calibration; this saved check does not assign how much of the
future error to each parameter.

These are **software known-answer controls**, not new aircraft observations.
They show that a numerically complete training fit under these declared
synthetic stress settings does not, by itself, provide an accurate future
physical trajectory. The current generated controls therefore cannot qualify
future prediction or its uncertainty. The source of the drift could involve
the active calibration bounds, parameter trade-offs, the fitting method or
the generated motion/noise settings. This check does not distinguish them.

The [saved report](FIT_ADJUSTED_FORECAST_REPORT.json) binds the original fit
and forecast artifacts, the unchanged analytic truth source and the scoring
code by hash. It records all four candidate scores and 100-report sections.
No original or reserved ESA recording was read. The scientific decision
remains **abstain**. The next gate is a separately frozen, finite oracle-control
comparison on these same two measured synthetic IMU streams: propagate from
the generator's true initial state with its true fixed calibration, retaining
the original random IMU errors. If that forecast is accurate while the fitted
forecast drifts, investigate calibration recovery and identifiability. If it
also drifts, investigate the observation model, noise and propagation. This
would be a software diagnostic, not a permitted substitute for fitting real
measurements or calibrated future coverage.
The [next-control design](ORACLE_CONTROL_DESIGN.md) fixes the inputs, test
order and finite work limits before any new native forecast is launched.
