# Prospective wider arithmetic comparison

The fixed-point replay brought 31 of 33 cost changes below the unchanged
numerical limit. Two still exceeded it. Run complete fits on four fresh
generated flight histories to see whether that improvement survives a full
optimization.

Use one truth trajectory for each geometry and field combination, with
different latitudes, route assignments and sensor offsets from the first
matched study. Use the same 24-second duration, 200 Hz packets, 14 training
receiver positions and nine withheld positions. Compare four candidate
models under both removal cases and both extreme offset caps, ±1 and
±20°/hour. The earlier study preserves the intermediate ±3 and ±10 results.

Use binary64 and wider arithmetic on identical inputs, with one zero start
per fit and the same optimizer, weights and stopping limits. Charge at most
80 fitting evaluations plus one forecast per identity. The 128 fit
identities use four single-thread workers with a three-hour cooperative wall
limit and qualified task recovery. This study uses generated data only.

Require every task to pass its technical checks. The wider arm must
pass the original stopping and 0.25 m withheld RMS screen on all 16
truth-matched fits, finish all four candidates in at least 12 of the 16
matched settings, and preserve every complete setting from the binary64
arm. Compare prediction agreement between arms separately. Preserve
unfinished results and keep independent aircraft and gyro-free qualification
as separate gates.
