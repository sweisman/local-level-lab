# Reconstruction allowances dominate the prediction widths

**All six saved cases pass all 18 exact width checks.** The nonlinear
reconstruction allowance accounts for 76.7–90.8% of the complete prediction
widths. This gives a more useful denominator than the earlier audit, which
compared position reconstruction only with the unshared allowance.

These are conservative ranges from generated software tests. They are not
measured aircraft position errors. No model was fitted or trajectory reintegrated.

| Candidate | Removal assumption | North width, km | East width, km | Height width, km | Reconstruction share, N / E / height |
|---|---|---:|---:|---:|---|
| Globe, specified field | None | 2026.6 | 2413.3 | 1462.7 | 87.5% / 88.7% / 90.7% |
| Globe, specified field | Profiled | 2024.5 | 2418.7 | 1461.0 | 87.4% / 88.5% / 90.5% |
| Globe, zero field | None | 1704.1 | 1995.6 | 1258.8 | 87.7% / 88.7% / 90.8% |
| Globe, zero field | Profiled | 1699.8 | 2001.9 | 1253.0 | 87.7% / 88.6% / 90.7% |
| Flat disc | None | 657.3 | 109.3 | 312.8 | 77.4% / 78.0% / 77.4% |
| Flat disc | Profiled | 687.5 | 114.9 | 339.3 | 76.7% / 76.9% / 77.3% |

The remaining width is mainly the affine range over permitted calibration
parameters. Arithmetic and outward-reporting increments are also retained
and checked exactly; the largest width-reporting increment is less than
0.000000001 m. Improving floating-point subtraction cannot resolve these ranges.

The next method must tighten the nonlinear reconstruction allowance while
preserving the physical bounds and earlier observation constraints. The
[static coupling comparison](../ilvis0-static-training-coupling/README.md)
tightens a reference-acceleration allowance by 3.7–7.1%, but has not recomputed
these trajectory ranges. Further diagnosis should target their larger
time-varying force and mounting-transform contributions before repeating
the full-history integration.

The audit took 1.64 seconds, with no native calls, new support solves,
aircraft reads or optimizer starts. The first audit's rounding-check failures
are preserved separately. Original prediction failures and all 53 main
model comparisons remain unchanged.

[Method and limits](PLAN.md) · [First audit](../ilvis0-prediction-width-budget/README.md) ·
[Shared arithmetic](../../analysis/lll/ilvis0_saved_budget_audit.py) ·
[Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md) ·
[Reproducibility](../REPRODUCIBILITY.md).
