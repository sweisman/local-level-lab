# The research in order

This page is a short route through the airborne work. An **IMU (inertial
measurement unit)** records turning with gyroscopes and force with
accelerometers. The research compares those measurements with positions from
a separate GPS receiver. The [method page](METHODOLOGY.md) explains each step;
the [full study record](STUDIES.md) preserves the detailed history, including
failed attempts.

| Stage | What it added | What it does not settle |
|---|---|---|
| [Decode the recordings](ILVIS0.md) | Recovered the recorded IMU increments, timestamps and primary GPS receiver stream from airborne lidar survey files. | The instrument's exact onboard corrections are not fully documented. |
| [Select stretches](ilvis0-highspeed-segments-20261008/ELIGIBILITY.md) | Chose 53 complete stretches totaling 424.3 minutes using flight quality and speed, before checking which model fitted best. | Several stretches share a flight or instrument. |
| [Compare Earth geometries](CURRENT_STATUS.md) | All 53 completed numerical comparisons prefer globe geometry to the tested stationary flat disc. The first 12 completed in the original run; separately checked work completed the other 41. | A preference is not yet a calibrated significance level, and the flat-disc candidate is one specified model. |
| [Compare background fields](CURRENT_STATUS.md) | On those globe-preferred stretches, the specified nonzero angular field fits better than zero field under both processing assumptions. | This does not measure the field's cause or distinguish solar from sidereal rate. |
| [Check what drives the result](ilvis0-measurement-contribution/README.md) | Raw-gyro graphs, reduced-observation checks and receiver-only controls probe the roles of gyroscopes, acceleration, GPS and height. | A complete, calibrated separation of each channel's contribution is still open. |
| [Predict measurements left out of fitting](PREDICTION_VALIDATION.md) | One airborne recording passed a complete retrospective comparison. In a different archive, two complete three-model settings on one development flight favor globe when predicting later positions; two settings remain unresolved. | These are development tests, not independent confirmation or an aircraft-wide accuracy guarantee. |
| [Check the ESA solver and calibration](prediction-observed-development/SHAPE_REMAINDER_METRES_RESULT.md) | [Two solvers agreed](mixed-tangent-hybrid/OBSERVED_DISPATCH_FRESH_RESULT.md) on all 16 matched globe comparisons. A separate check calculated how small the position error from the linear approximation needs to be to preserve the globe–disc difference. | The four-centimetre bound is a target under the tested assumptions. The proof still needs to account for how the gravity calculation changes with height. |
| [Test uncertainty on generated flights](PREDICTION_ERROR_LAW_PLAN.md) | A simulated-data calibration and validation passed its declared rule. One 96-recording whole-period check failed its 5% gate after four time-limit stops; a separately seeded [96-recording check](prediction-simultaneous-law-family-v3/RESULT.md) passed with 95 recordings passing and one numerical failure counted. | Simulated coverage does not establish error coverage for real aircraft. |
| [Confirm and quantify confidence](NEXT_STEPS.md) | Separate flight groups have been reserved, and shared recordings have been grouped for analysis. | Independent confirmation and a calibrated confidence level are still pending. |

The current **53 / 0 / 0** count means *globe preferred / flat preferred /
unresolved* within the selected comparison. It is not a count of independent
flights. The [stretch list](ilvis0-current-findings-20261015/STRETCHES.md)
shows each interval; the [detailed CSV](ilvis0-current-findings-20261015/stretch-analytics.csv)
includes speed, latitude, course, measured rate summaries, fit costs and
stopping reasons.

The separate [stationary ground experiment](STATIONARY.md) is being developed
for consumer IMUs. It does not use the airborne results as a calibration.
