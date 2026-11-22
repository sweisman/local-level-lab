# Earlier GPS residuals correct all three available rolling misses

At the 600-report cut, conditioning on earlier GPS residuals reduced later
horizontal RMS from **28.62 m to 0.28 m** under both inertial error laws.
At the 800-report cut it reduced the increment-law error from **144.72 m
to 0.14 m**. The archived point-law forecast at that cut has no matching
earlier-conditioned path, so its adjusted result is unavailable.

| Rolling cut | Error law | Raw horizontal / height RMS | Adjusted horizontal / height RMS | Fixed limits before → after |
| ---: | --- | ---: | ---: | --- |
| 200 | Both | 0.35 / 0.25 m | 0.47 / 0.24 m | Pass → pass |
| 400 | Both | 5.38 / 0.58 m | 0.56 / 0.17 m | Pass → pass |
| 600 | Both | 28.62 / 0.30 m | 0.28 / 0.22 m | Fail → pass |
| 800 | Increment | 144.72 / 4.32 m | 0.14 / 1.56 m | Fail → pass |
| 800 | Point | 144.72 / 4.32 m | Unavailable | Fail → unavailable |

Combining these with the [eight earlier turn and steady comparisons](ESA_RAW_ACCURACY_RESULT.md),
all **23 available adjusted paths** met the same four descriptive limits.
Eleven windows met them under both laws. The twelfth met them under the
increment law, with the point-law comparison outstanding. At 200 reports,
the adjustment increased horizontal RMS under both laws within the limits.

The comparison uses the same first 120 later GPS positions before and after
adjustment. It binds each available path to its archived earlier fit and
instrument error law. All eight rolling cases were recorded, with seven
charged comparisons, zero refits and no new reads of original files.

All twelve windows share development recording 187, and each window's
two laws share measurements. These point forecasts describe agreement
with GPS at this horizon. The [longer forecast uncertainty audit](CONDITIONAL_COVERAGE_RESULT.md)
found substantial height undercoverage under the increment law at the
800-report cut. Aircraft error coverage and independent-flight accuracy
remain open. The seven reserved flight groups remain closed.

[Frozen plan](ESA_MATCHED_CONDITIONING_PLAN.md) ·
[All scores and limit flags](esa-matched-conditioning.json) ·
[Verified evidence bundle](esa-matched-conditioning-evidence/replay.zip)
