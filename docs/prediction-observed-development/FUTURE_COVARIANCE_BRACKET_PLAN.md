# Qualify a range of future covariance changes

Keep the fitted earlier mean and the earlier error scale. Let the later
covariance acquire independent receiver scatter and a drifting position
offset, with both fixed at zero before the forecast cut. Declare the
largest allowed covariance increase before any later scoring. Compare
whole-path errors across the entire range. The calculation must recover
the original score when the increase is zero.

Test four held-out conditions using independent random streams. Use 256
fixed Gaussian histories per condition, a three-coordinate path, nine
earlier reports, six later reports and two affine calibration coefficients.
Use no increase, an increase inside the range, the upper endpoint and
a larger increase outside the range. Check the true score independently
using a dense covariance, including the fitted calibration term. For all
in-range histories, require the true score to lie inside the calculated
range and at least 92% of the score ranges to overlap the nominal 95%
reference. Report also how often the whole range lies inside that reference.
The out-of-range case is a stress test and does not change the limits.
Finally, add the same declared alternating-meter-scale forecast error to
a copy of the interior case to check that the bounds can still reject an
inadequate path.

Use one numerical thread, at most 1,024 small earlier fits and 1,280 later
scores. No aircraft data, new physical-model fit or native calls. This is
a fixed affine Gaussian test. Aircraft use still requires independently
supported covariance bounds, calibration uncertainty and a check of how
the observation law changes.
