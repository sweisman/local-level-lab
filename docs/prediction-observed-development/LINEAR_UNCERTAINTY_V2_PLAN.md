# Corrected ESA local-uncertainty development check

The [first task](LINEAR_UNCERTAINTY_V1_RESULT.md) stopped because its saved
forecast has no full Jacobian. Preserve that terminal result and use a new
study identity. Keep the same development recording 187, 800/400 split,
fitted point, model, clock, IMU/receiver error law, calibration bounds,
source assumptions and seven reserved ESA groups.

Build the full error operator **once** and replay the sealed early cost and
log-determinant. In the same bounded task, make one observation-free native
forecast at the saved fitted point, retaining all 26 Jacobian columns. Before
using that derivative, require:

1. The generated positions agree with the sealed forecast within 0.1 mm in
   the common receiver-coordinate metric.
2. The generated training Jacobian, whitened by the verified early operator,
   agrees with the sealed fit's whitened local Jacobian at relative tolerance
   `1e-6` and absolute tolerance `1e-8`.
3. The generated forecast uses the exact saved IMU prefix, initial state,
   fitted point and earlier receiver support. No later receiver position is
   available to the worker.

Then apply the existing full-column local Gaussian prediction calculation.
Report rank, estimability, bound feasibility and later covariance if valid.
A saved-only reporter may score the already opened 400 later receiver reports
after the task closes. This remains a local linear development diagnostic,
not calibrated coverage or an Earth-model decision.

One start, one numerical thread, one hour maximum, 450,000 native calls and
one billion packet visits. Qualify the replay and recovery checks before
launch. Preserve any failure and its full charge.
