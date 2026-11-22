# Allow intermediate amounts of the field to remain in the gyro

The [eight-window direction check](ESA_DIRECTION_HOLDOUT_SCORE_RESULT.md)
found a different shape preference on the strongest turn depending on
the field setting. On the same sealed measurements, check whether an
intermediate retained fraction gives either shape a smaller error.

Keep the observed angles, antenna settings and receiver processing fixed.
Verify the receiver export and exact selected-row hashes from the sealed
forecasts. Require the two ends of the retained-fraction calculation and
the separate zero-field case to reproduce the sealed predictions before
interpreting any intermediate result.

In the specified-field case, leave the physical field and its contribution
to the required forces fixed. Vary the fraction left in the gyro from zero
to one separately for each shape. Use 81 equally spaced fractions across
the full interval. Evaluate every angle pair, width, differentiation
method and antenna setting in the eight-window receipt. The zero-field
case, in which the physical field is absent, stays a separate candidate.

Bound the best error between grid points. For a pair of force directions,
factor out their shared frame rotation up to the first support. The remaining
rotation changes with retained fraction at no more than the angular rate
times elapsed time. The positive time weights and the force-vector norms
then bound the change in each averaged direction. Check that the predicted
vectors stay nonzero, combine the bounds over all 28 angles, and report a
lower and upper error for each shape after allowing the zero-field case.
An overlap of the shape error bounds leaves the preference unresolved for
that setting. Report the earlier absolute error references separately.

This is a sensitivity check on known development outcomes. It measures
shape discrimination under the declared field and processing alternatives.
Measurement of the free background field and independent-flight accuracy
remain separate roadmap steps.

Allow one verified receiver-file pass of 64,080 reports and 16 charged
window/width operations. For each operation allow two derivative methods,
two shapes, eight late supports, four nodes per receiver interval and 81
fractions, plus one endpoint replay of the full paired-method predictions.
Use one worker and one numerical thread with a finite 150-second ceiling.
Use the saved angle receipts. No new IMU reading, navigation fitting or
release of a reserved group is required.
