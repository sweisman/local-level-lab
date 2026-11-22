# Measure how far the observed shape scores are from a tie

Reuse the eight saved receiver scores and the exact archived matched-field
shape direction, times and working covariance. Hold both zero-field model
forecasts, calibrations and weights fixed. Use one outward adjoint pass to
bound the coefficients that map changes in the receiver path to score
changes. Use the local chart already used for the score.

Evaluate three error families. First, allow every coordinate at every report
to move within the same bound. Second, allow the same coordinate bound only
at the 120 later reports. Third, keep every earlier report fixed and start
the later position correction with zero position and velocity. Give that
correction a constant acceleration on each of four equal-duration blocks
covering the later interval. Use the same bound for every acceleration
component. This family permits continuous position and velocity and a change
in acceleration at each block boundary.

For each path and family, report a lower bound on the size of a change
needed to reach a tie. For the original export and the GPS L1 path,
also verify a constructed score reversal no more than 0.1% above
that bound. These are sensitivity thresholds for the fixed calculation.
They provide no evidence about how large the actual receiver errors are.
No data fitting, forecast propagation or reserved flight reads are allowed.
