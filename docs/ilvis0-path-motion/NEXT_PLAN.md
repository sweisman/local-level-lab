# From a qualified short adapter to full-history bounds

The [native adapter comparison](../ilvis0-path-native-controls/README.md) is complete:
six cases pass across all 27 parameters, using six native queries and 162
interval steps. It took 299.62 seconds. Its inputs, sources, limits and failures
are sealed; do not rerun it. Higher derivatives retain separate known-answer
controls because the native oracle supplies only first derivatives.

The [compiled midpoint step](../ilvis0-path-step/README.md) and
[packet loop](../ilvis0-compiled-path-packets/README.md) now each pass ten local
checks against known answers and the rational reference. A separate frozen
[64-packet native comparison](../ilvis0-compiled-path-controls/PLAN.md) covers all
six cases and all 27 parameter columns. Measure runtime and memory rather than
assuming that these short controls make recording-length ranges practical.

The [rotation-switch component](../ilvis0-rotation-branch-bounds/README.md)
bounds both local formulas and their switch differences. It is separate from
the completed adapter. Propagate incoming changes and the effects of switches
through subsequent steps; do not infer a smooth trajectory from local bounds.
Clock branches need complete support and one-sided changes too. Keep native
cumulative timestamps, ideal integration periods and execution error distinct.

Then bound the residual after the exact shared-source expression, preserving
cancellation. Independently bounding two large trajectory/source expressions
may erase the useful information. Test useful width over the original full
parameter and clock domain before any wider qualification study.

Whole-period prediction coverage, native execution error and a defensible
aircraft error law remain separate gates. No new observed fits, changes to
completed studies or expansion of active allowances follow from these controls.
