# Does more training data constrain the weak calibration direction?

Compare two sealed fits from the same opened ESA development flight: the
rotating-globe fit using the first 400 receiver reports and the fit using the
first 600. Analyze both declared IMU error laws. Verify that the 400 reports
are an exact prefix of the 600, and that source identity, parent, recipe,
candidate model, starting point and declared error-law parameters match.

Recompute each saved whitened training Jacobian's singular values and weakest
right singular vector. Also project the Z gyro-bias column and vertical
accelerometer-bias column against all other nuisance columns. Their residual
column norms measure local sensitivity conditional on those other columns;
their squares measure local information under the declared whitened model.
Compare absolute singular values, their ratios, conditional information, weak
loadings and fitted boundary positions at the two endpoints.
Within the 600-report fit, separately compare its first 400 whitened training
Jacobian rows with all 600 at the *same fitted parameters*. This isolates
the effect of added rows from the change in fitted parameter values. The
state-space whitening is sequential, so the first 400 rows represent the
earlier innovation prefix under that one fixed operator.
Describe GNSS-only ground course, speed and height over the first 400 reports
and added 200 reports, without treating course as aircraft heading.

This is read-only and uses zero new fits or reserved flight groups. Both fits
use overlapping observations and locally different fitted parameters, so the
two results are not independent evidence or a calibrated forecast test. Keep
the scientific decision at abstain.
