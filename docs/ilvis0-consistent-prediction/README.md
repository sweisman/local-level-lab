# Prediction with consistent calibration errors

48/48 cases pass correctness.

All six groups meet the unchanged twofold target against the projected baseline: **no**.

| Candidate / removal | Complete | Width N / E / height (m) | Ratio to immediate predecessor | Twofold target |
|---|---|---:|---:|---|
| Globe with specified field / zero | Yes | 1.2714, 1.6453, 1.0732 | 0.9988, 0.9978, 0.9973 | No |
| Globe with specified field / profiled | Yes | 1.3568, 1.7201, 1.1596 | 0.9988, 0.9979, 0.9975 | No |
| Globe with zero field / zero | Yes | 0.9752, 1.0492, 0.7555 | 0.9969, 0.9958, 0.9961 | Yes |
| Globe with zero field / profiled | Yes | 1.1307, 1.1952, 0.9115 | 0.9967, 0.9964, 0.9968 | No |
| Flat disc / zero | Yes | 0.6973, 0.2194, 0.5216 | 0.9955, 0.9963, 0.9930 | Yes |
| Flat disc / profiled | Yes | 0.8869, 0.2782, 0.7047 | 0.9971, 0.9969, 0.9954 | Yes |

Elapsed 7.9 seconds. Native calls and bounds: zero. The comparison reuses sealed generated results and adds qualified necessary calibration constraints. All original physical bounds and sectors remain. Future outcomes are checked only after prediction is saved. These widths are not measured aircraft errors or calibrated intervals.

[Frozen scope](PLAN.md) · [Component qualification](../ilvis0-calibration-consistency-controls/README.md) · [Predecessor](../ilvis0-transform-cover/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
