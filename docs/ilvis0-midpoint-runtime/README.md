# Complete-domain runtime comparison

2/6 pairs completed with exact report agreement. The fixed runtime screen did not pass.

| Candidate / processing | Original | Midpoint-only | Time ratio |
|---|---:|---:|---:|
| Specified-field globe / zero | incomplete | incomplete | unavailable |
| Specified-field globe / profiled | incomplete | incomplete | unavailable |
| Zero-field globe / zero | incomplete | incomplete | unavailable |
| Zero-field globe / profiled | incomplete | incomplete | unavailable |
| Flat disc / zero | 56.962 s | 55.097 s | 0.9673 |
| Flat disc / profiled | 56.011 s | 56.631 s | 1.0111 |

Median candidate/original ratio: 0.989165971470593; maximum: 1.0110647069080645. The frozen limits are a median at most 0.95, no ratio above 1.10, every pair complete and every report exact.

Elapsed 370.30 seconds. Charged 12/12 bounds and 172800/172,800 logical steps. Compiler and preparation time are outside each measured bound. The fixed order is balanced across cases; concurrent load can still affect timings.

This is an engineering screen on the original complete generated domains. It is not recording-scale qualification, an aircraft fit or calibrated observational coverage. Earlier failures stay unchanged.

[Frozen scope](PLAN.md) · [Exact-report qualification](../ilvis0-midpoint-native-controls/README.md).
