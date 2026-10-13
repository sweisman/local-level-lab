# Why the rectangular recovery trial stalled

The completed trial passed **8 of 24 archival fits**: all six completed controls,
two of fifteen unfinished primary fits, and none of three perturbed repeats.
No test stretch became fully resolved. The preceding continuation method passed
15/24; the rectangular method did not improve recovery. Original findings remain
**12 globe preferences, zero completed flat preferences and 41 unresolved stretches**.

This audit verifies sealed summaries, journals and every saved local residual/Jacobian.
It reads no original aircraft observations, performs no native integrations or new
archival fits, and changes no scientific labels. Small affine-system solves below
are numerical diagnostics, not additional flight results.

## Two failure mechanisms

- **10 early gradient failures:** the optimizer
  stopped on parameter-step size while the independent gradient check still failed.
- **3 early stability failures:** the gradient passed,
  but the saved local correction changed predicted observations beyond the stability limit.
- **3 exhausted fits:** perturbed starts spent their allowance
  without satisfying stationarity.

Of the 13 early failures, **11** have at least
one outward-pointing gradient on a coordinate less than 1e-12 inside its bound.
Many distances are one floating-point step. Such a coordinate can restrict the
optimizer's initial feasible step even when other coordinates still need to move.
Passed controls can also have near-bound coordinates; proximity alone does not
explain or invalidate a fit.

## Independently reproduced boundary stall

A two-coordinate control has residuals `(x−2, 2y−0.4)` inside the unchanged box
`−1 ≤ x,y ≤ 1`. Its exact bounded answer is `(1, 0.2)`, with squared residual cost 1.
Starting one floating-point step below `x=1` with `y=0` makes the rectangular solver
stop after two evaluations at cost 1.16, before correcting `y`. Starting exactly at
`x=1` recovers cost 1. This isolates a numerical boundary effect without aircraft
physics, unknown instruments or an Earth-model preference.

## Does the same explanation hold on the saved flight tangents?

For each saved point `u₀`, the audit holds the recorded residual `r₀` and Jacobian `J`
fixed and solves **`r(u) = r₀ + J(u−u₀)`**. The two starts differ only by moving
coordinates within 1e-12 of ±1 to their exact bounds. The physical parameter box,
gradient threshold, optimizer settings and 200-evaluation limit remain unchanged.
A bounded linear least-squares calculation supplies a separate local reference.

Across all 24 saved systems, the original start passes the gradient check in
**12/24** cases; the exact-bound start passes in
**16/24**. These are *local linear* completion counts,
not recovered archival fits or passes of the full nonlinear stability gate.

| Stretch / processing | Model / start | Archival evaluations | Gradient / limit | Local gradient: original → exact-bound |
|---|---|---:|---:|---|
| 03454752 / profiled_removal | flat_still / primary | 3 | 5.15 | False → True |
| 03454752 / profiled_removal | flat_still / repeat | 598 | 482 | False → False |
| 03454752 / profiled_removal | sphere_rotating / primary | 97 | 3.39 | False → False |
| 03454752 / profiled_removal | sphere_still / primary | 3 | 72.1 | False → False |
| 03454752 / unsubtracted | sphere_rotating / primary | 3 | 46.8 | True → True |
| 03454752 / unsubtracted | sphere_still / primary | 4 | 29.8 | False → False |
| 233183f6 / profiled_removal | sphere_rotating / primary | 4 | 0.000222 | True → True |
| 233183f6 / unsubtracted | sphere_rotating / primary | 3 | 0.00128 | True → True |
| 233183f6 / unsubtracted | sphere_rotating / repeat | 598 | 3.78e+03 | False → False |
| b365bdf3 / profiled_removal | flat_still / primary | 4 | 44.9 | False → True |
| b365bdf3 / profiled_removal | sphere_rotating / primary | 4 | 0.059 | True → True |
| b365bdf3 / profiled_removal | sphere_still / primary | 3 | 4.42 | False → True |
| b365bdf3 / unsubtracted | flat_still / primary | 4 | 107 | False → False |
| b365bdf3 / unsubtracted | sphere_rotating / primary | 3 | 56.1 | False → True |
| b365bdf3 / unsubtracted | sphere_still / primary | 4 | 3.37 | False → False |
| b365bdf3 / unsubtracted | sphere_still / repeat | 598 | 4.79e+03 | False → False |

`True` means the local affine solve passed the same gradient threshold. CSV and
JSON retain all 24 cases, objective values, bound movements and reference costs,
including local failures.

## Weak directions and interpretation

The failed saved Jacobians have a median condition ratio of
**9.51e+07**. Strong and weak parameter combinations
therefore act on markedly different scales. The most frequent coordinates among
the three largest components of the weakest directions are: gravity_delta (16/16), gyro_gain_x (14/16), gyro_gain_y (9/16), gyro_gain_z (9/16).
Those directions describe correlated local combinations, not individually measured
instrument errors. Column-normalized spectra and column correlations are also saved.

An affine model is exact only for these saved linear equations. It cannot establish
that a sizeable local correction improves the actual nonlinear trajectory. The
audit does not test derivative accuracy, receiver-time discontinuities, changing
calibration or global optimality. It cannot promote any of the sixteen failed fits.

## Next qualification

Test boundary handling on known nonlinear optima and correlated, nearly singular
controls while retaining the existing feasible bounds and acceptance tolerances.
Compare objective and predicted-observation recovery from predetermined starts.
Only a separately frozen and budgeted observed-data trial can establish whether a
numerical repair recovers the unfinished stretches. The exhausted perturbed starts
also require attention; exact-bound initialization is not assumed to solve them.

## Reproduce

From the repository root:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-rectangular-diagnosis-20261012/build_report.py
```

The report receipt hashes both completed input studies, all local tangent artifacts,
audit software and generated outputs, and records the numerical environment.
Local optimizer counts describe that environment; they are not guaranteed across
platforms. The audit preserves the original trial's source snapshots.
