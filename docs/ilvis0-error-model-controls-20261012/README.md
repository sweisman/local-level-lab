# Shared error model: software checks

**All 35 analytic checks passed.** The proposed covariance calculations are ready
for further development. They have not been fitted to NASA recordings, calibrated
as measurement uncertainty, or substituted into the original Earth-model analysis.

An **IMU (inertial measurement unit)** measures turning and acceleration. The NASA
analysis compares IMU-derived motion with receiver positions. Their remaining errors
are correlated across time and axes. These checks test the mathematics needed to
describe that dependence fairly for all three physical models.

## What was checked

| Control | Independent answer or failure caught |
|---|---|
| White and cross-axis error | Hand-specified covariance blocks, including negative axis correlations; white error does not link different epochs. |
| One or two correlation components | Known exponential covariances at irregular times; positive, ordered time scales. |
| Offset and drift | A prediction subset retains the full-record drift origin and scale rather than restarting drift at the split. |
| Coordinate changes | Different per-epoch rotations and unit scales transform cross-epoch blocks, preserve quadratic cost, and correctly change the density determinant. |
| Whitening | A hand-calculated triangular factor gives innovations [1, 1], quadratic cost 2 and determinant 36. |
| Blocked prediction | Training variance 4, future variance 9 and cross-covariance 2 give predicted residual 1 from training residual 2, with future conditional variance 8. Ignoring the correlation would instead give mean 0 and variance 9. |
| Exact Gaussian moments | Six symmetric, independently generated points reproduce identity whitening and the analytic prediction-error covariance, without Monte Carlo sampling. |
| Difficult matrices and invalid data | A nearly singular positive covariance remains usable; singular/indefinite matrices, invalid times, overlapping splits and malformed inputs are rejected. No hidden jitter, clipping or timestamp repair. |
| Shared specification | Copying inputs prevents later array changes from altering the common error specification. |

The module supports white error, up to two exponentially correlated components,
constant offset and linear drift with cross-axis terms. Matrices are supplied in a
common north/east/up frame; explicit transforms change frames or units. It does not
choose an Earth model or estimate its own covariance from model-specific residuals.

Tiny roundoff asymmetry is averaged only after a relative symmetry check. Component
eigenvalues within a stated machine-roundoff tolerance are retained, not clipped.
Every final covariance must be positive definite. Diagonal equilibration before
Cholesky factorization handles different units without adding error variance.

## What this does not establish

The Gaussian prediction formulas assume the trajectory/residual mean and covariance
parameters are known. A real fit estimates calibration, initial conditions and error
parameters; their uncertainty must be included before predictive coverage is claimed.
The controls do not prove the chosen error family describes the archive, establish
receiver precision, improve solver convergence, or change any model preference.
They make **zero observed fit starts, zero native predictions and zero archive reads**.

## Next step

Develop training-only covariance estimation and an explicit treatment of fitted-
parameter uncertainty, with independent numerical controls. Then freeze the same
error specification for every physical candidate and test blocked predictions under
a separately approved finite observed-data allowance. Preserve all existing results.
The [development plan](../ilvis0-residual-covariance-20261012/ERROR_MODEL_PLAN.md)
sets the scientific constraints. Independent statistical calibration remains separate.

## Reproduce

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-error-model-controls-20261012/build_report.py
```

The qualification is small deterministic matrix arithmetic and input validation;
it does not launch an Earth-model campaign. The report receipt hashes the source,
tests, development plan and generated outputs and records the numerical environment.
