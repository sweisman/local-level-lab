# The hardest ESA turn exceeds the error reference on every axis

At the native variance allowed by the quiet steady window, each axis of
turn 41116 alone exceeds the **whole-forecast upper reference of 438**.
The calculation gives lower bounds after allowing the added steady
and maneuver variances their most favorable ratios.

| Reports and coordinate | Lower bound on the whole-forecast score |
| --- | ---: |
| All 120 reports, all coordinates | 6,608 |
| All 120 reports, north only | 1,088 |
| All 120 reports, east only | 3,896 |
| All 120 reports, height only | 1,682 |
| Largest bound from a 30-report block, all coordinates | 407 |

Both descriptions of inertial measurement error agree to the displayed
precision. The full-path contrast finds a sufficient incompatibility
in all four turn windows and one of four steady windows. None of the
30-report contrasts for the hardest turn exceeds the whole-forecast
limit on its own. These are lower bounds, and the full and partial
scores cannot be added together.

The result shows that a correction confined to height would still
leave incompatible horizontal marginals. It does not identify the
physical cause or determine how to divide the remaining errors among
receiver accuracy, aircraft motion and the inertial forecast model.
Any new uncertainty rule needs an earlier-data fit and a separate
prediction test.

The two tasks completed 320 contrasts in 7.5 seconds on one thread. Eight
focused tests passed, covering the marginal calculation, the error
contrast and the preceding variance bounds. No trajectory fits or
reserved flights were used.

[Frozen method](ESA_FORECAST_ERROR_LOCALIZATION_PLAN.md) ·
[Scores for every axis and block](esa-forecast-error-localization-result.json) ·
[Execution receipts](esa-forecast-error-localization-evidence/README.md) ·
[Reproduction bundle](esa-forecast-error-localization-evidence/bundle.zip)
