# Known calibration on the saved noisy streams

Both frozen tasks completed. The same generated IMU measurements were forecast from the known initial state and sensor corrections, without fitting them to receiver positions. Future physical truth was used only for scoring reports 600–899.

| Noise construction | Known calibration horizontal RMS (m) | Fitted horizontal RMS (m) | Known calibration vertical RMS (m) | Fitted vertical RMS (m) |
| --- | ---: | ---: | ---: | ---: |
| increment | 59.66 | 50.47 | 31.93 | 1.54 |
| point | 637.12 | 84.35 | 7.14 | 4.94 |

Known calibration did not remove future drift in either generated stream. The fitted forecasts were more accurate on these two fixed draws, especially for point-rate noise. This control does not assign the drift to any one noise, timing or motion mechanism, establish calibrated prediction coverage, or decide an Earth model. The seven reserved ESA confirmation groups remain unopened.

The [machine-readable report](ORACLE_NOISY_REPORT.json) records exact scores and source/evidence hashes.
