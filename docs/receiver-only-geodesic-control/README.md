# Two receiver-only forecasts on the same withheld positions

Both controls fit speed and course using the last 60 seconds of earlier
primary-receiver positions. The first extends a straight line in local
coordinates; the second follows a constant-course path on a declared
sphere. Neither uses IMU values or withheld positions before forecasting.
All six saved tasks completed with zero native model calls.

| Recording | Straight horizontal RMS | Spherical horizontal RMS | Spherical height RMS |
|---|---:|---:|---:|
| `0e73879f…` | 86.55 m | 33.14 m | 8.12 m |
| `3df34ea3…` | 351.45 m | 151.91 m | 6.53 m |
| `7024120d…` | 199.21 m | 189.26 m | 12.73 m |

The sphere is an assumption of this navigation control, not an
independent curvature measurement. These simple forecasts cannot
distinguish globe from disc or identify the gyroscope's separate
contribution. The three recordings are retrospective development data,
and their errors do not establish a confidence level.

[All matched scores](results.csv) · [Frozen method](PLAN.md) ·
[IMU prediction pilot](../ilvis0-retrospective-prediction-pilot-v2/INTERPRETATION.md)
