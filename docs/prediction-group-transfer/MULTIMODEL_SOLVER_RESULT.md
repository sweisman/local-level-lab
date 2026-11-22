# Multimodel generated solver forecast check

**6/6** generated fixtures pass the four-fit numerical/forecast-agreement gate. 24/24 fits passed numerical stopping; 24/24 passed the separate generated physical screen; 0 had technical failures.

| Generated model | Calibration | Numerical stops | Physical screen | Largest later-path spread |
|---|---|---:|---:|---:|
| sphere_rotating | interior | 4/4 | 4/4 | 3.42e-07 m |
| sphere_rotating | z_gyro_boundary | 4/4 | 4/4 | 9.17e-07 m |
| sphere_still | interior | 4/4 | 4/4 | 3.15e-07 m |
| sphere_still | z_gyro_boundary | 4/4 | 4/4 | 8.83e-07 m |
| flat_still | interior | 4/4 | 4/4 | 3.03e-07 m |
| flat_still | z_gyro_boundary | 4/4 | 4/4 | 8.57e-07 m |

Largest later RMS error against generated truth: 0.363 m horizontal and 1.33 m in height.

These are software controls generated outside the fitter. The six model/calibration fixtures share one declared noise seed, so they are not six independent statistical replications. Each fit sees only 39 earlier receiver reports and predicts 20 later reports. Solver agreement and generated physical accuracy are separate outcomes. This does not revise any aircraft fit, calibrate prediction coverage or open reserved confirmation flights.

[Frozen plan](MULTIMODEL_SOLVER_PLAN.md) · [All fit outcomes](multimodel-solver-tasks.csv)
