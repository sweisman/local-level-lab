# Allowing gyro calibration narrows the difference between shapes

With all **12 gyro and accelerometer calibration coordinates** available,
the globe gave smaller later angular errors in **17 of 18 matched
comparisons**. The disc gave the smaller error in one retained-field
setting. Using GLONASS-derived velocity and 11-report averages, the disc
scored **0.0761° RMS** and the globe **0.0823° RMS**. The two calibrations
in that comparison were chosen on the earlier eight directions.

| Matched field setting | Globe / disc lower error | Globe later RMS | Disc later RMS | Paired difference, disc minus globe |
| --- | ---: | ---: | ---: | ---: |
| Zero field | 6 / 0 | 0.240–0.257° | 0.352–0.367° | +0.107 to +0.113° |
| Specified field retained in gyro | 5 / 1 | 0.008–0.084° | 0.065–0.089° | −0.006 to +0.063° |
| Specified field removed from gyro | 6 / 0 | 0.240–0.257° | 0.352–0.366° | +0.107 to +0.113° |

With the [gyro fixed](ESA_DIRECTION_ACCEL_CALIBRATION_RESULT.md), the
retained-field globe margin was +0.093 to +0.107°. Allowing gyro bias and
gain absorbs much of that difference. The six velocity and averaging
combinations reuse the same flight and should be read as sensitivity
checks. Their direction errors have no calibrated accuracy threshold.

The optimizer used an approximation to propose calibrations on the
earlier directions. All 108 proposals were replayed through the corrected
gyro increments before the later angles were scored. The largest earlier
approximation error was 0.000017 in unit-vector chord RMS, below the
frozen 0.0001 limit. Six starts failed the projected-gradient check on
the approximation. Each candidate and setting still had at least one
eligible start. Every proposal reached at least one working bound.
These are exact replays at the proposed points. Optimality for the exact
nonlinear calculation and coverage of the full calibration box are open.

The recorded work contains 108 starts, 14,088 search evaluations and 121
gyro packet passes. No full inertial fit, original data-file read or
reserved-flight access was used. The 120 later positions from the
original position forecast stayed outside this comparison.

## Reproduce the result

With the closed `data/esa-direction-joint-calibration-v1` study restored,
run the saved-report command to verify its artifacts and charges.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_direction_joint_calibration report
```

[Frozen design](ESA_DIRECTION_JOINT_CALIBRATION_PLAN.md) ·
[Starts, replay checks and later errors](esa-direction-joint-calibration-result.json)
