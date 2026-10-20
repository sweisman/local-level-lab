# Prediction with shared vector-norm bounds

48/48 cases pass correctness.

All six groups meet the unchanged twofold target against the projected baseline: **no**.

| Candidate / removal | Complete | Width N / E / height (m) | Ratio to immediate predecessor | Twofold target |
|---|---|---:|---:|---|
| Globe with specified field / zero | Yes | 1.2710, 1.6445, 1.0732 | 0.9997, 0.9995, 1.0000 | No |
| Globe with specified field / profiled | Yes | 1.3564, 1.7195, 1.1596 | 0.9997, 0.9996, 1.0000 | No |
| Globe with zero field / zero | Yes | 0.9751, 1.0492, 0.7554 | 1.0000, 1.0000, 1.0000 | Yes |
| Globe with zero field / profiled | Yes | 1.1306, 1.1951, 0.9115 | 0.9999, 0.9999, 1.0000 | No |
| Flat disc / zero | Yes | 0.6973, 0.2194, 0.5216 | 1.0000, 0.9999, 1.0000 | Yes |
| Flat disc / profiled | Yes | 0.8867, 0.2782, 0.7047 | 0.9999, 0.9999, 1.0000 | Yes |

Elapsed 36.9 seconds. Native calls and bounds: zero. The comparison reuses sealed generated results and adds qualified necessary vector-norm constraints. All original physical bounds and sectors remain. Future outcomes are checked only after prediction is saved. These widths are not measured aircraft errors or calibrated intervals.

[Frozen scope](PLAN.md) · [Component qualification](../ilvis0-shared-norm-controls/README.md) · [Predecessor](../ilvis0-consistent-prediction/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
