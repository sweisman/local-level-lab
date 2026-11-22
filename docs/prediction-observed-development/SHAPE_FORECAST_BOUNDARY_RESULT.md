# The shape forecasts stay apart beyond the first 20 reports

Removing the first 20 of the 120 later GPS report times kept **98.90–99.54%**
of the squared separation between the zero-field globe and disc forecasts
after allowing smooth position corrections. This holds across the two
complete fit settings and all four working covariance choices.

| First later reports omitted | Squared separation retained across all settings |
| ---: | ---: |
| 1 | 99.97–99.99% |
| 5 | 99.84–99.97% |
| 10 | 99.59–99.93% |
| 20 | 98.90–99.54% |

The separation is present well after the training cut. The calculation
leaves the omitted positions unknown. It carries their uncertainty forward
using the marginal covariance of the retained part of the forecast.
The full-period result reproduced the original squared distances in all
eight comparisons. A constructed correlated-error test verifies that
omitting reports preserves more uncertainty than conditioning on them.
The focused suite passed six tests.

The [frozen method](SHAPE_FORECAST_BOUNDARY_PLAN.md) used saved predictions
from one development recording. It started no fits and read no later GPS
positions or protected recordings. The result rules out reliance on the
first 20 reports under the tested weights. Validation of the weights
throughout the prediction period remains open.

[Source and input freeze](shape-forecast-boundary-freeze.json) ·
[Results for all eight comparisons](shape-forecast-boundary-result.json)
