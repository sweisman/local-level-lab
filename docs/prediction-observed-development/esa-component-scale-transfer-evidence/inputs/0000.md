# Can separate forecast-error scales transfer to unused windows?

Use the four existing matched turn and steady-window pairs from ESA
development flight 187. Preserve the 120 later reports, saved forecast
means, native factors and angular-exposure inputs exactly. Score both
declared IMU error descriptions as sensitivities on the same data.

For each held-out pair, fit the covariance on the other three pairs.
Compare the original covariance, one fitted multiplier on the original
covariance, and separate multipliers on the native, steady-acceleration
and maneuver components. Use the existing Gaussian scale fitter with log
variance bounds [−5, 5] and at most 100 likelihood evaluations per fold.
Project out no mean terms. Fit the common multiplier analytically within
the same bounds. The per-window likelihoods form a composite score because
all eight windows share a flight.

Report held-out joint negative log score and squared standardized error
for each window. Also count windows inside the same descriptive Gaussian
reference as the [common scale check](ESA_COMMON_SCALE_CHECK.md), with
360 dimensions and tail probabilities 0.05/16 and 1−0.05/16. This is a
reference for detecting gross mismatches. Fitted scales, correlated
windows and retrospective reuse rule out a calibrated coverage claim.
Keep optimizer failures and bound hits in the result. Select no new
forecast, noise term or interval after reviewing these outcomes.

Use `lll.esa_component_scale_transfer` and its focused tests. Bind the
existing release seals, selected pairs and original score hashes before
preparing inputs. Require all eight original covariance scores per law
to reproduce. Freeze eight tasks, one thread and a 120-second cooperative
limit. Each task can charge one primary likelihood estimation and up to
100 evaluations. The study starts zero inertial or navigation fits and
reads none of the seven reserved ESA groups.
