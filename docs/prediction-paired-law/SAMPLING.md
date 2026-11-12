# Sampling comparison

The 239,863 packet intervals before the last training receiver fix cover 799.55 seconds. Their durations range from 0.003333000 to 0.003334000 seconds.

For these timestamps, the point-endpoint law has 1.000004694 times the accumulated white-noise variance of the independent-increment law.
Both frozen gyro and acceleration settings use the same nominal 300 Hz long-run white-noise scale. Endpoint sharing changes the short-lag structure, but actual packet-timing variation here does not create a meaningful difference in accumulated white noise.

This is a calculation from verified packet times and declared synthetic settings, **not an estimate of actual IMU noise**. It does not explain every model-fit result or qualify prediction coverage. Testing an error law would require independent evidence about high-frequency sensor error or a different sampling design. Until then, carry both laws when assessing forecasts.

[Calculation plan](SAMPLING_PLAN.md) · [Paired-fit result](RESULT.md) · [Error-law roadmap](../PREDICTION_ERROR_LAW_PLAN.md).
