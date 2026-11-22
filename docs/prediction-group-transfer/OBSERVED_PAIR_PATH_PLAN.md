# Complete-vector connection between two saved aircraft fits

The [calibration-swap study](OBSERVED_CALIBRATION_SWAP_RESULT.md) found that
individual parameter-group swaps fit the training receiver positions poorly,
while each complete saved solution fits almost equally well. This study asks
whether the two complete solutions are connected by a low-cost path through
their **joint** 26-parameter calibration space.

Use the same two preselected maximum-disagreement inner-cut pairs, sealed IMU
increments, training receiver positions, model, bounds and clock. For each
pair calculate the full normalized parameter vector at 25%, 50% and 75%
along the straight line from solution A to B. The two endpoints are already
sealed in the calibration-swap study and are not rerun. There are six new
fixed vectors, no optimization and no later receiver observations in the
evaluator. At each vector, calculate the training cost and a continuous later
forecast, then compare its path only with the two saved endpoint forecasts.

Freeze source, input and numerical environment hashes and the exact six
identities before launch. Cap each task at one training tangent and one
forecast call. The total cap is **12 native calls and 220,247,055 packet
visits**, with four one-thread workers and a cooperative one-hour wall
limit. Charge each call before execution, preserve all outcomes and qualify
task-level reboot recovery. A restarted host may resume only unfinished
identities under a separate finite continuation.

A low-cost connection would support a weakly identified calibration valley;
a high-cost middle would support separated local basins. Neither proves that
either endpoint is a global optimum or physically adequate. Forecast behavior
along the line is a sensitivity diagnostic, not a confidence interval or an
Earth-model decision. Preserve every prior failed stopping label.
