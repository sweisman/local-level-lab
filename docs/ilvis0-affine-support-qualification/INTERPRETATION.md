# Joint linear constraints can be retained safely

All **24 generated identities pass**. Twelve polygon tests compare the bounds
with 57 independently enumerated exact feasible vertices. Eight larger tests
retain all 27 parameters, including 25 unidentified coordinates. Four weak
systems retain their full box ranges.

For example, knowing that two uncertain coordinates are equal may leave each
coordinate's range unchanged, while fixing their difference exactly at zero.
A coordinate box discards that information. The new support calculation keeps
the relationship when bounding a prediction.

The numerical optimizer only proposes multipliers. Exact arithmetic checks the
resulting inequality. Poor proposals cannot exclude feasible points; failed or
invalid proposals fall back to a full-box bound. Solver failure never silently
means an empty calibration region.

This qualifies a mathematical component, not actual aircraft uncertainty.
The previous generated native bounds still include large independent nonlinear
remainders. Keeping linear correlations alone cannot remove them. The next
separate feasibility study will cover the entire original orientation range
with smaller sectors, retaining every sector that has not been validly excluded.

No native evaluations, original IMU reads, observed Earth-model fits or protected
ESA evaluations were used. The completed allowance cannot be restarted.

[Frozen controls and results](README.md) ·
[Next generated feasibility plan](../ilvis0-orientation-cover/PLAN.md) ·
[Joint calibration method](../ilvis0-native-training-contraction/JOINT_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
