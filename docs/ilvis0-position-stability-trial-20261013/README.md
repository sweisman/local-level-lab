# Testing stability in metres

The [saved-result diagnosis](../ilvis0-boundary-diagnosis-20261013/README.md) found six
nearly stationary fits rejected by a local prediction-stability rule. Repeated starts
gave nearly identical tracks, while their stopping outcomes differed.

This separate trial replaces that local prerequisite with an **actual full-model
position check**: at most 1 mm RMS on each axis and 1 cm at any individual receiver
epoch. The original total-error and gradient limits remain. These are numerical
stability tolerances, not claims of instrument precision or statistical confidence.
The physical models, calibration bounds and data weights stay unchanged.

The [finite plan](PLAN.md) uses the same three unfinished stretches and completed
control, starting from all saved primary endpoints of the previous trial. It permits
24 starts and at most 14,448 native sweeps, with no retries and two numerical threads.
The trial is **complete and qualified: 24/24 fits passed**, including all six
controls and all three perturbed-start checks. It used 393 native sweeps.
All three previously unresolved test stretches now consistently favor globe.
[Completed results](RESULTS.md) preserve the individual checks and comparisons.
[Updated findings](FINDINGS.md) give the three newly resolved recordings, durations,
speeds and the combined 53-stretch tally, including the first complete IMU8 comparison.

The worker seals source/input/environment hashes, charges starts and calls before
execution, persists outside temporary shells and publishes results automatically.
The original first-pass findings remain preserved at 12 globe preferences, zero flat
and 41 unresolved. Adding the three qualified recoveries gives **15 globe, zero flat
and 38 unresolved**. The [wider recovery](../ilvis0-position-recovery-20261013/README.md)
uses a separate finite freeze; this completed trial cannot restart.

## Reproduce

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-position-stability-trial-20261013/qualify_position_stability.py
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_position_stability_worker.py --prepare-only
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_position_stability_worker.py --detach
```

Run qualification/preparation only for a new freeze. Never restart completed work or
reuse unused allowances. Publication after completion uses `--package-only`, which
performs no numerical fits.
