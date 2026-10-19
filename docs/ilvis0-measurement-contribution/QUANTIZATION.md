# Increment resolution, integration time and magnitude bounds

The first **17 deterministic quantization/period checks pass**. They qualify a
small mathematical helper, not an IMU (inertial measurement unit) error model or
a likelihood for recorded flights. No original measurements or fits are used.

## What is bounded

An integer delta-velocity count represents an increment, not a force rate.
For each packet, supply its conversion scale, a componentwise count-error bound,
and positive lower/upper integration periods under an explicit clock hypothesis.
The helper finds exact minimum and maximum vector norms in that component box,
then divides by the corresponding period bounds.

The signed integer counts are neither changed nor silently interpolated. A
missing, reversed or nonpositive integration interval is rejected. Packet-header
elapsed time is not automatically declared to be the increment integration
period. Nominal-period and header-period hypotheses remain distinct inputs.

For the empirically supported IMU8 delta-velocity scale 2⁻¹⁴ m/s/count, one count
at 200 Hz corresponds to about **0.0122 m/s² per component**. A declared one-count
error bound can change the norm by at most about **0.0211 m/s²** across three
components. A half-count assumption halves that worst-case bound, but requires
its own rounding justification. This is not a measured sensor-noise floor.
The helper does not choose a rounding mode or infer the true count-error bound.

## Averaging does not remove an unknown deterministic error

The defined aggregate is the sum of packet increment magnitudes divided by the
sum of their integration durations. This is a duration-weighted average of
packet-mean force magnitudes. It differs from an equal-weight mean of rates when
durations differ, and from the norm of a summed body vector during rotation.

Repeating the same quantized observation 100 times does not shrink its
deterministic bound. A 1/√N reduction would need an independently justified
random-error model and temporal dependence treatment. The bounds here make no
such assumption and provide no calibrated statistical coverage.

## What remains unbounded

The norm of an integrated force vector can be smaller than the integral of its
norm when the body rotates inside a packet. The helper's upper bound therefore
applies to packet-mean force, not instantaneous force or continuously averaged
force magnitude. It explicitly reports that no continuous-force upper bound has
been established. Such a bound needs a declared within-packet motion model;
an omitted gyro cannot be silently reused to provide it.

Calibration uncertainty, receiver differentiation, synchronization and nonlinear
magnitude bias must still be combined consistently. The completed averaging
matrix demonstrates why these effects cannot be ignored. Successful software
checks do not settle which physical integration period the archive represents.

Implementation: [increment bounds](../../analysis/lll/ilvis0_increment_bounds.py)
and [known-answer checks](../../analysis/tests/test_ilvis0_increment_bounds.py).

[Channel requirements](CHANNEL_CONTROLS.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
