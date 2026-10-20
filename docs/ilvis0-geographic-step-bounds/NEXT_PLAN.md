# Repeated packets and time intervals crossing boundaries

The geographic single-step controls are complete. Preserve their frozen sources,
allowance and results. The next component will compose these mathematical bounds
through a finite generated packet history, including the receiver lever arm.

For an observation time t, packet i contributes the fraction
`clip((t - packet_start[i]) / packet_duration[i], 0, 1)`.
Compute its exact interval and bound its deviation from the chosen affine
expansion by checking interval endpoints and the packet's two breakpoints.
Use the native derivative from the preceding packet at an internal boundary and retain
the resulting kink remainder. Do not apply one interior tangent across a kink.

Use the same time displacement for every packet. Conservative marginal bounds
may widen uncertainty, but must not remove calibration/time cross terms, reuse
an observation outside support, interpolate across a gap, or discard an original
increment. A zero packet fraction is exactly the identity. Unsupported time
support or a geographic-domain crossing must produce an explicit failure.

Check short and longer generated histories, all three physical candidates,
fixed and profiled removal, interior times, exact boundaries and intervals
crossing multiple boundaries. Compare native predictions and all nuisance
directions with an independent implementation. Check bounded derivatives where
they exist and one-sided derivatives at boundaries; global remainders must cover
both sides. Record growth and unsupported regions honestly.

Freeze finite counts and numerical tolerances before execution. This component
uses generated measurements only. Whole-record floating-point enclosure and
observational covariance remain separate gates; no new archival prediction
allowance follows from short mathematical controls.

[Completed geographic controls](INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
