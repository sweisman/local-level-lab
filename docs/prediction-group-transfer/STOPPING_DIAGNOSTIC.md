# Why ten transfer fits abstained

The [four-group transfer study](RESULT.md) sealed all 16 starts. Six
passed its original numerical stopping check; ten did not. Reading
their saved probes gives:

| Failed fixed check | Fits |
|---|---:|
| Cost change only | 7 |
| Cost change and stationarity | 2 |
| Stationarity before the full probe | 1 |

The seven cost-only fits already met the fixed position and
stationarity checks. Their fresh cost changes still exceeded the
original relative limit of 1e-08.
The failed fits remain failed. Close costs from different starts
cannot replace a passed stopping check, and this diagnostic makes
no model or uncertainty decision.

[All starts and costs](fit-audit.csv) · [Transfer result](RESULT.md)
