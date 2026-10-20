# Direction-preserving calibrated-force qualification

24/24 generated source/domain cases passed.

| Domain | Passing cases | Checked probes | Height-width fraction of old norm bound, min–max |
|---|---:|---:|---:|
| full | 6/6 | 384 | 0.09415–0.09415 |
| sector | 6/6 | 384 | 0.30693–0.30693 |
| fixed | 6/6 | 6 | undefined (zero old width) |
| gain-boundary | 6/6 | 384 | 0.09366–0.09366 |

Elapsed 9.5 seconds. Reconciled 24/24 setups, 24/24 interval actions, 1158/1,158 independent point oracles and 6948/6,948 scalar containment checks.

The exact interval construction preserves direction, signed increments, calibration ranges and the supplied installation matrix. The point comparison uses a 1e-10 m/s² numerical margin. Probes test the implementation; the analytic rotation inequality supplies the bound. Wider outcomes are retained.

This qualifies a static component only. It does not bound a full integrated trajectory or its floating-point execution. No original aircraft data, protected ESA data, native trajectory integration, LP or observed fit was used.

[Frozen scope](PLAN.md) · [Derivation](../ilvis0-directional-rotation/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
