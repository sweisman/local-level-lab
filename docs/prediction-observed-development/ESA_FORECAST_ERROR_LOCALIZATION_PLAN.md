# Locate the forecast error that survives the existing covariance terms

Reuse the eight already scored windows, two error descriptions and exact
receiver and forecast inputs from the [variance-range check](ESA_COMPONENT_SCALE_FEASIBILITY_RESULT.md).
Use its upper bound on the common native multiplier. Retain the full
forecast path and start no trajectory fits.

For each window, examine the full 120 reports, then each of four
consecutive 30-report blocks. In each interval, examine the full
three-axis residual and each axis separately. Use the appropriate
principal covariance for each marginal. Whiten by its native factor and
find a contrast orthogonal to the added steady and maneuver roots. Use
the remaining projection of the observed error as the contrast. Account
for its measured leakage into those roots, allowing both variance ratios
the full range up to exp(10).

The squared contrast over its maximum variance gives a lower bound on
the whole-window quadratic score. Compare it with the original upper
reference for all 360 coordinates. The threshold remains the
whole-window threshold, including when one axis or block is examined.
An exceedance therefore identifies a sufficient source of joint
incompatibility. It does not establish a per-block probability or an
independent detection. Report every block without selecting a new
prediction rule from these outcomes.

Test the marginal covariance and contrast bound against known
covariances, including an exactly removable error and a wholly
unexplained error. Freeze one task per error description, one thread,
120 seconds and twenty calculations per window. Read no reserved flight.
