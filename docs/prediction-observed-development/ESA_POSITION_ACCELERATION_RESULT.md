# Receiver positions narrow the acceleration uncertainty

The position-based estimate has much smaller reported uncertainty
than the velocity-based estimate. With 25 receiver reports, the
median force-magnitude standard deviation was 0.00044–0.00050 m/s²
assuming independent position errors. Allowing any time correlation
at the printed marginal covariances raises the upper bound to
0.0019–0.0022 m/s². All 96 individual upper bounds exceed the working
0.001 m/s² scale for steady acceleration error.

| Earlier window on recording 187 | Position SD, independent reports | Position upper SD, arbitrary time correlation | Median difference from velocity | Median difference between 11 and 25 positions |
| --- | ---: | ---: | ---: | ---: |
| 187-042470-044870 | 0.00044 | 0.00191 | 0.00293 | 0.01445 |
| 187-049554-051954 | 0.00048 | 0.00209 | 0.00372 | 0.01823 |
| 187-058525-060925 | 0.00050 | 0.00217 | 0.00630 | 0.02756 |

The first three numeric columns summarize the 25-report calculation
in m/s². Each window contributes 32 centers. The position and velocity
estimates were within 0.001 m/s² at 12 of the 96 centers with 25 reports.
Changing the number of positions used made a larger difference than
switching from positions to velocities at the longer time scale.

Position and velocity come from the same receiver solution. Neither
their agreement nor the printed uncertainty establishes true acceleration
at this precision. The two polynomial methods also average changes in
aircraft motion differently, even over the same number of reports. Use
matched averaging before comparing receiver acceleration with the raw
accelerometer. Check coarse maneuver calibration separately from the
harder question of measuring small steady drift.

The replay matched all 96 centers and completed all 192 derivative
calculations using only the earlier 2,400 receiver reports. It used the
same rotating-globe chart and fixed gravity convention as the velocity
check. It made no new trajectory fits or Earth-model comparisons.

[Plan and reproduction](ESA_POSITION_ACCELERATION_PLAN.md) ·
[Frozen inputs](esa-position-acceleration-freeze.json) ·
[Detailed results](esa-position-acceleration-result.json)
