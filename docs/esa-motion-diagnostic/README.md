# Receiver-motion diagnostic

**11/11 identities passed** in 34.46 seconds. No raw inertial reads, Earth-model fits or native integrations. Version-1 eligibility is unchanged.

| Velocity SD | Half-second correlation | Supplied-family coverage | Arbitrary-correlation coverage | False turn flags, adjacent / trend | Missed turns, adjacent / trend |
|---:|---:|---:|---:|---:|---:|
| 0.01 m/s | 0.0 | 256/256 | 256/256 | 69/0 of 128 | 0/0 of 128 |
| 0.01 m/s | 0.8 | 256/256 | 256/256 | 0/0 of 128 | 0/0 of 128 |
| 0.01 m/s | 0.98 | 256/256 | 256/256 | 0/0 of 128 | 0/0 of 128 |
| 0.05 m/s | 0.0 | 256/256 | 256/256 | 128/0 of 128 | 0/0 of 128 |
| 0.05 m/s | 0.8 | 256/256 | 256/256 | 127/1 of 128 | 0/0 of 128 |
| 0.05 m/s | 0.98 | 256/256 | 256/256 | 8/0 of 128 | 0/0 of 128 |
| 0.2 m/s | 0.0 | 256/256 | 256/256 | 128/23 of 128 | 0/0 of 128 |
| 0.2 m/s | 0.8 | 256/256 | 256/256 | 128/59 of 128 | 0/14 of 128 |
| 0.2 m/s | 0.98 | 256/256 | 256/256 | 127/31 of 128 | 0/3 of 128 |

Receiver diagnostic: 2048 fixed centers, 2 unsupported; 1507 complete windows meet airborne speed and IMU-time support.

Among those windows, adjacent differences flag 920 for turning; the trend point estimate flags 749. Median vertical speed exceeds 1 m/s in 201 windows.

Under reported marginal covariance and Gaussian errors, 0 trend intervals lie wholly within ±0.02°/s assuming temporal independence, versus 0 allowing arbitrary temporal correlation. Ambiguous intervals: 1434 and 1478, respectively.

[Every sampled window](observed-windows.csv).

Generated controls test the noise-free window trend, not arbitrary instantaneous motion. Receiver covariance and temporal assumptions are not observationally calibrated. A smoother point estimate does not establish steady flight or create eligible intervals.

[Frozen question and limits](PLAN.md) · [Original selection](../esa-development-selection/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
