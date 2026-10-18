# Find the appropriate knot within the timing cluster

The previous check stopped at a packet boundary whose left side was still
nonstationary. An exceptionally close neighboring boundary remained unchecked.
This study uses the existing complete-cluster search to find a negative-to-positive
timing-slope change nearby, then applies the unchanged two-sided stopping test.

It checks the same two preserved endpoints and two fresh controls. Its ceiling is
**58 native calls**, four numerical threads and zero nonlinear optimizer starts,
with no retries. All twelve software checks passed. Both source-to-final movement
and endpoint repeat agreement remain required. Earlier failures remain unchanged.

[Finite plan](PLAN.md) · [Saved left-side diagnosis](../ilvis0-left-boundary-audit-20261017/README.md) ·
[Current findings](../CURRENT_STATUS.md).
