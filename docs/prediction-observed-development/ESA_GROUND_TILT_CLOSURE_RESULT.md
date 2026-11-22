# Gyro and accelerometer agree on much of the motion at two ground stops

The iMAR gyro predicted changes in the accelerometer's direction better
than assuming the sensor stayed still. Agreement was much stronger at the
first stop. The result supports a tilt contribution to the large logged
rate variations even while the receiver reported low ground speed.

The [fixed check](ESA_GROUND_TILT_CLOSURE_PLAN.md) divided both previously
selected stops into complete one-second averages. It then used the original
gyro timestamps to predict how each earlier accelerometer direction would
appear later. No offset or sensor-axis alignment was fitted. The table gives
root-mean-square angular error in arcseconds, where 3,600 arcseconds equal one
degree.

| Stop | Separation | Pairs | Error assuming no motion | Error using the gyro |
| --- | ---: | ---: | ---: | ---: |
| First | 1 s | 2,705 | 874 | 298 |
| First | 10 s | 270 | 819 | 246 |
| Second | 1 s | 1,843 | 239 | 189 |
| Second | 10 s | 184 | 514 | 440 |

After removing the mean change from each series, the gyro reduced squared
error by **88–92%** at the first stop and **30–38%** at the second. The centered
direction changes had similarity 0.96 at the first stop and 0.59–0.61 at the
second, on a scale where 1 indicates agreement in direction. All complete
pairs were included. The two time scales reuse samples.

Accelerometer direction gives a tilt reference only when linear acceleration
is small. It cannot detect turning about its own axis. Both channels also
share the mounting and instrument processing. The check therefore leaves yaw,
gyro-only error and absolute airborne prediction accuracy unresolved.

The closed task verified the original file hash and both selected time ranges.
It decoded 1,365,152 intervals, used seven charged operations and ran zero
Earth-model fits. No reserved group was opened. The [summary receipt](esa-ground-tilt-closure-result.json)
binds the full per-pair results to the frozen calculation.

[Source and execution receipts](ground-tilt-closure-evidence/README.md) ·
[Verified reproduction bundle](ground-tilt-closure-evidence/bundle.zip)
