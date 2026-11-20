# Check the uncertainty attached to the adjusted rolling predictions

Use the seven available forecasts and the unavailable 800-report point-law
case from the [matched adjustment audit](ESA_MATCHED_CONDITIONING_RESULT.md).
Keep the same instrument laws, earlier fits, receiver source and first
120 later positions. Review the covariance attached to each sealed
adjusted path. Use the existing marginal 95% and three-axis 95% ellipsoid
descriptions. Report the fractions of later positions inside those ranges,
axis-wise standardized RMS, peak squared Mahalanobis distance and whether
any later position fell outside the nominal ranges. Keep each law and
window separate, including the unavailable case.

At cuts 600 and 800 also show the equivalent diagnostics over their
original 200- and 400-position horizons. These full declared horizons
show whether a shorter common prefix hides later forecast departures.
Keep the whole-horizon results separate from the common-horizon table.
The ranges treat fitted calibration as fixed. All windows share one
development recording, so counts describe the archived uncertainty and
do not estimate independent-flight coverage or calibrate a decision.

Use at most ten charged checks on one thread, with a 90-second cooperative
limit. Reuse the preserved forecast seals and the same archived receiver
source. Use no new integration, fits, original-file reads, or reserved
flight data. Any reported undercoverage stays visible.
