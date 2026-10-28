# The complete timing-optimizer matrix passes

All **48 fits, 24 paired-start comparisons and four original input replays
pass**. The independent audit reproduces the numerical checks and verifies
sources, compiled kernels, work charges and saved forecast results. Packaging
performs no new fits or native calculations.

| Test coverage | Fits passing |
|---|---:|
| Increment inputs | 24/24 |
| Point-rate inputs | 24/24 |
| Specified-field globe generated truth | 16/16 |
| Zero-field globe generated truth | 16/16 |
| Stationary-disc generated truth | 16/16 |

Each candidate fits data generated under its own stated physics. These rows
are known-answer software controls, not new aircraft results or votes for an
Earth model. Both processing settings retain their full 26 or 27 parameters.

The largest later horizontal RMS is 3.581 m; the largest height RMS is 2.058 m.
Every raw forecast meets its original accuracy screen. Matched starts agree
in cost and reconstructed training positions: the largest relative cost
separation is 2.45×10⁻¹⁴ and the largest per-axis RMS position difference is
about 11 nanometres. Agreement during training is not a calibrated uncertainty
range for later positions.

The run takes **65.7 minutes** after 203 source-bound software checks, using
990 fit evaluations, 590 bounded linear operations and 2,859,582 actual native
calls. Its unused allowance is closed. The original starts, generated values,
physical bounds, noise model and numerical limits are preserved.

This completes the declared optimizer qualification. A fresh calibration
release still needs a separate finite design and source/environment freeze.
Neither closed calibration campaign is resumed. Actual aircraft error laws,
longer-record prediction coverage and significance remain separate scientific
requirements. Protected ESA groups and the original 53-stretch findings are
unchanged.

[Every fit](results.csv) · [All 24 start comparisons](pairs.csv) ·
[Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).
