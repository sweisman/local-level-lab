# Sealed ESA forecast against three receivers

The unchanged early-only conditional forecast is scored against three PPP exports on the same 120 later times from opened recording 187. The `air1` score is reproduced exactly before the other two streams are scored. Their positions are moved to the forecast epoch using reported velocity and the submillisecond timestamp offset.

| Saved IMU error law | Receiver | Horizontal RMS (m) | Height RMS (m) |
| --- | --- | ---: | ---: |
| increment | air1 | 0.561 | 0.169 |
| increment | mosaic03 | 0.554 | 0.197 |
| increment | pwrpak7 | 0.563 | 0.197 |
| point | air1 | 0.561 | 0.169 |
| point | mosaic03 | 0.554 | 0.197 |
| point | pwrpak7 | 0.563 | 0.197 |

This comparison was designed after the `air1` result was known. The three GNSS receivers share an antenna and may share processing errors. Similar scores would check receiver-specific sensitivity, not prove physical accuracy, calibrated coverage or an Earth-model decision. No protected flight or new fit was used.

[Fixed method](PARALLEL_GNSS_FORECAST_PLAN.md) · [Detailed result](PARALLEL_GNSS_FORECAST_RESULT.json).
