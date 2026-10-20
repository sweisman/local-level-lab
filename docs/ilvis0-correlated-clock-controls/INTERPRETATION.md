# The shared-clock calculation passes

All **24 generated controls pass**, with **2,774 exact oracle points** across
dyadic, rounded-tag and variable-period clocks. First, middle and final prefixes
are checked at their interval endpoints, relevant packet knots and fixed
interior points. Selected one-sided slopes and any supplied upstream time-map
remainder are retained.

The component combines packets using their common time offset. It avoids
adding large independent kink allowances when the combined elapsed-time map is
linear. A streaming accumulator keeps exact rational center, endpoint and
remainder values without retaining the whole history.

This addresses the diagnosed overcount in the orientation-cover construction.
It does **not** establish the physical instrument clock, certify every
floating-point operation or make the existing native position ranges smaller
automatically. No native integration, aircraft fitting or archive reading was
performed, and the completed studies remain unchanged.

Next, a separately qualified native construction must use the correlated clock
in coordinate updates and preserve the shared duration in force/gravity terms.
It must reproduce the original physical model and all nuisance directions.
Only then can another finite generated comparison assess whether the ranges
are useful on realistic durations. Observational uncertainty and withheld
adequacy remain additional gates.

[Controls and frozen allowance](README.md) ·
[Regrouped propagation plan](../ilvis0-regrouped-history/PLAN.md) ·
[Earlier orientation-cover limitation](../ilvis0-orientation-cover/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
