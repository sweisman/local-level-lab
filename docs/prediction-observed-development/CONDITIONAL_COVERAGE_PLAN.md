# Saved ESA conditional-error diagnostic

**Question.** Do the sealed conditional covariance values have roughly the
same scale as the later receiver errors on development recording 187?

Read only the completed conditional-forecast study and its already opened
400 later receiver reports. Verify the study manifest, completion, saved
forecast shape, and the original scoring-input hash. Do not fit, propagate,
change the error law, open a reserved group, or set a decision threshold.

For each north/east/up component, report the later receiver-minus-forecast
error divided by the saved marginal standard deviation: mean, RMS, fraction
inside a nominal 95% interval, and lag-one correlation. Also report the
fraction inside the nominal 95% three-component covariance ellipsoid and
the range of predicted marginal standard deviations in metres. Validate
each covariance as symmetric positive definite. Use the same local receiver
metric as the existing scoring report.

These 400 reports are correlated and from one recording. The parameters were
fitted earlier and their uncertainty is omitted from the saved covariance.
The percentages are a **diagnostic**, not a calibrated coverage claim or
an Earth-model result. The scientific decision remains abstain.
