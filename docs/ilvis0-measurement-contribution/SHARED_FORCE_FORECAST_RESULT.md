# The GPS correction leaves the saved IMU forecast rankings unchanged

The [same GPS correction that cleared the IMU8 force-only gaps](SHARED_FORCE_WITNESS_RESULT.md)
left every saved forecast comparison in the same order. The globe forecast
had smaller horizontal and height errors than the disc forecast when both
used the specified angular field. This held at 30, 60 and 120 seconds and
over both full forecasts. The globe comparison with and without the field
also kept its original order.

| Recorder | Full forecast | Globe horizontal RMS | Disc horizontal RMS | Globe height RMS | Disc height RMS |
| --- | --- | ---: | ---: | ---: | ---: |
| IMU8 | Original GPS | 19.36 m | 242.51 m | 10.485 m | 22.218 m |
| IMU8 | Corrected GPS | 19.36 m | 242.51 m | 10.492 m | 22.224 m |
| IMU21 | Original and zero-correction control | 2.18 m | 70.07 m | 5.050 m | 8.281 m |

These are comparisons with the specified field in both shapes. The IMU8
GPS change reached 27.2 cm in height and 1.9 mm horizontally. Every paired
mean squared-error gap changed by less than 0.2%. The zero-field disc
forecasts remain unavailable on both recordings.

All six forecasts and 371 later receiver epochs were matched to their
original coordinates and timestamps. The calculation made no new fits
or propagations. The GPS correction was constructed using the force
comparisons on both periods. This is a sensitivity check, and it leaves
independent prediction coverage and gyro-only attribution open.

[Frozen method](SHARED_FORCE_FORECAST_PLAN.md) ·
[All score comparisons](shared-force-forecast.json) ·
[Verified evidence bundle](shared-force-forecast-evidence/replay.zip)
