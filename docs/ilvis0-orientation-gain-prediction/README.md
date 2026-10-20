# Prediction with orientation-constrained rotation/gain bounds

48/48 cases pass correctness.

All six groups meet the unchanged twofold target against the projected baseline: **no**.

| Candidate / removal | Complete | Width N / E / height (m) | Ratio to immediate predecessor | Twofold target |
|---|---|---:|---:|---|
| Globe with specified field / zero | Yes | 1.2502, 1.6244, 1.0732 | 0.9999, 0.9995, 1.0000 | No |
| Globe with specified field / profiled | Yes | 1.3356, 1.6994, 1.1596 | 0.9999, 0.9996, 1.0000 | No |
| Globe with zero field / zero | Yes | 0.9517, 1.0292, 0.7554 | 0.9996, 0.9993, 1.0000 | Yes |
| Globe with zero field / profiled | Yes | 1.1069, 1.1751, 0.9115 | 0.9997, 0.9994, 1.0000 | No |
| Flat disc / zero | Yes | 0.6751, 0.2130, 0.5216 | 0.9997, 0.9982, 1.0000 | Yes |
| Flat disc / profiled | Yes | 0.8647, 0.2725, 0.7047 | 0.9998, 0.9998, 1.0000 | Yes |

Elapsed 110.9 seconds. Native calls and bounds: zero. The comparison reuses sealed generated results and adds qualified necessary rotation/gain constraints. All original physical bounds and sectors remain. Future outcomes are checked only after prediction is saved. These widths are not measured aircraft errors or calibrated intervals.

[Frozen scope](PLAN.md) · [Component qualification](../ilvis0-orientation-gain-controls/README.md) · [Predecessor](../ilvis0-rotation-gain-prediction/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
