# Reported-velocity receiver control

This follow-up was designed **after** seeing that two position-only receiver rules missed the ESA development window. It uses the last earlier GNSS-reported velocity, keeps it constant and predicts the same later 120 times. It does not use IMU samples or later receiver values to make its forecast.

| Forecast | Later horizontal RMS (m) | Later height RMS (m) |
| --- | ---: | ---: |
| Receiver, reported velocity | 418.416 | 16.877 |
| Receiver, position-derived linear | 416.835 | 16.498 |
| Receiver, position-derived geodesic | 424.259 | 15.496 |
| Sealed conditioned IMU forecast | 0.561 | 0.169 |

These are comparisons with specific fixed forecast rules on one development recording. The reported GNSS velocity is not an independently calibrated trajectory or a future turn forecast. Neither this comparison nor the earlier one isolates the gyro channel or validates prediction coverage. No Earth-model decision follows.

[Chronology and rule](ROLLING_ORIGIN_400_VELOCITY_CONTROL_PLAN.md) · [Detailed result](ROLLING_ORIGIN_400_VELOCITY_CONTROL.json).
