# Find the best shape contrast with the original forecast conditioning

The [broader contrast](ESA_CALIBRATION_MAXIMUM_MARGIN_RESULT.md) allows
12.18 cm of uniform position error. Its earlier position weights are
unrestricted. Test how much of that allowance remains when earlier
positions affect the score only through the fixed covariance forecast.

Keep the saved two affine forecasts, all 102 calibration columns, both
full boxes and the original three-centimetre receiver covariance.
Propagate the earlier position differences through the archived
innovations filter up to the 400-report cut. Predict the later changes
with zero later innovations. This linear map is the only connection
from the earlier positions to the new contrast. Apply it consistently
to the affine calibration changes and to the possible earlier
integration errors. The original nominal difference already describes
the two conditional later paths, so its earlier coordinates stay zero.

Use a linear program to seek two calibrated paths with the smallest
maximum coordinate error that makes their conditional contrast vanish.
Maintain nine unrestricted smooth terms on the later coordinates.
Use one fixed single-thread proposal, with at most 2,000 iterations and
30 seconds. A feasible calibration pair and earlier error vector
always define a unique required later error vector. Bound that vector
by directed arithmetic through the original state update and forecast,
and record the resulting upper bound on the best error allowance.

Propose a direction from the program's later equality constraints.
Cancel constants, linear terms and quadratic terms exactly on each
later axis. Derive the earlier weights by the adjoint of the same
forecast from the earlier positions. Enclose the complete weight
intervals with directed arithmetic, then bound the signed difference
over both full parameter boxes and divide the positive lower bound by
twice the enclosing sum of absolute weights. Recheck the earlier
calibration-resistant direction under these same conditions. Preserve
all outcomes, including a missing or weak proposal.

Freeze both archived results, all original inputs, the finite software
tests and one task with six bound calls and 2,006 charged steps.
Use a 180-second cooperative allowance, one thread and zero new
aircraft fits or observations. Allow one separately charged recovery
attempt with a 180-second limit. The comparison bounds the best
linear error allowance for the saved affine model. It leaves the full
integration error and aircraft uncertainty unresolved.
