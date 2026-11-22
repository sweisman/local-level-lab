# Generated nominal 200 Hz solver check

**6/6** generated fixtures passed the four-fit forecast-agreement gate. 24/24 fits passed numerical stopping; 24/24 passed the separate generated physical screen; 0 had technical failures.

| Generated model | Calibration | Numerical stops | Physical screen | Largest later-path spread |
|---|---|---:|---:|---:|
| sphere_rotating | interior | 4/4 | 4/4 | 3.08e-08 m |
| sphere_rotating | z_gyro_boundary | 4/4 | 4/4 | 4.75e-07 m |
| sphere_still | interior | 4/4 | 4/4 | 1.61e-06 m |
| sphere_still | z_gyro_boundary | 4/4 | 4/4 | 9.81e-09 m |
| flat_still | interior | 4/4 | 4/4 | 1.3e-05 m |
| flat_still | z_gyro_boundary | 4/4 | 4/4 | 4.76e-07 m |

Largest later RMS error against generated truth: 3.34 m horizontal and 1.25 m in height.

This exact 200 Hz grid checks the nominal-clock software path and matched solver forecasts with distinct noise seeds. Each fit uses 39 earlier receiver reports and predicts 20 withheld reports. It cannot test sensitivity to irregular packet-header timestamps. It does not revise aircraft fits or calibrate aircraft prediction coverage.

[Frozen plan](NOMINAL_200HZ_SOLVER_PLAN.md) · [All fit outcomes](nominal-200hz-solver-tasks.csv)
