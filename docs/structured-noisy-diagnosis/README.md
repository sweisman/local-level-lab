# Why do short noisy fits reach calibration limits?

**20/24 fits pass numerical checks; 24/24 reach calibration limits.**

All compared planted sensor settings lie inside the permitted bounds.
Accurate later positions do not establish accurate or unique calibration.

The original outcomes remain unchanged. The complete uncertainty gate is not qualified.
These are matched software settings with one shared noise seed, not independent aircraft observations.

| Parameter | Lower bound | Upper bound | Interior | Unit |
|---|---:|---:|---:|---|
| accel_bias_z | 24 | 0 | 0 | m/s2 |
| accel_gain_y | 24 | 0 | 0 | % |
| gravity_delta | 24 | 0 | 0 | m/s2 |
| gyro_bias_y | 0 | 12 | 12 | deg/hour |
| gyro_bias_z | 24 | 0 | 0 | deg/hour |
| gyro_gain_x | 0 | 24 | 0 | % |
| time_offset | 6 | 14 | 4 | s |

The four stopping checks use their original frozen thresholds. A failed check is not relabeled.

| Unfinished fit | Failed check | Evaluations used |
|---|---|---:|
| increment-sphere_rotating-1-0 | relative_cost_change | 52/200 |
| increment-sphere_rotating-1-1 | relative_cost_change | 52/200 |
| point-sphere_still-1-0 | relative_cost_change | 53/200 |
| point-sphere_still-1-1 | relative_cost_change | 51/200 |

This report reads saved results only: no refits, original recordings or protected inputs.
A boundary-gradient sign is a local diagnostic, not proof of a unique optimum.
Reference comparisons exclude starting attitude, velocity, position and the gravity fixture.
A separately qualified experiment must distinguish weak calibration from an inadequate error model.

[Parent study](../structured-noisy-training/README.md) · [Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).
