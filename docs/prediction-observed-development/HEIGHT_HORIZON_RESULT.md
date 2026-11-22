# Where the ESA height forecast loses coverage

This saved-data check divides the two completed forecasts on the same ESA
development recording into fixed 100-second bins. It makes no new fit and
opens no reserved flight group. Signed errors below are **predicted height
minus receiver height**.

| Forecast period | Heights inside nominal 95% range | Mean raw height error | Mean conditioned height error | Mean conditioning adjustment | Mean recorded climb rate |
|---|---:|---:|---:|---:|---:|
| Shorter fit, reports 600–699 | 100/100 | +0.19 m | −0.15 m | −0.33 m | +0.28 m/s |
| Shorter fit, reports 700–799 | 100/100 | −0.36 m | −0.23 m | +0.14 m | −0.04 m/s |
| Longer fit, reports 800–899 | 25/100 | −4.39 m | +0.97 m | +5.35 m | +0.03 m/s |
| Longer fit, reports 900–999 | 0/100 | −3.07 m | +4.66 m | +7.73 m | −0.05 m/s |
| Longer fit, reports 1000–1099 | 0/100 | +0.35 m | +10.89 m | +10.54 m | −0.04 m/s |
| Longer fit, reports 1100–1199 | 0/100 | +6.37 m | +20.17 m | +13.80 m | +0.03 m/s |

The first two rows use the fit to reports 0–599 and have almost identical
values under both declared IMU error laws; the table shows the increment law.
The last four rows use the earlier completed fit to reports 0–799. They are
different forecasts on successive parts of one recording, not independent
flights or a controlled comparison of the two fit lengths.

The later height error grows even though the receiver reports little average
climb or descent. Mean ground speed rises from 92.4 to 95.4 m/s across those
four bins. The uncorrected error changes sign, while the conditional
adjustment keeps increasing in the same direction. The correction eventually
makes the height forecast worse. This timing pattern is evidence that the
current error-state extrapolation is inadequate over the longer horizon; it
does not identify whether the source is sensor error, calibration, aircraft
motion, clock interpretation or another modeling assumption.

The [machine-readable bins](height-horizon-result.json) include RMS, first and
last errors, speed, climb variability, source hashes and the exact scored
intervals. The [shorter forecast result](TRAINING_SPLIT_SCORE_RESULT.md) and
[earlier longer forecast](CONDITIONAL_COVERAGE_RESULT.md) give the full context.
These are retrospective development diagnostics; nominal ranges are not
calibrated confidence statements, and the scientific decision remains
**abstain**.
