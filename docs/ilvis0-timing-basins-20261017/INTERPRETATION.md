# What the saved comparisons establish

The four unresolved stretches contain two different numerical problems.

| Stretch | What differs between saved starting solutions | Next useful check |
|---|---|---|
| `0e73879f98c3b701fd7c42df` | Zero-field-globe time offsets differ by about 17.3 ms without removal and 70.0 ms with profiled removal; initial-position and acceleration corrections change with them. | Reoptimize nuisance parameters at the distinct time offsets and compare the resulting solutions. |
| `50f24131843071ae9312c082` | Zero-field-globe offsets differ by about 45.0 ms. The relative cost difference already exceeds the repeat limit. | Start the matched fixed-time profile here; a repair to the reporting error cannot supply repeat agreement. |
| `370cec66878c4c1cf84b4ceb` | Specified-field-globe endpoints differ by only about 14 ns; gravity and calibration changes dominate their parameter separation. | Diagnose the joint correction and its failed fresh check, rather than treating this as a widely separated timing solution. |
| `b4e44ddc0f130ecd45674c78` | Zero-field-globe offsets differ by about 57.1 ms; specified-field-globe offsets differ by less than 0.2 microseconds. | Separate the timing-profile problem from the large gravity/calibration correction and unsupported probes. |

Across the sixteen endpoints, only about **1–5% of the timing-column norm**
remains after projecting out the other active Jacobian columns. This describes
a strong local timing/calibration trade-off. The projection ignores bounds and
does not establish global non-identifiability or justify dropping a parameter.

The older local Jacobians do not accurately predict the residual differences
between several widely separated endpoints. Those differences need nonlinear
profiles. A tangent calculation cannot replace the proposed reoptimized comparison.

These are diagnostics of preserved pre-boundary-check solutions. They neither
relabel the four stretches nor rerun earlier fits. The completed batch compared
eight pairs, used sixteen local projection solves and made **zero native predictions**.

[Full saved comparison](README.md) · [Planned matched profile](PROFILE_PLAN.md) ·
[Current status](../CURRENT_STATUS.md).
