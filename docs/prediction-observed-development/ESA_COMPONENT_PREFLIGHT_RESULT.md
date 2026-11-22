# Where the two aircraft error terms can be tested

Steady acceleration error and short-lived maneuver error leave different
patterns in the predicted path. The earlier saved forecast can only test
the steady term. The later forecast can distinguish the two patterns in
the working model, although a single flight is too little to establish
how large either error should be on a new flight.

| Saved forecast, 120 later receiver reports each | Distinguishable variance terms, out of three | Information for the steady term | Information for the maneuver term |
| --- | ---: | ---: | ---: |
| After 200 training reports | 2 | 1.28–1.50 | 0 |
| After 400 training reports | 3 | 1.28–1.50 | 2.17–5.16 |

The third term is the original forecast covariance. The table reports
local information for each log variance after allowing the other scales
to vary. Ranges cover both existing descriptions of IMU measurement
error and both reference acceleration scales. They assume a fixed
predicted path and the working covariance model. They show which
effects can be separated and give no estimate of actual error scales.

## What the preselected windows contain

The earlier 800 receiver reports of each preselected window define the
interval inspected for recorded angular motion. Each entry below counts
receiver intervals whose root-mean-square angular speed exceeded the
working 1°/s trigger. Consecutive intervals can come from the same maneuver.

| Recording 187 window | First quarter | Second quarter | Third quarter | Fourth quarter | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| 187-042470-044870 | 0 | 0 | 0 | 0 | 0 |
| 187-049554-051954 | 123 | 64 | 0 | 0 | 187 |
| 187-058525-060925 | 11 | 1 | 1 | 82 | 95 |

The quiet window can serve as a control for steady error. The other two
provide examples with maneuver exposure mainly near opposite ends of
the training period. Keep all three selections. A calibration method
should first recover separate scales on generated data, recognize when
a scale is unsupported, and account for repeated intervals from the
same flight. Predictive coverage will require independent flights.

The check verified the archived forecast factors and both source files.
It decoded 719,097 inertial rows within the earlier windows, using the
sampled angular rate up to the next timestamp. No new trajectory fits
were run. Later receiver outcomes and reserved recordings remain unopened
by this check.

[Reproduction and limits](ESA_COMPONENT_PREFLIGHT_PLAN.md) ·
[Frozen inputs](esa-component-preflight-freeze.json) ·
[Detailed results](esa-component-preflight-result.json)
