# Saved linear corrections cross timing boundaries

**Both failed corrections cross all 119 integration boundaries; neither successful
control crosses one.** All four replays match the saved predicted cost changes
and step norms before their timing movement is interpreted.

| Noise family | Start | Original numerical result | Proposed timing change | Query boundaries crossed |
|---|---:|---|---:|---:|
| Successful control | 0 | Passed | 2.22045e-15 ms | 0 / 119 |
| Successful control | 1 | Passed | 0 ms | 0 / 119 |
| Failed setting | 0 | Failed | -0.644266 ms | 119 / 119 |
| Failed setting | 1 | Failed | -0.643062 ms | 119 / 119 |

## What this explains

The numerical check proposes a correction using a local linear approximation.
At the failed points, the timing correction moves into an adjacent integration
interval for every query. The observed cost rises rather than falling as that
linear approximation predicts. Both successful controls keep their timing fixed.

This identifies where to test the approximation. It does not demonstrate that
the recorded derivatives are wrong, or establish that either failed point is an
optimum. A two-sided timing check is needed before changing the solver.

## Scope and safeguards

Twenty-six known-answer software checks pass. Four saved 27-column linear
problems are replayed once, with their original bounds and 100-iteration limit.
All four solves were charged before execution. No nonlinear fit, native kernel,
noise draw, original aircraft record or protected confirmation group was used.
The failed fit labels and the 53-stretch findings remain unchanged. Calibration
and independent validation remain closed and blocked respectively.

[Four-record CSV](results.csv) · [Fixed review scope](PLAN.md) ·
[Timing proximity check](../prediction-clock-boundary-review/README.md) ·
[Next analyses](../NEXT_STEPS.md).
