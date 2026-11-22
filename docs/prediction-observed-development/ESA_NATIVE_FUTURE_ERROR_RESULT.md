# Later error needed to explain the ESA forecast misses

This check uses the fixed native forecasts and the 120 previously scored
receiver positions on ESA development recording 187. The forecast and
training weights stay fixed. It asks how large an extra after-cut error
would have to be for each forecast's mean squared standardized error
to reach one, a working benchmark.

| Forecast | Position RMS | Mean squared standardized error | Added white scatter per report | Added random walk at the final report |
|---|---:|---:|---:|---:|
| Specified-field globe | 0.65 m | 0.047 | Already below benchmark | Already below benchmark |
| Zero-field globe | 39.35 m | 14.54 | 16.85 m | 5.69 m |
| Zero-field disc | 62.96 m | 16.62 | 33.15 m | 9.82 m |

The added scales are standard deviations per axis. A single constant
offset could not absorb the time-varying misses of either zero-field
path. Even as the offset variance grows without limit, the remaining
average squared errors are about 14.21 and 16.48, respectively.

The specified-field model's standardized squared error averaged 0.00429
in training and 0.04683 in the later forecast, a factor of 10.9 on the
same working scale. Some of that difference can arise because its
calibration was fitted on the earlier positions. Both figures are
below one. Earlier fit and later forecast error therefore need separate
checks before adopting a variance scale or a claim about accuracy.

These are sensitivity scales for one already scored flight and three
declared error shapes. Neither relative receiver agreement nor this
comparison identifies the aircraft's absolute error or establishes
coverage. The replay made no new fits and used no reserved flights.

[Fixed study plan](ESA_NATIVE_FUTURE_ERROR_PLAN.md) ·
[Conditioned forecasts](ESA_CONDITIONED_CALIBRATION_RESULT.md) ·
[Frozen inputs](esa-native-future-error-freeze.json) ·
[Full score curves](esa-native-future-error-result.json)
