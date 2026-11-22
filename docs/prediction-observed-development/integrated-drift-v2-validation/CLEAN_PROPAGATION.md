# Clean 100 Hz propagation control

The independent analytic generator supplied exact motion and no
sensor or receiver error. The same local IMU integrator used in the
generated coverage study ran for 120 seconds at 100 Hz.

| Physical vibration | Maximum north error | Maximum east error | Maximum up error |
|---|---:|---:|---:|
| off | 0.000208 m | 0.000003 m | 0.000001 m |
| on | 0.000323 m | 0.000002 m | 0.000002 m |

The largest clean integration error is below 0.0004 m. The four
[saved generated exceedances](VIBRATION_DIAGNOSTIC.md) have absolute
prediction errors of 0.15–0.67 m at their maxima. Thus clean 100 Hz
integration error alone does not explain those misses. This control
does not diagnose changing sensor noise, conditioning or actual
aircraft data.

[Machine report](CLEAN_PROPAGATION.json) ·
[frozen coverage result](RESULT.md).
