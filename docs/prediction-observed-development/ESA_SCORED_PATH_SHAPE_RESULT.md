# How much forecast error follows a smooth drift?

The largest steady-flight forecast error was mostly a smooth height
discrepancy. After allowing for smooth position, velocity and acceleration
errors retrospectively, the four steady windows had similarly small
remaining error. The turning windows still varied widely. A better forecast
needs to account for both effects.

The [frozen calculation](ESA_SCORED_PATH_SHAPE.md) reproduced the original
joint score for all 16 forecasts and projected out nine smooth terms. The
two inertial error descriptions agree at the precision shown. The remaining
mean squared error is standardized by the forecast covariance and divided
by the 351 remaining dimensions.

| First GPS report | Flight condition | Smooth share of joint squared error | Remaining mean squared standardized error |
| ---: | --- | ---: | ---: |
| 21856 | Steady | 81.9% | 0.115 |
| 32716 | Steady | 15.7% | 0.082 |
| 36436 | Steady | 18.7% | 0.132 |
| 39916 | Steady | 25.8% | 0.137 |
| 22936 | Turn | 43.6% | 0.253 |
| 33796 | Turn | 6.6% | 1.948 |
| 37516 | Turn | 2.8% | 1.167 |
| 41116 | Turn | 13.0% | 2.981 |

At the end of window 21856, the smooth component of GPS height minus
predicted height was −1.39 m. The nine coefficients were estimated from
the later positions for diagnosis. They cannot be used as corrections
in a prediction test. An unexplained smooth component could reflect the
predicted path or temporally correlated measurement errors. All windows
come from one flight.

The first calculation stopped before reading receiver positions because
its release loader required expanded files already preserved in the archive.
The [failure receipt](esa-scored-path-shape-v1-failure.json) binds the
[original freeze](esa-scored-path-shape-freeze.json) and
[original source](esa-scored-path-shape-v1-source.py.gz). The corrected
calculation uses the hash-checked archive and verifies all terminal results
and forecast seals against the saved release. The two projection tests and
four forecast release tests passed. The corrected run used no new flight
fits or reserved recordings.

[Corrected freeze](esa-scored-path-shape-v2-freeze.json) ·
[Results for all 16 forecasts](esa-scored-path-shape-result.json)
