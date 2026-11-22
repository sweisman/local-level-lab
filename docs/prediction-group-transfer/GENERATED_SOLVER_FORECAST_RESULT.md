# Generated solver forecast check

**6/6** fixtures pass the frozen four-fit forecast-agreement gate. 24/24 fits passed their numerical stopping checks; 0 had technical failures.

| Generated model | Clock | Four-fit gate | Maximum path spread |
|---|---|---:|---:|
| sphere_rotating | nominal | pass | 1.8e-07 m |
| sphere_rotating | variable | pass | 3.39e-09 m |
| sphere_still | nominal | pass | 2.44e-07 m |
| sphere_still | variable | pass | 5.61e-09 m |
| flat_still | nominal | pass | 1.7e-08 m |
| flat_still | variable | pass | 1.24e-08 m |

The largest error against the generated later trajectory is 3.19e-05 m. This is a software known-answer error, not aircraft positioning accuracy.

These are independently generated, 12-second software controls. Only the first 16 receiver positions entered each fit; the final eight scored the saved forecast. The original and verified-stop solvers used identical inputs and physical bounds from zero and opposed starts. This does not reclassify any observed fit or calibrate aircraft prediction uncertainty.

[Frozen plan](GENERATED_SOLVER_FORECAST_PLAN.md) · [All tasks](generated-solver-forecast-tasks.csv)
