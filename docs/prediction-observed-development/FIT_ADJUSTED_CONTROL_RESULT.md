# Known-answer training-error check

The completed control asks whether fitting the full nonlinear aircraft model
can, by itself, produce the unusually small training error seen on the ESA
development recording. It generated two separate 900-second aircraft records
at 300 IMU samples per second, with 900 receiver reports each. The first 600
reports trained the model. Both declared IMU error laws were fitted to the
**same measurements** within each generated record.

| Generated error law | Fit with increment law | Fit with point law |
|---|---:|---:|
| Increment | 1,781.054 | 1,781.054 |
| Point | 1,814.957 | 1,814.957 |

These are whitened training costs across 1,800 receiver coordinates. All four
fits passed their numerical stopping checks. Every solution reached at least
two permitted calibration limits, so the interior linear reference cannot be
applied directly to these generated fits. The two generated costs are still
about **250 times** the ESA development value of **7.148** under the same
600-report training length. Neither generated record reproduced that very
small value. The two candidate laws had nearly identical costs on each record.

The result is a diagnostic, not a probability statement. Two generated records
cannot estimate the lower tail of a fitted cost distribution. Bound saturation
also needs explanation before treating these fits as a calibrated null model.
The [saved boundary audit](FIT_ADJUSTED_BOUNDARY_REPORT.md) estimates that
releasing all active limits would reduce cost by only 1.477 or 3.647 near the
saved solutions. That local linear check cannot exclude a different nonlinear
solution or establish an aircraft error law.
The [saved residual comparison](FIT_ADJUSTED_RESIDUAL_REPORT.md) finds
whitened error RMS near 1 in generated training fits but 0.063 in the ESA
development fit, with persistent observed height error.
The [saved input-rate comparison](GENERATED_RATE_COMPARISON.md) finds that the
recorded ESA IMU rates vary much more at short spans, so the cost difference
cannot be read as a simple comparison of raw rate variation.
The [known-answer future score](FIT_ADJUSTED_FORECAST_REPORT.md) also finds
50–84 m horizontal RMS error over the unused 300 seconds of the generated
recordings. Numerical convergence and a plausible training cost do not yet
qualify prediction under these stress settings.
The observed training residuals are much smaller than these generated controls,
while the observed later height forecasts remain inaccurate. A simple claim
that the declared error law fits the aircraft is therefore unsupported.

The study sealed **2/2 tasks with no technical errors** in about 78 minutes.
It charged its predeclared 2.8-million-native-call ceiling before execution;
that charge is an allowance receipt, not a count of completed native calls.
Its original inputs, four fitted artifacts, source/environment hashes, charges
and task seals are preserved. The [machine-readable report](FIT_ADJUSTED_CONTROL_RESULT.json)
binds the generated inputs and fits to the sealed study and the earlier
[ESA training reference](TRAINING_LINEAR_REFERENCE.md). No observed NASA or ESA
values entered generation or fitting, and no reserved ESA confirmation flight
was opened.

**Next gate:** diagnose the generated known-answer forecast drift alongside
the observed training-versus-later-prediction mismatch. Then define and
independently validate an observational error model and
an absolute prediction-adequacy rule before using reserved flights. A larger
tail-calibration study would need its own frozen sample size and finite work
allowance. The scientific decision remains **abstain**.

The frozen [question and limits](FIT_ADJUSTED_CONTROL_PLAN.md) and
[recovery command](FIT_ADJUSTED_CONTROL_RUN.md) remain separate from this
post-run interpretation.
