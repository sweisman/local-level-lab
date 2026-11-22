# Trace the growth inside the propagated position bound

The [four recorded checkpoints](ESA_PACKET_BOUND_GROWTH_RESULT.md) put most
of the growing allowance in the propagated position term. That term sums
contributions from residual velocity, the changing map from local motion to
geographic coordinates, and the uncertain clock. Trace these separately
before choosing which bound to tighten.

Reuse the two sealed prefixes, four query times, earlier-only
reference and all calibration ranges. In each packet, use the existing rate
and duration terms to record the three contributions to the position
remainder. Track the initial offset and arithmetic difference separately. Clone the running
totals when a query forks from the shared prefix so overlapping packets
are counted once in each report. Keep the numerical calculation unchanged.
Require byte-identical continuation bounds, identical packet-work counts,
and reconstruction of the recorded accumulated departure remainder at each
checkpoint within one nanometre after conversion to metres.

Allow one bound and up to 6,400 packet steps per candidate, two one-thread
workers, 480 seconds per bound and 550 seconds overall. Use the existing
technical recovery qualifications. This is bookkeeping for an upper bound.
It measures neither actual forecast error nor the size of a true physical
effect. No new fit, measured position or reserved flight is used.
