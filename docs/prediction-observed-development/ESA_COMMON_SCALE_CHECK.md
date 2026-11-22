# Can one uncertainty scale cover both flight conditions?

Use only the eight already scored windows on ESA development recording 187.
Check each inertial error description separately. In each case use the
forecast covariance that includes both steady and turn allowances. The
archived scores fix the predicted path and the shape of its covariance.
This check asks whether multiplying that covariance by one constant could
make the error sizes compatible across all windows.

Each forecast has 120 three-axis GPS reports. If its conditional error were
zero-mean Gaussian with the proposed covariance times a multiplier `s`,
its archived squared standardized error `Q`, divided by `s`, would follow a
chi-square distribution with 360 degrees of freedom. This uses the full
forecast covariance, including dependencies between coordinates and times.
For each window, invert that check to obtain the scale interval
`[Q / chi2_upper, Q / chi2_lower]`. Use the chi-square quantiles at
`0.05 / 16` and `1 - 0.05 / 16`. The union bound gives a simultaneous 95%
reference under the stated Gaussian model without treating windows as
independent. Use the same bands when checking each flight condition alone.

The diagnostic compares the largest lower end with the smallest upper end
for four steady windows, four turning windows and all eight windows. A
reversed interval means the windows have no common scale under this
reference. The two inertial error descriptions are sensitivity checks using
the same measurements. This is an exploratory diagnostic of one flight.
Its assumptions remain open, including the predicted mean, covariance
shape and between-flight variability.

The source data for this calculation are the `quadratic` fields under
`scores[forecast_identity].scores.both` in the
[turn score receipt](esa-repeat-turn-forecast-evidence/receiver-scores.json)
and [steady score receipt](esa-straight-control-evidence/receiver-scores.json).
Their SHA-256 hashes are `ae1fa59746e4f57cb539595afbde23d71899a7fdde73af438976c82daf3d988e`
and `af3c50ac7841ad3ab91ee811ebe8e51e216a8e7e37673bfa2f228d0b9bf4b19c`.
Use one numerical thread. The calculation uses 16 saved error values and
two quantiles. It starts zero fits and accesses no original recordings.

## Result

No common scale covers the eight windows under the reference above. Even
assigning one scale to steady flight and another to turns leaves incompatible
windows in each condition. The two inertial error descriptions agree to
the precision shown.

| Windows | Largest lower end | Smallest upper end | Common scale |
| --- | ---: | ---: | --- |
| Four turning | 2.748 | 0.541 | None |
| Four steady | 0.511 | 0.117 | None |
| All eight | 2.748 | 0.117 | None |

The quantiles are 290.939 and 437.691. In the turning group, windows
starting at GPS indices 41116 and 22936 set the two ends. In the steady
group, indices 21856 and 32716 set the ends. A useful next check is why
the forecast errors differ even among windows in the same motion category.
The score totals alone cannot distinguish poorly scaled covariance from a
systematic error in the predicted path.
