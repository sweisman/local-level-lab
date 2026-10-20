# Why the prediction ranges remain wide

6/6 cases supply exactly verified witnesses; 6/6 tasks completed.

This tests the current mathematical prediction region, using saved generated cases. It does not fit aircraft data or measure real sensor uncertainty.

| Candidate / removal | Affine width lower / upper (m), N; E; height | Lowest permitted total width (m) | Above target N / E / height |
|---|---|---|---|
| Globe with specified field / zero | 0.71712 / 0.71712; 0.97690 / 0.97690; 0.68658 / 0.68658 | 1.11389, 1.50520, 1.07318 | No / Yes / Yes |
| Globe with specified field / profiled | 0.76416 / 0.76416; 1.01935 / 1.01935; 0.73463 / 0.73463 | 1.19885, 1.57977, 1.15919 | No / Yes / Yes |
| Globe with zero field / zero | 0.53752 / 0.53752; 0.62312 / 0.62312; 0.49935 / 0.49935 | 0.81208, 0.93297, 0.75545 | No / No / No |
| Globe with zero field / profiled | 0.62550 / 0.62550; 0.71923 / 0.71923; 0.58744 / 0.58744 | 0.96795, 1.10242, 0.91149 | No / No / Yes |
| Flat disc / zero | 0.37181 / 0.37181; 0.14036 / 0.14036; 0.36202 / 0.36202 | 0.53199, 0.19784, 0.52155 | No / No / No |
| Flat disc / profiled | 0.47610 / 0.47610; 0.17385 / 0.17385; 0.46605 / 0.46605 | 0.71546, 0.25627, 0.70474 | No / No / No |

The lower value is established by two exactly feasible points; the upper value comes from the existing support certificate. Their difference measures what better optimization could still remove within this region. The total also includes the retained unshared and arithmetic allowances. Feasibility here does not establish a physically realizable calibration.

LP proposals: 36/36; elapsed 3.7 seconds. Zero new native integration, bounds or original-file reads. Unsupported cases remain without replacements.

[Frozen scope](PLAN.md) · [Known-answer controls](../ilvis0-feasible-witness-controls/README.md) · [Source predictions](../ilvis0-rotation-gain-prediction/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
