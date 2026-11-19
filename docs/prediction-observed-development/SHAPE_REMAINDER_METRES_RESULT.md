# A four-centimetre target for the shape calculation

If the earlier standardized nonlinear remainder can be bounded by 0.1
per candidate, a **4.03 cm** remainder bound on each position coordinate
at each report would preserve positive shape separation under all four
tested covariances. This is a target for a proof of the integrator's
nonlinear error over the feasible calibration region.

| Working covariance | Upper coefficient sum from earlier reports (per metre) | Upper coefficient sum from later reports (per metre) | Sufficient per-coordinate bound (cm) |
| --- | ---: | ---: | ---: |
| Full drift, fixed receiver weights | 0.5755 | 155.6295 | 4.09 |
| Full drift, reported receiver weights | 0.6582 | 157.7817 | 4.03 |
| Reduced drift, fixed receiver weights | < 10⁻¹² | 152.1681 | 4.19 |
| Reduced drift, reported receiver weights | < 10⁻¹² | 153.6060 | 4.15 |

The calculation allows both candidate errors to align against the shape
gap. It carries the earlier position error through the conditioning
before taking absolute values. Less than 0.42% of the coefficient sum
comes from earlier reports. Their separate role in determining which
calibration settings fit the training data still needs its own bound.

The backward calculation encloses the transpose of the exact linear
operator defined by its stored coefficients. The coefficient intervals
were narrower than 2 × 10⁻¹⁵ in all four cases. The constructed rational
reference and the four forward-versus-backward checks passed. The small
suite passed all three tests. The [frozen calculation](SHAPE_REMAINDER_METRES_PLAN.md)
used no fits, new integrations or reserved data.

A source-specific bound on each coordinate could use the same coefficients
without assuming one limit everywhere.

The archived scalar calculation reduces gravity as the simulated aircraft
climbs. It uses an inverse-square adjustment at each step's midpoint,
relative to the first GPS height of 1,482.531 m. The current interval
predictor holds gravity constant. At the saved later heights, the
inverse-square factor lowers gravity by roughly 0.04–0.06%. Those heights
illustrate the scale of the adjustment. They are insufficient to bound
its effect on the simulated positions.

To test the four-centimetre target, the interval predictor first needs
the same gravity calculation as the scalar integrator. It then needs to
bound the accumulated error over all calibration settings that fit the
earlier observations. Individual exact replays check specific settings.
[Exact replay results](SHAPE_REMAINDER_WITNESS_RESULT.md).

[Source and input freeze](shape-remainder-metres-freeze.json) ·
[All coefficient bounds and tolerances](shape-remainder-metres-result.json)
