# Check gyro-derived shape with the same background field on both paths

Reuse the sealed force-direction angles and the same earlier-only
stencils, velocity sources, fixed gravity and candidate force equations.
Predict directions for the globe and for the disc carrying the same
specified local north/down field. Retain the full specified field in
both force equations. Independently vary the fraction retained in
the gyro-based frame from zero to one for each shape.

For the globe use rotation about the fixed polar axis. The disc's
specified field is a local vector that varies along the route. Express
it in disc axes at each earlier receiver epoch. Hold the mean axis
vector over each intervening interval and integrate its noncommuting
rotations in time order. This defines a frame along the recorded path
without requiring a globally rigid rotating disc.

Evaluate both shapes at 41 equally spaced fractions. Include an
analytic lower bound on the RMS error between those fractions. For
each pair, reset the time origin for the bound at the first support
edge, since angles are invariant to a common starting rotation.
The derivative of the rotated force with respect to the fraction is
bounded by its magnitude times the elapsed field angle. Propagate
that bound through each vector average, normalization, pair angle,
and RMS. Verify that both globe endpoints reproduce the earlier
rotation-frame results.

Freeze one thread, at most 192 candidate vector supports and 7,872
weighted vector averages. Test the frame integration and the continuous
bound on constructed cases first. Use the existing measured angles
without rereading inertial samples. No fits, later 120 reports or
reserved flight groups. A ranking over this fraction range still
does not bound gyro gain, bias, direction errors, or a different
background field.

[Earlier gyro direction check](ESA_GYRO_FORCE_DIRECTION_RESULT.md)
