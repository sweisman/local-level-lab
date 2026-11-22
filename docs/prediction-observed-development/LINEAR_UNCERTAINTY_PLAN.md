# Does fitted calibration uncertainty explain the ESA height miss?

Use only the already opened ESA development recording 187, the same 800 early
receiver reports, the sealed fit, its complete 26-column native forecast
Jacobian, and the same declared IMU/receiver error law. Rebuild the full
error operator once. Verify its early log-determinant and weighted residual
cost against the sealed training result before computing anything further.

Apply the existing fixed-design Gaussian calibration calculation to **all**
active nuisance columns. Report its training rank, prediction estimability,
local parameter correction, and whether that correction stays inside every
original bound. Only an estimable, in-bounds calculation can supply additional
later covariance. Do not change the fit, model, clock, error law, numerical
cutoff, or 800/400 split. Do not use later receiver positions in this task.

After sealing the task, a saved-only reporter may compare its nominal
intervals with the 400 already opened later reports. Treat this as a local
linear diagnostic: it does not include nonlinear parameter uncertainty,
establish the instrument error law, calibrate coverage, or support an
Earth-model decision. The seven reserved ESA flight groups remain unopened.

The new study has one task, one start, one numerical thread, a one-hour
cooperative wall allowance, at most 450,000 native calls and one billion
packet visits. Qualify its early-only input binding, rank/bound gates,
source/environment freeze, and interruption recovery before launch. Preserve
any technical or scientific failure and its charges.
