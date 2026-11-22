# Most ESA prediction error is shared across rate methods

The completed [six-fit comparison](RATE_REFIT_V2_RESULT.md) shows that all
three plausible assignments of reported iMAR rates miss the same later
receiver positions. This saved-only check asks how much of that miss is shared
and how much changes with the rate assignment. It makes **no new fit**.

At each of the 1,200 receiver times, the calculation subtracts the saved
receiver position from each sealed forecast in north/east/up coordinates. It
averages the three rate-method errors within each IMU error law, then measures
each method's departure from that average. The two error laws are kept
separate; they are not independent observations.

| Part of recording | Shared horizontal error, RMS | Rate-method horizontal spread, RMS |
|---|---:|---:|
| First 800 receiver times, used for fitting | 39.06 m | 1.42 m |
| Later 400 receiver times, withheld during fitting | 245.85 m | 5.87 m |

The table uses the increment-law results. The point-law values agree within
0.001 m. In the last 100 receiver times, shared horizontal RMS reaches
**342.2 m**, while method spread is **7.6 m**. The full
[machine-readable diagnostic](rate-refit-common-residual.json) retains every
fixed 100-epoch block, vertical components and maximum differences.

The growing error is largely common to all three rate assignments. Therefore,
choosing left hold, right hold or the original linear-point conversion cannot
by itself make this development forecast accurate. This pattern does **not**
identify whether the remaining cause is initial state, sensor calibration,
force/trajectory modeling, receiver observations or a combination. It does not
determine which rate convention the instrument used.

The diagnostic reads only six hash-verified sealed forecasts and their original
saved development receiver rows. It uses zero native calls, no new model fit,
and no reserved ESA confirmation group. No rate method is selected from the
withheld positions; the scientific decision remains **abstain**.

[Frozen question](RATE_REFIT_COMMON_PLAN.md) ·
[Six-fit result](RATE_REFIT_V2_RESULT.md) ·
[Earlier accurate fit comparison](RATE_REFIT_HISTORICAL_COMPARISON.md).

Observed-study manifest:
`fabb0ef004ce452a7a0b0a14ac71c307b350d3b9b4d25ca8bc8545598f75c2ba`.
Summary:
`47f01b56eda5710d0698f26a4727b12945abfcaa8f8fe3be50ff5a8df0fc03a7`.
Diagnostic source:
`b940abcdcf73c0fd164b962848f94af93bece2300f2ad4da5888ec7d9e07021d`.
Its sealed-refit report dependency is
`98da948dc00e89da1949752bebcce210c102e4695451d133723d572ba8538900`.
