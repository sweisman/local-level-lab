# Matched prediction comparison

The launcher is implemented. Software qualification and a separate source/input/
environment freeze make the 12-fit comparison reviewable before launch.
The bounded 12-fit observed-data comparison has been approved and launched.
Its final results will be published separately after all charged identities finish.

The [method and cost](../ilvis0-prediction-covariance-preparation-20261012/README.md)
are fixed: at most **12 starts and 3,060 native sweeps**, no retries, one worker and
two numerical threads. Estimated ceiling runtime is **154–172 minutes**. This
estimate uses saved timings; the new error objective has not been benchmarked.

See the [frozen plan](PLAN.md) and [worker qualification](CONTROL.md). The scope
retains the existing October 5 trajectory, raw inertial measurement unit (IMU)
increments and receiver observations. It tests two common assumptions about
receiver-error correlation using calibration fitted before the prediction period.
It is retrospective development evidence. The existing findings stay unchanged.

The worker refuses to run without an authorization artifact matching its manifest
and exact allowance. This binds execution to the recorded study scope;
software qualification alone does not establish observational validity.

Prepare or verify the freeze without extracting or integrating NASA originals:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_prediction_covariance_worker.py --prepare-only
```

For a new, budgeted study, record the allowance with the same command and
`--record-authorization`, then launch with `--detach` instead. The detached launch
must run outside a short-lived command sandbox. The worker retains its lock,
journals and metadata after a terminal or network connection ends.

After interruption, check the exclusive lock and unchanged freeze before launching
again. An already charged identity without a saved result remains unresolved;
there is no retry. Completed studies refuse to run again.

Successful completion automatically publishes results. `--package-only` verifies
and republishes completed evidence without numerical work. It produces a public
results summary, fit table, receiver-epoch errors and compressed parameter-probe
diagnostics. Local rank and sampled sensitivity ranges are not calibrated
confidence intervals. Unfinished fits remain unresolved.
