# The native common-transform candidate passes

All **24 matched native controls pass**, using the same generated inputs and
acceptance limits as the earlier native qualification. The study charged
78 native evaluations and 348 bounds and completed in 38.2 seconds.

The candidate factors the fixed calibration transform out of changing force
samples before propagating the remaining error. It preserves the full original
dynamics, all 27 physical derivative directions and 24 auxiliary coordinates.
Internal feedback retains complete uncertainty; the shared contribution is
separated only in the final additive output.

Centre, independent-pose, derivative and probe-containment checks all pass.
This qualifies the candidate against the unchanged native kernel on the frozen
control set. It is not a whole-program floating-point certificate, a calibrated
aircraft error model or a new empirical model comparison.

The next gate is the typed 51-column training/prediction interface, with source,
clock and reference checks. A separately frozen complete orientation comparison
must then establish whether the new accounting improves prediction widths.
The 53-stretch empirical findings are unchanged.

[Qualification evidence](README.md) · [Frozen scope](PLAN.md) ·
[Derivation](../ilvis0-common-force-transform/NATIVE_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
