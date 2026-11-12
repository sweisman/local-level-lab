# What the same noisy IMU streams predict with known calibration

**6/6 oracle forecasts technically complete; 0 meet the existing physical accuracy screen.**

This generated-data check uses six sensor streams. Four earlier fits of each stream shared the same noise path. The new calculation supplies the true starting state and calibration, then predicts the same later receiver positions. This is not aircraft evidence or an Earth-model vote.

| Generating candidate | Processing | Known-calibration later horizontal RMS | Earlier fitted range |
|---|---|---:|---:|
| sphere_rotating | Zero | 439 m | 84.8–84.9 m |
| sphere_rotating | Profiled | 439 m | 85.3–86.4 m |
| sphere_still | Zero | 442 m | 87.3–88.6 m |
| sphere_still | Profiled | 442 m | 84.8–87 m |
| flat_still | Zero | 508 m | 86.4–88.5 m |
| flat_still | Profiled | 508 m | 83.6–86.7 m |

Horizontal RMS is the typical horizontal prediction error over the 400 later receiver epochs. The original fitted outcomes and failure labels have not been changed. A single synthetic noise seed cannot establish real-aircraft uncertainty or scientific significance.

[Frozen plan](PLAN.md) · [Study index](../STUDIES.md)
