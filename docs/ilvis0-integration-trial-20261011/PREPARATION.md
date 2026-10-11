# Prepared NASA integration comparison

**The launcher is prepared; no new NASA fits have started.**

An IMU (inertial measurement unit) measures turning and acceleration. Tests with
independently generated measurements showed that accounting for motion within each
recorded interval greatly improves recovery of a known gyro offset. The next test
applies that integration alternative to one existing NASA stretch, equally for all
three physical models.

The recording is `ILVIS0_applanix_57300_610_LVIS_38614965.013`, IMU type 21.
The selected stretch lasts **438 seconds**, with median ground speed **878.06 km/h**
and minimum **859.55 km/h**. Its selection is unchanged. The completed six-fit
[clock comparison](../ilvis0-clock-trial-20261010/README.md) supplies the reference.

Keep timing, measurements, calibration limits, initialization and solver unchanged.
Change only the treatment of motion within an IMU interval. Fit three models under
the existing two processing cases: **six starts, at most 200 native sweeps each,
including diagnostic predictions; no retries**. Estimated runtime is **90–120 minutes**,
using one worker and two numerical threads. A separate finite run allowance is required.

The alternative assumes ordinary integrated rates. The recorder may already compensate
those increments; applying the same correction twice would be inappropriate. The test
reports both treatments and their calibration behavior. A better fit by itself does
not identify the manufacturer's processing convention.

The [frozen plan](PLAN.md) specifies selection, controls, limits and reporting.
The [launcher](../../analysis/tests/ilvis0_integration_trial.py) verifies hashes and
environment, journals starts before fitting, retains interrupted failures, and publishes
saved results after completion. Publication performs no fits. Shape is compared first;
rotation is reported only after complete globe preferences. This is a development
comparison, with no corpus rerun or change to scientific decision thresholds.

From the repository root, preparation performs no fits:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_integration_trial.py --prepare-only
```

After the separate run allowance is approved, the durable launcher is:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_integration_trial.py --detach
```

Read runtime state in the output directory named by the launcher. A completion
record takes precedence over an older progress snapshot. To publish a completed
study again, use the same environment and `--package-only`; never restart it.
