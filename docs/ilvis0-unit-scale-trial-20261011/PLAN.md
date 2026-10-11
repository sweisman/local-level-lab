# Matched solver-scaling comparison

This is a separate development freeze, not a retry of a completed study. It tests
whether fixed scaling improves the numerical search while leaving the measurement
problem unchanged. An IMU (inertial measurement unit) supplies angular and velocity
increments; GPS positions in the first portion supply the fitting observations.

## Target and unchanged scientific inputs

Reuse control `570b37d23af5e245dd461051`,
`ILVIS0_applanix_57300_610_LVIS_38614965.013`, IMU type 21,
2015-10-05 12:45:50–12:53:08 UTC, median ground speed 878.06 km/h.
Use the previously saved 292 training epochs and 147 prediction epochs. Keep
training-only initialization, the IMU prefix with its existing latency allowance,
packet-header timing, covariance and its full-window normalization, both processing
cases, every physical bound, staged initialization and all three physical models.
Propagate the prediction continuously without a GPS reset or further fitting.

The full optimization stage changes only SciPy's `x_scale` from `jac` to `1.0`.
The initialization stage keeps `jac` scaling. The parameters already have normalized
bounds of −1 to +1; unit scaling holds the trust-region scale fixed rather than
updating it from Jacobian column norms. Preserve the original solver tolerances,
fresh projected-stationarity criterion and success requirement. Extra logging
records accepted-step cost/error changes, gradient components and right singular
vectors; these are diagnostics, not relaxed acceptance criteria.

## Qualification and success criteria

The analytic screen passed 24/24 known-optimum controls for both dense methods.
The iterative method failed six and is excluded. The implemented candidate passes
24 recovery controls plus a staged-initialization/budget test. These are small
software checks, not qualification of full airborne optimization or a global optimum.

Compare the six new fits with the six saved original prediction fits. Report every
change in convergence, objective, parameters at limits, stationarity, training errors
and prediction errors. A useful improvement must preserve convergence of the five
previously completed fits and complete the sixth. For previously converged identities,
the training objective must not worsen by more than 0.1%; larger changes are reported
as a failed qualification comparison, even if the model ordering looks favorable.
Improved objectives may indicate a better local fit, not proof of a global minimum.

Keep calibration robustness separate from numerical qualification: the audit found
Z gain switching from −2% in whole-stretch fits to +2% in training-only fits, and
gravity correction returning to its lower limit. A completed solver cannot explain
those parameter movements by itself. Preserve direct errors and covariance diagnostics
separately, including their omission of fitted-parameter uncertainty.

Shape compares the globe family with flat first. Report rotation only after all
six fits converge and both cases favor globe. Statistical decisions still abstain.
Do not widen bounds, add bias flexibility, change the split or use prediction errors
to select another starting point.

## Finite allowance and recovery

Proposed allowance: **six starts, one per identity, 200 evaluations per start,
no retries**, one worker with two total numerical threads. The 200 cap includes
initialization, the fresh final tangent and two post-fit value predictions.
The previous trial used 887 evaluations in 40.4 fitting/diagnostic minutes. Its
slowest measured rate projects about 56 minutes for all 1,200 evaluations; allow
roughly **55–65 minutes** plus setup/publication, without treating that estimate
as a wall-clock guarantee. This new numerical allowance requires explicit approval.

Freeze source/input/environment hashes and the exact split before launch. Preserve
the final v2 freeze at `data/ilvis0-unit-scale-trial-v2-20261011/`; the superseded
zero-start preparation at `data/ilvis0-unit-scale-trial-20261011/` must not be run.
The v2 manifest explicitly includes the stationarity and software-control dependencies.
Preserve
exclusive locks, append-only start charges and atomic hashed outputs. Check completion
and locks before recovery; interrupted starts remain charged, with no retry. Never
resume the original completed prediction trial or borrow its unused evaluations.
Publication performs no fitting; stop after the comparison, without automatic rollout
or replication starts.

Preparation starts no fits:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python analysis/tests/ilvis0_unit_scale_trial.py --prepare-only
```

After approval only, use the same environment with `--detach`. After completion,
use `--package-only`; render saved evidence with this guide's `build_report.py`.
