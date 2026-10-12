# Completing the unfinished comparisons: recovery qualification

The first pass left 41 of 53 eligible stretches numerically unresolved. This small
trial tests a way to complete those calculations while preserving the selected
measurements, physical models, calibration bounds and both processing cases.
It follows the [representative selection](../ilvis0-convergence-recovery-preparation-20261012/README.md).
The receiver-covariance/prediction comparison has finished with 10 of 12 fits
converged; its combined comparison remains unresolved.

The recovery trial is complete: **15/24 fits passed**, including all six completed
controls and eight unfinished primary fits. None of its three unresolved stretches
became fully resolved, and subset qualification failed. See [results](RESULTS.md)
and the [saved stopping audit](../ilvis0-recovery-diagnosis-20261012/README.md).
Do not resume this completed trial. The original 53-stretch findings remain unchanged.

## What changes

Continue from the original saved feasible parameter values, instead of starting
again from zero. Allow up to 600 additional fitting evaluations for each planned
start. Keep the nominal 200 Hz integration clock, original correlated GPS-error
objective and physical bounds. This is a numerical continuation, not a change
to the science model or a relaxation of acceptance checks.

The new solver requires a fresh stationarity check and either three stable
accepted steps or an independently evaluated bounded correction that confirms
stable cost and predicted observations. Exhausting the budget alone never passes.
The controls exposed premature internal optimizer stopping; its internal gradient
tolerance was tightened, while the final stationarity and stability criteria
remain fixed. Parameter uniqueness is not required in a demonstrably weak direction.

## Finite scope

| Purpose | Starts |
|---|---:|
| Continue unfinished fits in three preselected failure examples | 15 |
| Recheck all six fits of the completed October 5 control | 6 |
| Repeat one predefined fit per failure example from a perturbed saved point | 3 |
| **Total** | **24** |

There are no retries. Each identity permits 600 fitting sweeps and two direct
track predictions: **14,448 native sweeps maximum**. One worker uses two numerical
threads. Same-recording first-pass timings estimate roughly **10–14 hours at the
ceiling**; warm starts may take much less. The estimate is not a wall-time guarantee.

Previously converged fits in the three unresolved stretches are reused unchanged.
A recovered whole-stretch comparison still requires all six fits to converge.
The six control fits are rerun to test agreement. No original failure is relabeled;
recovered comparisons receive a separate record.

## Checks before expanding to all 41

The qualification requires all planned fits to pass their numerical checks. The
control must agree with its saved objectives within a relative tolerance of
`1e-6` and tracks within 1 cm RMS on each axis. The three perturbed-start repeats
must agree with their continuations to the same tolerances. These are numerical
agreement criteria, not calibrated measurement uncertainty or scientific significance.
The original saved objective must reproduce before each ordinary continuation.

Software checks cover known interior/boundary optima, gain–offset ambiguity, weak
27-parameter directions, independent short IMU/GPS controls, and both column and
unit numerical scaling. The actual runner path is checked for all three models.
They establish small-control behavior, not global minima on long archival recordings.
The observed trial provides the next qualification evidence. Additional scientific
diagnostics remain deferred; this trial does not automatically authorize an all-41 run.

See the [frozen plan](PLAN.md) and [software controls](CONTROL.md). Originals, source
snapshots, environment, selected intervals, results and native-call journals are
hashed. Interrupted calls remain charged. Packaging never triggers fitting.

## Commands

From the repository root, prepare without fitting:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_recovery_worker.py --prepare-only
```

Only after this exact finite allowance is approved, record authorization and launch
as separate commands:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_recovery_worker.py --record-authorization
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_recovery_worker.py --detach
```

Check the worker lock and completion before any resume. Do not repeat charged starts.
Completed evidence can be repackaged using `--package-only` without numerical fits.
