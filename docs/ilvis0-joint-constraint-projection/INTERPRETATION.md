# Initial worker-entry failure

The study ended before any audit identity or LP proposal started. Its adapter
could not load through the standalone worker entry. It therefore provides no
calibration-range result. Preserve the original freeze, zero charge totals and
worker logs.

The corrected import is covered by a standalone-loader regression test and a
[separate version 2 freeze](../ilvis0-joint-constraint-projection-v2/PLAN.md).
No mathematical assumptions or acceptance limits were changed.
