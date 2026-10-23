# Reduce repeated work without changing prediction bounds

Repeated prediction times currently repeat much of the same packet history.
A possible improvement is to keep one untruncated prefix, copy its state for
each requested prediction, and evaluate that prediction's uncertain final
packets separately. This would reduce repeated work; it would not make the
mathematical bounds tighter.

**Complete native reuse remains unqualified.** The completed six-case comparison
keeps its original complete-history path unchanged. Separately, the
[typed source-copy controls](../ilvis0-prefix-source-controls/README.md) now pass
all eighteen cases against independent cold kernels. The
[complete-state implementation plan](../ilvis0-prefix-reuse/NATIVE_PLAN.md)
addresses the geographic, force and clock states still needed before use.

## What the source establishes

The reference, interval-derivative and point-derivative source kernels store
fixed-size, trivially copyable C++ states. Their query time enters through the
clipped packet fraction. For a packet strictly before the earliest possible
query, that fraction is constant one. The accumulated body rotation and source
values then do not depend on the later query time.

The relevant implementations are
[reference source](../../analysis/lll/ilvis0_source_stream.cpp),
[interval derivatives](../../analysis/lll/ilvis0_source_derivative_intervals.cpp)
and [point derivatives](../../analysis/lll/ilvis0_source_point_derivatives.cpp).
The point kernel preserves both one-sided derivatives at a knot, while the
reference kernel retains the preceding-packet derivative. Equality with a
packet boundary therefore cannot be treated as an ordinary full-prefix case.

This observation covers those source kernels. It does not yet establish safe
reuse of the geographic integrator, common clock, force integrals or complete
Python/C++ state.

## Proposed implementation

1. Use the latest declared prediction time for a canonical prefix. Process
   requests in increasing time order, advancing that prefix only through
   packets whose end is **strictly earlier** than every relevant lower clock
   endpoint. Account for both represented and exact packet-time arithmetic.
2. Fork the complete state for a request, retarget only its query-time fields,
   and process its remaining uncertain packets. Preserve the original clipping,
   boundary ownership, derivative and outward-rounding rules. The canonical
   prefix must remain unchanged by the fork.
3. Include every state component: geographic position and departures, velocity,
   relative attitudes, raw-force integrals, all source kernels, common-clock
   bookkeeping and direct-source remainder accumulators. Copying one opaque
   kernel buffer alone is insufficient. Retarget its query through a checked
   typed API, not guessed byte offsets.
4. Bind reusable state to the exact input and parameter hashes, expansion,
   calibration reference, conditioning proof, compiler, numerical environment,
   arithmetic backend, packet index and source layout. A changed training proof
   starts a separate prefix; it cannot inherit the old proof's trajectory state.
5. Keep one canonical state and one working fork where possible. Bound memory
   and prefix/tail work before launch, charging computed steps and restored
   states explicitly. Reuse is not a way to reset a completed allowance.

## Qualification before use

Compare independent cold runs with the proposed reused-prefix path for all
three models and both processing cases. Require the same requested times,
physical bounds, all 27 parameter directions, all 24 shared coordinates,
source bindings and warning behavior. Check native centres, derivative rows,
coefficient maps, outward intervals and known probes—not just runtime or a
successful return code.

Include nonzero and asymmetric clocks, nonuniform packet durations, exact
boundaries and both sides of each boundary. Reject a fork taken after clipping
has begun, an incompatible conditioning proof, a changed source/layout or an
incomplete state. Demonstrate that processing one fork cannot alter another.
First qualify small deterministic cases, then a separately frozen long-history
comparison with finite work limits. No active or completed study is restarted.

Passing this work would qualify an efficiency improvement only. Useful
prediction widths, whole-period coverage and the observation-error model remain
separate scientific requirements.

[Current comparison](README.md) · [Frozen calculation](PLAN.md) ·
[Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md).
