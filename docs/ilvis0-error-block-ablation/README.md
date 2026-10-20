# Which internal error terms keep predictions wide?

**Oracle-assisted diagnostic: these are not available prediction intervals.**

24/24 cases pass containment and support checks; state: complete.

Each row supplies the exact simulated value of one internal error block. Those values would be unknown for a real calibration. This diagnoses the mathematical construction and cannot clear a prediction or scientific decision gate.

| Candidate / removal | Block fixed to its known value | Conditional width N / E / height (m) | Reduction from source sector N / E / height |
|---|---|---:|---:|
| Globe with specified field / zero | Reference terms | 1.10465, 1.48979, 1.07318 | 0.00%, 0.00%, 0.00% |
| Globe with specified field / zero | Acceleration/clock | 1.10463, 1.48977, 1.07318 | 0.00%, 0.00%, 0.00% |
| Globe with specified field / zero | Acceleration remainder | 1.10015, 1.48364, 1.04095 | 0.41%, 0.41%, 3.00% |
| Globe with specified field / zero | Force matrix | 1.07466, 1.47068, 1.01297 | 2.71%, 1.28%, 5.61% |
| Globe with specified field / profiled | Reference terms | 1.18961, 1.56436, 1.15919 | 0.00%, 0.00%, 0.00% |
| Globe with specified field / profiled | Acceleration/clock | 1.18959, 1.56434, 1.15918 | 0.00%, 0.00%, 0.00% |
| Globe with specified field / profiled | Acceleration remainder | 1.18586, 1.55906, 1.12681 | 0.31%, 0.34%, 2.79% |
| Globe with specified field / profiled | Force matrix | 1.16010, 1.54557, 1.09909 | 2.48%, 1.20%, 5.18% |
| Globe with zero field / zero | Reference terms | 0.80473, 0.91772, 0.75545 | 0.00%, 0.00%, 0.00% |
| Globe with zero field / zero | Acceleration/clock | 0.80471, 0.91770, 0.75545 | 0.00%, 0.00%, 0.00% |
| Globe with zero field / zero | Acceleration remainder | 0.80422, 0.91569, 0.72179 | 0.06%, 0.22%, 4.45% |
| Globe with zero field / zero | Force matrix | 0.77521, 0.89961, 0.69536 | 3.67%, 1.97%, 7.95% |
| Globe with zero field / profiled | Reference terms | 0.96065, 1.08716, 0.91149 | 0.00%, 0.00%, 0.00% |
| Globe with zero field / profiled | Acceleration/clock | 0.96063, 1.08714, 0.91148 | 0.00%, 0.00%, 0.00% |
| Globe with zero field / profiled | Acceleration remainder | 0.96010, 1.08501, 0.87758 | 0.06%, 0.20%, 3.72% |
| Globe with zero field / profiled | Force matrix | 0.93105, 1.06917, 0.85141 | 3.08%, 1.66%, 6.59% |
| Flat disc / zero | Reference terms | 0.52571, 0.19333, 0.52155 | 0.00%, 0.00%, 0.00% |
| Flat disc / zero | Acceleration/clock | 0.52571, 0.19333, 0.52155 | 0.00%, 0.00%, 0.00% |
| Flat disc / zero | Acceleration remainder | 0.52463, 0.19310, 0.49025 | 0.20%, 0.12%, 6.00% |
| Flat disc / zero | Force matrix | 0.49395, 0.18804, 0.46207 | 6.04%, 2.73%, 11.40% |
| Flat disc / profiled | Reference terms | 0.70930, 0.25176, 0.70474 | 0.00%, 0.00%, 0.00% |
| Flat disc / profiled | Acceleration/clock | 0.70930, 0.25176, 0.70474 | 0.00%, 0.00%, 0.00% |
| Flat disc / profiled | Acceleration remainder | 0.70747, 0.25129, 0.67258 | 0.26%, 0.18%, 4.56% |
| Flat disc / profiled | Force matrix | 0.67769, 0.24639, 0.64530 | 4.46%, 2.13%, 8.43% |

All 51 coordinates and previous training constraints remain. Each conditional block is fixed only to its saved known physical value. These effects are not additive percentages of real uncertainty, and the selected source sector is not the complete union across sectors.

Used 144/144 LP proposals and 144 independent support checks in 54.4 seconds. Zero new native integration, bounds or original aircraft reads.

[Frozen scope](PLAN.md) · [Source predictions](../ilvis0-column-orientation-prediction/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
