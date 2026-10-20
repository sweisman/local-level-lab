# Bounding force changes inside an IMU packet

Eleven additional mathematical checks pass alongside the seventeen existing
quantization/period checks. They bound continuous force magnitude when an
explicit continuous motion assumption is supplied. No recording is selected
or analyzed by these controls.

An **IMU (inertial measurement unit)** records an integrated force vector. If
that vector turns during a packet, its integrated magnitude can be smaller
than the integral of its magnitude. Fine sampling alone does not make them equal.

## The direction-cone bound

Write body-frame force as \(f(t)=m(t)u(t)\), with \(m\geq0\) and unit direction
\(u\). Suppose a continuous direction can be assigned angular speed no larger
than \(\beta\) throughout a packet of duration \(T\). Relative to the midpoint
direction, the force lies within a cone of half-angle \(\beta T/2\).

For \(\beta T/2<\pi/2\), projection onto the midpoint direction and the triangle
inequality give

\[
\left\|\overline f\right\|\leq\overline{\|f\|}\leq
\frac{\left\|\overline f\right\|}{\cos(\beta T/2)}.
\]

The force magnitude may change within the packet; constant magnitude is not
required. The bound concerns the **body-frame force direction**, not merely
aircraft angular speed. Changes in the required navigation force also affect it.
An omitted gyro or fused attitude cannot silently supply this assumption.

For illustration, an assumed direction rate of 10°/s over 5 ms raises an upper
bound near 9.81 m/s² by about 0.00000094 m/s². That is an example motion envelope,
not measured sensor performance. Summing body vectors across one second can
lose much more information than using individual 5 ms packets.

## Period uncertainty and unsupported assumptions

The helper retains the count-error box and lower/upper integration periods.
It uses each packet's largest possible period for the cone angle, bounds the
integral of magnitude and divides by the allowed total duration. It assumes
neither independent random errors nor a 1/√N reduction in deterministic bounds.

Without a direction-rate assumption, or if any packet's cone reaches 90°, the
continuous upper bound remains explicitly unavailable. A complete rotation
can integrate to zero despite substantial continuous force; the tests retain
that counterexample. Unsupported cones are not clipped.

## Verification and remaining work

Independent exact integrals cover rotating forces with constant and changing
magnitude, uncertain periods, no direction assumption and a full rotation.
All existing integer, sign, quantization and duration tests still pass.

This supplies one deterministic component of C03's error budget. It does not
establish a recording's direction envelope, integration clock, calibration,
synchronization, receiver-derivative uncertainty or statistical coverage. Common
motion/support rules and combined uncertainty remain before C04's recorded-data
comparison. The main 53-stretch findings are unchanged.

[Averaging tests](../../analysis/tests/test_ilvis0_force_averaging.py) ·
[Increment bounds](../../analysis/lll/ilvis0_increment_bounds.py) ·
[Quantization](QUANTIZATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
