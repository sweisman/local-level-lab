# One-step check of training-compatible alternatives

**4/4 numerical diagnostics complete.**

These generated probes preserve the original five noisy training observations and physical bounds. One linear repair is proposed per preselected seed. Only the subsequent nonlinear training check establishes feasibility.

| Processing | Feasible new points | Sampled N spread | Sampled E spread | Sampled height spread |
|---|---:|---:|---:|---:|
| Zero removal | 0/2 | 0.000 m | 0.000 m | 0.000 m |
| Profiled removal | 0/2 | 0.000 m | 0.000 m | 0.000 m |

Spreads include the original truth. These are sampled separations, not outer bounds. The original 20/20/50 m width targets are unchanged.

The proposal deliberately constrains its computed future north prediction to remain near the seed. It uses no future observation. This is a counterexample search, not an unbiased held-out prediction test.

All failures are preserved. There are no iterated repairs, new aircraft fits or changes to existing studies. No statistical confidence level or aircraft error law is established.

[Frozen limits](PLAN.md) · [Original probes](../ilvis0-truth-probes/INTERPRETATION.md) · [Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md).
