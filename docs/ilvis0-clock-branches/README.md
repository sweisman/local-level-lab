# Accounting for packet boundaries

Eleven exact-arithmetic checks now cover an affine clock offset across every
relevant packet boundary. They preserve the native sequential timestamp sums,
the earlier packet's ownership of an exact boundary, reversed clock paths and
isolated endpoint cases. An eight-minute input has a complete 401-segment cover
for its ±1-second clock range at 438 seconds. Unsupported or incomplete ranges fail.

One detail matters: a rounded cumulative packet endpoint can differ slightly
from its start plus its ideal integration period. The resulting partial-packet
fraction can be just above one. The new calculation records that difference;
it does not clip it away or declare the older strict adapter to cover it.

A second component allows explicit jumps in the predicted residual itself,
including at the path endpoints. Seven checks verify the signed jump terms;
the combined clock, jump and earlier quadrature checks total 32 distinct passes.

This is bookkeeping and mathematical support. Native floating-point branch
selection, actual trajectory jump bounds and complete-record prediction ranges
remain to be qualified. No aircraft data or findings changed.

[Mathematics](MATHEMATICS.md) · [Next implementation](NEXT_PLAN.md) ·
[Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md)
