# Longer inputs and clock shifts reach the calculation correctly

**All six interface cases pass in 109 seconds.** The generated inputs now span
eight minutes, long enough to cover the earlier 438-second prediction plan.
Their original four-minute measurement prefix is preserved exactly.

The new software-test clock bound is ±1 second. The old and current callers
agree exactly on positions, all 27 calibration-derivative columns and warning
flags at the declared long-duration queries. The checked calls return no
warnings, and the clock derivative remains present. All other calibration
limits and initial settings are preserved.

Both callers use the same numerical kernel. This verifies input handling and
clock support, not the physical model independently. It also does not supply
useful nonlinear prediction ranges or a validated measurement-error law. The
±1-second clock bound is a declared qualification assumption, not a measured
instrument specification.

The next task is to constrain long predictions using their own earlier
observations, retaining every constraint through later refinements. No aircraft
fit or protected ESA observation enters these controls.

[Verified results](README.md) · [Frozen scope](PLAN.md) ·
[Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md).
