# Analytic solver screen

This small software test uses independently known optima, not NASA measurements. It compares dense least squares with Jacobian scaling, dense least squares with unit scaling, and regularized iterative least squares. All have the same box constraints, stopping tolerances and 200-evaluation cap. There are eight controls and three deterministic starts per variant, including two 27-parameter controls with a Jacobian condition ratio of 50 million.

Passing requires solver success, a fresh stationarity check, agreement with the known objective and predicted residuals, and parameter recovery where unique. A success flag alone does not pass. These controls do not qualify full airborne integration, its staged initialization, or a global model optimum.

| Variant | Passed / 24 | Recorded evaluations |
|---|---:|---:|
| dense_jac | 24 / 24 | 331 |
| dense_unit | 24 / 24 | 301 |
| lsmr_jac | 18 / 24 | 1346 |

## Preserved failures

- lsmr_jac::mixed_interior::0: The maximum number of function evaluations is exceeded. Objective 1, residual error 0.000158091, stationarity 1.81664e-10.
- lsmr_jac::mixed_interior::1: The maximum number of function evaluations is exceeded. Objective 1, residual error 0.000178975, stationarity 1.29202e-10.
- lsmr_jac::mixed_interior::2: The maximum number of function evaluations is exceeded. Objective 1, residual error 0.000103558, stationarity 5.90322e-10.
- lsmr_jac::mixed_boundary::0: The maximum number of function evaluations is exceeded. Objective 1, residual error 0.00013977, stationarity 4.73209e-10.
- lsmr_jac::mixed_boundary::1: The maximum number of function evaluations is exceeded. Objective 1, residual error 0.000173495, stationarity 1.8205e-10.
- lsmr_jac::mixed_boundary::2: The maximum number of function evaluations is exceeded. Objective 1, residual error 0.000233835, stationarity 3.45351e-10.

[Complete results](solver-screen.csv) preserve every control. The screen makes **zero observed fit starts and zero native predictions**. Its completed evidence is frozen; `--render-only` regenerates this page without solving.
