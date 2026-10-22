# Can training-compatible calibrations predict different later positions?

**12/12 numerical checks complete; 12/12 proposed points satisfy nonlinear training.**

| Processing | Feasible points | Sampled N spread | Sampled E spread | Sampled height spread |
|---|---:|---:|---:|---:|
| Zero removal | 6/6 | 21.753 m | 13.483 m | 1.664 m |
| Profiled removal | 6/6 | 7.195 m | 8.698 m | 0.759 m |

These are spreads between sampled feasible numerical trajectories and the zero reference, **not outer uncertainty bounds**. The original width targets are 20 m north, 20 m east and 50 m height. A small sampled spread does not prove those targets achievable over the entire parameter domain.

| Processing | Ray | Actual training maximum | Future N / E / height change | Feasible |
|---|---|---:|---|---|
| Zero | N − | 0.616 m | -9.025 / -1.798 / 0.128 m | Yes |
| Zero | N + | 0.795 m | 12.728 / 0.745 / -0.793 m | Yes |
| Zero | E − | 0.841 m | -5.248 / -8.657 / 0.864 m | Yes |
| Zero | E + | 0.574 m | 1.665 / 4.826 / -0.036 m | Yes |
| Zero | height − | 0.695 m | -2.041 / 3.895 / -0.143 m | Yes |
| Zero | height + | 0.701 m | -1.026 / -4.458 / 0.870 m | Yes |
| Profiled | N − | 0.657 m | -2.600 / -4.073 / 0.415 m | Yes |
| Profiled | N + | 0.787 m | 4.594 / 1.261 / 0.090 m | Yes |
| Profiled | E − | 0.751 m | -2.524 / -5.818 / 0.535 m | Yes |
| Profiled | E + | 0.683 m | 1.455 / 2.605 / 0.090 m | Yes |
| Profiled | height − | 0.601 m | -0.940 / 2.741 / -0.035 m | Yes |
| Profiled | height + | 0.856 m | -2.355 / -5.957 / 0.725 m | Yes |

Each point is chosen from earlier saved training quantities, frozen before one new full-model query, and checked against the unchanged ±1-metre training allowance. The quadratic proposal heuristic cannot establish feasibility; only the reported nonlinear check determines that label. Every original direction is retained; no new outcome causes a retry.

These generated zero-reference cases are separate from the active long-record study with perturbed training observations. They do not establish aircraft uncertainty, native execution-error bounds, scientific significance or a change to the 53-stretch findings.

[Frozen scope](PLAN.md) · [Original nonlinear probes](../ilvis0-density-native-probes/README.md) · [Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md).
