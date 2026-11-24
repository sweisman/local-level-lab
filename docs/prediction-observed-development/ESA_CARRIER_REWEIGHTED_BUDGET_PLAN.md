# Check the new range weights with imperfect position anchors

Use the original ESA 187 weights and the four fixed choices from the
[range and motion tradeoff](ESA_CARRIER_WEIGHT_TRADEOFF_RESULT.md).
Reconstruct the same receiver geometry and preserve every retained
satellite set. Apply the weights to the saved aircraft carrier residuals
and the matching Nuuk Museum measurements. Report the signed aircraft,
ground and aircraft-minus-ground scores.

For each new choice, interpolate the six unknown anchor errors linearly
between their times. Compute the corresponding signed score weights
after subtracting the range response. The sum of absolute weights gives
the maximum score change per metre of independent componentwise anchor
error. The remaining trajectory error is zero at the anchor times and
uses the saved continuous acceleration bound.

Keep the earlier example assumptions of a one-metre error allowance per
anchor coordinate, 1.876 mm/s² RMS acceleration error and 2 mm RMS of
range error outside ground coverage. Include the validated nonlinear
geometric remainder and the observed full aircraft score. Solve for
how much range error allowance remains in the ground-covered directions.
Reproduce the earlier 0.96 mm allowance with its original anchor and
motion coefficients before evaluating the four new choices.

This is a replay of one open development flight. With zero independent
aircraft error caps the scientific decision remains an abstention.
Use one task, one numerical thread, 246 charged calculations and a
90-second wall cap. Use zero new model fits, original measurement reads
and reserved-flight reads.
