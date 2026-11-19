# Local calibration barely closes the conditioned shape gap

One pair of zero-field globe and disc forecasts on ESA recording 187
was about **25.20–26.25 standardized units apart** after conditioning on
earlier positions and allowing smooth errors. In the saved local linear
approximation, the two candidates could close at most **1.72%** of that
distance within the larger of the two earlier fit-loss allowances.

| Allowed increase in earlier squared loss | Largest upper bound on gap closure | Smallest lower bound on distance left | At least this share of the gap remained |
| ---: | ---: | ---: | ---: |
| 0.001 | 0.159 | 25.04 | 99.37% |
| 0.01 | 0.437 | 24.77 | 98.28% |

The bounds cover all 27 saved calibration directions, the original
parameter limits and changes of at most 0.10 in each normalized parameter.
The calculation propagated changes through earlier-data conditioning and
then removed the nine smooth position terms. It used the four working
covariances from the [forecast pair study](FORECAST_PAIR_INFORMATION_RESULT.md).

Ten of the 16 optimization calls ended without reporting convergence.
All 16 returned feasible trials. The upper bounds use convexity of the
earlier affine loss and hold independently of whether those numerical
searches found the best feasible trial. The eight focused software checks
passed. The [frozen method](CONDITIONED_SHAPE_CALIBRATION_PLAN.md) used no
new trajectory fits, later GPS positions or reserved flight groups.

These are local linear bounds under stated loss allowances. Applying a
bound to the actual nonlinear paths requires checking the approximation
throughout the allowed calibration region. The working covariance and
the allowances also need independent empirical support.

[Source and input freeze](conditioned-shape-calibration-freeze.json) ·
[All bounds and numerical exit flags](conditioned-shape-calibration-result.json)
