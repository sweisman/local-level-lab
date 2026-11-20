# A GPS-only prediction reference on the ESA development recording

Two fixed rules used only the final 60 seconds of the **800 earlier GPS
receiver positions** to predict the same 400 later positions used by the
sealed IMU forecast. Neither rule used IMU measurements or later positions
while constructing its prediction. Both used 61 earlier positions.

| Prediction | Later horizontal RMS | Largest horizontal error | Later height RMS |
|---|---:|---:|---:|
| Straight local velocity from GPS | 535 m | 1,055 m | 15.2 m |
| Constant course on a sphere from GPS | 572 m | 1,111 m | 14.8 m |
| Saved IMU forecast, either error law | about 249 m | about 390 m | 4.35 m |

The IMU forecast is closer to the receiver trajectory than these **two fixed,
simple GPS-only rules** on this one development recording. It still fails
the preset horizontal accuracy limits, including the **40 m RMS training
miss**. This comparison does not isolate the gyroscope from accelerometry,
calibration or motion assumptions. The spherical GPS rule assumes globe
geometry and cannot independently establish curvature. No uncertainty or
Earth-model decision is calibrated by these numbers.

The [machine-readable audit](drift-audit.json) binds the sealed study, the
fixed rule source hashes and the [predeclared comparison](RECEIVER_REFERENCE_PLAN.md).
It reports every score, including both IMU error-law results, without a new
fit or native propagation. Seven ESA confirmation groups remain unopened.

[ESA continuation](CONTINUATION_RESULT.md) · [error-trend audit](DRIFT_AUDIT.md).
