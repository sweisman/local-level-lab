# Qualify the reference coefficients before native use

The source preflight demonstrates a tighter value range while preserving the
actual training bounds. The next task is to qualify the reference linear map
for the same `A=R f` and `B=R(P−I)f` source, retaining all 27 physical columns.

Compute the full reference coefficients independently and compare them with
the coefficients used by the native body-rotation calculation. Preserve the
clock's exact branch convention and record distance to packet boundaries.
Unused coordinates remain explicit zero columns. A boundary-specific reference
map must not be described as a unique two-sided derivative at a kink.

For any verified reference row `J` and value interval `[l,u]`, a conservative
affine-error radius about reference value `c` is

`max(|l−c|, |u−c|) + sum_j |J_j| max(|lower_j−center_j|, |upper_j−center_j|)`.

This bound works even when the linear map is not an exact derivative. However,
the row must be the one consumed by the propagation method, or an additional
coefficient-discrepancy allowance must be retained. Compare the resulting radius
with the original remainder before any expensive integration test. A narrower
value interval need not produce a narrower affine-error radius.

If that comparison improves the actual baseline, develop the dynamic candidate
with componentwise operations and preserved training-conditioned information.
Keep native centers, all shared errors, original physical bounds and acceptance
limits. Qualify independent motions and the original native control matrix
before a separately frozen complete comparison. No observed fitting follows
from this preflight alone.
