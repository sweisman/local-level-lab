# The forecast contrast tolerates 4.69 mm/s of accumulated velocity error

The certified ESA contrast can tolerate **4.69 mm/s** of uniform error
in interval-average velocity per axis, when other errors are zero.
This calculation lets each velocity error affect all subsequent
positions. It uses the same two affine forecasts and calibration
boxes as the [2.25 cm position-error check](ESA_COMPACT_FORECAST_MARGIN_RESULT.md).

| Separate error source | Contribution to the allowed error |
| --- | --- |
| Position errors that can change freely at each report | 2.25 cm maximum per coordinate if acting alone |
| Velocity errors integrated through the whole path | 4.69 mm/s maximum per coordinate if acting alone |
| Initial position and velocity errors before the cut | Almost entirely cancel directly in this contrast |

Almost all of the sensitivity to integrated velocity error is after
the cut, including the interval crossing it. Constant offsets are
almost entirely removed. Earlier errors can still change the velocity
and other physical states carried into the forecast. To use this
margin, bound the resulting velocity error over the later intervals
and budget direct position errors, such as lever-arm differences,
alongside it. The two maxima share one allowance and cannot both
be used in full. These checks do not establish that the actual
errors are within either limit.

One task completed with three charged calls and six passing software
checks. No aircraft fits or reserved observations were used.

[Frozen plan](ESA_INTEGRATED_CONTRAST_SUPPORT_PLAN.md) ·
[Verified evidence](esa-integrated-contrast-support-evidence/README.md)
