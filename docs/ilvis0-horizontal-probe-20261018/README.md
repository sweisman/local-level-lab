# Fixed-point horizontal correction checks

Completed **36 generated-motion tangent evaluations**, zero optimizer starts and zero original-recording reads. Original fit labels and paired-start failures remain unchanged.

| Endpoint | Original probe passes | Ridge probe passes | Original actual cost | Ridge actual cost |
|---|---|---|---:|---:|
| sphere_rotating-bias1_unsubtracted-horizontal-zero | True | True | 1.45344e-12 | 7.16853e-15 |
| sphere_rotating-bias1_unsubtracted-horizontal-opposed | True | True | 4.66245e-10 | 4.71239e-10 |
| sphere_rotating-bias1_profiled_removal-horizontal-zero | True | True | 7.57714e-11 | 1.31182e-12 |
| sphere_rotating-bias1_profiled_removal-horizontal-opposed | True | True | 4.30418e-11 | 3.78868e-12 |
| sphere_still-bias1_unsubtracted-horizontal-zero | True | True | 2.15609e-08 | 2.16297e-08 |
| sphere_still-bias1_unsubtracted-horizontal-opposed | True | True | 3.25756e-12 | 9.56259e-15 |
| sphere_still-bias1_profiled_removal-horizontal-zero | True | True | 5.86559e-12 | 4.47772e-13 |
| sphere_still-bias1_profiled_removal-horizontal-opposed | True | True | 3.08e-12 | 1.38936e-12 |
| flat_still-bias1_unsubtracted-horizontal-zero | False | True | 1.17446e-07 | 5.33921e-14 |
| flat_still-bias1_unsubtracted-horizontal-opposed | False | True | 1.34287e-07 | 1.675e-14 |
| flat_still-bias1_profiled_removal-horizontal-zero | False | True | 1.08721e-07 | 2.90777e-14 |
| flat_still-bias1_profiled_removal-horizontal-opposed | False | True | 1.00477e-07 | 1.72477e-14 |

Passing an endpoint probe does not qualify a fitting algorithm or demonstrate paired-start repeatability. No observed-data refit follows automatically.

[Frozen scope](PLAN.md) · [Saved-array diagnosis](../ilvis0-horizontal-correction-audit-20261018/INTERPRETATION.md).
