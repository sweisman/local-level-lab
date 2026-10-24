# Short-term changes in the ESA rates

**The saved training interval contains substantial changes at short time scales. They cannot be treated as independent sensor noise.**

This check uses 13.33 minutes and 239,864 logged samples from the earlier training portion of development recording 187. It opens no original files or later receiver positions. The software passed 21 source-bound checks; the completed result and work charges are verified.

Each comparison removes a straight-line trend from three samples, using their actual timestamps. The table shows RMS contrast size. Its normalization would preserve the variance of independent equal-variance point errors; that assumption is not established for these measurements.

| Endpoint separation | Gyro X (rad/s) | Gyro Y (rad/s) | Gyro Z (rad/s) | Force X (m/s²) | Force Y (m/s²) | Force Z (m/s²) |
|---:|---:|---:|---:|---:|---:|---:|
| 0.006667 s | 0.00738694 | 0.0239555 | 0.00190048 | 1.38668 | 0.60522 | 2.38835 |
| 0.02 s | 0.00256361 | 0.00719168 | 0.00129621 | 0.250616 | 0.255776 | 0.420529 |
| 0.200001 s | 0.00264236 | 0.00588149 | 0.00153808 | 0.274858 | 0.243461 | 0.393851 |
| 2.00001 s | 0.00874429 | 0.0231708 | 0.00266596 | 1.46703 | 0.644593 | 2.2539 |

For example, the Y gyroscope contrast falls from about 0.024 rad/s at 6.7 ms separation to 0.0072 rad/s at 20 ms, then rises at two seconds. Independent point noise alone would not explain that time-scale pattern. Aircraft motion, vibration and processing can contribute. These are body-axis changes, not estimates of a background rotation field.

No fitted motion, fused attitude or expected rotation is subtracted. Logged rates are not silently converted into a white increment-noise specification: linear-point integration shares endpoints and creates correlations. The synthetic noise test uses independently perturbed increments and remains a separate problem.

The next error-model step must account for sampling and temporal structure. These statistics do not identify isolated instrument noise, changing sensor bias or calibrated confidence, and do not justify changing the frozen stress-test noise levels or accuracy limits.

The check charges 360,029 saved input samples, 239,864 training samples and 109,536 contrasts. It finishes in 2.36 seconds on one numerical thread, with no native calls or optimizer starts. Original and protected flight data remain untouched.

[Frozen plan](PLAN.md) · [Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
