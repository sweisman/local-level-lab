# Saved linear-system comparison of the failed corrections

Both completed targets pass their endpoint side-gradient checks and agree closely with each other, but fail the fresh right-side correction. This audit compares bounded affine solves at their saved center Jacobians. It makes **zero native predictions and zero archival fits**.

| Source | Saved right step, max normalized | Replayed left / right / fixed-time step | Center Jacobian rank |
|---|---:|---:|---:|
| bias1_profiled_removal/primary | 0.256252 | 0.256252 / 0.256252 / 0.00166112 | 27/27 |
| bias1_profiled_removal/repeat | 0.25777 | 0.25777 / 0.25777 / 0.000167706 | 27/27 |

The full numerical report preserves every correction, predicted cost, solver status and singular value. Fixing time here removes only the timing column for an affine diagnostic; it does not qualify a free-time fit or justify accepting the original endpoint. Small singular directions and parameter bounds remain explicit.

A center Jacobian is not the complete record of both side Jacobians used by the failed test. Comparing it with a saved side correction can expose a discrepancy, but cannot establish whether that discrepancy comes from the side tangent, the bounded linear solve or nonlinear propagation. The next native diagnostic should preserve those side arrays and corrected-point arrays directly, under its own finite allowance, before choosing a replacement numerical method.

No stopping tolerance, model, physical bound or published disposition changes. Findings remain **51 globe / 0 flat / 2 unresolved**.

[Finite plan](PLAN.md) · [Source results](../ilvis0-final-pair-boundary-v2-20261018/RESULTS.md) · [Next steps](../NEXT_STEPS.md).
