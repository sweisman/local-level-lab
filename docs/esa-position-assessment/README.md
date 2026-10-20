# Position and velocity on the same ESA receiver windows

Completed all 2,048 fixed centers in 43.5 seconds: 2046 supported, 2 unsupported; 1507 supported windows retain the earlier airborne classification.

| Error assumption | Supported airborne intervals | Trend wholly within ±0.02°/s | Definitely outside |
|---|---:|---:|---:|
| Independent epochs | 1507 | 606 | 635 |
| Supplied correlation 0.8 | 1507 | 531 | 590 |
| Arbitrary temporal correlation | 1507 | 96 | 391 |

Point estimates flag 756 of these windows for turning, compared with 749 in the earlier velocity-trend diagnostic.

These are noise-free cubic-trend intervals under supplied error assumptions. They are not guarantees of quiet instantaneous flight. Real covariance remains uncalibrated; position and velocity belong to the same receiver solution. The independent cubic residual calculation is a consistency check, not independent position truth.

The original ESA inventory still has **zero eligible intervals**. No revised selection or model decision is created here. There were no raw-IMU reads, native trajectories, Earth-model fits or protected confirmation reads.

[Every sampled window](windows.csv) · [Frozen scope](PLAN.md) · [Software qualification](../esa-position-motion/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
