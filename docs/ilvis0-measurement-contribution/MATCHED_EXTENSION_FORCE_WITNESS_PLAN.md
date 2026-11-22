# Test one shared GPS correction on the added IMU8 flight

The [force-only check](MATCHED_EXTENSION_FORCE_RESULT.md) left 79 positive
later gaps for three candidates on this flight. Test whether a single
position perturbation can clear them. Use the same perturbation at each
epoch across all three receiver tracks, both clocks and all four models.
Keep the earlier-only accelerometer gains fixed. The added IMU21 flight
has no gaps to explain under this inequality.

Reuse the [original witness method](SHARED_FORCE_WITNESS_V2_PLAN.md) and
its declared receiver covariance. Derive a proposal from the positive
saved inequalities only, with at most 96 force gradients and 128
projection steps. Recompute the nonlinear force bounds for all 12,600
inequalities, including the training windows and the previously satisfied
cases. Report gaps before and after, all receiver corrections, and the
largest position change. Compare the same four sealed full-IMU forecasts
with the shifted reference tracks without refitting.

This uses the actual observed discrepancies, including later ones, to
construct a sensitivity example. It supplies no estimate of the receiver's
actual errors. If the procedure leaves gaps, preserve them. Its finite
search does not establish that no shared correction could work.

Use a single worker and thread, a five-minute cooperative cap, no inertial
fits and no forecast propagations. Reserve one gradient batch, one
projection batch, all eight subdivisions of each force interval and twelve
forecast error checks. Qualify the existing recovery path with at most one
technical restart and a ten-minute continuation cap.
