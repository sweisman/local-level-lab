# Whole-fit CPU comparison

The six generated twenty-minute cases passed the paired wide/selective fitting and prediction checks. They cover three physical candidates and both processing settings. Each pair used the same generated IMU and receiver data, bounds, optimizer, start, training split and withheld positions; only tangent arithmetic changed. No observed or protected recording was read.

The new timing markers measure process CPU from compiled-kernel availability through the saved optimizer fit, excluding compilation and later forecast scoring. On that measure, the wide/selective CPU ratio ranged from **1.96 to 2.61**, with a **2.38 median** across six matched cases. Summed fit CPU was **8,285 seconds wide** versus **3,504 seconds selective**. The predeclared operational criterion required a median ratio above 1.25 and no case below 1.0; it passed. Complete-calculation CPU, including compilation and forecasting, is also saved separately.

All six numerical comparisons independently passed convergence and physical prediction checks. The worker charged 136 native calls and 28,913,633,028 packet/query visits in 71.1 minutes, with no errors. The saved-result replay verified the source, inputs, charges, paired forecasts and timing records. This establishes a worthwhile speed improvement for these generated long records. Moving the selective path into an observed-aircraft fitter still requires a separately frozen source-bound release and its own adequacy checks; this study makes no Earth-model decision.

[Frozen plan](PLAN.md) · [Numerical agreement study](../long-fit-study/README.md) · [Roadmap](../../ANALYSIS_ROADMAP.md).
