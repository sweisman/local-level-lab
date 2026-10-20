# What the midpoint local-step controls establish

All **30 frozen identities passed** across three physical candidates, two
hemispheres, zero/profiled removal, narrow/broad boxes and zero-rate centers.
The study used 1,920 generated probes, 1,950 calls through a wrapper around the
unchanged C local step, and 3,870 independent reference calls. No archive
originals, full-record native sweeps or optimizer starts were used.

The largest sampled remainder/bound ratio is about 0.99997. The largest
C/reference value discrepancy is about 1.3e-13 in these short controls.
The derivative reference uses complex-step differentiation and is also checked
against an independent known answer and symmetric differences in component tests.

The bounds cover joint attitude, calibration, force, velocity, latitude, gravity
and processing-removal effects over declared input regions. They retain the
native distinction between removal in attitude propagation and physical
Coriolis. That distinction also holds for the stationary disc candidate.

This closes the local-step component under its supplied global input bounds.
It does not yet produce those bounds from the complete geographic state or
propagate the native predictor/corrector, antenna lever arm and receiver timing.
The nominal comparison uses the double-precision C kernel; it is not a proof
of a long-record floating-point enclosure or every precision variant.

The mathematical bounds are derived analytically. The probes test their
implementation; their largest observed error is not used as the bound. No
new archive prediction fit, empirical coverage result or scientific detection
follows from this component qualification.

[Results](README.md) · [Frozen plan](PLAN.md) · [Next closure](NEXT_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
