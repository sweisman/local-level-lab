# Can the fitted model predict the next part of the flight?

**Completed: five of six training fits converged; one reached its evaluation limit.**
This trial fitted the first 4.85 minutes of a previously selected flight stretch and predicted the final
2.43 minutes without using those later GPS positions for fitting or resetting
the aircraft state. An IMU (inertial measurement unit) supplies the turning and
acceleration measurements used to propagate the predicted track.

The source is `ILVIS0_applanix_57300_610_LVIS_38614965.013`, IMU type 21,
2015-10-05 12:45:50–12:53:08 UTC. The whole stretch is 7.30 minutes at median
receiver ground speed 878.1 km/h. The exact chronological split is 292 training
GPS epochs and 147 prediction epochs.

The completed [clock test](../ilvis0-clock-trial-20261010/README.md) preserved
globe and rotation preference. The [calibration test](../ilvis0-calibration-trial-20261011/README.md)
preserved it with Z gain fixed to zero, while the Z-offset comparison had one
unfinished fit. This test kept the original primary calibration limits
and asked whether the close fit carries into the next part of the same track.

In the fully converged processing case, horizontal prediction RMS was **2.45 m
for rotating globe, 142.9 m for stationary globe and 166.0 m for stationary flat
disc**. This completed comparison favors globe shape. The other case remains
unresolved because its flat-disc fit exhausted its allowance; its unfinished
fit does not count as equal model support. The full two-case verdict and rotation
conclusion are withheld. See the [results](RESULTS.md) for vertical errors,
training errors, both processing cases and stopping records.

All three physical models received the same training/prediction split under both
existing processing cases: **six starts, at most 200 evaluations each, no retries**.
The trial used **887 evaluations and 40.4 minutes** of fitting/diagnostics, with two
numerical threads. See the [frozen plan](PLAN.md) for initialization, covariance,
numerical allowances and recovery rules.

Direct track errors are reported separately from covariance-based diagnostics.
Neither includes uncertainty in the fitted calibration parameters or provides a
calibrated detection threshold. The whole recording was already examined during
development; this is a retrospective prediction check, not independent confirmation.

From the repository root, preparation verifies the freeze and starts no fits:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_prediction_trial.py --prepare-only
```

The numerical study is complete and frozen. Do not relaunch or retry its unfinished
fit. `--package-only` publishes saved evidence without fitting, and `build_report.py`
renders the report without prediction or optimization. Forty-seven focused tests
passed when publishing the completed report.
