# Exact injected gyro components

The seeded white-error and changing-bias arrays were regenerated from the frozen clean stream. Their sum reproduces both archived measured IMU streams exactly. No fit or native forecast was run.

| Error law | Gyro component | Signed body-axis angle sum X/Y/Z (degrees) |
| --- | --- | --- |
| increment | white | -0.0091, -0.0111, -0.0015 |
| increment | bias | 0.0048, 0.0154, 0.0162 |
| point | white | -0.0266, -0.0025, 0.0098 |
| point | bias | 0.0049, -0.0130, -0.0095 |

These signed sums are input checks, not navigation-frame angular motion or separate causal effects on predicted position. The [machine-readable report](ORACLE_NOISE_COMPONENTS.json) records all gyro and accelerometer component summaries and hashes.
