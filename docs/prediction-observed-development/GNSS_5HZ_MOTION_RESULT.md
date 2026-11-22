# Receiver course changes and logged gyroscope rate

The opened ESA development flight has a 5 Hz GNSS-only PPP export as well as the recorded 300 Hz IMU stream. This fixed comparison uses only the earlier 400 receiver report times and no later outcome. It compares course change from GNSS velocity with the mean logged body-down gyro rate over the same span.

| Span (seconds) | Supported centers | Correlation | Mean gyro minus course (°/hour) | RMS of changing difference (°/hour) |
|---:|---:|---:|---:|---:|
| 2 | 397/400 | 0.915 | -96 | 378 |
| 10 | 389/400 | 0.969 | -98 | 223 |

The common low-frequency variation is substantial. The remaining difference includes aircraft heading versus ground course (crab), bank and pitch coupling, mount alignment, time tagging and possible instrument error. It is **not an estimate of gyro noise or the background rotation field**. The spans overlap and are not independent flights or trials. No Earth model was fitted.

Both frozen tasks passed their support checks, with zero native calculations. This result does not qualify a prediction-error range or release the seven reserved ESA flight groups.

[Fixed plan](GNSS_5HZ_MOTION_PLAN.md) · [Saved numerical summary](GNSS_5HZ_MOTION_RESULT.json) · [Observed error plan](OBSERVED_ERROR_PLAN.md).
