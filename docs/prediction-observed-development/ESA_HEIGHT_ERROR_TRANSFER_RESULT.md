# The NASA height correction did not carry over to the ESA flight

The earlier forecast's height error failed to improve any of the six
later ESA forecasts. Median height error rose from **0.58 m to 0.75 m**.
Horizontal errors stayed identical. The increment and sampled-rate error
laws gave nearly identical results because they used the same flight and
closely matching forecasts.

| Earlier → later training cut | Error law | Height RMS before → after | Horizontal RMS |
| --- | --- | ---: | ---: |
| 200 → 400 | Increment | 0.577 → 0.748 m | 5.380 m |
| 200 → 400 | Sampled rate | 0.577 → 0.748 m | 5.381 m |
| 400 → 600 | Increment | 0.298 → 0.454 m | 28.622 m |
| 400 → 600 | Sampled rate | 0.298 → 0.454 m | 28.622 m |
| 600 → 800 | Increment | 4.316 → 4.442 m | 144.720 m |
| 600 → 800 | Sampled rate | 4.316 → 4.442 m | 144.720 m |

Each test used the first 120 receiver reports after each training cut.
All source fits passed their original stopping checks. The correction
used only the earlier signed height errors and was saved before each
later score was opened. All six calculations completed with zero new
navigation fits. The seven reserved flight groups stayed closed.

This result and the [seven-group NASA check](../prediction-group-transfer/HEIGHT_TRANSFER_RESULT.md)
show that the same correction behaves differently across these examples.
Keep the raw ESA forecasts as the reference. A method for aircraft
prediction needs to account for the changing error and retain the large
horizontal misses in its adequacy checks.

[Frozen plan](ESA_HEIGHT_ERROR_TRANSFER_PLAN.md) ·
[Scores and source receipts](esa-height-error-transfer.json) ·
[Verified evidence bundle](esa-height-error-transfer-evidence/replay.zip)
