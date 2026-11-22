# The turn result holds across three receiver exports

All three receiver exports gave the globe a smaller best direction error
in the four second-leg cells. This comparison allows each shape to use
zero physical background field or the specified field with any fraction
retained in the gyroscope. All 96 matched settings had separated globe
and disc error bounds.

| Receiver export | Globe lower error | Smallest gap between the shape error bounds | Largest change from `air1` in the fixed angle predictions |
| --- | ---: | ---: | ---: |
| `air1` | 32/32 | 0.0170° RMS | Reference |
| `mosaic03` | 32/32 | 0.0187° RMS | 0.00782° RMS |
| `pwrpak7` | 32/32 | 0.0193° RMS | 0.00833° RMS |

The [first-leg comparisons](ESA_DIRECTION_HOLDOUT_RECEIVER_RESULT.md)
and this check now cover all eight flight cells with the alternate
receivers. The second leg uses the [whole-second times](ESA_DIRECTION_HOLDOUT_CLOCK_RESULT.md)
in the same cells as the original half-second check. Each receiver
prediction uses the same measured inertial angles at those shifted times.
The receiver exports share an antenna and all eight cells come from one
development recording.

## The strongest turn

Holding the physical field at zero favors the disc in all eight settings
per receiver. With the specified field retained in the gyro, all eight
settings per receiver favor globe. The table shows median RMS errors over
those settings. The field-removal setting gives smaller, mixed gaps.

| Receiver and sampling | Globe at zero field | Disc at zero field | Globe with specified field retained | Disc with specified field retained |
| --- | ---: | ---: | ---: | ---: |
| `air1`, original half seconds | 0.1703° | 0.0800° | 0.0123° | 0.2032° |
| `air1`, whole seconds | 0.1720° | 0.0782° | 0.0110° | 0.2025° |
| `mosaic03`, whole seconds | 0.1720° | 0.0778° | 0.0106° | 0.2020° |
| `pwrpak7`, whole seconds | 0.1708° | 0.0784° | 0.0107° | 0.2039° |

The field-range comparison on the turn still favors globe when both
shapes can choose from the tested field alternatives. This strongest-turn
check shows that the different answers at zero field and with the field
retained persist across the receiver exports and sampling phases.
An independent check of angle accuracy and an error model for future
flights are still needed.

## Reproduce the check

The [plan](ESA_DIRECTION_HOLDOUT_CLOCK_SCORE_PLAN.md) binds the sealed
receiver windows and earlier scores. All four inertial slices passed the
clock and support checks. They contain 478,920 original sample intervals
with a largest gap of 3.334 ms. The task used 29 charged operations and
zero fits in 87 seconds on one numerical thread. It used no reserved
flight group.

The [verified receipt](esa-direction-holdout-clock-score.json) has SHA-256
`b6e3eab5fa10cfe68038a1137de8cccf947cb497cb881a828ba7cd516205c0a0`.
Manifest SHA-256 is
`6c68d3e21cbb382c88bd35b89437258264e28fd0ecece87c2ef78a8ef8f95cb3`.
The [portable evidence bundle](esa-direction-holdout-evidence/clock-score/bundle.zip)
contains the frozen source, receiver inputs, charges and every scored window.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_direction_holdout_clock_score prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.studies run data/esa-direction-holdout-clock-score-v1 --reserved-threads 0
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_direction_holdout_clock_score report
```
