# Timing and calibration differences in the remaining stretches

Eight outstanding primary/repeat pairs, from all four unresolved stretches, are compared at their preserved pre-boundary-check endpoints. No new fit, integration, original-file read or disposition change is involved.

| Stretch / case / model | Repeat minus primary time | Relative cost difference | Local timing retained, primary / repeat |
|---|---:|---:|---:|
| `0e73879f98c3b701fd7c42df::bias1_profiled_removal::sphere_still` | -69.9996 ms | 6.42158e-06 | 0.048 / 0.0474 |
| `0e73879f98c3b701fd7c42df::bias1_unsubtracted::sphere_still` | -17.297 ms | 1.15662e-05 | 0.046 / 0.0473 |
| `370cec66878c4c1cf84b4ceb::bias1_profiled_removal::sphere_rotating` | -1.39197e-05 ms | 2.92008e-09 | 0.0127 / 0.0127 |
| `50f24131843071ae9312c082::bias1_unsubtracted::sphere_still` | -44.9967 ms | 2.10474e-06 | 0.0193 / 0.0202 |
| `b4e44ddc0f130ecd45674c78::bias1_profiled_removal::sphere_rotating` | -0.000112003 ms | 2.31758e-10 | 0.0121 / 0.0121 |
| `b4e44ddc0f130ecd45674c78::bias1_profiled_removal::sphere_still` | 57.0566 ms | 9.69382e-06 | 0.0141 / 0.0146 |
| `b4e44ddc0f130ecd45674c78::bias1_unsubtracted::sphere_rotating` | 0.000172776 ms | 9.30699e-10 | 0.0121 / 0.0121 |
| `b4e44ddc0f130ecd45674c78::bias1_unsubtracted::sphere_still` | 57.0566 ms | 9.69381e-06 | 0.0141 / 0.0146 |

## Interpretation

A time difference changes which part of the inertial stream corresponds to a receiver epoch. The local projection asks how much the timing tangent can be imitated by changing the other active nuisance parameters. It includes parameters at their limits and temporarily ignores those limits for this linear diagnostic. It supplies no new convergence or scientific gate.

The saved first-order predictions and their errors are preserved in the report data. Large endpoint separations require a nonlinear profile before a local tangent can describe the intervening cost. Small cost differences alone do not establish matching reconstructed tracks.

The next matched profile should hold selected time offsets fixed while reoptimizing the other nuisance parameters from both saved starting solutions. It must then distinguish a numerically incomplete profile from a genuinely different stable solution. Fixed-time profiles are diagnostic and cannot replace the full free-time comparison or its repeat checks.

[Current status](../CURRENT_STATUS.md) · [Next steps](../NEXT_STEPS.md) · [Finite plan](PLAN.md).
