# Complete native-prefix implementation

The shared implementation now passes its [short frozen comparison](../ilvis0-native-prefix-controls/README.md):
twelve supported cases reproduce the full original reports and all 51 design
columns; two unsupported initial-source cases retain the same rejection.
The next gate is long-history equivalence with measured time and memory.
Short-input success does not establish useful full-record prediction uncertainty.

The source-copy component is only one part of the repeated-history optimization.
The complete candidate preserves the original native calculation. Keep the
original cold implementation available through its sealed source freeze for
comparison; do not change a completed study or replace its implementation.

## Shared implementation

The remainder integrator now has preparation, packet advancement and finalization
functions shared by cold and batched execution, preserving expression order.
Keep physical calibration and error arithmetic
in the existing shared libraries; do not create another independent scientific
implementation for each study.

Preparation owns immutable packet arrays, their source identity, calibration
reference, conditioning proof, expansion point, physical box, geographic model,
initial state, acceleration intervals, corrected packet inputs and matrix bounds.
It verifies those identities once. A changed proof, calibration box, source,
environment or arithmetic backend creates a different preparation.

The packet cursor owns every changing value:

- geographic position and velocity, plus the separated position departures;
- left and right relative attitudes;
- accumulated acceleration remainder and raw-force integrals;
- common-clock prefix, its exact duration, represented tags and defect;
- nominal elapsed time, selected slope, packet indices and source-step counts;
- physical, reference, domain-derivative and direct point-source states.

All bounded vectors, rotations and coordinate objects must remain immutable or
be copied explicitly. Copy the clock's complete arithmetic state, not just its
elapsed time. Source buffers use the typed C++ copy interfaces. The physical
source stream and direct-remainder stream must also preserve their Python body
rotation and accumulated remainder terms, while updating the query identity.

## Query execution

Declare query times and the common clock support before computation. Advance
one canonical cursor only while a packet is wholly before the earliest possible
query, under both represented and exact duration arithmetic. Keep a strict
margin: an exact endpoint remains a knot case.

For each query, copy that cursor, set the new query through checked interfaces,
and process its uncertain tail. The parent cannot inherit a clipped tail from
any query. A copy retains its packet position and remaining packet allowance.
It does not restart a resource counter or extend a time allowance.

Initially compute the final common-clock force-profile certificate by the
existing cold routine for each query. This preserves its whole-history maxima,
drift and hash semantics. Optimizing that separate certificate can follow only
after cold/batched native equivalence passes. Finalization must retain all 24
shared source-expression coordinates and every unshared remainder term.

## Qualification and accounting

First compare small deterministic cases with the sealed original cold routine
for all three candidates and both processing treatments. Include nonuniform
periods, nonzero/asymmetric clocks, exact knots, nearby binary64 values and changed
proof/source rejection. Compare centers, all 27 derivatives where supplied,
coefficient maps, complete remainder vectors and warning/binding metadata.
Check that one copy cannot change its parent or another copy.

Only then freeze a finite long-history comparison. Record actual prefix and tail
work separately from the logical history represented by each output. Count
source operations and restored states before execution. A prefix reused by ten
queries is not ten newly calculated prefixes, and reused outputs do not create
new statistical observations. Measure memory and wall time against the cold
reference; do not assume a speedup from source copying alone.

Keep the four-thread total limit and all old budgets closed. Passing this work
qualifies efficiency, not useful prediction widths. The complete-cadence
training/noise connection, whole-period prediction coverage and observation-law
adequacy remain separate gates. No aircraft fit or protected ESA confirmation
work follows automatically.

[Source-copy design](DESIGN.md) ·
[Original prefix requirements](../ilvis0-long-remainder-feasibility/PREFIX_REUSE_PLAN.md) ·
[Prediction qualification](../ilvis0-joint-projection-controls/NEXT_PLAN.md)
