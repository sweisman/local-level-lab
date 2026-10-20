# Preserve joint calibration constraints

The completed contraction keeps every true generated parameter, but enclosing
all feasible possibilities in one coordinate box loses important correlations.
The shared training-error calculation is now complete as a separate component;
it does not fix that geometric limitation.

## Why a linear improvement alone is insufficient

In the first generated specified-field/no-removal case, the saved post-contraction
nonlinear remainder allowances are about 210.64 m north, 156.78 m east and
144.16 m in height. Adding these symmetric allowances independently already
contributes widths of roughly **421 / 314 / 288 m**, before any remaining affine
uncertainty. An exact solution of the affine constraints alone cannot remove
that contribution from the current construction.

This is a limitation of the computed enclosure, not a lower bound on actual
aircraft uncertainty. The next method must preserve joint constraints **and**
reduce nonlinear overestimation. Narrowing a box around a fitted answer without
proving that other possibilities are excluded is not acceptable.

## First: certify affine support without trusting optimizer status

Implement a separate support calculation for the full parameter box intersected
with necessary training inequalities. Keep all 27 columns. A numerical linear
program may propose nonnegative inequality multipliers, but it does not certify
the result. For any such multipliers `lambda`, the bound

`c*x <= lambda*b + max_box((c - A.T*lambda)*x)`

is valid whenever `A*x <= b`. Evaluate this certificate with exact rational
arithmetic from the supplied binary inputs, then check outward endpoints.
Use the opposite signed objective for a lower bound. A poor proposed multiplier
can only loosen the bound; never label a region empty from an unverified solver
status. Missing certificates fall back to the full box or explicitly abstain.

Qualify against independent small exact polytope optima, deliberately wrong or
incomplete solver proposals, weak/contradictory constraints, zero columns and
27-coordinate correlated examples. Known feasible points must remain enclosed.
Record finite software identities and arithmetic/runtime limits before launch.
This mathematical component authorizes no aircraft fits.

## Then: test a complete orientation cover on generated inputs

Prepare a separate finite feasibility study that partitions the original yaw
interval into closed sectors covering **the whole original interval**. Recenter
native expansions in each sector, retain every other calibration bound, and
carry sector-specific training inequalities through to future support bounds.
The union must include all sectors not rigorously excluded by necessary
constraints. Never choose sectors using future truth or model preference.

Reuse the completed generated experiment's input definitions and all three
physical candidates under both processing cases; create a new source/input
freeze and work allowance. Preserve the old result. Compare truth containment,
union widths, remainder widths and cost with the saved broad-box baseline.
Time the new component before freezing the number of sectors and native calls.
Stop at the finite allowance; a correct but still broad result fails usefulness.

No observed prediction fit follows until useful global propagation, numerical
error treatment, training-only fit provenance and observational assumptions are
qualified. Protected ESA outcomes remain untouched.

[Completed contraction](INTERPRETATION.md) ·
[Shared error-source assessment](../ilvis0-receiver-scale-assessment/INTERPRETATION.md) ·
[Canonical roadmap](../ANALYSIS_ROADMAP.md).
