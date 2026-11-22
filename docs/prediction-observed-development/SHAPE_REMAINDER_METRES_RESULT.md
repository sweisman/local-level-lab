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
relative to the first GPS height of 1,482.531 m. At the saved later heights,
the inverse-square factor lowers gravity by roughly 0.04–0.06%. Those
heights illustrate the scale of the adjustment. They are insufficient
to bound its effect on the simulated positions.

The geographic step now includes the same midpoint gravity law, with
an outward-rounded bound on the gravity term and its linearization
error. A generated sequence of 19 full packets and one partial packet
agreed with the compiled native calculation for all three models. The
checks varied starting height, vertical speed, anchor gravity and report
time. They used generated inputs and numerical comparison tolerances.

The shared-prefix predictor now applies the same correction. It keeps
the anchor gravity in the reference acceleration and adds only the
height-dependent difference to both halves of the midpoint calculation.
Its reports identify the gravity anchor and require it to match when
combining bounds with native derivatives.

On a generated 13-packet record, the shared-prefix and cold calculations
gave identical reports for three query times under each Earth model.
The test covered times near packet boundaries, matched the compiled
native positions within one micrometre and checked the bounds at three
calibration settings. The next check is whether the bounds remain useful
as the history grows over the settings that fit the earlier observations.
Neither these short tests nor the individual exact replays establish
the accumulated error over that region.
[Exact replay results](SHAPE_REMAINDER_WITNESS_RESULT.md) ·
[Generated histories up to 40 seconds](SHAPE_GRAVITY_HISTORY_RESULT.md).

[Source and input freeze](shape-remainder-metres-freeze.json) ·
[All coefficient bounds and tolerances](shape-remainder-metres-result.json)
