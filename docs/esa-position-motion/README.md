# Position-based receiver-motion checks

10/10 generated-data identities passed.

These checks qualify software under stated error assumptions. They do not show that a real ESA interval meets the selection rules.

All 24 analytic paths pass, including both hemispheres, longitude wrapping, nonuniform epochs, turning and climb. Maximum course error is 1.81e-10°/s; maximum speed error is 8.21e-10 m/s.

| Position scale (m) | Half-second correlation | Supplied-law coverage | Arbitrary-correlation coverage | Independence diagnostic |
|---:|---:|---:|---:|---:|
| 0.01 | 0.0 | 256/256 | 256/256 | 256/256 |
| 0.01 | 0.8 | 252/256 | 256/256 | 124/256 |
| 0.01 | 0.98 | 254/256 | 256/256 | 127/256 |
| 0.05 | 0.0 | 255/256 | 256/256 | 255/256 |
| 0.05 | 0.8 | 254/256 | 256/256 | 123/256 |
| 0.05 | 0.98 | 255/256 | 256/256 | 103/256 |
| 0.2 | 0.0 | 254/256 | 256/256 | 254/256 |
| 0.2 | 0.8 | 255/256 | 256/256 | 120/256 |
| 0.2 | 0.98 | 256/256 | 256/256 | 113/256 |

Passing requires an exact one-sided 99% lower coverage bound of at least 0.95 in every declared family. A miss in any of the nine trend coefficients or an unsupported interval counts as a missed realization. Independence under correlated errors is reported without being treated as a valid model.

Completed in 18.5 seconds. Reconciled 2,328/2,328 reserved assessments. All generated measurements and intervals are retained. No receiver or IMU file was read, no model was fitted, and no confirmation group was inspected.

The intervals describe a noise-free polynomial trend. Instantaneous motion requires a separate approximation bound. Reported receiver covariance is still uncalibrated, and the existing zero-eligible inventory is unchanged.

[Frozen plan](PLAN.md) · [Previous velocity diagnostic](../esa-motion-diagnostic/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
