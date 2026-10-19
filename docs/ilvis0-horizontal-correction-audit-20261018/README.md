# Saved horizontal correction audit

All twelve saved endpoints were inspected with three affine formulations each: **36 linear solves**, zero native predictions and zero model refits. The failed parent qualification remains unchanged.

| Endpoint | Original fit passed | Rank / columns | Original probe max step | Scaled probe max step | Ridge probe max step |
|---|---|---:|---:|---:|---:|
| sphere_rotating-bias1_unsubtracted-horizontal-zero | True | 23/26 | 0.001 | 0.001 | 5.53e-07 |
| sphere_rotating-bias1_unsubtracted-horizontal-opposed | True | 23/26 | 0.001 | 0.001 | 3.99e-05 |
| sphere_rotating-bias1_profiled_removal-horizontal-zero | True | 24/27 | 0.001 | 0.001 | 5.51e-06 |
| sphere_rotating-bias1_profiled_removal-horizontal-opposed | True | 24/27 | 0.001 | 0.001 | 1.18e-05 |
| sphere_still-bias1_unsubtracted-horizontal-zero | True | 24/26 | 0.001 | 0.001 | 0.000115 |
| sphere_still-bias1_unsubtracted-horizontal-opposed | True | 23/26 | 0.001 | 0.001 | 1.71e-05 |
| sphere_still-bias1_profiled_removal-horizontal-zero | True | 24/27 | 0.001 | 0.001 | 4.24e-05 |
| sphere_still-bias1_profiled_removal-horizontal-opposed | True | 24/27 | 0.001 | 0.001 | 7.92e-06 |
| flat_still-bias1_unsubtracted-horizontal-zero | False | 23/26 | 0.001 | 0.001 | 2.1e-06 |
| flat_still-bias1_unsubtracted-horizontal-opposed | False | 23/26 | 0.001 | 0.001 | 1.52e-06 |
| flat_still-bias1_profiled_removal-horizontal-zero | False | 24/27 | 0.001 | 0.001 | 2.06e-06 |
| flat_still-bias1_profiled_removal-horizontal-opposed | False | 24/27 | 0.001 | 0.001 | 1.06e-06 |

These are linear predictions at saved endpoints. They cannot establish a fresh nonlinear improvement, change stopping labels or qualify observed-data fitting. Ridge regularization changes the diagnostic correction objective; it does not change any physical-model score.

[Scope and call-allowance correction](PLAN.md) · [Interpretation](INTERPRETATION.md) · [Next analyses](../NEXT_STEPS.md).
