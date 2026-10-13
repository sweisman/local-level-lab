# Boundary-aware recovery trial

**Complete: 17/24 fits passed using 2,399 native sweeps.** All six completed controls,
nine of fifteen unfinished primaries and two of three repeats passed. No test stretch
became fully resolved, so the method did not qualify for rollout. See the
[results](RESULTS.md) and [saved-result diagnosis](../ilvis0-boundary-diagnosis-20261013/README.md).
The finite plan below records the study's original design; do not restart completed work.

This trial tests a numerical repair on the same three unfinished stretches and
completed control used by the earlier recovery comparisons. The observations,
physical models, calibration bounds and error assumptions stay unchanged.

The new solver takes a bounded linear step, checks its actual nonlinear cost and
shortens rejected moves. It removes only roundoff-sized slack at parameter limits.
All successful fits still require the original fresh stationarity and stability checks.
The [known-answer comparison](../ilvis0-boundary-controls-20261012/README.md) passed
40/40 controls, but it cannot establish success on the aircraft recordings.

The [finite plan](PLAN.md) defines **24 starts / 14,448 native sweeps**:
15 unfinished fits, six completed controls and three predetermined perturbed repeats.
Each start has at most 600 fitting calls and two diagnostic predictions. No retries
or replacement starts are permitted. At the ceiling, runtime is estimated at
**10–14 hours**, with one worker and two total numerical threads.

All planned fits must pass; completed controls and perturbed repeats must also agree
in objective and predicted positions. Original results remain **12 globe preferences,
zero completed flat preferences and 41 unresolved stretches**. Numerical trial
outputs abstain from calibrated scientific decisions.

## Reproduce

Prepare software evidence and the separate frozen trial from the repository root:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-boundary-recovery-trial-20261012/seal_controls.py
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_boundary_worker.py --prepare-only
```

Run the prepared study with a durable worker:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_boundary_worker.py --detach
```

The launcher records the frozen finite limits automatically. It preserves exclusive
locks, source/input/environment checks, precharged append-only journals and atomic
hashed outputs. Interrupted identities remain spent and unresolved. Results publish
automatically when the trial completes; `--package-only` publishes without fitting.
Do not restart completed work or reuse its unused allowance.
