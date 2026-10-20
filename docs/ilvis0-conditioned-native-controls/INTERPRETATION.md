# The tighter acceleration bound survives native checks

All six longer generated controls passed. Native predictions, all 27 derivative
columns and all shared coefficient arrays remain unchanged. The known physical
probe stays inside each factored remainder bound, and the original acceleration
Taylor remainder is retained exactly.

The remaining unshared position bounds shrink by roughly 3–19%, depending on
axis and candidate. The 92–93% reduction in the acceleration-change radius does
not translate directly into a similar reduction in complete position uncertainty:
other terms remain. Complete prediction widths have not yet been recomputed.

The study used its twelve native calls, six enclosure calls and 36 independently
verified exact supports, finishing in 94.1 seconds. There were no LP proposals,
original aircraft reads or observed fits. The conditioned bound applies only
to its hashed training region, not the entire physical bounding box.

Next, test all original eight sectors in each of six model/processing groups
under a separate finite freeze. Keep the unchanged all-axis, all-group prediction
target. These controls do not establish real aircraft error coverage or clear
the gate for observed fitting.

[Results](README.md) · [Next comparison](NEXT_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
