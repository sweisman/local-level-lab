# Why a fit can remain numerically unresolved

In the prediction pilots, a fit reconstructs an aircraft path from the IMU
measurements while estimating calibration. Before its model comparison is
accepted, a fresh calculation checks that the solver has settled. For an
ordinary nonzero-cost fit, several checks must pass together. Near-zero generated
controls have a separate, tested repeat rule.

| Check | What it asks |
|---|---|
| Stationarity | Would a permitted small calibration change still substantially improve the fit? |
| Cost stability | Does a fresh correction leave the weighted mismatch effectively unchanged? |
| Position stability | Does that correction leave the calculated positions unchanged to within the declared numerical tolerances? |

The position-stability limits are 1 mm RMS and 1 cm maximum on each axis.
These compare two calculated paths. They are **not** accuracy limits against
the receiver, sensor specifications or confidence intervals. A numerically
settled fit can still predict the unused receiver observations badly.

The separate cost check can fail even when the position change is very small.
That calls for diagnosing the numerical calculation; it does not count as
evidence for or against a physical model. The original fit label stays unchanged.

For the [first ESA pilot](esa-development-pilot/README.md), a saved-results audit
finds 15 fits satisfying all these checks, eight failing the RMS position check,
and one failing both RMS and maximum position checks. This agrees with its
original 15 numerical passes and nine unresolved fits.

The [shared diagnostic](../analysis/lll/stopping_diagnostics.py) verifies saved
fit hashes and reads thresholds from the study's frozen source. It performs no
fit or trajectory integration and does not apply a revised stopping rule.
The [completed gravity revision](esa-observed-height-pilot/README.md) has eight
numerical passes, nine position-stability failures and seven
cost-stability failures. All eight specified-field forecasts meet the physical
accuracy limits, but only one passes the numerical gate. The other seven remain
ineligible for model comparisons. The [completed fixed-point diagnostic](esa-stopping-resolution/README.md)
reproduces every saved cost and numerical outcome. Repeated calculations are
identical, while very small calibration changes still upset cost stability.
For the field-globe cases, local position changes remain below 4 micrometres.
The [completed precision comparison](esa-precision-diagnostic/README.md) reproduces
both original residual vectors exactly in binary64. Wider integration precision
brings all eight field-globe cost changes below the same limit. Changing only
longitude wrapping is insufficient. No threshold or original fit label changes;
all 48 [long known-motion derivative controls](esa-wide-tangent-controls/README.md)
now pass, and the [24-case training study](esa-wide-training-controls/README.md)
qualifies every case under the unchanged stopping and accuracy checks. The
[matched observed revision](esa-observed-wide-pilot/INTERPRETATION.md) now returns
22 numerically qualified forecasts after 56 source-bound adapter/audit checks.
All eight earlier passes are retained and fourteen more starts qualify. Two
disc starts reach the cooperative runtime ceiling; those are incomplete
calculations, not model ties. Original failed fits keep their historical labels.

[Prediction method](PREDICTION_VALIDATION.md) · [Roadmap](ANALYSIS_ROADMAP.md).
