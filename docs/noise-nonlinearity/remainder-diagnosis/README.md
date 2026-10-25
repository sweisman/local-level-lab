# Why the longer noise check failed

Both two-minute settings pass. The twenty-minute settings retain 13/16 and 15/16
passing matched controls. All four departures occur in height; every horizontal
component passes the unchanged test.

| Input format | Duration | Largest vertical nonlinear departure | Controls failing the height check |
|---|---:|---:|---:|
| Increments | 2 min | 0.02285 cm | 0/16 |
| Rate points | 2 min | 0.05431 cm | 0/16 |
| Increments | 20 min | 7.261 cm | 3/16 |
| Rate points | 20 min | 4.357 cm | 1/16 |

The test allows the larger of 1 mm and 1% of each predicted coordinate standard
deviation. The failures are small nonlinear height effects, not failures to
reproduce a flight by metres or kilometres. Their response is closely quadratic:
halving the injected errors quarters the non-reversing component. Across all
settings, the largest departure from that quadratic relation is below 0.0001 mm.

The largest non-reversing horizontal component is 9.1 cm, but it remains inside
its separately scaled limit. That quantity should not be confused with the
full horizontal prediction error, whose twenty-minute expected scale is about
34 m under the declared noise law.

The 16 seed pairs also provide a small descriptive sample of error growth. The
horizontal mean-squared error divided by its predicted value ranges from 0.90
to 1.33 across settings. These ratios are not calibrated confidence intervals;
epochs and positive/negative paths are correlated, and seeds are shared between
settings. Known calibration is supplied throughout.

Keep both failed settings and the original accuracy limits. This result supports
using the covariance calculation to understand error scale, while showing that
a claim of exact linear behavior at the specified 1% tolerance would be wrong.
It does not explain the much larger long-record fitting errors by itself, or
establish uncertainty when calibration must be fitted. That remains the next
qualification question. No aircraft result or reserved ESA group changes.

Recompute the diagnosis with the frozen source and environment using
`lll.noise_nonlinearity_report.remainder_diagnosis(root, "docs/noise-nonlinearity")`.
The supplement preserves the source, exact input hashes, qualification report
and derived statistics. It performs no integration, fitting or noise generation.

[Full matched check](../README.md) · [Next analyses](../../NEXT_STEPS.md).
