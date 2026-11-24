# Find the independent accuracy required to preserve the ESA score gap

Use the [continuous trajectory study](ESA_CARRIER_CONTINUOUS_BOUND_RESULT.md)
and its saved solver weights. Reconstruct the score decomposition with
those weights fixed. Repeat none of the numerical searches. Check each
saved upper bound before reusing the weights.

In the decomposition, every term has a coefficient and an error cap.
Sum the acceleration term, position-anchor term, range terms and
remaining numerical error bound. Add the validated geometric remainder
separately to each range cap. Recompute that remainder and the maximum
possible position error if the anchor or acceleration cap changes.

For each satellite set, find the one-at-a-time caps on anchor position
error, acceleration error, and range error in directions covered by
the ground receiver. Hold the other example caps fixed. Also find a
single factor by which all four example caps could grow together.
Use 32 bisection steps and keep the largest tested value whose bound is
strictly below the gap. Search only up to 5 m per coordinate, 10 mm/s²
RMS acceleration error, 20 mm RMS covered range error and five times
the example limits. A bound that reaches the search ceiling reports
only that ceiling. The limits are tradeoffs for one development
window and cannot be calibrated on the same range observations.

Use one task, one numerical thread, 245 charged calculations and a
120-second wall cap. Use sealed flight 187 material, with zero original
downloads, model fits and reserved-flight reads.
