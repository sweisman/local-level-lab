# Quantify the motion error the Nuuk sample times could miss

The [Nuuk comparison](ESA_NUUK_GROUND_PHASE_RESULT.md) tests the previously
constructed displacement at four matched times. To determine how much the
sampling alone leaves open, compute the lowest acceleration error that
spans the same fixed affine score gap while having zero position error at
those four times. Keep the original zero position and velocity at both
ends of the 120-second scoring window. All times, score weights and the
score gap come from sealed results.

Use one continuous, piecewise linear acceleration along each of the three
coordinates. Insert the exact ground times into the score grid with zero
score weight at new knots. Project the score's acceleration kernel away
from the constant and the position kernels for the four ground times and
the endpoint. Use the continuous time integral of squared acceleration
as the energy measure. Independently integrate the result and verify the
position anchors, endpoint velocity and score change in exact arithmetic.
Report the added minimum acceleration and peak displacement at the knots.

Allow one task, two bounded operations over 125 knots, one worker, one
thread and a 90-second cooperative cap. Bind the sealed source, inputs and
tests and reuse the qualified finite technical recovery procedure. Use no
new receiver or inertial fits and read no reserved recording. The result
is a stress test of the fixed score and sampling. The RMS acceleration of
the constructed error is a requirement of this example, with no measured
probability or aircraft error allowance implied.
