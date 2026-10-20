# Future bounds after joint coordinate projection

48/48 cases pass; state: complete.

Saved native predictions, derivatives and training observations are reused. Only the future nonlinear bound and its support are recomputed. These are generated prediction ranges, not actual aircraft errors or calibrated intervals.

| Model / removal | Complete | Width N / E / height (m) | Ratio to previous widths |
|---|---|---:|---:|
| 0 / 0 | Yes | 2.513, 2.813, 1.841 | 0.974, 0.971, 0.973 |
| 0 / 1 | Yes | 2.599, 2.889, 1.927 | 0.974, 0.972, 0.974 |
| 1 / 0 | Yes | 2.257, 2.311, 1.616 | 0.978, 0.972, 0.979 |
| 1 / 1 | Yes | 2.414, 2.471, 1.773 | 0.979, 0.974, 0.981 |
| 2 / 0 | Yes | 2.023, 0.616, 1.530 | 0.996, 0.993, 0.995 |
| 2 / 1 | Yes | 2.207, 0.671, 1.713 | 0.996, 0.994, 0.995 |

Model 0 is globe with specified field; model 1 is globe with zero field; model 2 is flat disc. Removal 0 fixes zero removal; removal 1 profiles it. Every physical direction and all shared-error variables remain. No new native integration calls, original aircraft reads or observed fits occur.

[Frozen scope](PLAN.md) · [Coordinate projection](../ilvis0-joint-constraint-projection-v2/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
