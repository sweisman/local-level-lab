# Saved clock-boundary review

**Both failed fits place all 119 receiver queries close to internal integration boundaries.**
The reconstructed clock arrays match their original saved hashes. This identifies a useful
diagnostic target; it does not establish a derivative error or the cause of the failure.

| Saved start | Median distance to boundary | Maximum distance | Numerical result |
|---|---:|---:|---|
| 0 | 303.582 ns | 303.582 ns | Failed; unchanged |
| 1 | 3.807 ns | 3.807 ns | Failed; unchanged |

The offset is near −2/300 seconds, an internal clock boundary rather than the
permitted offset limit. The recorded fresh correction fails cost stability while
passing the stationarity and position-change checks. A later qualification should
test both timing branches and known optima before changing any solver.

Twenty-two software checks pass. This review reads two saved fits and generates
only clock metadata: zero new noise draws, optimizer starts or native calls.
Validation remains blocked; the original 53 aircraft comparisons are unchanged.

[Per-query CSV](results.csv) · [Fixed review scope](PLAN.md) ·
[Calibration outcome](../prediction-calibration-compensated/INTERPRETATION.md) ·
[Next analyses](../NEXT_STEPS.md).
