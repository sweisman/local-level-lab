# Preserve the tighter vertical bound during force rotation

The [six-source reference comparison](../ilvis0-source-reference/INTERPRETATION.md)
qualifies a tighter error allowance for the body-rotation term. A new local
operator carries that term into the navigation-frame force expression without
spreading horizontal uncertainty into the vertical axis.

The operator evaluates `(Q−I)(A+B)+B`, keeping separate bounds on each coordinate
and all 27 affine-reference columns. Its output row includes the first-order
contributions from both force sources and the navigation-frame rotation.
Rounding of that coefficient row is bounded with exact rational arithmetic
over the supplied parameter domain and added to the output error allowance.

Five deterministic tests pass. Independent polynomial sources check nonlinear
error containment and all-column retention; a yaw-only rotation checks that
horizontal uncertainty does not become a vertical allowance. Separate checks
cover coefficient rounding and rejection of incomplete or invalid inputs.

This is an operator test, not a complete aircraft calculation. Callers must
provide qualified source bounds around the exact reference rows they supply.
The [transport implementation](../ilvis0-cached-transport-controls/INTERPRETATION.md)
now passes all 24 native controls while retaining coordinate and useful norm
bounds through velocity and coordinate extraction. The next task is to connect
the tighter body-source interval at the actual packet prefixes. A separately
qualified complete prediction comparison still precedes new aircraft fitting.

Implementation: `analysis/lll/ilvis0_source_action.py`.
Checks: `analysis/tests/test_ilvis0_source_action.py`.

[Integration plan](../ilvis0-source-reference/NEXT_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
