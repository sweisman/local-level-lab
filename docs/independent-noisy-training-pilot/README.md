# Fitted predictions with fresh noise

**48/48 starts pass numerical checks; 48/48 complete forecasts are available.**

Each candidate is fitted to its own generating truth: these are not Earth-model votes.
The two fresh seeds are diagnostic draws. Settings and starts sharing a seed
are dependent; this is not a collection of independent flights.
Prediction uncertainty is not calibrated. No tail threshold or detection is inferred.

| Seed | Numerical passes | Raw physical screen passes | Conditional physical screen passes |
|---|---:|---:|---:|
| 26102610 | 24/24 | 24/24 | 24/24 |
| 26102611 | 24/24 | 24/24 | 24/24 |

Primary starts use qualified training cost and declared order, never later errors.
The error/noise score is the maximum over the entire later block. Its covariance
treats fitted calibration as known; the score is not a confidence level.

| Seed / input / model / processing | Primary start | Raw horizontal RMS | Conditional horizontal RMS | Maximum error/noise score |
|---|---:|---:|---:|---:|
| 26102610 / increment / flat_still / 0 | 0 | 2.724 m | 2.724 m | 10.104 |
| 26102610 / increment / flat_still / 1 | 1 | 3.038 m | 3.019 m | 9.202 |
| 26102610 / increment / sphere_rotating / 0 | 1 | 2.802 m | 2.779 m | 9.962 |
| 26102610 / increment / sphere_rotating / 1 | 1 | 2.816 m | 2.795 m | 8.930 |
| 26102610 / increment / sphere_still / 0 | 1 | 2.721 m | 2.708 m | 9.866 |
| 26102610 / increment / sphere_still / 1 | 0 | 2.856 m | 2.835 m | 8.866 |
| 26102610 / point / flat_still / 0 | 0 | 2.707 m | 2.688 m | 9.609 |
| 26102610 / point / flat_still / 1 | 0 | 2.745 m | 2.729 m | 8.522 |
| 26102610 / point / sphere_rotating / 0 | 1 | 2.488 m | 2.468 m | 9.311 |
| 26102610 / point / sphere_rotating / 1 | 0 | 2.537 m | 2.519 m | 8.258 |
| 26102610 / point / sphere_still / 0 | 1 | 2.528 m | 2.507 m | 9.277 |
| 26102610 / point / sphere_still / 1 | 0 | 2.576 m | 2.558 m | 8.193 |
| 26102611 / increment / flat_still / 0 | 0 | 3.670 m | 3.655 m | 10.296 |
| 26102611 / increment / flat_still / 1 | 0 | 2.901 m | 2.875 m | 7.848 |
| 26102611 / increment / sphere_rotating / 0 | 1 | 3.465 m | 3.449 m | 9.700 |
| 26102611 / increment / sphere_rotating / 1 | 1 | 2.778 m | 2.751 m | 7.535 |
| 26102611 / increment / sphere_still / 0 | 0 | 3.450 m | 3.434 m | 9.665 |
| 26102611 / increment / sphere_still / 1 | 1 | 2.762 m | 2.735 m | 7.500 |
| 26102611 / point / flat_still / 0 | 1 | 3.779 m | 3.762 m | 11.216 |
| 26102611 / point / flat_still / 1 | 1 | 2.993 m | 2.965 m | 8.789 |
| 26102611 / point / sphere_rotating / 0 | 0 | 3.554 m | 3.536 m | 10.677 |
| 26102611 / point / sphere_rotating / 1 | 1 | 2.861 m | 2.832 m | 8.531 |
| 26102611 / point / sphere_still / 0 | 1 | 3.542 m | 3.524 m | 10.642 |
| 26102611 / point / sphere_still / 1 | 1 | 2.847 m | 2.819 m | 8.496 |

[Every start, including failures](results.csv) · [Frozen plan](PLAN.md) · [Next analyses](../NEXT_STEPS.md).

The original calibration bounds, accuracy screens and earlier failures remain unchanged.
No aircraft observations or reserved ESA groups were used.
