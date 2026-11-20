# Training limits flagged one of three later ESA misses

The fixed training limits warned of the largest horizontal miss. Two
other raw forecasts failed later even though their training residuals met
all four limits. Both inertial error laws gave the same outcome at every
window on development recording 187.

| Outcome | Windows under each law |
| --- | ---: |
| Later failure with a training warning | 1 |
| Later failure without a training warning | 2 |
| Later pass with a training warning | 0 |
| Later pass without a training warning | 9 |
| Missing score | 0 |

| Later miss | Training horizontal RMS | Later horizontal RMS | Training warning |
| --- | ---: | ---: | --- |
| Rolling cut 600 | 8.08 m | 28.62 m | No |
| Rolling cut 800 | 39.96 m | 144.72 m | Yes, RMS and peak horizontal error |
| Steady 21856 | 3.01 m | 11.54 m | No |

The table shows the increment law. The audit computed the flags from the
original fitted paths and earlier GPS observations, using the same fixed
limits as the [later raw accuracy audit](ESA_RAW_ACCURACY_RESULT.md).
The twelve warning records were sealed before they were compared with the
later outcomes. All 24 evaluations completed without new fits or original
file reads.

A large training error can warn against relying on a forecast. A small
training error alone leaves failures possible, so the later-position
check remains necessary. The windows share one flight. These counts leave
independent-flight accuracy and uncertainty uncalibrated.

[Frozen plan](ESA_TRAINING_WARNING_PLAN.md) ·
[All limits and scores](esa-training-warning.json) ·
[Verified evidence bundle](esa-training-warning-evidence/replay.zip)
