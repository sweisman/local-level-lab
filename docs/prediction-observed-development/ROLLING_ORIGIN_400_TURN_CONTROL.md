# GPS-only constant-turn forecast

This development rule was designed after the fixed-course GPS-only controls were scored. It fits one course turn rate to the last 60 earlier GNSS velocity reports and forecasts the same later 120 times. It uses no IMU data or later GNSS value to make its forecast.

The earlier fitted course turn rate is 0.522 degrees per minute.

| Forecast | Later horizontal RMS (m) | Later height RMS (m) |
| --- | ---: | ---: |
| GPS-only, constant turn | 448.369 | 16.877 |
| GPS-only, fixed reported velocity | 418.416 | 16.877 |
| Sealed conditioned IMU | 0.561 | 0.169 |

This single previously opened window is exploratory. The two GNSS fields share one PPP solution; the forecast is not an independent motion standard. Neither its success nor its failure isolates the gyroscope contribution or calibrates prediction coverage. No Earth-model decision follows.

[Fixed method](ROLLING_ORIGIN_400_TURN_CONTROL_PLAN.md) · [Detailed result](ROLLING_ORIGIN_400_TURN_CONTROL.json).
