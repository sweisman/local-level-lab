# Check both sides of the timing boundary

The closest-to-complete unresolved stretch stopped with only its time-alignment
coordinate failing stationarity. Its saved endpoint is about 1.2 nanoseconds
from an integration-packet boundary, where the relevant local derivative changes.

This study checks both sides of that exact boundary for two preserved endpoint
solutions and checks two smooth controls afresh. It uses the existing branch
diagnostic and keeps all physical bounds and numerical acceptance limits.
Movement is checked from each original source through the final selected point.

The ceiling is **66 native calls**, four numerical threads and zero nonlinear
optimizer starts, with no retries. Eleven software checks passed. The interrupted
trial is preserved and is not resumed. Successful checks still need saved
companion/model review before changing the published findings.

Completed: 24 native calls in about nine minutes. Both controls passed; both
target left checks failed while their right checks passed. The
[saved left-side audit](../ilvis0-left-boundary-audit-20261017/README.md) identifies
an unchecked neighboring packet boundary, about 0.26 ps away. A separate
[clustered-boundary diagnostic](../ilvis0-clustered-boundary-20261017/README.md)
searches that local cluster and retains the original final stopping gate.

[Finite plan](PLAN.md) · [Saved-endpoint diagnosis](../ilvis0-profile-seeded-audit-20261017/README.md) ·
[Current findings](../CURRENT_STATUS.md).
