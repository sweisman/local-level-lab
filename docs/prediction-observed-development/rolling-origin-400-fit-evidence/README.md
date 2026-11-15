# Earlier-origin fit result

The first 400 receiver reports in the already opened ESA development window
were fitted under both preregistered IMU error laws. The following 120 receiver
positions were absent from the fit inputs. Both numerical tasks sealed and
passed. They used one start each and eight evaluations each; neither fit had
an active calibration bound.

| Assumed IMU error law | Training cost | Evaluations | Active bounds |
| --- | ---: | ---: | ---: |
| Recorded increments | 5.102913 | 8 | 0 |
| Point rates | 5.102906 | 8 | 0 |

The nearly equal costs do not identify which error law describes the aircraft.
These are fits to the first 400 positions, not tests on the next 120. A separate
early-only conditioning calculation must close before those later positions
are scored. No physical adequacy or Earth-model decision follows from this
fit result.

The verified study is `data/esa-rolling-origin-400-development-v1-20261115`.
Its manifest SHA-256 is
`ed1c026bbcb4d280913d0ef58280967dcfa7cc784f73b32773182db00f0864cb`
and its completion seals summary SHA-256
`8f5a8cd721873c8ee9d0cb18fa20e194b97efd1746d27cc96a1c2b4b5c1b5da3`.
