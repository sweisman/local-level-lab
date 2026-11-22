# Saved stopping audit for the twenty-group forecast extension

All 80 planned fits are included: 30 passed and 50 did not.
No fit used its full 200-evaluation allowance; the maximum was 83. 1 failed the final stationarity check. All 80 fits had at least one calibration parameter at a permitted bound.

| Fresh stopping probe | Fits |
|---|---:|
| `fresh_position_probe_not_stable` | 49 |
| `fresh_position_stability_verified` | 30 |
| `not_stationary` | 1 |

Failed checks within the nonpassing starts can overlap:

| Frozen check | Fits |
|---|---:|
| cost | 49 |
| fresh stationarity | 5 |
| stationarity | 1 |

This is a saved-data numerical diagnosis. It does not turn a failed fit
into a pass or show that the fitted physical model is adequate. The
nearby starts can have similar costs even when both fail their frozen
stopping checks. A new solver qualification would need separate
known-answer controls and a new finite observed study.

[All starts and scores](remaining-fit-audit.csv) · [Complete stopping fields](remaining-stopping-audit.json) · [Forecast transfer result](REMAINING_GROUPS_PREDICTION_RESULT.md)
