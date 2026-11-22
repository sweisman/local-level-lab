# Do recorded IMU channels change together?

This saved-data check uses the first 13.33 minutes of ESA development recording 187. It reads the same sealed training samples used by the [rate-variation study](../esa-training-rate-variation/README.md). No new fit, original file or reserved flight group is opened.

Each row takes disjoint groups of three samples, removes a straight line at their actual timestamps, then compares the six resulting channel changes. The table shows the strongest same-time pairing between a gyroscope and an accelerometer axis.

| Sample span (s) | Groups | Axis pair | Correlation |
| ---: | ---: | --- | ---: |
| 0.0067 | 79954 | gyro_y / force_x | -0.628 |
| 0.0200 | 26651 | gyro_y / force_x | -0.360 |
| 0.2000 | 2665 | gyro_y / force_x | -0.239 |
| 2.0000 | 266 | gyro_y / force_x | -0.747 |

A shared change can reflect aircraft motion or vibration. No shared change would not prove sensor noise: motion can affect axes at different times or leave one channel nearly unchanged. This check does not separate sensor bias, sensor noise, aircraft motion or receiver error and does not calibrate prediction uncertainty.

[All six-axis correlations and source hashes](RECORDED_CHANNEL_DEPENDENCE.json) · [Next qualification](OBSERVED_ERROR_PLAN.md).
