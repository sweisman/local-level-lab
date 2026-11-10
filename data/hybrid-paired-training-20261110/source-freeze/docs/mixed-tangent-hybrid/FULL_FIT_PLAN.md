# Next gate: matched training and forecast

The selective-precision kernel has passed the six generated twenty-minute
derivative checks. Its next gate is whether a complete fit and prediction made
with that kernel agrees with the unchanged wide-precision reference.

Use only deterministic generated IMU increments and receiver positions. Hold
the physical model, input arrays, initial state, calibration bounds, optimizer,
start, stopping rule, training split and forecast times fixed within each pair.
The only paired change is the tangent arithmetic. Construct and hash the input
arrays before either fit. Save each fit and forecast separately, including
training cost, convergence, evaluations, active nuisance columns, prediction
coordinates, timing, compiler and kernel hashes.

Qualify the paired adapter with cheap known-answer and failure tests before
freezing a study. The first finite matrix is three physical candidates × two
processing settings, each a generated 120-second case with one start. Both
fits within a case use identical generated inputs and withheld truth. Each
reference and selective fit has at most 200 tangent evaluations. Across six
cases, the allowance is at most 2,412 native calls and 4,517,436,000
packet/query work units. Each case also allows exactly 72,000 constructed
intervals and 72,398 generated samples across both sides. Allow at most two
hours of wall time, four workers with one numerical thread each, no retries
and no observed-data reads. Charge construction and native calls separately.

Before the run, freeze the exact source and environment, all six identities,
the generated-input recipe, evaluation and wall limits, and comparison rules.
Pass only if both sides independently converge, retain every active nuisance
column, meet the existing physical prediction limits, and differ by no more
than 0.01 m in three-dimensional position at any forecast epoch. Compare the
complete saved prediction series and training costs; report their differences
even if a gate fails. A failed pair stays failed. These paired fits each use
their own matching generated truth, so this first matrix does not test
ordering among the three physical candidates.

This is software qualification. It does not calibrate a scientific decision,
change the production fitter or consume protected observations. A passing
short-fit matrix supports, but does not replace, a later long-fit comparison.
