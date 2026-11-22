# Receiver-only forecast control

On the same preselected 400-training/120-later ESA development window, two fixed rules predict from earlier GPS receiver positions alone. Neither uses IMU data or later receiver positions to make its forecast. The IMU rows reuse the sealed early-only conditioned forecasts.

| Forecast | Later horizontal RMS (m) | Later height RMS (m) |
| --- | ---: | ---: |
| Receiver only: linear | 416.835 | 16.498 |
| Receiver only: geodesic | 424.259 | 15.496 |
| IMU plus receiver: increment, conditioned | 0.561 | 0.169 |
| IMU plus receiver: point, conditioned | 0.561 | 0.169 |

The receiver-only rules estimate speed from the last minute of positions and hold it constant. They do not use the receiver export’s reported velocity columns or adapt to later turns. Their large miss on this maneuvering window does not prove that the gyro alone caused the IMU forecast advantage: accelerometers, model assumptions and the earlier receiver correction contribute too. This is one development recording, not independent validation or a calibrated physical-accuracy claim. No Earth-model decision follows.

[Fixed rules and selection](ROLLING_ORIGIN_400_RECEIVER_CONTROL_PLAN.md) · [Detailed result](ROLLING_ORIGIN_400_RECEIVER_CONTROL.json).
