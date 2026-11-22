# The maneuver response and straight-flight drift need separate scales

On the two 120-report development forecasts, a motion-dependent error
term received **no triggers** in the earlier window and **21 triggers**
in the later one. Triggers came from the recorded inertial angular
rate. The conditional forecast positions stayed fixed throughout.

| Error covariance with its scale estimated from the earlier holdout | Later mean squared standardized error | Later negative log score, lower is better |
|---|---:|---:|
| Archived covariance | 4.06 | −657.3 |
| Add persistent acceleration | 13.75 | 847.8 |
| Add the maneuver response | 1.94 | −1,029.0 |
| Add both under one variance scale | 5.92 | −552.4 |

The two IMU error descriptions give the same results to the displayed
precision. The maneuver addition improves both the squared score and
the joint score that penalizes wider uncertainty. The later squared
score remains above the early reference of one. The persistent
addition makes the earlier residual under its larger covariance
smaller, so the common variance estimate decreases. That smaller
scale transfers poorly, even when the maneuver term is also present.

On the separate 400-report [straight-flight holdout](ESA_MANEUVER_ERROR_RESULT.md),
a quadratic height displacement accounts for **99.8%** of the height
error energy. Its best constant acceleration is −0.000331 m/s² in the
reported upward coordinate, and the remaining height error is 0.535 m
RMS. The coefficient was chosen retrospectively from this same height
error. It describes the miss and supplies neither a measured inertial
bias nor a forecast correction that has been validated.

The straight-flight result supports a persistent drift term. The
shorter comparison supports testing a separate maneuver term. A
single variance multiplier is inadequate on these windows. A turn-free
window provides no information about the maneuver term's amplitude.
The next qualification should keep the component scales separate and
test them on windows that actually exercise both effects before using
a rule on an independent flight.

This development check reused one opened flight. No trajectory fits
were restarted, no new inertial sweeps were needed and no reserved
flight groups were opened.

[Fixed plan](ESA_MOTION_ERROR_LAW_PLAN.md) ·
[Earlier scale evidence](esa-motion-error-law-earlier.json) ·
[Full transfer and straight-flight results](esa-motion-error-law-result.json) ·
[Frozen design](esa-motion-error-law-freeze.json)
