# Estimate all accelerometer biases and gains from earlier directions

Reuse the previous eight earlier and eight later supports. Keep the three
velocity sources, two averaging widths and three matched field assumptions.
Hold the measured gyro increments fixed. Permit all six accelerometer
coordinates in the existing working bounds, ±0.10 m/s² for each bias and
±0.02 for each relative gain. Average each transported sensor channel and
each transported axis on the original supports. Applying a constant
calibration to those means is algebraically the same as correcting each
sample before averaging.

For each shape and setting fit the first eight unit directions. Eliminate
the proper starting rotation analytically at each calibration proposal by
minimizing squared chord distance between unit directions. Fit the original
box with three matched starts, zero and opposite half-box perturbations.
Allow at most 200 training evaluations per start. A usable fit needs a
full-rank starting rotation and a box-projected gradient no larger than
10⁻¹⁰ in squared chord loss per normalized calibration coordinate.
Retain every start and score the later directions with that calibration and
starting rotation held fixed. Select by earlier squared chord loss only.
Measure numerical start-to-start differences separately from the later
model difference.

Report the rank of the six-axis direction derivative after accounting for
the starting rotation, with a relative singular-value cutoff of 10⁻⁸.
A common gain scale is unobservable in unit directions, so this rank
diagnostic does not identify an absolute gain. Preserve the original
six-dimensional box and every coordinate. Do not use later observations
to choose starts, alignments, bounds or an error scale.

Freeze at most 108 starts, with a limit of 21,600 earlier calculations,
one thread and a 90-second wall ceiling. Read no protected flight groups
or the 120 later receiver reports from the original position comparison.
The resulting one-flight retrospective comparison gives no significance
or calibrated accuracy claim.
