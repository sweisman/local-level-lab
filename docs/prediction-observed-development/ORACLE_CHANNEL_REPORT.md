# Which injected IMU channel drives the generated drift?

Four frozen forecasts completed on the same two generated noise draws. Each kept one noisy IMU channel and replaced the other with its clean counterpart. All used the known initial state and sensor calibration; later truth only scored reports 600–899.

| Error law | Noisy channel | Future horizontal RMS (m) | Future vertical RMS (m) |
| --- | --- | ---: | ---: |
| increment | gyro only | 75.71 | 2.67 |
| increment | accelerometer only | 17.41 | 35.09 |
| increment | both | 59.66 | 31.93 |
| point | gyro only | 651.36 | 14.64 |
| point | accelerometer only | 19.83 | 6.57 |
| point | both | 637.12 | 7.14 |

On both fixed draws, the gyro channel dominates horizontal error. The full-noise error is not the sum of the two separate errors; the channels interact in propagation. This does not isolate white noise from changing bias, estimate a recorded ESA noise law, or qualify prediction coverage. The seven reserved ESA confirmation groups remain unopened.

See the [clean forecast](ORACLE_CLEAN_REPORT.md), [full-noise forecasts](ORACLE_NOISY_REPORT.md), and [machine-readable scores](ORACLE_CHANNEL_REPORT.json).
