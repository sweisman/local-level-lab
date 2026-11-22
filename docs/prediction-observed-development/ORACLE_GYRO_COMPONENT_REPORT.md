# Which gyro error component drives the generated drift?

Four sealed forecasts separately retained the original white gyro noise or changing gyro bias. Accelerometer increments, initial state and calibration were kept exact. The increment law adds errors to each sample interval; the point law adds errors to sampled rates before they are integrated. Later truth scored the future predictions; it did not enter them.

| Error law | Gyro error | Future horizontal RMS (m) | Future vertical RMS (m) |
| --- | --- | ---: | ---: |
| increment | white gyro noise | 181.49 | 3.04 |
| increment | changing gyro bias | 242.77 | 5.21 |
| increment | both gyro components | 75.71 | 2.67 |
| point | white gyro noise | 673.30 | 8.94 |
| point | changing gyro bias | 300.31 | 6.91 |
| point | both gyro components | 651.36 | 14.64 |

The signed horizontal error directions have white/bias cosine increment: -0.977, point: -0.295. A negative value means their separate errors tend to oppose each other over the future interval. These are two fixed synthetic noise draws. The combined error need not equal the sum of the separate errors. This comparison does not identify the error process in a recorded aircraft IMU or qualify prediction uncertainty. No reserved confirmation group was opened.

See the [full channel comparison](ORACLE_CHANNEL_REPORT.md) and [machine-readable scores](ORACLE_GYRO_COMPONENT_REPORT.json).
