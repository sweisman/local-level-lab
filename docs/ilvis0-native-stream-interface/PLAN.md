# Native source for the training-only prediction interface

Connect the qualified streaming value/27-column tangent source to the existing
structured prediction interface without changing frozen kernels or uncertainty
calculations. This is a software prerequisite, not another aircraft fit.

The new source accepts explicit initial state, normalized parameter center and
limits, model/processing configuration, training/future query times and a frozen
coordinate frame. Its API has no future-position or fused-navigation argument.
All 27 columns, including inactive/unidentified directions, remain present.

Process every increment in bounded blocks with exact clock/packet order. Select
query support without using future positions. Keep seed and fitted-center
provenance explicit: this adapter cannot prove that an externally supplied seed
or fit was produced using training data alone. Such provenance remains a required
input dependency in a future observed-data freeze.

Bind the native source receipt to kernel/source/environment hashes, input ID,
initial state, parameter limits/center, complete parameter order, query schedule
and coordinate frame. Reject mismatched families and incomplete predictions.
Do not substitute a future-observation-derived metric or drop columns.

Generated controls compare the complete native interface with unchanged kernels
under all three models and both processing cases. Check chunk-layout invariance,
coordinates and rejected dependency mismatches. An unknown global nonlinear
remainder must still produce an unsupported envelope and scientific abstention.
Passing source/interface tests must not change that gate or relabel old fits.

No original archive or protected ESA outcome is read. The separate finite
integration qualification has 24 generated identities (three models, two
processing cases, two query phases and two latency centers). Each uses 600
packets, an unchanged whole-array reference and 83-packet streamed blocks.
It allows 500 native calls, 100,000 packet visits, four total numerical threads
and 120 cooperative wall seconds, with no retries. Calls are charged first.

Acceptance requires native values within 1 micrometre, every derivative within
1e-7 metres per normalized parameter, and the complete structured interface
abstaining when its nonlinear bound is absent. Source/runtime dependencies and
task identities freeze before execution. Passing is interface qualification,
not a supported observational prediction.
