# Receiver velocity resolves maneuvers better than small steady drift

The three selected ESA training windows show different levels of aircraft
motion. The largest estimated horizontal acceleration rose from 0.18 to
1.12 m/s² across the windows using the 25-report calculation. That gives
the next calibration check more motion to work with than the ground stops.

At the much smaller 0.001 m/s² drift scale, receiver velocity alone gives
little leverage. The median standard deviation propagated from the printed
velocity covariances was 0.038–0.043 m/s² even assuming independent reports.
Allowing any temporal correlation at those same marginals raises the median
upper bound to 0.166–0.187 m/s².

| Earlier window on recording 187 | Peak horizontal acceleration, m/s² | Median force-magnitude SD, independent reports | Median upper SD, arbitrary time correlation | Median difference between 11- and 25-report magnitudes |
| --- | ---: | ---: | ---: | ---: |
| 187-042470-044870 | 0.18 | 0.038 | 0.166 | 0.015 |
| 187-049554-051954 | 0.47 | 0.043 | 0.187 | 0.016 |
| 187-058525-060925 | 1.12 | 0.043 | 0.185 | 0.031 |

The peak and SD columns use the 25-report calculation. The last three
columns are in m/s². Only one of 96 matched times had force magnitudes
within 0.001 m/s² of each other at the two time scales. Smoothing can
change the estimate when the aircraft is actually accelerating. This
disagreement by itself cannot measure receiver error.

The estimates use the conventional rotating-globe receiver chart and a
fixed gravity magnitude. The reported covariance provides a sensitivity
calculation, with no independent check of its accuracy. This analysis
used 2,400 earlier receiver reports, no inertial measurements and no
new trajectory fits. The next check can compare acceleration inferred
from the same receiver's positions, whose printed covariance differs
from the velocity covariance. Agreement would be an internal check
because both estimates come from the same GNSS solution.

[Plan and reproduction](ESA_RECEIVER_ACCELERATION_PLAN.md) ·
[Frozen inputs](esa-receiver-acceleration-freeze.json) ·
[Detailed results](esa-receiver-acceleration-result.json)
