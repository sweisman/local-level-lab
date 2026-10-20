# Prediction with shared rotation/gain bounds

48/48 cases pass correctness.

All six groups meet the unchanged twofold target against the projected baseline: **no**.

| Candidate / removal | Complete | Width N / E / height (m) | Ratio to immediate predecessor | Twofold target |
|---|---|---:|---:|---|
| Globe with specified field / zero | Yes | 1.2503, 1.6252, 1.0732 | 0.9837, 0.9882, 1.0000 | No |
| Globe with specified field / profiled | Yes | 1.3357, 1.7000, 1.1596 | 0.9848, 0.9887, 1.0000 | No |
| Globe with zero field / zero | Yes | 0.9520, 1.0299, 0.7554 | 0.9763, 0.9817, 1.0000 | Yes |
| Globe with zero field / profiled | Yes | 1.1072, 1.1759, 0.9115 | 0.9793, 0.9839, 1.0000 | No |
| Flat disc / zero | Yes | 0.6753, 0.2134, 0.5216 | 0.9685, 0.9727, 1.0000 | Yes |
| Flat disc / profiled | Yes | 0.8648, 0.2725, 0.7047 | 0.9753, 0.9796, 1.0000 | Yes |

Elapsed 67.1 seconds. Native calls and bounds: zero. The comparison reuses sealed generated results and adds qualified necessary rotation/gain constraints. All original physical bounds and sectors remain. Future outcomes are checked only after prediction is saved. These widths are not measured aircraft errors or calibrated intervals.

[Frozen scope](PLAN.md) · [Component qualification](../ilvis0-rotation-gain-controls/README.md) · [Predecessor](../ilvis0-norm-prediction/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
