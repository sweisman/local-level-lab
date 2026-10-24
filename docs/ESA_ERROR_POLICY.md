# Working assumptions for ESA receiver errors

The receiver export reports uncertainty in north, east and height, including
the correlations between those axes. These values help weight a fit; they are
not an independent measurement of the receiver's true error.

The completed position assessment found residual correlation after fitting
local trends. That supports testing persistent errors, but does not determine
their exact size or duration. The following two cases are fixed research
assumptions. Neither provides calibrated confidence or a detection threshold.

| Case | Added uncertainty floor, north/east/height | Scale of standard deviations | Correlated variance share | Correlation time |
|---|---|---:|---:|---:|
| Short memory | 0.05 / 0.05 / 0.15 m | 1 | 95% | 1 second |
| Larger persistent errors | Same floor, before scaling | 3 | 95% | 60 seconds |

The floor is added in quadrature to the reported covariance. Scaling applies
to the full matrix, preserving its cross-axis terms. Five percent of the
working variance remains independent between observations. The rest follows
the stated exponentially decaying correlation.
The time-varying loading uses each working matrix's lower Cholesky factor,
followed by the common receiver-coordinate conversion. This fixes the
cross-time interpretation as well as the within-epoch variances.

The numbers above are chosen sensitivity cases, not sensor specifications,
estimated error bars or guaranteed bounds. They are set before examining any
ESA model preference. A common preferred geometry across these cases would
show robustness to these choices, not establish statistical significance.

## Frames and data boundaries

- Retain the receiver's full north/east/up covariance. The three cross terms
  are north–east, north–height and east–height; height is upward.
- Reject nonfinite or nonpositive-definite reported covariance. Do not repair
  it by adding the floor or clipping eigenvalues.
- Use the same receiver-coordinate weight for every physical candidate. The
  conversion to latitude, longitude and ellipsoidal height uses the receiver's
  declared WGS84 chart. It is an observation convention, not new curvature evidence.
- Use actual, strictly increasing timestamps within one GPS week. Do not
  interpolate measurements or fill gaps. Interval selection handles gaps separately.
- Construct training weights from training rows only. Gyro values, fitted
  residuals, later positions and preferred-model labels are not policy inputs.

## Implementation and verification

The shared `lll.airquantumgrav_error_policy` adapter uses the existing
`lll.ilvis0_error_model` and `lll.ilvis0_structured_covariance` components.
Policy identifiers and numerical values are versioned. Receiver measurements
are preserved, with a hash of the fields used by the policy.

The passing software tests check full cross-axis handling, height sign, time ordering,
invalid covariance rejection before floors, unchanged input rows and independence
from model/outcome metadata. They compare small dense covariance matrices against
the structured operator for residuals and all 27 derivative columns. A dense
request specifies an epoch cap, at most 2,048, and fails before allocation
when exceeded. Long records use the structured operator.

The [76 software checks](esa-error-policy-checks/README.md) have saved source,
environment and test-report bindings. The policies are now used in the
[completed first pilot](esa-development-pilot/README.md) and the
[completed gravity revision](esa-observed-height-pilot/README.md). The
[wider-precision revision](esa-observed-wide-pilot/INTERPRETATION.md) completes
three adequate matched comparisons under the same policies. Their use does
not establish that either covariance describes the true receiver error or
the complete uncertainty of an inertial prediction.
No protected confirmation data is released by these software checks or pilots.

The [completed known-noise test](esa-noisy-prediction/INTERPRETATION.md) retains
these weights while adding generated receiver and IMU errors. All 24 fits
converge, but none passes the physical accuracy screen. Receiver-only weights
are not a qualified complete prediction-error model under those stress settings.
The weights and failed outcomes remain unchanged; full sensor-error propagation
and fitted-calibration uncertainty are the next gates.

[Software verification](esa-error-policy-checks/README.md).

[Receiver assessment](esa-position-assessment/INTERPRETATION.md) ·
[Training-only controls](esa-training-forecast-controls/README.md) ·
[Roadmap](ANALYSIS_ROADMAP.md).
