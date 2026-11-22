# The direction forecast still favors the globe with all accelerometer axes free

The globe had smaller later force-direction errors in **all 18 matched
comparisons** when each shape could fit all three accelerometer biases
and all three gains from the earlier directions. With the specified field
retained in the gyro, the later globe error was **0.004–0.020° RMS**, versus
**0.109–0.113°** for the disc. The gyro increments stayed fixed.

| Field setting, matched between shapes | Later angular RMS, globe | Later angular RMS, disc | Globe advantage across paired settings |
| --- | ---: | ---: | ---: |
| Zero field | 0.293–0.306° | 0.402–0.417° | 0.109–0.112° |
| Specified field retained in gyro | 0.004–0.020° | 0.109–0.113° | 0.093–0.107° |
| Specified field removed from gyro | 0.294–0.307° | 0.403–0.418° | 0.108–0.112° |

All 108 starts met the frozen projected-gradient criterion. The numerical
library reported a line-search warning for 41 of them. Those flags remain
in the results. The later RMS errors for the three starts at each setting
agreed within 4.7 × 10⁻⁹°.

The calibration derivative has rank five after accounting for the unknown
starting rotation. A common gain scale cancels
when a force vector is converted to a unit direction. At least one calibration
coordinate hit its working bound in 99 starts. With the specified field
retained, the globe's earlier fit selected X biases from −0.009 to +0.015
m/s² and the disc selected +0.027 to +0.051 m/s². With the field absent from
the gyro, both shapes selected the +0.10 m/s² X limit. These fitted values
do not determine the instrument's true calibration.

This is an earlier-only calibration with eight later direction checks on
one previously opened flight. The direction errors have no calibrated
acceptance limit. The test leaves gyro gain, gyro bias, partial onboard
field removal and independent-flight coverage open. All 108 starts and
6,659 actual training evaluations were retained. The prepaid ceiling was
21,600. No full inertial fit or reserved-flight data was used.

## Reproduce the result

With the closed `data/esa-direction-accel-calibration-v1` study restored,
verify the saved scores and charges without fitting.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_direction_accel_calibration report
```

[Frozen design](ESA_DIRECTION_ACCEL_CALIBRATION_PLAN.md) ·
[All starts, boundary values and later errors](esa-direction-accel-calibration-result.json)
