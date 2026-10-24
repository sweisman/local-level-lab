# Long-record arithmetic and runtime comparison

The small prototype passes all nine source-bound checks. This separate gate
tests six twenty-minute generated cases: all three physical candidates under
both processing assumptions. It compares the existing wider arithmetic with
the isolated mixed-precision derivative prototype at one fixed nonzero
parameter vector. No optimizer or observed measurement is used.

Both methods receive identical 300 Hz increments, 1,200 query epochs, complete
26/27-column parameter domains and the same initial state. The trajectory
contains turns and a climb. All positions are generated software inputs; this
is not a training/withheld-prediction test.

Require bitwise-identical coordinates and pre-cast residual differences,
including signed zeros, and identical timing-boundary counts. After dividing
each derivative row by the fixed 0.05 m software coordinate weight, compare
every column with relative and absolute tolerances both 2×10⁻¹⁰. Preserve any
failure without relaxing these limits.

Measure process CPU and wall time for one native call per method in each case.
Alternate the first method by processing case. Exclude construction, compilation
and serialization from these kernel timings. A sampled speed ratio is not a
guarantee about full fitting runtime. Preserve both complete value/derivative
arrays, compiler/source bindings and binary hashes for saved-only verification.

The separate allowance is six identities, twelve tangent calls and
5,184,000,000 conservative packet/query work units. Each case constructs at most
360,000 intervals and generates 362,001 samples. Use one numerical thread and a
cooperative two-hour ceiling, with no retries. Reserve capacity for the three
other active workers. Charge work before execution.

Before launch, qualify the finite definition, strict value/column checks,
closed-result guard and a real two-second pipeline bridge. Bind the complete
source and environment set before its test report is produced. The earlier
nine-check prototype evidence remains unchanged.

Use the shared study lifecycle and existing trajectory/problem/native helpers.
Published verification reads saved matrices, metadata and journals; it does not
repeat native calculations. Hash-identical binary artifacts can share archive
storage. Source libraries are not copied to create another worker.

Passing this comparison still requires a separate full training/forecast
qualification before any observed fitting change. The active noisy-data study,
all existing outcomes and protected confirmation groups remain unchanged.

[Small prototype](../mixed-tangent-prototype/README.md) ·
[Reproducibility](../REPRODUCIBILITY.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
