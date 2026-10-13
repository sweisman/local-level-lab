# Recovering the remaining airborne comparisons

**The wider recovery run is active.** It starts with six fresh control fits, then
continues the frozen primary and repeated-start schedule. Results are published
automatically after completion; the current combined findings below precede this run.

The revised numerical method passed **24/24 fits**, including all control and
repeated-start checks. The [qualification results](../ilvis0-position-stability-trial-20261013/RESULTS.md)
recover three previously unresolved stretches, all favoring globe. Together with
the preserved first study, that gives **15 globe preferences, none for flat and
38 unresolved stretches** before the wider recovery run.

The [frozen plan](PLAN.md) applies the same method to the remaining original
unfinished calculations. It reuses 18 qualified results and permits **159 new
starts**: 115 primary fits, 38 repeated starts and six fresh controls. All physical
models, observations and calibration bounds remain unchanged.
The [stretch inventory](../ilvis0-position-recovery-preparation-20261013/stretches.csv)
records source filenames, hashes, UTC intervals, duration, speed and recorded IMU type;
the [task ledger](../ilvis0-position-recovery-preparation-20261013/tasks.csv) identifies
new and reused calculations.

The worker uses two numerical threads, records each attempt before execution and
allows no retries. Its ceiling is 95,718 native sweeps, estimated at 51–76 hours
if difficult fits consume their full allowances. Actual time may be shorter.

Every newly completed stretch needs six passing model fits and its scheduled repeat.
Fresh control failures withhold the recovery findings. Globe/flat is reported first;
the background-field comparison follows only for consistent globe preferences.
These are numerical model preferences, not calibrated statistical detections.

## Execution and continuation

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_position_recovery_worker.py --prepare-only
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_position_recovery_worker.py --detach
```

Prepare only a new freeze. Before continuation, check its exclusive worker lock,
completion record and unchanged source/input/environment hashes. Charged interrupted
starts remain unfinished; the worker continues only unstarted identities. Never
restart completed work. Publication is automatic on completion; `--package-only`
verifies and packages existing evidence without numerical fitting.
