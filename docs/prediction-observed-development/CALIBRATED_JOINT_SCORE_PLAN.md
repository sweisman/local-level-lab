# Check the whole-path score when calibration is estimated earlier

The ESA abstention exposes an uncertainty-scale mismatch. A revised method
must keep uncertainty from calibration fitted on the earlier observations.
Start with an exact software control for a fixed affine trajectory model
and a Gaussian error law whose overall variance may be unknown. This is a
separate control with no nonlinear aircraft fit.

Reuse the existing earlier-only generalized least-squares estimator. It
returns the predicted mean, the calibration uncertainty shared across later
epochs and the training rank. Score the whole later path by combining the
correlated error operator with the low-rank calibration term. Verify the
joint quadratic and determinant against a separate dense conditioning and
prediction calculation. A direction invisible during training that can
change the later path must still cause abstention.

For a known covariance scale, compare the joint error with the fixed-Gaussian
reference. For an unknown common scale, estimate it from the earlier residual
sum of squares using the earlier residual degrees of freedom. Under the
exact affine model the estimated calibration and the earlier residual scale
are independent. The ratio of later and earlier mean squared standardized
errors therefore has an F reference over repeated complete histories. Check
both calculations locally.

Use a fixed 12/8-report affine history with two nuisance coefficients.
Generate position error by summing independent random-walk increments and
adding independent receiver scatter. Use 1,024 histories each for the nominal
scale, a ninefold common variance and a ninefold receiver-variance increase
only after the cut. Fix the three random seeds to 20261118031–20261118033.
Both proportional cases must give 92.5–97.5% empirical inclusion for the
earlier-scale F reference. The later-only increase must give at most 85%
inclusion, demonstrating a limitation rather than hiding it. Save the fixed
scale reference results as well. Allow one declared covariance operator and
3,072 affine fits and scores, one thread, and no aircraft or reserved reads.

This qualifies only the software calculation for a declared affine law.
Bounds, nonlinear aircraft calibration, an incorrect covariance shape and
multiple fitted-model selection all require additional controls. Do not apply
the F reference to the ESA or NASA scores from the previous studies, and keep
the protected groups closed.
