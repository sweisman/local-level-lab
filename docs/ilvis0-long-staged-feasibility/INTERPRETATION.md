# Packet-boundary check stopped the first run

All six starts ended after their first native query, before any source bounds
or predictions were calculated. The run charged six queries in 19 seconds.
It says nothing about whether the intended prediction ranges are useful.

The queries themselves succeeded. The wrapper incorrectly treated a nonzero
packet-boundary counter as a motion warning. In the native kernel, that counter
records a query at the start or end of an IMU integration packet. It is separate
from the failure status. An independent timestamp calculation reproduces all
six saved counters; a native-kernel regression checks boundary and interior
queries separately.

The original failed results and frozen acceptance rule remain unchanged. The
[separate corrected study](../ilvis0-long-staged-feasibility-v2/PLAN.md) checks
the counter against timestamps, retaining the same input records, calibration
bounds, query times, width targets and finite per-case budgets. This correction
does not establish smooth derivatives at packet boundaries or full numerical
coverage; those remain explicit qualification requirements.

[Preserved results](README.md) · [Roadmap](../ANALYSIS_ROADMAP.md)
