# Matched integration-clock trial

**Completed: all six fits converged.** This comparison asks whether the completed control's model
preference survives reoptimizing under packet-header timing, rather than only changing
the clock at its old parameters.

The globe family fits better than the flat disc under both processing cases; within
the globe family, rotating globe fits better than still globe. Reoptimizing under
packet-header timing restores rotating-globe vertical error to about **0.70 m**,
compared with **9.36 m** when changing timing at the old parameters. Horizontal
error is about **0.081 m**, versus **29.0 m** for still globe and **60.5–63.6 m**
for flat disc. The six fits used 963 evaluations and about 52 minutes of fitting.

This control's model preference survives the clock change. Z-axis gyro gain and
offset still reach their allowed limits, so calibration-boundary diagnosis remains
necessary. This trial establishes neither the instrument's actual clock convention
nor a calibrated statistical significance level.

An **IMU (inertial measurement unit)** records turning and acceleration. The
[residual diagnostic](../ilvis0-residual-diagnostic-20261010/README.md) found that
packet-header intervals raised the control's vertical error from about 0.70 m to 9.36 m
at unchanged parameters. Its original nominal-clock fit remains preserved.

The fixed target is the same 7.30-minute control already selected for the solver trial:
`570b37d23af5e245dd461051`, from `ILVIS0_applanix_57300_610_LVIS_38614965.013`.
Its median receiver ground speed is 878.1 km/h. No intervals are selected again.

The approved allowance is **six new starts, at most 200 evaluations each, no retry
reserve**: rotating globe, still globe and flat disc under the two existing processing
cases. Only the clock changes. Calibration limits, receiver covariance, original
initialization, gravity, coordinates and the original frozen optimizer stay the same.
The six nominal reference fits are reused, not refitted. This avoids mixing the revised
solver with the clock test; the revised solver did not improve the observed trial.

Save convergence/stationarity, costs, calibration estimates and signed boundaries,
per-epoch residuals, whitened diagnostics, and the nominal-clock counterfactual at
each new parameter point. Report shape before rotation and preserve failures. Relative
preferences remain development findings, with no new significance threshold.

At the previous trial's measured 3.60 seconds per evaluation, using the entire
1,200-evaluation allowance takes about **72 minutes**. At its slowest measured rate,
the estimate is about **87 minutes**, plus extraction/packaging. This is an estimate,
not a wall-clock guarantee; early stopping may reduce it. Use two numerical threads.

The source/input/environment freeze and tested launcher were prepared before approval.
`--prepare-only` does not extract raw observations or make model evaluations.
The detached worker has completed. Preserve the frozen results and do not launch it
again. To regenerate the evidence package without fitting:

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/ilvis0_clock_trial.py --package-only
```

The worker uses an inherited exclusive lock, durable start charges, hashed atomic
results and source/environment checks. An interrupted charged start is not retried.
Completed work supports `--package-only`; packaging never fits.

All completed NASA studies and their unused allowances remain frozen. This trial
does not expand to the other 52 stretches or introduce new calibration assumptions.
