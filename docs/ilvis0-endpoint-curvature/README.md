# What the saved endpoint derivatives explain

2/2 saved-data diagnostics pass.

| Processing | Linear RMS | Shared-source RMS | Endpoint-average RMS | Endpoint improves shared |
|---|---:|---:|---:|---:|
| Zero removal | 199.216002 m | 9.068310 m | 12.868664 m | 2/6 |
| Profiled removal | 926.866068 m | 45.353416 m | 71.408189 m | 0/6 |

The table compares the same six saved epochs for all three expressions. Reference and endpoint-derivative expressions are additionally checked at every one of the 293 epochs. No shared maps are invented for missing epochs. All 27 physical derivative columns remain.

The endpoint average approximates a derivative line integral. It is **not a curvature bound** or a prediction uncertainty interval. Its exactness for quadratic examples does not extend to arbitrary nonlinear motion; the software checks include a cubic counterexample. The derivatives at the known generated probes are available here, but are not supplied as unknown aircraft calibration information.

Grouped terms describe this directional curvature expression, not unique physical causes. No coefficients or points are fitted or adjusted, and no new native integration, LP proposals, source oracles or aircraft fits are performed. All earlier evidence and whole-period/error-law requirements remain unchanged.

[Frozen scope](PLAN.md) · [Shared-source diagnostic](../ilvis0-probe-shared-map-audit/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
