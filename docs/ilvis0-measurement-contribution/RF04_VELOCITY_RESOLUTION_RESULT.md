# How RF04 reports GPS velocity

The reported speed and course reproduce the reported north/east velocity
to **0.000026 m/s RMS** when projected onto those axes. All **443**
course values fall on a **0.02° grid** within the test tolerance, while
405 fall on a 0.1° grid. This is consistent with averaging five readings
rounded to tenths of a degree. The archive supplies one report per second,
so the original five readings and the exact averaging rule remain unknown.
The tested 0.001-knot speed grid and its five-reading average match 75
and 350 of the 443 reports, respectively.
[Frozen plan](RF04_VELOCITY_RESOLUTION_PLAN.md)

On this nearly southbound stretch, small changes in reported course change
the east component much more than the north component. Using a hypothetical
0.1° course step and 0.001-knot speed step, rounding at the two endpoints
could account for the magnitude of every tested east discrepancy. The north
disagreement sometimes exceeds that allowance. [Acceleration cross-check](RF04_REFERENCE_ACCELERATION_RESULT.md)

| Window | Median north / east rounding allowance, m/s² | Later north windows beyond allowance, onboard / carrier phase | Later east windows beyond allowance |
| --- | ---: | ---: | ---: |
| 2 s | 0.0084 / 0.1994 | 12 / 12 | 0 of 118 for each track |
| 6 s | 0.0028 / 0.0665 | 40 / 41 | 0 of 118 for each track |
| 10 s | 0.0017 / 0.0399 | 49 / 51 | 0 of 118 for each track |

Rounding is a plausible contributor to the east discrepancy. The test
does not measure its actual contribution or bound other GPS errors.
NCAR documents an offset between the GPS antenna and its own inertial
reference, which can also affect the velocity measured while the aircraft
turns. The position of the Applanix antenna relative to that reference
still needs evidence before this can become an error correction.
[NCAR processing note](https://ncar.github.io/aircraft_ProcessingAlgorithms/3-the-state-of-the-aircraft#global-positioning-systems)

All nine charged operations completed on one numerical thread. The
study replayed the earlier acceleration statistics for both tracks
without a new Earth-model fit, original IMU decode or reserved ESA read.
SHA-256 `f7d3b25dee6935d195a09d827ff3cabc3bf76fa9179660e3b969d2852337af26`.
[Machine-readable result](rf04-velocity-resolution-result.json) ·
[Frozen execution evidence](rf04-velocity-resolution-evidence/README.md)
