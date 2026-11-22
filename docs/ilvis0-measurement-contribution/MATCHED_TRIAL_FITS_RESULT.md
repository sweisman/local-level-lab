# The trial calculation preserved all eight generated fits

All eight fits reproduced the original solver records and forecasts exactly.
The proposed steps, accepted and rejected decisions, final parameters and
stopping checks matched in each case. Seven fits passed the numerical stop.
The specified-field globe fit on a zero-field history retained its failure.

| Calculation | Full tangent calls including forecasts | Value-only calls |
|---|---:|---:|
| Sealed reference | 290 | 0 |
| Value-only trial check | 127 | 258 |

The method skipped 163 full tangent calculations, a 56% reduction in that
work. The study did not retime the sealed reference fits, so the reduction
is a count of expensive calculations. The [aircraft point check](MATCHED_TRIAL_PROBE_RESULT.md)
supplies individual CPU timing. The cases here were chosen to exercise
the solver's rejection and stopping behavior, so they do not estimate
typical savings on aircraft data.

The [frozen plan](MATCHED_TRIAL_FITS_PLAN.md) compares two complete four-model
settings. An independent read of the closed results matched every fit and
forecast against the frozen inputs and verified all 385 charges. No aircraft
fit was started. The next gate is an equal-limit recorded-data check with
one passing control and the saved zero-field disc stopping failure.

[Sealed fit, forecast and accounting record](../ilvis0-matched-trial-fits-runtime/README.md).
