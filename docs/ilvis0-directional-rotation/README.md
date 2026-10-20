# Preserve direction when bounding a rotation

The current propagation method uses vector-length bounds in several places.
They are conservative, but can assign uncertainty to every coordinate even when
the geometry keeps one coordinate nearly fixed. This is a possible source of
unnecessary height uncertainty, not yet a demonstrated explanation of the full
prediction widths.

A simple component now has an exact bound: rotating a vertical unit vector
around its own axis cannot change its vertical component. With a small sideways
tilt, the change in that component is quadratic in the tilt, even if rotation
around the vertical axis is large.

The implementation uses rotation-vector coordinates, not Euler angles. It passes
12 local checks, including 384 independent numerical rotations, known-axis,
exact rational and large-angle cases. It has
not been connected to the aircraft propagation code. All existing studies and
their bounds remain unchanged.

## Mathematical bound

Let `u` be a coordinate unit vector, `w` a rotation vector in radians, and
`R = exp([w]×)`. Put `q = |w × u|²`. Rodrigues' formula gives

`u · R u = 1 − q (1 − cos |w|) / |w|²`.

The limiting value at zero is understood. Since the ratio lies between zero and
one half, the component along `u` is between `max(−1, 1 − q/2)` and `1`.
Also `|R u − u|² = 2(1 − u · R u) ≤ min(4, q)`. The squared transverse component
is at most `min(1, q)`. For a supplied box, bound `q` by the sum of squared maximum
absolute values of the two perpendicular rotation-vector coordinates. All
arithmetic in the component implementation uses exact rational numbers.

For example, perpendicular coordinates bounded by 0.01 and 0.005 radians imply
a parallel-component loss of at most 0.0000625. The parallel coordinate may range
over ±20 radians without changing that bound. This is a mathematical example,
not an inferred aircraft calibration.

## Next qualification

Derive a source-bound action on a general force vector and a known installation
rotation. Preserve transverse force, reference-center departures, calibration
errors and numerical margins. Test it against independent known motions before
replacing any norm-based operation in a separately frozen propagation candidate.
A successful isolated component cannot qualify a full prediction method.

[Previous diagnostic](../ilvis0-training-remainder-diagnostic/INTERPRETATION.md) ·
[Implementation](../../analysis/lll/ilvis0_axis_rotation_bounds.py) ·
[Tests](../../analysis/tests/test_ilvis0_axis_rotation_bounds.py) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
