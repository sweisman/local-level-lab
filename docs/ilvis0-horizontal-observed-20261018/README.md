# Horizontal-only recorded-flight refits

Completed 24/24 fits, with 24 passing the numerical fit gate. Used 1112 of 4,860 permitted native calls, including twelve reconstruction checks. The original **53 globe / zero flat / zero unresolved** findings are preserved.

| Stretch | IMU configuration | Duration (min) | Horizontal-only matched result | Passed repeat pairs |
|---|---:|---:|---|---:|
| b365bdf39150ee6afc303ac1 | 8 | 9.75 | globe | 6/6 |
| 7df21c836bec5751f83c0cce | 21 | 4.07 | unresolved | 3/6 |

These are development refits under assumed covariance and calibration limits. Horizontal-only scoring retains heights in initialization, covariance and propagation, as well as both IMU channels. An unresolved fit or repeat withholds the matched comparison; it is not equal model support.

[Frozen selection, method and allowance](PLAN.md) · [Measurement-contribution study](../ilvis0-measurement-contribution/README.md).
