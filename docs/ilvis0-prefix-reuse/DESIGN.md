# Reusing unchanged packet prefixes

Complete-cadence prediction bounds currently repeat much of the same packet
history. Reusing a verified prefix can reduce that cost without narrowing a
physical bound or changing a model. The accepted design is in the
[prefix plan](../ilvis0-long-remainder-feasibility/PREFIX_REUSE_PLAN.md).

The first component gives the reference, domain-derivative and point-derivative
source kernels typed copy-and-retarget entry points. New translation units include
the existing kernels; no measurement or derivative formula is copied. Each state
records whether every processed packet was a constant, complete packet. A fork
must reject any history that touched a clipped fraction, even if a later query
would put that history before its endpoint.

The copied state includes the body rotation, all 27 parameter columns, force,
mount transformation, elapsed time and derivative intervals. Copying it must not
change its parent or another copy. Its layout, binary/compiler identity, input
hashes, physical domain, reference binding and packet allowance remain attached.
Retargeting changes only the query expression, through C++ fields of the declared
type. Python must never guess byte offsets into a buffer.

Both represented packet tags and exact binary-duration arithmetic constrain the
fork. The last packet must end strictly before the earliest supported new query.
Equality remains a knot case and is not eligible. The original packet allowance
is preserved; reused work is not counted as newly calculated work or a fresh start.

Small tests compare independent cold source streams with copied streams for
nonuniform periods, nonzero clock shifts, exact endpoints and adjacent values.
They check all output values and derivative columns, failure behavior and parent
isolation. A separately frozen finite source comparison follows only after those
tests pass. No aircraft files, fits or protected confirmation outcomes are needed.

This source-only component does **not** qualify complete native-prefix reuse. The geographic
position/velocity, relative attitudes, accumulated force integrals, common-clock
state and conditioning proof still need a complete-state implementation and
independent cold-run checks before it can replace an existing native bound.
V01 remains unqualified and the 53-stretch findings remain unchanged.

The [complete-state short controls](../ilvis0-native-prefix-controls/README.md)
have now passed separately. Their long-history follow-up remains necessary.
