# A stronger GPS-only prediction control

The first receiver-only forecast extended a straight line in local
coordinates. A second, separately frozen control fitted the **same last minute
of earlier GPS positions** but followed a constant course along a declared
sphere. It scored exactly the same withheld receiver positions. No IMU values
entered either forecast.

| Recording | Straight GPS-only horizontal RMS | Spherical GPS-only horizontal RMS | Available field-globe IMU horizontal RMS |
|---|---:|---:|---:|
| A, southern IMU8 | 351.45 m | 151.91 m | 15.5–19.3 m among qualified starts; no complete three-model setting |
| B, northern IMU21 | 199.21 m | 189.26 m | 0.84–1.13 m; all four matched settings complete |
| C, southern IMU21 | 86.55 m | 33.14 m | 3.30 m in one complete matched setting |

Accounting for a curved route improves the receiver-only forecast, especially
on A and C. It does **not** erase the large prediction gap on B, where the
full three-model IMU comparison completes under all four clock/processing
settings. The spherical control's height RMS is 6.53 m on A, 12.73 m on B and
8.12 m on C.

This remains a **limited control**. The spherical path assumes globe geometry;
it is not independent evidence of curvature. Holding course and speed
constant cannot model every aircraft adjustment. Better GPS-only trajectory
methods might predict more closely. The comparison establishes that the
complete IMU-based procedure predicts B far better than these two fixed
receiver-only procedures; it does not isolate the gyroscope from the
accelerometer, fitted calibration, or physical motion assumptions. The three
recordings are retrospective development data, and none of these differences
is a calibrated significance result.

[Hash-checked matched scores](README.md) · [All values](results.csv) ·
[Original IMU pilot](../ilvis0-retrospective-prediction-pilot-v2/INTERPRETATION.md) ·
[Frozen spherical rule](PLAN.md)
