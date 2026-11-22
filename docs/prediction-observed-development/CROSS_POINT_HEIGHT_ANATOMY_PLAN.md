# Saved ESA height-error anatomy

Use only the two sealed, same-law conditional forecasts and the 400 later
receiver reports from development recording 187. Verify the existing
cross-point coverage report and its source/summary hashes before reading
saved artifacts. Make no new fit, prediction or aircraft-original read.

For each saved parameter setting, compute the first later epoch whose absolute
height error exceeds `1.96` times its declared standard deviation, the longest
continuous exceedance, the final signed error, and the empirical 95th
percentile of absolute standardized error. Compare the two signed height-error
series and their differences. The empirical percentile is a descriptive
diagnostic on one correlated trajectory, not a coverage calibration or an
independent 400-case sample.

Preserve the existing failed coverage result. Report whether the error is
shared across parameter settings, and use that finding to choose the next
generated error-law control. Seven reserved ESA groups remain closed.
