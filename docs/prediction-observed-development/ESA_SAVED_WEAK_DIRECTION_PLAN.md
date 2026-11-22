# Existing ESA fit: saved weak-direction comparison

Question: Does the Z-axis gyro-bias weakness found in the generated
three-model study also appear in the already opened ESA development fit?

Read the sealed 24-task ESA 400/120 development matrix. Count all tasks and
retain nonconverged statuses. For each converged fit, independently recompute
the singular-value decomposition of its saved whitened training Jacobian and
check it against the saved singular values. Report the weakest direction's
three largest absolute parameter loadings, its weakest/strongest singular
ratio, and near-bound calibration flags. Group summaries by candidate model
and processing profile. Compare descriptions with the sealed generated audit.

This is a local, in-sample calibration diagnostic from one opened ESA flight.
It does not prove a device defect, validate forecast uncertainty or make a new
Earth-model decision. It performs zero new fits and opens none of the seven
reserved ESA groups.
